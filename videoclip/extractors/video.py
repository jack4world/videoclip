"""
YouTube 视频下载模块
使用 yt-dlp 下载 YouTube 视频为 MP4 格式，同时下载字幕
"""
import json
import yt_dlp
from pathlib import Path
from typing import Optional, Dict, Tuple, List

from videoclip.extractors.base import BaseExtractor
from videoclip.utils.logger import get_logger
from videoclip.utils.file_utils import safe_filename

logger = get_logger(__name__)


class YouTubeDownloader(BaseExtractor):
    """YouTube 视频下载器（支持同时下载字幕）"""
    
    def download(self, url: str, filename: Optional[str] = None, 
                 download_subtitles: bool = True) -> Dict[str, str]:
        """
        下载 YouTube 视频和字幕
        
        Args:
            url: YouTube 视频 URL
            filename: 可选的自定义文件名（不含扩展名）
            download_subtitles: 是否下载字幕（默认True）
            
        Returns:
            包含视频和字幕路径的字典:
            {
                'video_path': str,
                'subtitle_path': str or None,  # 字幕文件路径（如果有）
                'subtitle_lang': str or None,  # 字幕语言
            }
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
                
                # 检查可用的字幕
                available_subs = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})
                
                logger.info(f"可用字幕语言: {list(available_subs.keys())}")
                logger.info(f"自动生成字幕语言: {list(auto_subs.keys())}")
            
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
            
            # 添加字幕下载选项
            if download_subtitles:
                ydl_opts.update({
                    'writesubtitles': True,           # 下载字幕
                    'writeautomaticsub': True,        # 下载自动生成的字幕
                    'subtitleslangs': ['en', 'en-US', 'en-GB', 'zh', 'zh-Hans', 'zh-CN'],  # 优先英文和中文
                    'subtitlesformat': 'json3/srv3/vtt/srt/best',  # 字幕格式优先级
                })
            
            # 下载视频
            logger.info(f"开始下载视频: {video_title}")
            if download_subtitles:
                logger.info("同时下载字幕...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 查找下载的视频文件
            downloaded_file = self.output_dir / f"{filename}.mp4"
            if not downloaded_file.exists():
                files = list(self.output_dir.glob(f"{filename}.*mp4"))
                if files:
                    downloaded_file = files[0]
                else:
                    files = list(self.output_dir.glob("*.mp4"))
                    if files:
                        downloaded_file = max(files, key=lambda p: p.stat().st_mtime)
            
            if not downloaded_file.exists():
                raise FileNotFoundError(f"下载的文件未找到: {downloaded_file}")
            
            logger.info(f"视频下载完成: {downloaded_file}")
            
            result = {
                'video_path': str(downloaded_file),
                'subtitle_path': None,
                'subtitle_lang': None,
            }
            
            # 查找下载的字幕文件
            if download_subtitles:
                subtitle_info = self._find_subtitle_file(filename)
                if subtitle_info:
                    result['subtitle_path'] = subtitle_info['path']
                    result['subtitle_lang'] = subtitle_info['lang']
                    logger.info(f"字幕下载完成: {subtitle_info['path']} (语言: {subtitle_info['lang']})")
                else:
                    logger.warning("未找到可用的字幕文件")
            
            return result
                
        except Exception as e:
            logger.error(f"下载视频时出错: {str(e)}")
            raise
    
    def _find_subtitle_file(self, filename: str) -> Optional[Dict[str, str]]:
        """
        查找下载的字幕文件
        
        Args:
            filename: 视频文件名（不含扩展名）
            
        Returns:
            字幕信息字典 {'path': str, 'lang': str} 或 None
        """
        # 按优先级查找字幕文件
        subtitle_extensions = ['.json3', '.srv3', '.vtt', '.srt']
        lang_priority = ['en', 'en-US', 'en-GB', 'zh', 'zh-Hans', 'zh-CN']
        
        # 首先按语言优先级查找
        for lang in lang_priority:
            for ext in subtitle_extensions:
                subtitle_file = self.output_dir / f"{filename}.{lang}{ext}"
                if subtitle_file.exists():
                    return {'path': str(subtitle_file), 'lang': lang}
        
        # 如果没找到，查找任何字幕文件
        for ext in subtitle_extensions:
            files = list(self.output_dir.glob(f"{filename}.*{ext}"))
            if files:
                # 从文件名中提取语言
                file_path = files[0]
                lang = file_path.stem.replace(filename + '.', '')
                return {'path': str(file_path), 'lang': lang}
        
        return None
    
    def convert_youtube_subtitle_to_json(self, subtitle_path: str, output_path: Optional[str] = None) -> str:
        """
        将 YouTube 下载的字幕转换为标准 JSON 格式
        
        Args:
            subtitle_path: YouTube 字幕文件路径（.json3, .vtt, .srt 等）
            output_path: 输出 JSON 文件路径
            
        Returns:
            转换后的 JSON 文件路径
        """
        subtitle_path = Path(subtitle_path)
        
        if output_path is None:
            output_path = subtitle_path.with_suffix('.json')
        else:
            output_path = Path(output_path)
        
        ext = subtitle_path.suffix.lower()
        
        if ext == '.json3':
            return self._convert_json3_to_json(subtitle_path, output_path)
        elif ext == '.vtt':
            return self._convert_vtt_to_json(subtitle_path, output_path)
        elif ext == '.srt':
            return self._convert_srt_to_json(subtitle_path, output_path)
        else:
            logger.warning(f"不支持的字幕格式: {ext}，尝试按 json3 格式解析")
            return self._convert_json3_to_json(subtitle_path, output_path)
    
    def _convert_json3_to_json(self, input_path: Path, output_path: Path) -> str:
        """将 YouTube JSON3 格式字幕转换为标准格式"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = []
        full_text = []
        
        # json3 格式的事件列表
        events = data.get('events', [])
        
        for event in events:
            # 跳过没有字幕内容的事件
            segs = event.get('segs', [])
            if not segs:
                continue
            
            # 提取时间（毫秒转秒）
            start_ms = event.get('tStartMs', 0)
            duration_ms = event.get('dDurationMs', 0)
            start = start_ms / 1000.0
            end = (start_ms + duration_ms) / 1000.0
            
            # 提取文本
            text_parts = []
            for seg in segs:
                text = seg.get('utf8', '')
                if text and text.strip():
                    text_parts.append(text)
            
            text = ''.join(text_parts).strip()
            if text and text != '\n':
                segments.append({
                    'id': len(segments),
                    'start': start,
                    'end': end,
                    'text': text
                })
                full_text.append(text)
        
        result = {
            'transcription': ' '.join(full_text),
            'segments': segments,
            'source': 'youtube',
            'original_file': str(input_path)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"字幕转换完成: {output_path} ({len(segments)} 个段落)")
        return str(output_path)
    
    def _convert_vtt_to_json(self, input_path: Path, output_path: Path) -> str:
        """将 VTT 格式字幕转换为标准格式"""
        import re
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        segments = []
        full_text = []
        
        # VTT 时间戳格式: 00:00:00.000 --> 00:00:00.000
        pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n((?:(?!\d{2}:\d{2}:\d{2}).+\n?)+)'
        
        def parse_time(time_str):
            parts = time_str.replace(',', '.').split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        
        matches = re.findall(pattern, content)
        
        for i, (start_str, end_str, text) in enumerate(matches):
            start = parse_time(start_str)
            end = parse_time(end_str)
            text = text.strip()
            # 移除 VTT 标签
            text = re.sub(r'<[^>]+>', '', text)
            
            if text:
                segments.append({
                    'id': i,
                    'start': start,
                    'end': end,
                    'text': text
                })
                full_text.append(text)
        
        result = {
            'transcription': ' '.join(full_text),
            'segments': segments,
            'source': 'youtube',
            'original_file': str(input_path)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"字幕转换完成: {output_path} ({len(segments)} 个段落)")
        return str(output_path)
    
    def _convert_srt_to_json(self, input_path: Path, output_path: Path) -> str:
        """将 SRT 格式字幕转换为标准格式"""
        import re
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        segments = []
        full_text = []
        
        # SRT 格式块
        blocks = re.split(r'\n\n+', content.strip())
        
        def parse_time(time_str):
            parts = time_str.replace(',', '.').split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 第一行是序号，第二行是时间戳，后面是文本
                time_line = lines[1]
                time_match = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', time_line)
                
                if time_match:
                    start = parse_time(time_match.group(1))
                    end = parse_time(time_match.group(2))
                    text = ' '.join(lines[2:]).strip()
                    
                    if text:
                        segments.append({
                            'id': len(segments),
                            'start': start,
                            'end': end,
                            'text': text
                        })
                        full_text.append(text)
        
        result = {
            'transcription': ' '.join(full_text),
            'segments': segments,
            'source': 'youtube',
            'original_file': str(input_path)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"字幕转换完成: {output_path} ({len(segments)} 个段落)")
        return str(output_path)
    
    def extract(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        实现基类接口（对于下载器，input_path是URL）
        
        Args:
            input_path: YouTube URL
            output_path: 不使用（保留接口兼容性）
            
        Returns:
            下载的视频文件路径
        """
        result = self.download(input_path)
        return result['video_path']

