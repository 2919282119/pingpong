"""
离线生成标准动作骨骼模板。

用法：
    python scripts/generate_templates.py

输入：4 段专业运动员标准动作视频，放在 scripts/input_videos/ 目录下
    - fore_topspin.mp4      # 马龙正手拉上旋
    - back_topspin.mp4      # 马龙反手拉上旋
    - fore_underspin.mp4    # 樊振东正手起下旋
    - back_underspin.mp4    # 樊振东反手起下旋

输出：app/templates/ 目录下 4 个 .npy 文件
"""

import logging
import sys
from pathlib import Path

import numpy as np
import mediapipe as mp

# ---- config ----
INPUT_DIR = Path(__file__).resolve().parent / "input_videos"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "templates"

TEMPLATE_CONFIGS = [
    ("fore_topspin", "fore_topspin.mp4"),
    ("back_topspin", "back_topspin.mp4"),
    ("fore_underspin", "fore_underspin.mp4"),
    ("back_underspin", "back_underspin.mp4"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("generate_templates")


def extract_keypoints(video_path: str) -> np.ndarray:
    """Extract MediaPipe Pose keypoints from video, return (N, 33, 4)."""
    import cv2

    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open: {video_path}")

    landmarks = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        if results.pose_landmarks:
            pts = np.array([
                [lm.x, lm.y, lm.z, lm.visibility]
                for lm in results.pose_landmarks.landmark
            ], dtype=np.float32)
        else:
            pts = np.full((33, 4), np.nan, dtype=np.float32)
        landmarks.append(pts)

    cap.release()
    pose.close()

    keypoints = np.stack(landmarks, axis=0)

    # Interpolate NaN frames
    for i in range(33):
        for d in range(4):
            col = keypoints[:, i, d]
            mask = np.isnan(col)
            if mask.all():
                col[:] = 0.0
            elif mask.any():
                idx = np.where(~mask)[0]
                col[mask] = np.interp(np.where(mask)[0], idx, col[idx])

    return keypoints


def normalize_template(keypoints: np.ndarray) -> np.ndarray:
    """Center keypoints relative to hip center and normalize scale."""
    hip_center = (
        keypoints[:, [23, 24], :2].mean(axis=1, keepdims=True)
    )
    keypoints[:, :, :2] -= hip_center

    # Scale by torso height (nose-hip distance)
    nose = keypoints[:, 0, :2]
    hip = keypoints[:, 23, :2]
    torso = np.linalg.norm(nose - hip, axis=1, keepdims=True)
    torso = np.clip(torso, 1e-6, None)
    keypoints[:, :, :2] /= torso.mean()

    return keypoints


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, filename in TEMPLATE_CONFIGS:
        input_path = INPUT_DIR / filename
        if not input_path.exists():
            logger.warning("Skipping %s: file not found at %s", name, input_path)
            continue

        logger.info("Processing %s...", name)
        kp = extract_keypoints(str(input_path))
        kp = normalize_template(kp)

        # Temporal downsampling: keep ~30 frames per template
        target_len = 30
        if len(kp) > target_len:
            indices = np.linspace(0, len(kp) - 1, target_len, dtype=int)
            kp = kp[indices]

        out_path = OUTPUT_DIR / f"template_{name}.npy"
        np.save(str(out_path), kp)
        logger.info("  Saved %s: %d frames -> %s", name, len(kp), out_path)

    logger.info("Done. %d/%d templates generated.", sum(
        1 for _, fn in TEMPLATE_CONFIGS if (INPUT_DIR / fn).exists()
    ), len(TEMPLATE_CONFIGS))


if __name__ == "__main__":
    main()
