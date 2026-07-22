import logging
from pathlib import Path

import numpy as np
import yaml

from app.config import THRESHOLDS_PATH, REPORT_TEMPLATES_PATH
from app.models.schemas import (
    MetricResult, SegmentReport, AnalysisReport, VideoInfo, TypeStatistics,
)

logger = logging.getLogger(__name__)


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ReportGenerator:
    """Map computed metrics to scores and human-readable feedback."""

    def __init__(self):
        self.thresholds = _load_yaml(THRESHOLDS_PATH)["metrics"]
        self.texts = _load_yaml(REPORT_TEMPLATES_PATH)["metrics"]
        logger.info("ReportGenerator loaded %d metric configs", len(self.thresholds))

    def _score_metric(self, metric_name: str, abs_diff: float) -> tuple[float, str]:
        """Return (score, level) for a single metric."""
        cfg = self.thresholds.get(metric_name)
        if cfg is None:
            return 50.0, "fair"

        for level, limits in cfg.items():
            lo = limits.get("min", -1e9)
            hi = limits.get("max", 1e9)
            lo2 = limits.get("min2", None)
            hi2 = limits.get("max2", None)

            if lo <= abs_diff <= hi:
                return float(limits["score"]), level
            if lo2 is not None and hi2 is not None and lo2 <= abs_diff <= hi2:
                return float(limits["score"]), level

        return 50.0, "fair"

    def _get_feedback(self, metric_name: str, level: str) -> tuple[str, str]:
        """Return (problem, suggestion) text."""
        texts = self.texts.get(metric_name, {}).get(level, {})
        return texts.get("problem", ""), texts.get("suggestion", "")

    def generate(self, video_info: VideoInfo,
                 segment_data: list[dict]) -> AnalysisReport:
        """Build the full report from processed segment data.

        segment_data: list of dicts with keys:
            start_ms, end_ms, action_type, template_source,
            similarity_score, metrics (dict from comparator.compute_metrics)
        """
        segment_reports: list[SegmentReport] = []
        all_scores = []

        for seg in segment_data:
            metrics_list: list[MetricResult] = []
            metric_scores = []
            for name, vals in seg["metrics"].items():
                score, level = self._score_metric(name, vals["diff"])
                problem, suggestion = self._get_feedback(name, level)
                metrics_list.append(MetricResult(
                    name=name,
                    user_value=vals["user"],
                    template_value=vals["template"],
                    diff=vals["diff"],
                    score=score,
                    level=level,
                    problem=problem,
                    suggestion=suggestion,
                ))
                metric_scores.append(score)

            sim_score = seg.get("similarity_score", 0)
            # Combine DTW (60%) + metrics average (40%) for segment score
            avg_metric = float(np.mean(metric_scores)) if metric_scores else 0
            seg_score = round(sim_score * 0.8 + avg_metric * 0.2, 1)
            all_scores.append(seg_score)

            segment_reports.append(SegmentReport(
                start_ms=seg["start_ms"],
                end_ms=seg["end_ms"],
                action_type=seg["action_type"],
                template_source=seg.get("template_source", "ma_long"),
                similarity_score=seg_score,
                user_video_url=seg.get("user_video_url", ""),
                template_video_url=seg.get("template_video_url", ""),
                metrics=metrics_list,
            ))

        overall = round(float(np.mean(all_scores)), 1) if all_scores else 0.0
        by_type: dict[str, int] = {}
        for seg in segment_reports:
            by_type[seg.action_type] = by_type.get(seg.action_type, 0) + 1

        return AnalysisReport(
            video_info=video_info,
            overall_score=overall,
            action_segments=segment_reports,
            statistics=TypeStatistics(
                total_segments=len(segment_reports),
                by_type=by_type,
            ),
        )
