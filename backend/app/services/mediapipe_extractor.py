import logging
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

logger = logging.getLogger(__name__)

LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]

_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_lite.task"


class MediaPipeExtractor:
    """Extract 33-body-keypoint sequences from video using MediaPipe PoseLandmarker."""

    def __init__(self):
        self._detector = None

    def _lazy_init(self):
        if self._detector is not None:
            return
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"PoseLandmarker model not found at {_MODEL_PATH}"
            )
        base_options = python.BaseOptions(model_asset_path=str(_MODEL_PATH))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._detector = vision.PoseLandmarker.create_from_options(options)
        logger.info("MediaPipe PoseLandmarker initialized (model=%s)", _MODEL_PATH.name)

    def extract(self, video_path: str) -> np.ndarray:
        self._lazy_init()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        logger.info("Extracting keypoints from %d frames (%.1f fps)...", total_frames, fps)

        landmarks_list: list[np.ndarray] = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            timestamp_ms = int(frame_idx * 1000 / fps) if fps > 0 else frame_idx
            detection_result = self._detector.detect_for_video(mp_image, timestamp_ms)

            if detection_result.pose_landmarks:
                pts = np.array([
                    [lm.x, lm.y, lm.z, lm.visibility]
                    for lm in detection_result.pose_landmarks[0]
                ], dtype=np.float32)
            else:
                pts = np.full((33, 4), np.nan, dtype=np.float32)

            landmarks_list.append(pts)
            frame_idx += 1

            if frame_idx % 100 == 0:
                logger.info("  processed %d/%d frames", frame_idx, total_frames)

        cap.release()
        self.close()
        logger.info("Keypoints extracted: %d frames", len(landmarks_list))

        keypoints = np.stack(landmarks_list, axis=0)
        keypoints = self._interpolate_nans(keypoints)
        return keypoints

    @staticmethod
    def _interpolate_nans(keypoints: np.ndarray) -> np.ndarray:
        frames, n_pts, dims = keypoints.shape
        result = keypoints.copy()
        for i in range(n_pts):
            for d in range(dims):
                col = result[:, i, d]
                mask = np.isnan(col)
                if mask.all():
                    col[:] = 0.0
                elif mask.any():
                    indices = np.where(~mask)[0]
                    col[mask] = np.interp(
                        np.where(mask)[0],
                        indices,
                        col[indices],
                    )
        return result

    def close(self):
        if self._detector is not None:
            self._detector.close()
            self._detector = None
