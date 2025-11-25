#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频到视频的完整处理流程

此脚本将：
1. 使用 audio_to_images.py 将音频转录为文本并生成对应图片
2. 使用 video_creator.py 将生成的图片转换为视频
3. 可选：添加文字叠加到视频
"""

import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def debug_print(message):
    """调试打印函数"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] DEBUG: {message}")

# 导入必要的模块
try:
    from audio_to_images import audio_to_images_pipeline
    debug_print("成功导入 audio_to_images_pipeline")
except Exception as e:
    print(f"警告：导入 audio_to_images_pipeline 失败: {e}")
    print(traceback.format_exc())
    raise

try:
    from utils.video_creator import VideoCreator
    debug_print("成功导入 VideoCreator")
except Exception as e:
    print(f"警告：导入 VideoCreator 失败: {e}")
    print(traceback.format_exc())
    raise

def audio_to_video_pipeline(audio_path, style="艺术风格", max_images=8, 
                          extract_keywords=True, output_filename=None, 
                          duration_per_image=None, add_text_overlay=False, 
                          transition_duration=1.0, target_resolution=None,
                          use_beat_sync=False):
    """
    音频到视频的完整处理流程
    
    参数:
        audio_path: 音频文件路径
        style: 生成图片的风格
        max_images: 最大生成图片数量
        extract_keywords: 是否提取关键词（否则使用完整句子）
        output_filename: 输出视频文件名
        duration_per_image: 每张图像显示时长（秒），设置为"auto"时自动计算
        add_text_overlay: 是否添加文字叠加
        transition_duration: 转场动画时长（秒）
        target_resolution: 视频目标分辨率，如(1920, 1080)
        use_beat_sync: 是否根据音乐节奏切换图片
    
    返回:
        生成的视频路径
    """
    try:
        print(f"\n{'='*60}")
        print(f"开始音频到视频的完整处理流程...")
        print(f"{'='*60}")
        
        # 1. 首先使用 audio_to_images_pipeline 生成图片
        print("\n📋 第一步：从音频生成图片")
        image_paths = audio_to_images_pipeline(
            audio_path=audio_path,
            style=style,
            max_images=max_images,
            extract_keywords=extract_keywords
        )
        
        if not image_paths:
            raise ValueError("无法生成图片，视频创建失败")
        
        print(f"\n📋 第二步：将生成的图片转换为视频")
        print(f"使用 {len(image_paths)} 张图片创建视频")
        
        # 2. 创建视频
        video_creator = VideoCreator()
        
        if use_beat_sync:
            print("🎵 使用音乐节奏同步模式")
            video_path = video_creator.create_slideshow_with_beat(
                image_paths=image_paths,
                audio_path=audio_path,
                output_filename=output_filename
            )
        else:
            print("⏱️ 使用固定时长模式")
            video_path = video_creator.create_slideshow(
                image_paths=image_paths,
                audio_path=audio_path,
                output_filename=output_filename,
                duration_per_image=duration_per_image,
                transition_duration=transition_duration,
                target_resolution=target_resolution
            )
        
        if not video_path:
            raise ValueError("视频创建失败")
        
        print(f"\n✅ 视频创建成功: {video_path}")
        
        # 3. 可选：添加文字叠加
        if add_text_overlay:
            print("\n📝 第三步：添加文字叠加到视频")
            
            # 尝试从转录文件中获取文字内容
            try:
                # 获取最近的转录文件
                transcript_dir = Path("output/transcribed")
                if transcript_dir.exists():
                    # 查找与当前音频相关的最新转录文件
                    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
                    transcript_files = list(transcript_dir.glob(f"{audio_name}_*_transcript.txt"))
                    
                    if transcript_files:
                        # 按修改时间排序，获取最新的文件
                        transcript_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        latest_transcript = transcript_files[0]
                        
                        print(f"🔍 找到最近的转录文件: {latest_transcript}")
                        
                        # 读取转录内容
                        with open(latest_transcript, "r", encoding="utf-8") as f:
                            transcript = f.read()
                        
                        # 简单分割文本，为每个图片创建一个文字片段
                        # 这里使用简单的策略，实际应用可能需要更复杂的文本分割
                        words = transcript.split()
                        segment_length = max(1, len(words) // len(image_paths))
                        
                        # 生成文字列表
                        text_list = []
                        current_time = 0
                        
                        # 尝试确定每张图片的显示时长
                        if duration_per_image and duration_per_image != "auto":
                            img_duration = duration_per_image
                        else:
                            # 估算时长
                            from utils.audio_processor import AudioProcessor
                            processor = AudioProcessor("tiny")  # 使用tiny模型快速获取音频时长
                            audio_duration = processor.get_audio_duration(audio_path)
                            img_duration = audio_duration / len(image_paths)
                        
                        for i in range(len(image_paths)):
                            start_idx = i * segment_length
                            end_idx = min((i + 1) * segment_length, len(words))
                            text = " ".join(words[start_idx:end_idx])
                            
                            # 确保文本不为空
                            if not text and i < len(words):
                                text = words[i] if i < len(words) else f"图片 {i+1}"
                            elif not text:
                                text = f"图片 {i+1}"
                            
                            text_list.append({
                                'text': text,
                                'start_time': current_time,
                                'duration': img_duration
                            })
                            current_time += img_duration
                        
                        print(f"📝 准备添加 {len(text_list)} 段文字到视频")
                        
                        # 添加文字叠加
                        video_with_text = video_creator.add_text_overlay(
                            video_path=video_path,
                            text_list=text_list
                        )
                        
                        if video_with_text and video_with_text != video_path:
                            print(f"✅ 文字叠加完成: {video_with_text}")
                            video_path = video_with_text
                        else:
                            print("⚠️ 文字叠加失败或未添加新文字")
                    else:
                        print("⚠️ 未找到相关的转录文件，跳过文字叠加")
                else:
                    print("⚠️ 转录文件目录不存在，跳过文字叠加")
            except Exception as e:
                print(f"❌ 添加文字叠加时出错: {e}")
                print("将继续使用没有文字叠加的视频")
        
        print(f"\n🎉 完整流程执行成功！")
        print(f"最终生成的视频: {video_path}")
        print(f"\n您可以使用以下命令查看视频:")
        print(f"  explorer.exe {os.path.dirname(video_path)}")
        
        return video_path
        
    except Exception as e:
        print(f"\n❌ 处理流程出错: {e}")
        print("详细错误信息:")
        print(traceback.format_exc())
        return None

def main():
    """主函数，处理命令行参数"""
    import argparse
    
    # 确保必要的目录存在
    print("检查必要的目录...")
    for dir_path in ["output/images", "output/transcribed", "output/videos"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("目录检查完成")
    
    parser = argparse.ArgumentParser(description='音频转视频的完整处理工具')
    parser.add_argument('--audio', required=True, help='音频文件路径')
    parser.add_argument('--style', default='艺术风格', help='生成图片的风格')
    parser.add_argument('--max-images', type=int, default=8, help='最大生成图片数量')
    parser.add_argument('--full-sentences', action='store_true', help='使用完整句子而不是提取关键词')
    parser.add_argument('--output-filename', help='输出视频文件名')
    parser.add_argument('--duration', type=float, help='每张图像显示时长（秒）')
    parser.add_argument('--add-text', action='store_true', help='添加文字叠加')
    parser.add_argument('--transition', type=float, default=1.0, help='转场动画时长（秒）')
    parser.add_argument('--resolution', help='目标分辨率，格式如 1920x1080')
    parser.add_argument('--beat-sync', action='store_true', help='根据音乐节奏切换图片')
    
    args = parser.parse_args()
    
    # 解析分辨率参数
    target_resolution = None
    if args.resolution:
        try:
            width, height = map(int, args.resolution.split('x'))
            target_resolution = (width, height)
            print(f"设置视频分辨率: {width}x{height}")
        except ValueError:
            print(f"警告：无效的分辨率格式 {args.resolution}，将使用默认设置")
    
    print(f"\n开始处理音频文件: {args.audio}")
    print(f"图片风格: {args.style}")
    print(f"最大图片数量: {args.max_images}")
    print(f"使用{'完整句子' if args.full_sentences else '关键词'}生成图片")
    
    if args.beat_sync:
        print("启用音乐节奏同步模式")
    elif args.duration:
        print(f"每张图片显示时长: {args.duration}秒")
    
    if args.add_text:
        print("将添加文字叠加")
    
    video_path = audio_to_video_pipeline(
        audio_path=args.audio,
        style=args.style,
        max_images=args.max_images,
        extract_keywords=not args.full_sentences,
        output_filename=args.output_filename,
        duration_per_image=args.duration,
        add_text_overlay=args.add_text,
        transition_duration=args.transition,
        target_resolution=target_resolution,
        use_beat_sync=args.beat_sync
    )
    
    if video_path:
        print(f"\n✅ 所有处理已完成！")
    else:
        print(f"\n❌ 处理过程中出现错误")
        sys.exit(1)

if __name__ == "__main__":
    main()