import logging
from pathlib import Path

import numpy as np

from app import config
from app.models.schemas import AnalysisReport, VideoInfo
from app.services.video_preprocessor import preprocess_video
from app.services.mediapipe_extractor import MediaPipeExtractor
from app.services.comparator import dtw_similarity, compute_metrics
from app.services.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


def _create_bmn_detector():
    """Create BMN detector — prefers ONNX GPU over Paddle CPU."""
    if config.ONNX_MODELS_DIR.joinpath("resnet50.onnx").exists():
        logger.info("Using ONNX Runtime GPU acceleration")
        from app.services.onnx_inference import ONNXBMNDetector
        return ONNXBMNDetector()
    logger.info("Falling back to PaddlePaddle CPU inference")
    from app.services.paddle_infer import BMNDetector
    return BMNDetector()


class AnalysisPipeline:
    """Orchestrate the full video analysis pipeline."""

    def __init__(self):
        self.bmn = _create_bmn_detector()
        self.pose_extractor = MediaPipeExtractor()
        self.report_gen = ReportGenerator()

    def _template_video_url(self, action_type: str) -> str:
        """Get URL for the template video file."""
        fname = config.TEMPLATE_VIDEO_FILES.get(action_type)
        if fname is None:
            return ""
        return f"/media/templates/{fname}"

    def _load_template(self, action_type: str) -> np.ndarray | None:
        """Load skeleton template .npy for the given action type."""
        fname = config.TEMPLATE_FILES.get(action_type)
        if fname is None:
            logger.warning("No template file configured for %s", action_type)
            return None
        path = config.TEMPLATES_DIR / fname
        if not path.exists():
            logger.warning("Template file not found: %s", path)
            return None
        return np.load(str(path))

    def run(self, video_path: str, action_type: str,
            progress_tracker=None) -> AnalysisReport:
        """Run the full analysis pipeline.

        Args:
            video_path: Path to uploaded video file.
            action_type: User-selected action type.
            progress_tracker: Optional ProgressTracker for progress updates.
        """
        # 1. Preprocess
        logger.info("Step 1: Preprocessing video...")
        if progress_tracker:
            progress_tracker.update("preprocessing")
        proc_path, raw_info = preprocess_video(video_path)
        video_info = VideoInfo(
            duration_s=raw_info.duration_s,
            processed_fps=config.TARGET_FPS,
            original_width=raw_info.width,
            original_height=raw_info.height,
        )

        try:
            # 2. BMN temporal detection
            logger.info("Step 2: BMN temporal detection...")
            if progress_tracker:
                progress_tracker.update("detecting")
            segments = self.bmn.detect(proc_path, raw_info.duration_s, action_type)
            if not segments:
                logger.warning("No action segments detected")
                return AnalysisReport(
                    video_info=video_info,
                    overall_score=0.0,
                    action_segments=[],
                    statistics={"total_segments": 0, "by_type": {}},
                )

            # 3-5. Per-segment processing
            logger.info("Step 3-5: Processing %d segments...", len(segments))
            segment_data = []

            for seg in segments:
                logger.info("  Segment: [%.0f-%.0fms] %s",
                            seg.start_ms, seg.end_ms, seg.action_type)

                # Truncate video to this action segment (keep file for playback)
                if progress_tracker:
                    progress_tracker.update("extracting")
                seg_path = self._trim_segment(proc_path, seg.start_ms, seg.end_ms)
                if seg_path is None:
                    continue

                # MediaPipe keypoint extraction
                user_kp = self.pose_extractor.extract(seg_path)

                # Compare against selected template
                selected_tmpl = self._load_template(seg.action_type)
                if selected_tmpl is None:
                    continue
                n = min(len(user_kp), len(selected_tmpl))
                user_kp_aligned = user_kp[:n]
                tmpl_aligned = selected_tmpl[:n]

                if progress_tracker:
                    progress_tracker.update("comparing")
                sim_score = dtw_similarity(user_kp_aligned, tmpl_aligned)
                full_metrics = compute_metrics(user_kp_aligned, tmpl_aligned)

                metrics = {}
                metric_names = [
                    ("elbow_angle", "肘关节夹角"),
                    ("racket_height", "引拍高度"),
                    ("hip_rotation", "转腰髋偏移"),
                    ("cog_fluctuation", "重心起伏"),
                    ("swing_range", "挥拍轨迹范围"),
                    ("swing_speed", "挥拍速度"),
                ]
                for mkey, _ in metric_names:
                    if progress_tracker:
                        progress_tracker.update("comparing", f"{next(n for k,n in metric_names if k==mkey)}分析对比中...")
                    if mkey in full_metrics:
                        metrics[mkey] = full_metrics[mkey]

                segment_data.append({
                    "start_ms": seg.start_ms,
                    "end_ms": seg.end_ms,
                    "action_type": seg.action_type,
                    "template_source": "ma_long",
                    "similarity_score": sim_score,
                    "user_video_url": f"/media/segments/{Path(seg_path).name}",
                    "template_video_url": self._template_video_url(seg.action_type),
                    "metrics": metrics,
                })

            # 6. Generate report
            logger.info("Step 6: Generating report...")
            if progress_tracker:
                progress_tracker.update("generating")
            report = self.report_gen.generate(video_info, segment_data)
            logger.info("Analysis complete: overall_score=%.1f, %d segments",
                        report.overall_score, report.statistics.total_segments)
            return report

        finally:
            # Clean up preprocessed video only (keep trimmed segments for playback)
            Path(proc_path).unlink(missing_ok=True)

    @staticmethod
    def _trim_segment(video_path: str, start_ms: float,
                      end_ms: float) -> str | None:
        """Extract a sub-clip using ffmpeg."""
        import subprocess
        stem = Path(video_path).stem
        out = str(config.TEMP_DIR / f"seg_{stem}_{int(start_ms)}_{int(end_ms)}.mp4")
        duration_s = (end_ms - start_ms) / 1000.0
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_ms / 1000.0),
            "-i", video_path,
            "-t", str(duration_s),
            "-c:v", "libx264", "-preset", "fast",
            "-vsync", "vfr",
            "-an", out,
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return out
        except subprocess.CalledProcessError as e:
            logger.error("Failed to trim segment: %s", e.stderr)
            return None
