#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频转文字再生成对应图片的连接脚本

此脚本将：
1. 使用 audio_processor.py 将音频转录为文本
2. 提取关键词或使用整个句子作为关键词
3. 使用 image_generator.py 根据关键词生成图片
"""

import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径，确保可以正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加详细的调试输出
def debug_print(message):
    """调试打印函数"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] DEBUG: {message}")

# 导入模块时添加错误处理
try:
    from utils.audio_processor import AudioProcessor
    debug_print("成功导入 AudioProcessor")
except Exception as e:
    print(f"警告：导入 AudioProcessor 失败: {e}")
    print(traceback.format_exc())
    raise

try:
    from utils.image_generator import create_images_for_sentences, generate_image
    debug_print("成功导入 image_generator 函数")
except Exception as e:
    print(f"警告：导入 image_generator 函数失败: {e}")
    print(traceback.format_exc())
    raise

def audio_to_images_pipeline(audio_path, style="艺术风格", max_images=8, extract_keywords=True):
    """
    音频转图片的完整流程
    
    参数:
        audio_path: 音频文件路径
        style: 生成图片的风格
        max_images: 最大生成图片数量
        extract_keywords: 是否提取关键词（否则使用完整句子）
    
    返回:
        生成的图片路径列表
    """
    try:
        print(f"\n{'='*50}")
        print(f"开始音频到图片的处理流程...")
        
        # 检查音频文件是否存在
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        print(f"音频文件: {audio_path}")
        debug_print(f"音频文件大小: {os.path.getsize(audio_path) / 1024:.2f} KB")
        
        # 1. 初始化音频处理器并转录音频
        print("初始化音频处理器...")
        processor = AudioProcessor("base")  # 可以根据需要使用更大的模型如 "small" 或 "medium"
        
        # 2. 转录音频
        print("开始转录音频...")
        transcript = processor.transcribe_audio(audio_path)
        
        # 检查转录结果
        if not transcript or not transcript.strip():
            print("警告：转录结果为空或只有空白字符")
            # 添加默认关键词作为备用
            default_keywords = ["音乐", "艺术", "自然", "风景", "创意"]
            print(f"使用默认关键词: {default_keywords}")
            return generate_default_images(default_keywords, style, max_images)
        
        print(f"转录文本长度: {len(transcript)} 字符")
        print(f"转录文本: {transcript[:150]}...")
        
        # 3. 分割句子
        print("分割句子...")
        try:
            _lang = 'english' if any(ch.isascii() and ch.isalpha() for ch in transcript) else 'chinese'
            sentences = processor.split_into_sentences(transcript, language=_lang)
            print(f"分割得到 {len(sentences)} 个句子")
            
            # 检查句子分割结果
            if not sentences:
                print("警告：句子分割结果为空")
                # 添加默认句子作为备用
                sentences = [transcript[:50]] if len(transcript) > 50 else [transcript]
                print(f"使用简化句子: {sentences}")
            
            # 打印所有句子
            for i, sent in enumerate(sentences, 1):
                print(f"句子 {i}: '{sent}'")
        except Exception as e:
            print(f"警告：句子分割失败: {e}")
            # 使用默认关键词作为备用
            sentences = [transcript[:50]] if len(transcript) > 50 else [transcript]
            print(f"使用简化句子: {sentences}")
        
        # 4. 提取关键词或使用完整句子
        print("处理文本内容...")
        try:
            keywords = []
            if extract_keywords:
                print("提取关键词...")
                for sentence in sentences:
                    # 检查句子长度
                    if len(sentence) < 5:
                        print(f"跳过太短的句子: {sentence}")
                        continue
                    
                    # 简单处理：取句子前10个字符作为关键词
                    keyword = sentence[:10].strip()
                    # 确保关键词不为空
                    if not keyword:
                        keyword = "音乐"
                    keywords.append(keyword)
                    print(f"关键词: '{keyword}'")
            else:
                # 过滤短句子
                keywords = [s for s in sentences if len(s) >= 5]
                print(f"使用完整句子作为关键词，共 {len(keywords)} 个")
            
            # 限制关键词数量并填充
            keywords = keywords[:max_images]
            if len(keywords) < max_images:
                _fill = ["音乐","艺术","自然","风景","创意"]
                i = 0
                while len(keywords) < max_images:
                    keywords.append(_fill[i % len(_fill)])
                    i += 1
            
            # 5. 保存转录结果和关键词
            print("保存转录结果和关键词...")
            output_dir = Path("output/transcribed")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_name = os.path.splitext(os.path.basename(audio_path))[0]
            
            # 保存转录文本
            transcript_file = output_dir / f"{audio_name}_{timestamp}_transcript.txt"
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"转录结果已保存到: {transcript_file}")
            
            # 保存句子和关键词
            keywords_file = output_dir / f"{audio_name}_{timestamp}_keywords.txt"
            with open(keywords_file, "w", encoding="utf-8") as f:
                for i, (sentence, keyword) in enumerate(zip(sentences[:len(keywords)], keywords), 1):
                    f.write(f"句子 {i}: {sentence}\n")
                    f.write(f"关键词 {i}: {keyword}\n\n")
            print(f"关键词已保存到: {keywords_file}")
            
            # 6. 生成图片
            print(f"开始生成图片，风格: {style}，最大数量: {max_images}")
            debug_print(f"使用的关键词列表: {keywords[:max_images]}")
            
            # 使用批量生成图片函数
            image_paths = create_images_for_sentences(keywords[:max_images], style, max_images)
            
            # 检查是否成功生成图片
            if not image_paths:
                print("警告：未能生成任何图片，尝试使用默认关键词")
                # 使用默认关键词作为备用
                default_keywords = ["音乐", "艺术", "自然", "风景", "创意"]
                image_paths = create_images_for_sentences(default_keywords[:max_images], style, max_images)
            
            print(f"\n图片生成完成!")
            print(f"总共成功生成 {len(image_paths)} 张图片")
            for path in image_paths:
                print(f"- {path}")
            
            return image_paths
        except Exception as e:
            print(f"错误：生成图片过程中发生错误: {e}")
            # 尝试使用默认图片生成
            print("尝试使用默认关键词生成图片...")
            default_keywords = ["音乐", "艺术", "自然", "风景", "创意"]
            image_paths = create_images_for_sentences(default_keywords[:max_images], style, max_images)
            return image_paths
        
    except Exception as e:
        print(f"❌ 处理流程出错: {e}")
        print("详细错误信息:")
        print(traceback.format_exc())
        
        # 即使出错也要尝试生成默认图片
        print("尝试使用默认关键词生成图片...")
        return generate_default_images(["音乐", "艺术", "抽象", "创意"], style, min(4, max_images))

