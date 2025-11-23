"""
视频剪辑处理器
整合所有功能模块，实现完整的视频剪辑流程
"""
import sys
from pathlib import Path
from typing import Optional

from videoclip.extractors import AudioExtractor, SubtitleExtractor, YouTubeDownloader
from videoclip.analyzers import ContentAnalyzer
from videoclip.clippers import VideoClipper
from videoclip.config import get_settings
from videoclip.config.constants import DIR_DOWNLOADS, DIR_AUDIO, DIR_CLIPS
from videoclip.utils.logger import get_logger

logger = get_logger(__name__)


class VideoClipProcessor:
    """视频剪辑处理器 - 整合所有功能"""
    
    def __init__(self, work_dir: Optional[str] = None):
        """
        初始化处理器
        
        Args:
            work_dir: 工作目录，如果为None则使用配置中的默认值
        """
        self.settings = get_settings()
        self.work_dir = self.settings.get_work_dir(work_dir)
        
        # 创建子目录
        self.downloads_dir = self.work_dir / DIR_DOWNLOADS
        self.audio_dir = self.work_dir / DIR_AUDIO
        self.clips_dir = self.work_dir / DIR_CLIPS
        
        self.downloads_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
        self.clips_dir.mkdir(exist_ok=True)
        
        # 初始化各个模块
        self.downloader = YouTubeDownloader(output_dir=str(self.downloads_dir))
        self.audio_extractor = AudioExtractor(output_dir=str(self.audio_dir))
        self.subtitle_extractor = SubtitleExtractor()
        self.content_analyzer = ContentAnalyzer()
        self.video_clipper = VideoClipper(output_dir=str(self.clips_dir))
    
    def process(self, youtube_url: Optional[str] = None, video_path: Optional[str] = None, 
                keep_intermediate: bool = False, custom_prompt: Optional[str] = None):
        """
        处理完整的视频剪辑流程
        
        Args:
            youtube_url: YouTube 视频 URL（可选，如果提供了 video_path 则不需要）
            video_path: 已下载的视频文件路径（可选，如果提供了 youtube_url 则不需要）
            keep_intermediate: 是否保留中间文件（音频文件等）。注意：字幕文件和精彩片段分析结果始终保留
            custom_prompt: 自定义分析提示词（可选），如果不提供则使用默认提示词
        """
        try:
            logger.info("=" * 60)
            logger.info("开始处理视频剪辑流程")
            logger.info("=" * 60)
            
            # 步骤 1: 获取视频文件（下载或使用已有文件）
            step_num = 1
            total_steps = 5
            
            if video_path:
                # 使用已提供的视频文件
                video_path_obj = Path(video_path)
                if not video_path_obj.exists():
                    raise FileNotFoundError(f"视频文件不存在: {video_path_obj}")
                if not video_path_obj.is_absolute():
                    video_path_obj = video_path_obj.resolve()
                video_path = str(video_path_obj)
                logger.info(f"\n[步骤 {step_num}/{total_steps}] 使用已提供的视频文件...")
                logger.info(f"✓ 视频文件: {video_path}\n")
            elif youtube_url:
                # 下载 YouTube 视频
                logger.info(f"\n[步骤 {step_num}/{total_steps}] 下载 YouTube 视频...")
                video_path = self.downloader.download(youtube_url)
                logger.info(f"✓ 视频下载完成: {video_path}\n")
            else:
                raise ValueError("必须提供 --url 或 --video 参数之一")
            
            # 步骤 2: 提取音频
            step_num += 1
            logger.info(f"[步骤 {step_num}/{total_steps}] 提取音频...")
            audio_path = self.audio_extractor.extract(video_path)
            logger.info(f"✓ 音频提取完成: {audio_path}\n")
            
            # 步骤 3: 提取字幕和时间戳
            step_num += 1
            logger.info(f"[步骤 {step_num}/{total_steps}] 提取字幕和时间戳...")
            subtitle_path = self.subtitle_extractor.extract(audio_path)
            logger.info(f"✓ 字幕提取完成: {subtitle_path}\n")
            
            # 步骤 4: 分析精彩内容
            step_num += 1
            logger.info(f"[步骤 {step_num}/{total_steps}] 分析精彩内容...")
            if custom_prompt:
                logger.info("使用自定义提示词进行分析")
            highlights_path = self.content_analyzer.analyze(subtitle_path, custom_prompt=custom_prompt)
            logger.info(f"✓ 内容分析完成: {highlights_path}\n")
            
            # 步骤 5: 裁剪视频
            step_num += 1
            logger.info(f"[步骤 {step_num}/{total_steps}] 裁剪视频片段并生成字幕...")
            highlights_data = self.content_analyzer.load_results(highlights_path)
            highlights = highlights_data.get("highlights", [])
            
            if not highlights:
                logger.warning("⚠ 未找到精彩片段，无法进行裁剪")
                return
            
            # 加载完整字幕数据，用于为每个片段生成对应的字幕
            subtitle_data = self.subtitle_extractor.load_subtitles(subtitle_path)
            
            # 裁剪视频并为每个片段生成字幕
            clipped_results = self.video_clipper.clip_multiple(
                video_path, highlights, subtitle_data=subtitle_data
            )
            logger.info(f"✓ 视频裁剪完成，共生成 {len(clipped_results)} 个片段\n")
            
            # 清理中间文件（可选）
            # 注意：字幕文件和精彩片段分析结果始终保留
            if not keep_intermediate:
                logger.info("清理中间文件...")
                try:
                    # 只清理音频文件，保留字幕和分析结果
                    Path(audio_path).unlink()
                    logger.info("✓ 音频文件已清理（字幕和分析结果已保留）\n")
                except Exception as e:
                    logger.warning(f"⚠ 清理中间文件时出错: {str(e)}\n")
            
            self._print_summary(clipped_results, subtitle_path, highlights_path)
            
        except Exception as e:
            logger.error(f"\n❌ 处理过程中出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    def _print_summary(self, clipped_results: list, subtitle_path: str, highlights_path: str):
        """打印处理结果摘要"""
        logger.info("=" * 60)
        logger.info("处理完成！")
        logger.info("=" * 60)
        logger.info(f"\n📁 输出文件位置:")
        logger.info(f"  • 视频片段目录: {self.clips_dir}")
        logger.info(f"  • 完整字幕文件: {subtitle_path}")
        logger.info(f"  • 精彩片段分析: {highlights_path}")
        logger.info(f"\n📹 共生成 {len(clipped_results)} 个视频片段（每个片段都有对应的字幕文件）:")
        for result in clipped_results:
            video_name = Path(result["video_path"]).name
            logger.info(f"\n  片段 {result['index']}: {video_name}")
            logger.info(f"    ⏱  时间: {result['start_time']:.2f}s - {result['end_time']:.2f}s ({result['duration']:.2f}s)")
            if result.get("text"):
                logger.info(f"    📝 内容: {result['text'][:60]}...")
            if result.get("subtitle_srt_path"):
                srt_name = Path(result["subtitle_srt_path"]).name
                logger.info(f"    📄 字幕: {srt_name} (SRT格式)")
            if result.get("subtitle_path"):
                json_name = Path(result["subtitle_path"]).name
                logger.info(f"    📄 字幕: {json_name} (JSON格式)")

