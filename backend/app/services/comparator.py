import logging

import numpy as np
from scipy.spatial import ConvexHull
from fastdtw import fastdtw

logger = logging.getLogger(__name__)

# MediaPipe Pose landmark indices (right-handed player)
L_SHOULDER = 11
R_SHOULDER = 12
R_ELBOW = 14
R_WRIST = 16
L_HIP = 23
R_HIP = 24


def normalize_keypoints(keypoints: np.ndarray) -> np.ndarray:
    """Normalize keypoints: hip-center + torso scale."""
    if keypoints.ndim != 3 or keypoints.shape[1:] != (33, 4):
        return keypoints
    result = keypoints.copy()
    hip_center = result[:, [L_HIP, R_HIP], :2].mean(axis=1, keepdims=True)
    result[:, :, :2] -= hip_center
    nose = result[:, 0, :2]  # NOSE=0
    hip = result[:, L_HIP, :2]
    torso = np.linalg.norm(nose - hip, axis=1, keepdims=True)
    torso = np.clip(torso, 1e-6, None)
    result[:, :, :2] /= torso.mean()
    return result


def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle (degrees) at point b formed by vectors a->b and c->b."""
    v1 = a - b
    v2 = c - b
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm < 1e-10:
        return 0.0
    cos = np.clip(dot / norm, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def _acceleration_features(normalized_seq: np.ndarray) -> np.ndarray:
    """Compute per-frame accelerations (second diff) of (x,y) keypoints.

    Returns (T-2, 66) array, in the same normalized space.
    """
    vel = np.diff(normalized_seq[:, :, :2], axis=0)      # (T-1, 33, 2)
    acc = np.diff(vel, axis=0)                            # (T-2, 33, 2)
    return acc.reshape(len(acc), -1)


def dtw_similarity(user_seq: np.ndarray, template_seq: np.ndarray) -> float:
    """DTW similarity combining position + acceleration comparison.

    1. Normalize both sequences to the same coordinate space.
    2. Compute position-DTW on (x,y) keypoints.
    3. Compute acceleration-DTW on second differences.
    4. Weighted combination: 60% position + 40% acceleration.
    """
    user_norm = normalize_keypoints(user_seq)
    tmpl_norm = normalize_keypoints(template_seq)

    n_u = user_norm.shape[0]
    n_t = tmpl_norm.shape[0]
    pos_u = user_norm[:, :, :2].reshape(n_u, -1)
    pos_t = tmpl_norm[:, :, :2].reshape(n_t, -1)

    # Position DTW
    pos_dist, _ = fastdtw(pos_u, pos_t, dist=2)

    # Acceleration DTW
    acc_u = _acceleration_features(user_norm)
    acc_t = _acceleration_features(tmpl_norm)
    acc_dist, _ = fastdtw(acc_u, acc_t, dist=2)

    # Normalize and combine
    pos_norm = np.sqrt(n_u + n_t) * 0.5
    acc_norm = np.sqrt(len(acc_u) + len(acc_t)) * 0.5

    pos_score = max(0.0, 100.0 - (pos_dist / max(pos_norm, 1e-10)))
    acc_score = max(0.0, 100.0 - (acc_dist / max(acc_norm, 1e-10)))

    return round(pos_score * 0.6 + acc_score * 0.4, 1)


def _arm_angles(keypoints: np.ndarray) -> np.ndarray:
    """Per-frame right arm elbow angle."""
    angles = []
    for frame in keypoints:
        a = calculate_angle(frame[R_SHOULDER, :2],
                            frame[R_ELBOW, :2],
                            frame[R_WRIST, :2])
        angles.append(a)
    return np.array(angles)


def _racket_height(keypoints: np.ndarray) -> np.ndarray:
    """Per-frame relative wrist height (wrist_y - shoulder_y)."""
    return keypoints[:, R_WRIST, 1] - keypoints[:, R_SHOULDER, 1]


def _hip_offset(keypoints: np.ndarray) -> np.ndarray:
    """Per-frame horizontal offset between hip center and shoulder center."""
    hip_cx = (keypoints[:, L_HIP, 0] + keypoints[:, R_HIP, 0]) / 2
    sh_cx = (keypoints[:, L_SHOULDER, 0] + keypoints[:, R_SHOULDER, 0]) / 2
    return np.abs(hip_cx - sh_cx)


def _cog_fluctuation(keypoints: np.ndarray) -> float:
    """Variance of hip center y-coordinate (stability)."""
    hip_cy = (keypoints[:, L_HIP, 1] + keypoints[:, R_HIP, 1]) / 2
    return float(np.var(hip_cy))


def _wrist_acceleration(keypoints: np.ndarray) -> float:
    """Maximum wrist acceleration in normalized coordinate space."""
    vel = np.diff(keypoints[:, R_WRIST, :2], axis=0)
    acc = np.diff(vel, axis=0)
    acc_mag = np.linalg.norm(acc, axis=1)
    return float(np.max(acc_mag)) if len(acc_mag) > 0 else 0.0


def _swing_range(keypoints: np.ndarray) -> float:
    """Convex hull area of wrist trajectory in normalized coords."""
    pts = keypoints[:, R_WRIST, :2]
    if len(pts) < 3:
        return 0.0
    try:
        hull = ConvexHull(pts)
        return float(hull.area)
    except Exception:
        return 0.0


def compute_metrics(user_kp: np.ndarray,
                    template_kp: np.ndarray) -> dict[str, dict]:
    """Compute all 5 comparison metrics between user and template."""
    user_angles = _arm_angles(user_kp)
    tmpl_angles = _arm_angles(template_kp)

    metrics = {
        "elbow_angle": {
            "user": float(np.max(user_angles) if len(user_angles) > 0 else 0),
            "template": float(np.max(tmpl_angles) if len(tmpl_angles) > 0 else 0),
        },
        "racket_height": {
            "user": float(np.min(_racket_height(user_kp))),
            "template": float(np.min(_racket_height(template_kp))),
        },
        "hip_rotation": {
            "user": float(np.mean(_hip_offset(user_kp))),
            "template": float(np.mean(_hip_offset(template_kp))),
        },
        "cog_fluctuation": {
            "user": _cog_fluctuation(user_kp),
            "template": _cog_fluctuation(template_kp),
        },
        "swing_range": {
            "user": _swing_range(user_kp),
            "template": _swing_range(template_kp),
        },
        "swing_speed": {
            "user": _wrist_acceleration(user_kp),
            "template": _wrist_acceleration(template_kp),
        },
    }

    for name, vals in metrics.items():
        vals["diff"] = round(abs(vals["user"] - vals["template"]), 4)

    return metrics
