# 音乐幻灯片生成器

一个将音频转换为文字，然后生成对应图片，并最终合成视频的工具。

## 安装指南

### 1. 克隆仓库
```bash
git clone <repository-url>
cd music_slideshow1
```

### 2. 安装依赖

**重要提示：请确保使用兼容的Python版本！**

推荐Python版本：3.8 - 3.10

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置API密钥

该项目使用硅基流动的API进行图像生成，需要设置API密钥。

**方法1：环境变量设置**

- **Windows**:
  ```bash
  set SILICON_API_KEY=sk-swbvirjuyutfhjkzykvziqsoeoebazzaslyiyrcgqzypngml
  ```

- **Linux/Mac**:
  ```bash
  export SILICON_API_KEY=your_actual_api_key_here
  ```

**方法2：.env文件**

1. 复制示例文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑.env文件，填入实际的API密钥：
   ```
   SILICON_API_KEY=your_actual_api_key_here
   ```

## 使用方法

### 基本用法

```bash
# 将音频转换为图片
python audio_to_images.py --audio_path input/audio.mp3 --style "艺术风格" --max_images 8

# 将音频转换为视频
python audio_to_video_pipeline.py --audio_path input/audio.mp3 --style "艺术风格" --max_images 8
```

### 主要参数说明

- `--audio_path`: 音频文件路径
- `--style`: 生成图片的风格
- `--max_images`: 最大生成图片数量
- `--extract_keywords`: 是否提取关键词

## 注意事项

1. **Python版本兼容性**：请使用Python 3.8 - 3.10版本，确保与whisper模型兼容
2. **API密钥管理**：不要在代码中硬编码API密钥，使用环境变量或.env文件
3. **依赖安装**：确保正确安装所有依赖，特别是ffmpeg（用于音频处理）
4. **错误处理**：程序现在具有更好的错误处理能力，即使API调用失败也能提供友好的错误信息

## 故障排除

### 常见问题

1. **whisper兼容性错误**：如果遇到与whisper相关的错误，请确认Python版本在3.8-3.10之间

2. **API密钥错误**：
   - 确保已正确设置SILICON_API_KEY环境变量
   - 检查API密钥是否有效
   - 确保没有将API密钥直接硬编码在代码中

3. **图片生成失败**：
   - 检查网络连接
   - 验证API密钥是否正确
   - 查看程序输出的错误信息

## 文件结构

```
music_slideshow1/
├── input/           # 输入音频文件
├── output/          # 输出目录
│   ├── images/      # 生成的图片
│   ├── videos/      # 生成的视频
│   └── transcribed/ # 转录的文本
├── utils/           # 工具模块
│   ├── audio_processor.py  # 音频处理
│   ├── image_generator.py  # 图像生成
│   └── video_creator.py    # 视频创建
├── audio_to_images.py      # 音频转图片脚本
├── audio_to_video_pipeline.py # 音频转视频完整流程
├── requirements.txt        # 项目依赖
├── .env.example           # 环境变量示例
└── README.md              # 项目说明
```