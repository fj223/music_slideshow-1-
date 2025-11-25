import os

# 项目路径配置
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(PROJECT_ROOT, "input")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
OUTPUT_IMAGES = os.path.join(OUTPUT_DIR, "images")
OUTPUT_VIDEOS = os.path.join(OUTPUT_DIR, "videos")
OUTPUT_TRANSCRIBED = os.path.join(OUTPUT_DIR, "transcribed")

# 创建输出目录
for directory in [INPUT_DIR, OUTPUT_IMAGES, OUTPUT_VIDEOS, OUTPUT_TRANSCRIBED]:
    os.makedirs(directory, exist_ok=True)

# Whisper配置
WHISPER_CONFIG = {
    "model_size": "base",  # tiny, base, small, medium, large
    "language": "chinese"  # 自动检测或指定语言
}

# 图像生成配置
IMAGE_CONFIG = {
    "max_images": 8,           # 最大图像数量
    "min_sentence_length": 5,   # 最小句子长度
    "image_size": "1024x1024",  # 图像尺寸
    "default_style": "艺术风格"  # 默认图像风格
}

# 视频配置
# ... 之前的配置保持不变 ...

# 视频配置
VIDEO_CONFIG = {
    "fps": 24,                  # 视频帧率
    "duration_per_image": 5,    # 每张图像显示秒数
    "output_quality": "high",   # 输出质量
    "transition_duration": 1.0, # 转场动画时长
    "default_output_format": "mp4"
}

# 国产API配置（暂时留空，后续添加）
CHINESE_API_CONFIG = {
    "baidu": {
        "api_key": "",
        "secret_key": ""
    },
    "aliyun": {
        "access_key_id": "",
        "access_key_secret": ""
    }
}