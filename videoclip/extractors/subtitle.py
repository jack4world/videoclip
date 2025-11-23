"""
字幕提取模块
使用本地 Whisper 模型从音频中提取字幕和时间戳
"""
import json
from pathlib import Path
from typing import Dict, Optional

import whisper

from videoclip.extractors.base import BaseExtractor
from videoclip.config import get_settings
from videoclip.utils.logger import get_logger
from videoclip.config.constants import PATTERN_SUBTITLE

logger = get_logger(__name__)


class SubtitleExtractor(BaseExtractor):
    """字幕提取器（使用本地 Whisper 模型）"""
    
    def __init__(self, model_size: Optional[str] = None):
        """
        初始化字幕提取器
        
        Args:
            model_size: Whisper 模型大小
                - "tiny": 最快，精度较低 (~39M)
                - "base": 平衡速度和精度 (~74M) [默认]
                - "small": 较好精度 (~244M)
                - "medium": 高精度 (~769M)
                - "large": 最高精度 (~1550M)
        """
        # 注意：字幕提取器不需要output_dir，因为输出路径由音频文件路径决定
        super().__init__(".")
        self.settings = get_settings()
        self.model_size = model_size or self.settings.whisper_model_size
        
        logger.info(f"正在加载 Whisper 模型: {self.model_size}...")
        self.model = whisper.load_model(self.model_size)
        logger.info("✓ Whisper 模型加载完成")
    
    def extract(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        从音频文件中提取字幕和时间戳
        
        Args:
            audio_path: 音频文件路径
            output_path: 输出字幕文件路径（JSON格式），如果为None则自动生成
            
        Returns:
            字幕文件路径
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        if output_path is None:
            output_path = audio_path.parent / PATTERN_SUBTITLE.format(stem=audio_path.stem)
        else:
            output_path = Path(output_path)
        
        try:
            logger.info(f"开始提取字幕: {audio_path.name}")
            logger.info(f"使用 Whisper 模型: {self.model_size}")
            
            # 使用 Whisper 进行语音识别
            logger.info("正在使用 Whisper 进行语音识别（这可能需要一些时间）...")
            result = self.model.transcribe(
                str(audio_path),
                verbose=False,
                word_timestamps=True,  # 启用单词级别的时间戳
                language=None  # 自动检测语言
            )
            
            # 提取完整文本
            transcription = result.get("text", "").strip()
            
            # 提取分段信息（带时间戳）
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "id": segment.get("id", 0),
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "text": segment.get("text", "").strip()
                })
            
            # 提取单词级别的时间戳
            words = []
            for segment in result.get("segments", []):
                segment_words = segment.get("words", [])
                for word_info in segment_words:
                    words.append({
                        "word": word_info.get("word", ""),
                        "start": word_info.get("start", 0),
                        "end": word_info.get("end", 0),
                        "probability": word_info.get("probability", 0)
                    })
            
            # 保存字幕数据（格式与 DashScope API 兼容）
            subtitle_data = {
                "audio_file": str(audio_path),
                "transcription": transcription,
                "segments": segments,
                "words": words,
                "language": result.get("language", "unknown")
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"字幕提取完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"提取字幕时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def load_subtitles(self, subtitle_path: str) -> Dict:
        """
        加载字幕文件
        
        Args:
            subtitle_path: 字幕文件路径
            
        Returns:
            字幕数据字典
        """
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            return json.load(f)

