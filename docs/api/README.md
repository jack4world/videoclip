# API 参考文档

VideoClip Python API 的完整参考文档。

## 快速开始

```python
from videoclip import VideoClipProcessor

processor = VideoClipProcessor(work_dir="work")
processor.process(video_path="video.mp4")
```

## 核心类

### VideoClipProcessor

主处理器类，整合所有功能模块。

```python
from videoclip import VideoClipProcessor

processor = VideoClipProcessor(work_dir="work")
```

#### 方法

##### `process(youtube_url=None, video_path=None, keep_intermediate=False, custom_prompt=None)`

处理完整的视频剪辑流程。

**参数：**
- `youtube_url` (str, optional): YouTube 视频 URL
- `video_path` (str, optional): 本地视频文件路径
- `keep_intermediate` (bool): 是否保留中间文件（默认: False）
- `custom_prompt` (str, optional): 自定义分析提示词

**示例：**
```python
processor.process(
    video_path="video.mp4",
    keep_intermediate=True,
    custom_prompt="找出所有关于技术创新的片段"
)
```

## 提取器模块

### AudioExtractor

音频提取器。

```python
from videoclip.extractors import AudioExtractor

extractor = AudioExtractor(output_dir="audio")
audio_path = extractor.extract("video.mp4")
```

### SubtitleExtractor

字幕提取器（使用 Whisper）。

```python
from videoclip.extractors import SubtitleExtractor

extractor = SubtitleExtractor(model_size="base")
subtitle_path = extractor.extract("audio.wav")
subtitle_data = extractor.load_subtitles(subtitle_path)
```

### YouTubeDownloader

YouTube 视频下载器。

```python
from videoclip.extractors import YouTubeDownloader

downloader = YouTubeDownloader(output_dir="downloads")
video_path = downloader.download("https://www.youtube.com/watch?v=VIDEO_ID")
```

## 分析器模块

### ContentAnalyzer

内容分析器（使用 Qwen API）。

```python
from videoclip.analyzers import ContentAnalyzer

analyzer = ContentAnalyzer()
highlights_path = analyzer.analyze(
    subtitle_path="subtitles.json",
    custom_prompt="找出精彩片段"
)
highlights_data = analyzer.load_results(highlights_path)
```

## 裁剪器模块

### VideoClipper

视频裁剪器。

```python
from videoclip.clippers import VideoClipper

clipper = VideoClipper(output_dir="clips")
clipped_path = clipper.clip(
    video_path="video.mp4",
    start_time=10.5,
    end_time=25.3,
    output_filename="clip_01"
)
```

#### 批量裁剪

```python
highlights = [
    {"start_time": 10.5, "end_time": 25.3, "text": "..."},
    {"start_time": 50.0, "end_time": 65.0, "text": "..."}
]

results = clipper.clip_multiple(
    video_path="video.mp4",
    highlights=highlights,
    subtitle_data=subtitle_data
)
```

## 配置管理

### Settings

配置类（单例模式）。

```python
from videoclip.config import get_settings

settings = get_settings()
print(settings.qwen_api_key)
print(settings.whisper_model_size)
```

### 可用配置项

- `qwen_api_key`: DashScope API 密钥
- `qwen_model`: Qwen 模型名称（默认: qwen-plus）
- `whisper_model_size`: Whisper 模型大小（默认: base）
- `subtitle_max_chars`: 字幕每段最大字符数（默认: 15）
- `default_work_dir`: 默认工作目录（默认: work）

## 工具函数

### 日志

```python
from videoclip.utils.logger import setup_logging, get_logger

setup_logging(level=logging.INFO, log_file="app.log")
logger = get_logger(__name__)
logger.info("处理开始")
```

### 文件工具

```python
from videoclip.utils.file_utils import safe_filename, ensure_dir

safe_name = safe_filename("My Video File!", max_length=50)
ensure_dir(Path("output"))
```

## 完整示例

```python
from videoclip import VideoClipProcessor
from videoclip.config import get_settings

# 获取配置
settings = get_settings()

# 创建处理器
processor = VideoClipProcessor(work_dir="work")

# 处理视频
processor.process(
    video_path="video.mp4",
    keep_intermediate=True,
    custom_prompt="找出所有关于人工智能的观点"
)
```

## 扩展开发

### 创建自定义提取器

```python
from videoclip.extractors.base import BaseExtractor

class MyExtractor(BaseExtractor):
    def extract(self, input_path: str, output_path: str = None) -> str:
        # 实现提取逻辑
        pass
```

### 创建自定义分析器

```python
from videoclip.analyzers.base import BaseAnalyzer

class MyAnalyzer(BaseAnalyzer):
    def analyze(self, input_path: str, output_path: str = None, **kwargs) -> str:
        # 实现分析逻辑
        pass
    
    def load_results(self, results_path: str) -> dict:
        # 实现结果加载逻辑
        pass
```

## 相关文档

- [架构设计](../architecture.md)
- [扩展开发](../guides/extension.md)

