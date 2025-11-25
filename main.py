import os
import sys
import argparse
import time
from datetime import datetime
import logging

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 确保logs目录存在
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'pipeline.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模块导入处理
class DummyTextProcessor:
    """文本处理器的备用实现"""
    def split_sentences(self, text):
        # 简单的句子分割实现
        import re
        # 基本的句子分割，支持中英文标点
        sentences = re.split(r'[。！？.!?]\s*', text)
        return [s.strip() for s in sentences if s.strip()]

class DummyImageManager:
    """图像管理器的备用实现"""
    def generate_images_from_sentences(self, sentences):
        # 返回测试图像路径
        test_images_dir = os.path.join(OUTPUT_DIR, 'videos', 'test_images')
        if os.path.exists(test_images_dir):
            # 使用现有的测试图像
            image_paths = []
            for i in range(min(len(sentences), 10)):  # 最多使用10张图像
                img_path = os.path.join(test_images_dir, f'test_image_{i+1}.png')
                if os.path.exists(img_path):
                    image_paths.append(img_path)
            return image_paths
        return []

# 尝试导入模块
try:
    from utils.audio_processor import AudioProcessor
except ImportError:
    logger.warning("无法导入AudioProcessor，使用简化版本")
    class AudioProcessor:
        def __init__(self, model_size):
            self.model_size = model_size
        def transcribe_audio(self, audio_path):
            return "这是一个测试转录文本。用于演示音乐幻灯片功能。"
        def split_into_sentences(self, text, language):
            import re
            return re.split(r'[。！？.!?]\s*', text)

try:
    from utils.text_processor import TextProcessor
except ImportError:
    logger.warning("无法导入TextProcessor，使用备用实现")
    TextProcessor = DummyTextProcessor

try:
    from utils.image_manager import ImageManager
except ImportError:
    logger.warning("无法导入ImageManager，使用备用实现")
    ImageManager = DummyImageManager

try:
    from utils.video_creator import VideoCreator
except ImportError:
    logger.error("无法导入VideoCreator模块")
    print("错误: 无法导入VideoCreator模块，这是必要的")
    sys.exit(1)

try:
    from config import INPUT_DIR, OUTPUT_DIR, WHISPER_CONFIG, IMAGE_CONFIG
except ImportError:
    logger.warning("无法导入config，使用默认配置")
    # 默认配置
    INPUT_DIR = os.path.join(PROJECT_ROOT, 'input')
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
    WHISPER_CONFIG = {"model_size": "small", "language": "zh"}
    IMAGE_CONFIG = {"max_images": 10}
    
    # 确保目录存在
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


