"""
异步分析任务管理器

管理多个分析任务的创建、进度跟踪、结果查询和历史记录。
"""

import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from app.models.schemas import AnalysisReport
from app.services.pipeline import AnalysisPipeline
from app.config import TEMP_DIR

logger = logging.getLogger(__name__)

# Progress step labels (Chinese)
STEP_LABELS = {
    "preprocessing": "视频预处理中...",
    "detecting": "时序动作检测中...",
    "extracting": "骨骼关键点提取中...",
    "comparing_elbow_angle": "肘关节夹角分析对比中...",
    "comparing_racket_height": "引拍高度分析对比中...",
    "comparing_hip_rotation": "转腰髋偏移分析对比中...",
    "comparing_cog_fluctuation": "重心起伏分析对比中...",
    "comparing_swing_range": "挥拍轨迹范围分析对比中...",
    "generating": "报告生成中...",
    "done": "分析完成",
    "error": "分析出错",
}


def _metric_step(metric_name: str) -> str:
    return f"comparing_{metric_name}"


class ProgressTracker:
    """Tracks progress of a single analysis task."""

    def __init__(self):
        self.step: str = "queued"
        self.message: str = "等待处理..."
        self._lock = threading.Lock()

    def update(self, step: str, message: Optional[str] = None):
        with self._lock:
            self.step = step
            self.message = message or STEP_LABELS.get(step, step)

    def get_progress(self) -> dict:
        with self._lock:
            return {"step": self.step, "message": self.message}


_HISTORY_FILE = TEMP_DIR / "analysis_history.json"


def _load_history() -> list[dict]:
    try:
        if _HISTORY_FILE.exists():
            return json.loads(_HISTORY_FILE.read_text("utf-8"))
    except Exception:
        pass
    return []


def _save_history(entries: list[dict]):
    try:
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _HISTORY_FILE.write_text(json.dumps(entries, ensure_ascii=False), "utf-8")
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to save history: %s", e)


class AnalysisManager:
    """Manages async analysis tasks with history."""

    def __init__(self):
        self._tasks: dict[str, dict] = {}
        self._pipeline = AnalysisPipeline()
        # Restore persisted history
        for entry in _load_history():
            result = self._load_result(entry["id"])
            self._tasks[entry["id"]] = {
                "id": entry["id"],
                "user_id": entry.get("user_id"),
                "action_type": entry["action_type"],
                "status": "done",
                "progress": None,
                "result": result,
                "error": None,
                "created_at": entry["created_at"],
                "_summary": entry if result is None else None,
            }

    def create_task(self, video_path: str, action_type: str, user_id: str) -> str:
        """Create a new analysis task and start background processing."""
        task_id = uuid.uuid4().hex[:8]
        tracker = ProgressTracker()

        self._tasks[task_id] = {
            "id": task_id,
            "user_id": user_id,
            "action_type": action_type,
            "status": "queued",
            "progress": tracker,
            "result": None,
            "error": None,
            "created_at": time.time(),
        }

        thread = threading.Thread(
            target=self._run,
            args=(task_id, video_path, action_type, tracker),
            daemon=True,
        )
        thread.start()
        logger.info("Analysis task %s created for %s", task_id, video_path)
        return task_id

    def _run(self, task_id: str, video_path: str,
             action_type: str, tracker: ProgressTracker):
        """Run analysis in background thread."""
        task = self._tasks[task_id]
        try:
            result = self._pipeline.run(video_path, action_type, tracker)
            task["status"] = "done"
            task["result"] = result
            tracker.update("done")
            # Persist full result and history
            self._save_result(task_id, result)
            self._persist_history()
        except Exception as e:
            logger.exception("Task %s failed", task_id)
            task["status"] = "error"
            task["error"] = str(e)
            tracker.update("error", str(e))
        finally:
            # Clean up uploaded video file
            Path(video_path).unlink(missing_ok=True)

    def _save_result(self, task_id: str, report: "AnalysisReport"):
        """Save full result JSON to disk."""
        try:
            path = TEMP_DIR / f"result_{task_id}.json"
            path.write_text(report.model_dump_json(), "utf-8")
        except Exception as e:
            logger.warning("Failed to save result for %s: %s", task_id, e)

    def _load_result(self, task_id: str) -> Optional[dict]:
        """Load full result JSON from disk."""
        try:
            path = TEMP_DIR / f"result_{task_id}.json"
            if path.exists():
                return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
        return None

    def _persist_history(self):
        """Write completed analyses to disk."""
        entries = []
        for t in self._tasks.values():
            if t["status"] == "done" and t.get("result") is not None:
                r = t["result"]
                score = r["overall_score"] if isinstance(r, dict) else r.overall_score
                segs = r["statistics"]["total_segments"] if isinstance(r, dict) else r.statistics.total_segments
                entries.append({
                    "id": t["id"],
                    "user_id": t.get("user_id"),
                    "action_type": t["action_type"],
                    "overall_score": score,
                    "total_segments": segs,
                    "created_at": t["created_at"],
                })
        entries.sort(key=lambda x: x["created_at"], reverse=True)
        _save_history(entries)

    def get_task(self, task_id: str, user_id: str) -> Optional[dict]:
        """Get task info by ID, only if it belongs to the user."""
        task = self._tasks.get(task_id)
        if task is None or task.get("user_id") != user_id:
            return None

        # Handle in-memory tasks with active progress tracker
        if task.get("progress") and hasattr(task["progress"], "get_progress"):
            progress = task["progress"].get_progress()
            return {
                "id": task["id"],
                "action_type": task["action_type"],
                "status": task["status"],
                "progress": progress["message"],
                "result": task["result"].model_dump() if task["result"] else None,
                "error": task["error"],
                "created_at": task["created_at"],
            }

        # Handle persisted/completed tasks
        if task.get("result"):
            r = task["result"]
            if hasattr(r, "model_dump"):
                r = r.model_dump()
            return {
                "id": task["id"],
                "action_type": task["action_type"],
                "status": "done",
                "progress": "分析完成",
                "result": r,
                "error": None,
                "created_at": task["created_at"],
            }

        # Summary-only fallback
        return {
            "id": task["id"],
            "action_type": task["action_type"],
            "status": "done",
            "progress": "分析完成",
            "result": None,
            "error": None,
            "created_at": task["created_at"],
        }

    def get_history(self, user_id: str, limit: int = 20) -> list[dict]:
        """Get completed analysis history for a user."""
        entries = []
        for t in self._tasks.values():
            if t["status"] == "done" and t.get("user_id") == user_id:
                r = t.get("result")
                if r is not None:
                    score = r["overall_score"] if isinstance(r, dict) else r.overall_score
                    segs = r["statistics"]["total_segments"] if isinstance(r, dict) else r.statistics.total_segments
                    entries.append({
                        "id": t["id"],
                        "action_type": t["action_type"],
                        "overall_score": score,
                        "total_segments": segs,
                        "created_at": t["created_at"],
                    })
                elif t.get("_summary"):
                    entries.append(t["_summary"])
        entries.sort(key=lambda x: x["created_at"], reverse=True)
        return entries[:limit]

    def clear_history(self, user_id: str):
        """Clear completed tasks and persisted history for a user."""
        for t in list(self._tasks.values()):
            if t["status"] == "done" and t.get("user_id") == user_id:
                (TEMP_DIR / f"result_{t['id']}.json").unlink(missing_ok=True)
                del self._tasks[t["id"]]
        self._persist_history()
        logger.info("Analysis history cleared for user %s", user_id)
