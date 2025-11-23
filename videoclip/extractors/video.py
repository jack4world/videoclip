"""
YouTube 视频下载模块
使用 yt-dlp 下载 YouTube 视频为 MP4 格式
"""
import yt_dlp
from pathlib import Path
from typing import Optional

from videoclip.extractors.base import BaseExtractor
from videoclip.utils.logger import get_logger
from videoclip.utils.file_utils import safe_filename

logger = get_logger(__name__)


class YouTubeDownloader(BaseExtractor):
    """YouTube 视频下载器"""
    
    def download(self, url: str, filename: Optional[str] = None) -> str:
        """
        下载 YouTube 视频
        
        Args:
            url: YouTube 视频 URL
            filename: 可选的自定义文件名（不含扩展名）
            
        Returns:
            下载的视频文件路径
        """
        try:
            # 先获取视频信息
            info_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'video')
            
            # 如果未指定文件名，使用视频标题
            if filename is None:
                filename = safe_filename(video_title, max_length=50)
            
            # 配置下载选项
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': str(self.output_dir / f'{filename}.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': False,
            }
            
            # 下载视频
            logger.info(f"开始下载视频: {video_title}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 查找下载的文件
            downloaded_file = self.output_dir / f"{filename}.mp4"
            if not downloaded_file.exists():
                # 尝试查找其他可能的文件名
                files = list(self.output_dir.glob(f"{filename}.*"))
                if files:
                    downloaded_file = files[0]
                else:
                    # 使用默认格式查找最新下载的文件
                    files = list(self.output_dir.glob("*.mp4"))
                    if files:
                        downloaded_file = max(files, key=lambda p: p.stat().st_mtime)
            
            if not downloaded_file.exists():
                raise FileNotFoundError(f"下载的文件未找到: {downloaded_file}")
            
            logger.info(f"视频下载完成: {downloaded_file}")
            return str(downloaded_file)
                
        except Exception as e:
            logger.error(f"下载视频时出错: {str(e)}")
            raise
    
    def extract(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        实现基类接口（对于下载器，input_path是URL）
        
        Args:
            input_path: YouTube URL
            output_path: 不使用（保留接口兼容性）
            
        Returns:
            下载的视频文件路径
        """
        return self.download(input_path)