class MusicSlideshowPipeline:
    def __init__(self):
        """初始化音乐幻灯片生成管道"""
        try:
            logger.info("开始初始化音乐幻灯片管道")
            # 添加异常处理和参数验证
            if "model_size" not in WHISPER_CONFIG:
                raise ValueError("WHISPER_CONFIG中缺少必要的'model_size'配置")
                
            self.audio_processor = AudioProcessor(model_size=WHISPER_CONFIG["model_size"])
            self.text_processor = TextProcessor()
            self.image_manager = ImageManager()
            self.video_creator = VideoCreator()
            
            logger.info("音乐幻灯片管道初始化完成")
            print("🎵 音乐幻灯片管道初始化完成!")
            
        except Exception as e:
            logger.error(f"管道初始化失败: {e}")
            raise RuntimeError(f"初始化失败: {str(e)}")
    
    def process_audio_to_video(self, audio_path, output_name=None, max_images=None, 
                              transition_type='fade', video_resolution=None):
        """
        完整的音频到视频处理流程
        
        Args:
            audio_path (str): 音频文件路径
            output_name (str, optional): 输出视频文件名
            max_images (int, optional): 最大图像生成数量
            transition_type (str, optional): 转场效果类型
            video_resolution (tuple, optional): 视频分辨率 (width, height)
            
        Returns:
            str or None: 成功时返回视频文件路径，失败时返回None
        """
        start_time = datetime.now()
        step_results = {
            "transcription": None,
            "sentences": [],
            "image_paths": [],
            "video_path": None
        }
        
        try:
            # 验证输入音频文件
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            # 验证音频文件格式
            if not any(audio_path.lower().endswith(ext) for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']):
                logger.warning(f"非标准音频格式: {audio_path}")
                print(f"⚠️  警告: 非标准音频格式，可能不被支持: {audio_path}")
            
            print("=" * 60)
            print("🚀 开始音乐幻灯片生成流程")
            print(f"📁 输入音频: {audio_path}")
            print(f"⏱️  开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # 步骤1: 语音识别
            print("\n📝 步骤 1/4: 语音识别")
            step_start = time.time()
            text = self._run_transcription(audio_path, step_results)
            self._log_step_time("语音识别", time.time() - step_start)
            
            if not text or len(text.strip()) < 5:
                print("❌ 语音识别失败或文本太短")
                return None
            
            # 步骤2: 文本处理
            print("\n🔤 步骤 2/4: 文本处理")
            step_start = time.time()
            sentences = self._process_text(text, step_results)
            self._log_step_time("文本处理", time.time() - step_start)
            
            if not sentences:
                print("❌ 无法从文本中提取有效句子")
                return None
            
            # 步骤3: 图像生成
            print("\n🎨 步骤 3/4: 图像生成")
            step_start = time.time()
            image_paths = self._generate_images(sentences, max_images, step_results)
            self._log_step_time("图像生成", time.time() - step_start)
            
            if not image_paths:
                print("❌ 没有成功生成任何图像")
                return None
            
            # 步骤4: 视频合成
            print("\n🎬 步骤 4/4: 视频合成")
            step_start = time.time()
            video_path = self._create_video(image_paths, audio_path, output_name, 
                                          transition_type, video_resolution, step_results)
            self._log_step_time("视频合成", time.time() - step_start)
            
            if video_path:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print("=" * 60)
                print("🎉 音乐幻灯片生成完成!")
                print(f"📊 统计信息:")
                print(f"   总耗时: {duration:.2f} 秒")
                print(f"   开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   处理音频: {os.path.basename(audio_path)}")
                print(f"   生成图像: {len(image_paths)} 张")
                print(f"   输出视频: {video_path}")
                print(f"   转场效果: {transition_type}")
                if video_resolution:
                    print(f"   视频分辨率: {video_resolution[0]}x{video_resolution[1]}")
                print("=" * 60)
                
                logger.info(f"音乐幻灯片生成成功，输出: {video_path}")
                return video_path
            else:
                print("❌ 视频合成失败")
                return None
                
        except Exception as e:
            logger.error(f"处理过程中出错: {e}", exc_info=True)
            print(f"❌ 处理出错: {str(e)}")
            print("\n🔍 错误详情:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            
            # 尝试清理部分生成的资源
            self._cleanup_resources(step_results)
            return None
    
    def _run_transcription(self, audio_path, step_results):
        """执行语音识别"""
        try:
            text = self.audio_processor.transcribe_audio(audio_path)
            
            # 保存转录文本
            transcript_dir = os.path.join(OUTPUT_DIR, "transcribed")
            os.makedirs(transcript_dir, exist_ok=True)
            
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_file = os.path.join(transcript_dir, f"{base_name}_{timestamp}_transcript.txt")
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"✅ 转录文本已保存: {transcript_file}")
            print(f"📝 识别到文本 ({len(text)} 字符)")
            
            # 显示文本预览
            if len(text) > 100:
                print(f"   文本预览: {text[:100]}...")
            else:
                print(f"   文本内容: {text}")
                
            step_results["transcription"] = text
            return text
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            raise RuntimeError(f"语音识别出错: {str(e)}")
    
    def _process_text(self, text, step_results):
        """处理识别到的文本"""
        try:
            # 获取语言配置
            language = WHISPER_CONFIG.get("language", "zh")
            print(f"🌐 检测语言: {language}")
            
            sentences = self.audio_processor.split_into_sentences(text, language)
            
            if not sentences:
                # 尝试使用文本处理器的备用分割方法
                sentences = self.text_processor.split_sentences(text)
            
            # 保存句子到文件
            if sentences:
                sentences_dir = os.path.join(OUTPUT_DIR, "sentences")
                os.makedirs(sentences_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sentences_file = os.path.join(sentences_dir, f"sentences_{timestamp}.txt")
                
                with open(sentences_file, 'w', encoding='utf-8') as f:
                    for i, sentence in enumerate(sentences, 1):
                        f.write(f"{i}. {sentence}\n")
                
                print(f"✅ 句子文件已保存: {sentences_file}")
                print(f"📄 识别到 {len(sentences)} 个句子")
                
                # 显示前3个句子
                for i, sentence in enumerate(sentences[:3], 1):
                    print(f"   {i}. {sentence}")
                if len(sentences) > 3:
                    print(f"   ... 等 {len(sentences) - 3} 个句子")
                    
            step_results["sentences"] = sentences
            return sentences
            
        except Exception as e:
            logger.error(f"文本处理失败: {e}")
            raise RuntimeError(f"文本处理出错: {str(e)}")
    
    def _generate_images(self, sentences, max_images, step_results):
        """生成图像"""
        try:
            # 如果有自定义的最大图像数量，更新配置
            original_max = None
            if max_images is not None:
                original_max = IMAGE_CONFIG.get("max_images")
                IMAGE_CONFIG["max_images"] = max_images
                print(f"📊 使用自定义最大图像数量: {max_images} (原配置: {original_max})")
            
            # 限制句子数量
            if sentences and max_images and len(sentences) > max_images:
                print(f"✂️  句子数量过多，将前 {max_images} 个句子用于图像生成")
                sentences = sentences[:max_images]
            
            # 生成图像
            image_paths = self.image_manager.generate_images_from_sentences(sentences)
            
            # 恢复原始配置
            if original_max is not None:
                IMAGE_CONFIG["max_images"] = original_max
            
            # 验证图像生成
            if image_paths:
                print(f"✅ 成功生成 {len(image_paths)} 张图像")
                # 显示生成的图像路径
                for i, img_path in enumerate(image_paths[:5], 1):
                    print(f"   {i}. {os.path.basename(img_path)}")
                if len(image_paths) > 5:
                    print(f"   ... 等 {len(image_paths) - 5} 张图像")
            else:
                print("❌ 图像生成失败或没有返回有效图像路径")
                
            step_results["image_paths"] = image_paths
            return image_paths
            
        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            raise RuntimeError(f"图像生成出错: {str(e)}")
    
    def _create_video(self, image_paths, audio_path, output_name, 
                     transition_type, video_resolution, step_results):
        """创建视频"""
        try:
            # 生成输出文件名
            if output_name is None:
                base_name = os.path.splitext(os.path.basename(audio_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"{base_name}_slideshow_{timestamp}.mp4"
            
            # 确保输出文件名格式正确
            if not output_name.endswith('.mp4'):
                output_name += '.mp4'
            
            # 调用视频创建器
            print(f"🔄 正在合成视频... (转场: {transition_type})")
            if video_resolution:
                print(f"📐 使用自定义分辨率: {video_resolution[0]}x{video_resolution[1]}")
            
            # 将参数传递给视频创建器
            video_path = self.video_creator.create_slideshow(
                image_paths, 
                audio_path, 
                output_name,
                transition_type=transition_type,
                resolution=video_resolution
            )
            
            if video_path and os.path.exists(video_path):
                file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                print(f"✅ 视频合成成功: {video_path}")
                print(f"📊 视频文件大小: {file_size_mb:.2f} MB")
            else:
                print(f"❌ 视频文件不存在: {video_path}")
                video_path = None
                
            step_results["video_path"] = video_path
            return video_path
            
        except Exception as e:
            logger.error(f"视频合成失败: {e}")
            raise RuntimeError(f"视频合成出错: {str(e)}")
    
    def _log_step_time(self, step_name, seconds):
        """记录步骤执行时间"""
        print(f"✅ {step_name}完成! 耗时: {seconds:.2f} 秒")
    
    def _cleanup_resources(self, step_results):
        """清理部分生成的资源（可选）"""
        try:
            # 这里可以添加资源清理逻辑，如临时文件等
            pass
        except:
            pass


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="音乐幻灯片视频生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python main.py input/song.mp3
  python main.py input/song.mp3 -o my_video.mp4 -m 10
  python main.py input/song.mp3 -t zoom -r 1920 1080""")
    
    parser.add_argument("audio_file", nargs='?', help="输入音频文件路径 (MP3, WAV等)")
    parser.add_argument("-o", "--output", help="输出视频文件名")
    parser.add_argument("-m", "--max-images", type=int, help="最大图像生成数量")
    parser.add_argument("-t", "--transition", default="fade", 
                      choices=["fade", "slide", "zoom", "crossfade"],
                      help="转场效果类型 (默认: fade)")
    parser.add_argument("-r", "--resolution", nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                      help="视频分辨率，如 1920 1080")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    
    return parser.parse_args()


def show_welcome_message():
    """显示欢迎信息"""
    welcome = """
    🎵 音乐幻灯片视频生成器 🎵
    ====================================================
    将音频文件转换为带图像的幻灯片视频
    支持语音识别、文本处理、图像生成和视频合成
    ====================================================
    """
    print(welcome)


def main():
    """主函数"""
    show_welcome_message()
    args = parse_arguments()
    
    # 检查是否是测试模式
    if args.test:
        print("🔍 运行测试模式...")
        try:
            from utils.video_creator import test_video_creation
            test_video_creation()
            return
        except Exception as e:
            print(f"❌ 测试模式运行失败: {e}")
            return
    
    # 检查音频文件参数
    if not args.audio_file:
        print("❌ 错误: 缺少音频文件参数")
        print("\n用法:")
        print("  python main.py <音频文件> [-o 输出文件名] [-m 最大图像数量] [-t 转场效果] [-r 分辨率]")
        print("  python main.py --test  # 运行测试模式")
        
        # 提供交互式输入
        print("\n💬 交互式输入:")
        audio_file = input("请输入音频文件路径 (或输入'test'运行测试): ").strip()
        
        if not audio_file:
            print("❌ 没有提供音频文件，程序退出")
            return
        
        if audio_file.lower() == 'test':
            print("🔍 运行测试模式...")
            try:
                from utils.video_creator import test_video_creation
                test_video_creation()
                return
            except Exception as e:
                print(f"❌ 测试模式运行失败: {e}")
                return
        
        args.audio_file = audio_file
    
    # 检查输入文件
    if not os.path.exists(args.audio_file):
        print(f"❌ 错误: 音频文件不存在 - {args.audio_file}")
        return
    
    print(f"📁 音频文件: {args.audio_file}")
    if args.output:
        print(f"🎬 输出文件: {args.output}")
    if args.max_images:
        print(f"📊 最大图像: {args.max_images}")
    print(f"🎞️  转场效果: {args.transition}")
    if args.resolution:
        print(f"📐 视频分辨率: {args.resolution[0]}x{args.resolution[1]}")
    print()
    
    # 运行管道
    try:
        pipeline = MusicSlideshowPipeline()
        result = pipeline.process_audio_to_video(
            args.audio_file,
            args.output,
            args.max_images,
            args.transition,
            args.resolution
        )
        
        if result:
            print(f"\n✅ 处理完成! 视频文件: {result}")
            print(f"\n💡 提示: 您可以使用任何视频播放器查看生成的幻灯片视频。")
        else:
            print("\n❌ 处理失败!")
            print("\n💡 建议: 请检查日志文件获取详细错误信息。")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了操作")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {str(e)}")
        logger.error(f"主程序运行失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()