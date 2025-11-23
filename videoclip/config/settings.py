"""
配置管理模块
统一管理所有配置项，包括环境变量、默认值等
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """配置类 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 加载环境变量
        load_dotenv()
        
        # API 配置
        self.qwen_api_key: Optional[str] = os.getenv("QWEN_API_KEY")
        self.qwen_base_url: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        
        # 模型配置
        self.whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "base")
        self.qwen_model: str = os.getenv("QWEN_MODEL", "qwen-plus")
        self.qwen_temperature: float = float(os.getenv("QWEN_TEMPERATURE", "0.7"))
        self.qwen_max_tokens: int = int(os.getenv("QWEN_MAX_TOKENS", "2000"))
        
        # 工作目录配置
        self.default_work_dir: str = os.getenv("WORK_DIR", "work")
        
        # 字幕配置
        self.subtitle_max_chars: int = int(os.getenv("SUBTITLE_MAX_CHARS", "15"))
        
        # 视频编码配置
        self.video_codec: str = os.getenv("VIDEO_CODEC", "libx264")
        self.audio_codec: str = os.getenv("AUDIO_CODEC", "aac")
        self.video_preset: str = os.getenv("VIDEO_PRESET", "medium")
        self.video_crf: int = int(os.getenv("VIDEO_CRF", "23"))
        
        # 音频格式配置
        self.audio_format: str = os.getenv("AUDIO_FORMAT", "wav")
        
        self._initialized = True
    
    def validate(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            配置是否有效
        """
        if not self.qwen_api_key:
            print("⚠ 警告: QWEN_API_KEY 未设置，某些功能可能无法使用")
        return True
    
    def get_work_dir(self, work_dir: Optional[str] = None) -> Path:
        """
        获取工作目录路径
        
        Args:
            work_dir: 自定义工作目录，如果为None则使用默认值
            
        Returns:
            工作目录Path对象
        """
        work_dir = work_dir or self.default_work_dir
        path = Path(work_dir)
        path.mkdir(exist_ok=True)
        return path


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取配置实例（单例）
    
    Returns:
        Settings实例
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate()
    return _settings