def generate_default_images(keywords, style, max_images):
    """使用默认关键词生成图片"""
    image_paths = []
    for i, keyword in enumerate(keywords[:max_images], 1):
        try:
            prompt = f"{keyword}，{style}，高清，8K"
            print(f"尝试生成默认图片 {i}: '{prompt}'")
            image_path = generate_image(prompt)
            # 保存图片路径，只添加成功生成的图片
            if image_path:
                image_paths.append(image_path)
        except Exception as e:
            print(f"生成默认图片失败: {e}")
    return image_paths

if __name__ == "__main__":
    # 示例用法
    import argparse
    
    # 确保必要的目录存在
    print("检查必要的目录...")
    Path("output/images").mkdir(parents=True, exist_ok=True)
    Path("output/transcribed").mkdir(parents=True, exist_ok=True)
    print("目录检查完成")
    
    parser = argparse.ArgumentParser(description='音频转文字再生成图片的工具')
    parser.add_argument('--audio', required=True, help='音频文件路径')
    parser.add_argument('--style', default='艺术风格', help='生成图片的风格')
    parser.add_argument('--max-images', type=int, default=8, help='最大生成图片数量')
    parser.add_argument('--full-sentences', action='store_true', help='使用完整句子而不是提取关键词')
    parser.add_argument('--model', default='base', help='Whisper模型大小: tiny, base, small, medium, large')
    parser.add_argument('--debug', action='store_true', help='启用调试输出')
    
    args = parser.parse_args()
    
    # 设置调试模式
    global _debug_enabled
    _debug_enabled = args.debug
    
    print(f"\n开始处理音频文件: {args.audio}")
    print(f"使用Whisper模型: {args.model}")
    print(f"图片风格: {args.style}")
    print(f"最大图片数量: {args.max_images}")
    print(f"使用{'完整句子' if args.full_sentences else '关键词'}生成图片")
    
    try:
        image_paths = audio_to_images_pipeline(
            audio_path=args.audio,
            style=args.style,
            max_images=args.max_images,
            extract_keywords=not args.full_sentences
        )
        
        if image_paths:
            print("\n🎉 流程执行成功！")
            print(f"总共生成了 {len(image_paths)} 张图片")
            print(f"图片保存在: output/images/")
            print("\n提示：您可以使用以下命令查看生成的图片:")
            print(f"  explorer.exe output/images/")
        else:
            print("\n❌ 未能生成任何图片")
            print("请检查错误信息并尝试解决问题")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("详细错误信息:")
        print(traceback.format_exc())
        print("\n建议解决方法:")
        print("1. 检查音频文件路径是否正确")
        print("2. 确保有足够的磁盘空间")
        print("3. 检查网络连接是否正常")
        print("4. 尝试使用更大的Whisper模型 (--model small/medium)")
        sys.exit(1)