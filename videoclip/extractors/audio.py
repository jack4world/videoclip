"""
音频提取模块
从视频文件中提取音频
"""
import ffmpeg
from pathlib import Path
from typing import Optional

from videoclip.extractors.base import BaseExtractor
from videoclip.config import get_settings
from videoclip.utils.logger import get_logger

logger = get_logger(__name__)


class AudioExtractor(BaseExtractor):
    """音频提取器"""
    
    def __init__(self, output_dir: str = "audio"):
        """
        初始化音频提取器
        
        Args:
            output_dir: 音频保存目录
        """
        super().__init__(output_dir)
        self.settings = get_settings()
    
    def extract(self, video_path: str, output_format: Optional[str] = None, output_path: Optional[str] = None) -> str:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_format: 输出音频格式（wav, mp3等），如果为None则使用配置中的默认值
            output_path: 输出文件路径（可选），如果为None则自动生成
            
        Returns:
            提取的音频文件路径
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        output_format = output_format or self.settings.audio_format
        
        if output_path is None:
            output_filename = video_path.stem + f".{output_format}"
            output_path = self.output_dir / output_filename
        else:
            output_path = Path(output_path)
        
        try:
            logger.info(f"开始提取音频: {video_path.name}")
            
            # 使用 ffmpeg 提取音频
            stream = ffmpeg.input(str(video_path))
            acodec = 'pcm_s16le' if output_format == 'wav' else 'libmp3lame'
            stream = ffmpeg.output(stream, str(output_path), acodec=acodec)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"音频提取完成: {output_path}")
            return str(output_path)
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"提取音频时出错: {error_msg}")
            raise
        except Exception as e:
            logger.error(f"提取音频时出错: {str(e)}")
            raise

