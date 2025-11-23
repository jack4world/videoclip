"""
常量定义
"""

# 文件扩展名
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".flv"]
AUDIO_EXTENSIONS = [".wav", ".mp3", ".m4a", ".flac", ".aac"]
SUBTITLE_EXTENSIONS = [".srt", ".vtt", ".ass", ".json"]

# 默认值
DEFAULT_WHISPER_MODEL = "base"
DEFAULT_QWEN_MODEL = "qwen-plus"
DEFAULT_SUBTITLE_MAX_CHARS = 15

# 目录名称
DIR_DOWNLOADS = "downloads"
DIR_AUDIO = "audio"
DIR_CLIPS = "clips"

# 文件名模式
PATTERN_SUBTITLE = "{stem}_subtitles.json"
PATTERN_HIGHLIGHTS = "{stem}_highlights.json"
PATTERN_CLIP_SUBTITLE_JSON = "{filename}_subtitle.json"
PATTERN_CLIP_SUBTITLE_SRT = "{filename}_subtitle.srt"

