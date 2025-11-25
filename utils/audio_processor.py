import whisper
import os
from pydub import AudioSegment
import tempfile

class AudioProcessor:
    def __init__(self, model_size="base"):
        """
        初始化语音识别处理器
        model_size: "tiny", "base", "small", "medium", "large"
        """
        print(f"正在加载Whisper模型 ({model_size})...")
        self.model = whisper.load_model(model_size)
        print("Whisper模型加载完成！")
    
    def get_audio_duration(self, audio_path):
        """
        获取音频文件时长
        
        参数:
            audio_path: 音频文件路径
            
        返回:
            音频时长（秒）
        """
        try:
            # 简单使用 wave 或 librosa 获取音频时长
            if audio_path.lower().endswith('.wav'):
                import wave
                with wave.open(audio_path, 'r') as w:
                    frames = w.getnframes()
                    rate = w.getframerate()
                    duration = frames / float(rate)
                    return duration
            else:
                # 尝试使用 librosa（如果可用）
                try:
                    import librosa
                    duration = librosa.get_duration(filename=audio_path)
                    return duration
                except ImportError:
                    # 如果没有 librosa，尝试使用 pydub
                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_file(audio_path)
                        return len(audio) / 1000.0  # 转换为秒
                    except Exception:
                        # 最简单的回退方法 - 估算
                        file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
                        # 假设平均比特率为 128 kbps
                        estimated_duration = (file_size * 8 * 1024) / 128
                        return max(1, estimated_duration)  # 至少返回1秒
        except Exception as e:
            print(f"获取音频时长失败: {e}")
            return 60  # 默认返回60秒作为安全值
    
    def transcribe_audio(self, audio_path, language=None):
        """
        转录音频文件为文本
        
        参数:
            audio_path: 音频文件路径
            language: 指定语言代码，如 'zh'、'en'，默认为 None（自动检测）
        
        返回:
            转录的文本内容
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            # 如果不是 wav 格式，先转换
            if not audio_path.lower().endswith('.wav'):
                print(f"音频格式不是 wav，正在转换: {audio_path}")
                audio_path = self.convert_to_wav(audio_path)
            
            # 加载音频
            audio = whisper.load_audio(audio_path)
            # 处理长音频
            audio = whisper.pad_or_trim(audio)
            
            # 制作梅尔频谱图
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # 如果未指定语言，自动检测
            if language is None:
                _, probs = self.model.detect_language(mel)
                detected_language = max(probs, key=probs.get)
                print(f"检测到的语言: {detected_language}")
                language = detected_language
            
            # 解码音频
            options = whisper.DecodingOptions(language=language)
            result = whisper.decode(self.model, mel, options)
            
            return result.text
        except Exception as e:
            print(f"转录音频失败: {e}")
            return ""
    
    def convert_to_wav(self, audio_path):
        """
        将音频转换为WAV格式（如果需要）
        """
        if audio_path.lower().endswith('.mp3'):
            print("正在转换MP3到WAV格式...")
            audio = AudioSegment.from_mp3(audio_path)
            wav_path = audio_path.replace('.mp3', '.wav')
            audio.export(wav_path, format="wav")
            return wav_path
        return audio_path
    
    def split_into_sentences(self, text, language='chinese'):
        """
        将文本分割成句子
        """
        # 简单的分句逻辑（中文以句号、问号、感叹号分割）
        import re
        
        if language == 'chinese':
            # 中文分句
            sentences = re.split(r'[。！？!?]', text)
        else:
            # 英文分句
            sentences = re.split(r'[.!?]', text)
        
        # 过滤空字符串和空白句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        print(f"分割为 {len(sentences)} 个句子")
        return sentences

if __name__ == "__main__":
    processor = AudioProcessor("base")
    video_file = "input/audio/The_Beatles_-_Yellow_Submarine_47950273.mp3"      # 换成你的 MP4
    text = processor.transcribe_audio(video_file)   # 无需先转 WAV
    sentences = processor.split_into_sentences(text, language='chinese')
    print("整段文本：\n", text)
    print("分句结果：\n", sentences)