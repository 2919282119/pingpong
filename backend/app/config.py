import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Action types
ACTION_TYPES = ("fore_topspin", "back_topspin", "fore_underspin", "back_underspin")

# Templates (skeleton keypoints .npy)
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATE_FILES = {
    "fore_topspin": "template_fore_topspin.npy",
    "back_topspin": "template_back_topspin.npy",
    "fore_underspin": "template_fore_underspin.npy",
    "back_underspin": "template_back_underspin.npy",
}
# Template video files (for side-by-side playback)
TEMPLATE_VIDEO_FILES = {
    "fore_topspin": "fore_topspin.mp4",
    "back_topspin": "back_topspin.mp4",
    "fore_underspin": "fore_underspin.mp4",
    "back_underspin": "back_underspin.mp4",
}

# Config
CONFIG_DIR = BASE_DIR / "config"
THRESHOLDS_PATH = CONFIG_DIR / "thresholds.yaml"
REPORT_TEMPLATES_PATH = CONFIG_DIR / "report_templates.yaml"

# Video preprocessing
TARGET_FPS = 10
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720

# CUDA
CUDA_DEVICE = os.environ.get("CUDA_VISIBLE_DEVICES", "0")

# Temp files
TEMP_DIR = BASE_DIR / "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ONNX Runtime GPU models
ONNX_MODELS_DIR = BASE_DIR / "onnx_models"

# Baidu Maps API
BAIDU_MAP_AK = os.environ.get("BAIDU_MAP_AK", "BAIDU_MAP_AK_ENV_VAR")

# PaddleVideo BMN model path (configurable)
PADDLEVIDEO_BMN_MODEL = os.environ.get(
    "PP_BMN_MODEL", "/models/paddlevideo/bmn/"
)
