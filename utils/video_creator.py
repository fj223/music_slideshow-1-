import os
import sys
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, TextClip
from config import OUTPUT_VIDEOS, VIDEO_CONFIG, IMAGE_CONFIG

class VideoCreator:
    def __init__(self):
        self.output_dir = OUTPUT_VIDEOS
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_slideshow(self, image_paths, audio_path, output_filename=None, 
                        duration_per_image=None, transition_duration=1.0, 
                        target_resolution=None):
        """
        创建图像幻灯片视频
        
        参数:
            image_paths: 图像路径列表
            audio_path: 音频文件路径
            output_filename: 输出视频文件名
            duration_per_image: 每张图像显示时长（秒），设置为"auto"时自动计算
            transition_duration: 转场动画时长（秒）
            target_resolution: 视频目标分辨率，如(1920, 1080)，默认使用第一张图像的分辨率
        """
        if not image_paths:
            raise ValueError("没有提供图像路径")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 设置默认值
        if duration_per_image is None:
            duration_per_image = VIDEO_CONFIG["duration_per_image"]
        
        if output_filename is None:
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            output_filename = f"{base_name}_slideshow.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"🎬 开始创建视频幻灯片...")
        print(f"  图像数量: {len(image_paths)}")
        print(f"  音频文件: {audio_path}")
        print(f"  输出路径: {output_path}")
        
        try:
            # 1. 加载音频文件
            print("📻 加载音频文件...")
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # 2. 计算每张图像的显示时长
            if duration_per_image == "auto":
                # 自动计算：总音频时长 / 图像数量
                duration_per_image = audio_duration / len(image_paths)
                print(f"  自动计算每张图像时长: {duration_per_image:.2f}秒")
            
            # 获取目标分辨率
            if target_resolution is None:
                # 尝试从配置中获取，或者默认为None（使用原始图像尺寸）
                target_resolution = None
            
            # 3. 创建图像剪辑列表
            print("🖼️ 创建图像剪辑...")
            image_clips = []
            
            for i, image_path in enumerate(image_paths):
                if not os.path.exists(image_path):
                    print(f"⚠️ 图像文件不存在，跳过: {image_path}")
                    continue
                
                try:
                    # 创建图像剪辑
                    img_clip = ImageClip(image_path)
                    
                    # 如果指定了目标分辨率，统一调整所有图像尺寸
                    if target_resolution:
                        img_clip = img_clip.resized(target_resolution)
                    
                    # 设置显示时长
                    img_clip = img_clip.set_duration(duration_per_image)
                    
                    # 添加淡入淡出效果（首尾图像特殊处理）
                    
                    
                    image_clips.append(img_clip)
                    print(f"  ✅ 已加载图像 {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")
                    
                except Exception as e:
                    print(f"❌ 加载图像失败 {image_path}: {e}")
                    continue
            
            if not image_clips:
                raise ValueError("没有成功加载任何图像")
            
            # 4. 合并图像剪辑
            print("🔗 合并图像剪辑...")
            video_clip = concatenate_videoclips(image_clips, method="compose")
            
            # 5. 设置音频
            print("🎵 设置音频...")
            
            # 如果视频时长超过音频时长，截断视频
            if video_clip.duration > audio_duration:
                print(f"⚠️ 视频时长({video_clip.duration:.2f}s)超过音频时长({audio_duration:.2f}s)，将截断视频")
                video_clip = video_clip.subclip(0, audio_duration)
            
            # 如果音频时长超过视频时长，截断音频
            audio_clip = audio_clip.subclip(0, video_clip.duration)
            
            # 设置音频到视频
            video_clip = video_clip.set_audio(audio_clip)
            
            # 6. 写入视频文件
            print("💾 写入视频文件...")
            video_clip.write_videofile(
                output_path,
                fps=VIDEO_CONFIG["fps"],
                codec='libx264',
                audio_codec='aac'
            )
            
            # 7. 清理资源
            for clip in [video_clip, audio_clip] + image_clips:
                try:
                    clip.close()
                except Exception:
                    pass  # 忽略清理过程中的错误
            
            print(f"✅ 视频创建成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 视频创建失败: {e}")
            # 确保清理资源
            try:
                audio_clip.close()
            except:
                pass
            
            # 清理其他可能已创建的资源
            try:
                for clip in image_clips:
                    clip.close()
            except:
                pass
                
            return None
    
    def create_slideshow_with_beat(self, image_paths, audio_path, output_filename=None):
        """
        创建根据音乐节奏切换的图像幻灯片
        
        尝试使用 librosa 进行音频节奏分析，如果不可用则回退到固定时长
        """
        print("🎵 正在分析音频节奏...")
        
        try:
            # 尝试导入 librosa 进行节奏分析
            import librosa
            import numpy as np
            
            # 加载音频并分析节拍
            y, sr = librosa.load(audio_path)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            
            # 转换节拍时间戳为秒
            beat_times = librosa.frames_to_time(beats, sr=sr)
            
            # 计算平均节拍间隔作为图像切换时间
            if len(beat_times) > 1:
                avg_beat_interval = np.mean(np.diff(beat_times))
                # 确保时间合理（不小于1秒，不大于8秒）
                duration_per_image = max(1.0, min(8.0, avg_beat_interval * 2))  # 每两拍切换一次
                print(f"  检测到节奏: {tempo:.1f} BPM")
                print(f"  计算每张图像显示时长: {duration_per_image:.2f}秒")
            else:
                # 如果无法检测到足够的节拍，使用默认值
                duration_per_image = 4.0
                print("  无法检测到足够的节拍信息，使用默认时长")
                
        except ImportError:
            # 如果 librosa 不可用，使用固定时长
            print("  librosa 库未安装，使用固定时长")
            duration_per_image = 4.0
        except Exception as e:
            # 处理其他可能的异常
            print(f"  节奏分析失败: {e}，使用固定时长")
            duration_per_image = 4.0
        
        return self.create_slideshow(
            image_paths, 
            audio_path, 
            output_filename,
            duration_per_image=duration_per_image
        )
    
    def add_text_overlay(self, video_path, text_list, output_filename=None):
        """
        为视频添加文字叠加
        
        参数:
            video_path: 原始视频路径
            text_list: 文字列表，每个元素包含 {'text': '文字内容', 'start_time': 开始时间, 'duration': 持续时间}
            output_filename: 输出视频文件名
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if not text_list:
            print("⚠️ 没有提供文字内容，跳过文字叠加")
            return video_path
        
        # 设置输出文件名
        if output_filename is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_filename = f"{base_name}_with_text.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"📝 开始添加文字叠加...")
        print(f"  原始视频: {video_path}")
        print(f"  文字数量: {len(text_list)}")
        print(f"  输出路径: {output_path}")
        
        try:
            # 加载视频
            video_clip = VideoFileClip(video_path)
            
            # 创建文字剪辑列表
            text_clips = []
            
            for i, text_info in enumerate(text_list):
                text = text_info.get('text', '')
                start_time = text_info.get('start_time', 0)
                duration = text_info.get('duration', video_clip.duration - start_time)
                
                # 确保时间范围有效
                if start_time >= video_clip.duration:
                    print(f"⚠️ 文字 {i+1} 的开始时间超出视频时长，跳过")
                    continue
                
                duration = min(duration, video_clip.duration - start_time)
                
                # 创建文字剪辑
                try:
                    # 尝试使用中文字体，如果失败则使用默认设置
                    try:
                        # 创建带背景的文字剪辑，更易读
                        txt_clip = TextClip(
                            text,
                            fontsize=36,
                            color='white',
                            bg_color='rgba(0,0,0,0.5)',
                            font='SimHei',
                            size=(video_clip.w - 40, None),
                            method='caption'
                        )
                    except:
                        txt_clip = TextClip(
                            text,
                            fontsize=36,
                            color='white',
                            bg_color='rgba(0,0,0,0.5)',
                            size=(video_clip.w - 40, None),
                            method='caption'
                        )
                    
                    # 设置位置和时长
                    txt_clip = txt_clip.with_position('bottom').with_start(start_time).with_duration(duration)
                    
                    text_clips.append(txt_clip)
                    print(f"  ✅ 已添加文字 {i+1}/{len(text_list)}")
                    
                except Exception as e:
                    print(f"❌ 添加文字 {i+1} 失败: {e}")
                    continue
            
            # 合并视频和文字
            if text_clips:
                video_with_text = CompositeVideoClip([video_clip] + text_clips)
                
                # 写入新视频
                print("💾 写入带文字的视频文件...")
                video_with_text.write_videofile(
                    output_path,
                    fps=video_clip.fps,
                    codec='libx264',
                    audio_codec='aac'
                )
                
                # 清理资源
                video_with_text.close()
            else:
                print("⚠️ 没有成功添加任何文字")
                output_path = video_path  # 返回原始视频路径
            
            # 清理资源
            video_clip.close()
            for clip in text_clips:
                clip.close()
            
            print(f"✅ 文字叠加完成: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 文字叠加失败: {e}")
            # 确保清理资源
            try:
                video_clip.close()
            except:
                pass
            return None

def test_video_creation():
    """测试视频创建功能"""
    print("测试视频创建功能...")
    
    # 创建一些测试图像（如果不存在）
    test_images = []
    test_image_dir = os.path.join(OUTPUT_VIDEOS, "test_images")
    os.makedirs(test_image_dir, exist_ok=True)
    
    # 使用英文文本避免编码问题，同时添加错误处理
    from PIL import Image, ImageDraw
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    
    for i in range(5):
        img_path = os.path.join(test_image_dir, f"test_{i}.jpg")
        if not os.path.exists(img_path):
            try:
                img = Image.new('RGB', (800, 600), color=colors[i % len(colors)])
                d = ImageDraw.Draw(img)
                # 使用英文文本避免编码问题
                d.text((100, 100), f"Test Image {i+1}", fill=(255, 255, 255))
                img.save(img_path)
                print(f"  ✅ 创建测试图像 {i+1}/5")
            except Exception as e:
                print(f"❌ 创建测试图像 {i+1}/5 失败: {e}")
        test_images.append(img_path)
    
    # 创建测试音频（一段静音）
    from pydub import AudioSegment
    test_audio_path = os.path.join(test_image_dir, "test_audio.wav")
    if not os.path.exists(test_audio_path):
        silence = AudioSegment.silent(duration=10000)  # 10秒静音
        silence.export(test_audio_path, format="wav")
    
    # 创建视频
    creator = VideoCreator()
    result = creator.create_slideshow(test_images, test_audio_path, "test_video.mp4", duration_per_image=2.0)
    
    if result:
        print(f"✅ 测试视频创建成功: {result}")
    else:
        print("❌ 测试视频创建失败")
    
    return result

if __name__ == "__main__":
    test_video_creation()