# 代码示例

VideoClip 的代码示例集合。

## 基本示例

### 示例1：处理本地视频

```python
from videoclip import VideoClipProcessor

processor = VideoClipProcessor(work_dir="work")
processor.process(video_path="video.mp4")
```

### 示例2：从 YouTube 下载并处理

```python
from videoclip import VideoClipProcessor

processor = VideoClipProcessor()
processor.process(
    youtube_url="https://www.youtube.com/watch?v=VIDEO_ID",
    keep_intermediate=True
)
```

### 示例3：使用自定义提示词

```python
from videoclip import VideoClipProcessor

custom_prompt = """
请找出所有关于技术创新的片段。

要求：
1. 识别出涉及技术创新的内容
2. 每个片段包含时间戳和内容描述

字幕内容：
{subtitle_text}
"""

processor = VideoClipProcessor()
processor.process(
    video_path="video.mp4",
    custom_prompt=custom_prompt
)
```

## 高级示例

### 示例4：单独使用各个模块

```python
from videoclip.extractors import AudioExtractor, SubtitleExtractor
from videoclip.analyzers import ContentAnalyzer
from videoclip.clippers import VideoClipper

# 1. 提取音频
audio_extractor = AudioExtractor(output_dir="audio")
audio_path = audio_extractor.extract("video.mp4")

# 2. 提取字幕
subtitle_extractor = SubtitleExtractor()
subtitle_path = subtitle_extractor.extract(audio_path)

# 3. 分析内容
analyzer = ContentAnalyzer()
highlights_path = analyzer.analyze(subtitle_path)

# 4. 加载结果
highlights_data = analyzer.load_results(highlights_path)
highlights = highlights_data.get("highlights", [])

# 5. 裁剪视频
clipper = VideoClipper(output_dir="clips")
subtitle_data = subtitle_extractor.load_subtitles(subtitle_path)

results = clipper.clip_multiple(
    video_path="video.mp4",
    highlights=highlights,
    subtitle_data=subtitle_data
)

print(f"生成了 {len(results)} 个视频片段")
```

### 示例5：批量处理多个视频

```python
from pathlib import Path
from videoclip import VideoClipProcessor

video_dir = Path("videos")
processor = VideoClipProcessor()

for video_file in video_dir.glob("*.mp4"):
    print(f"处理: {video_file.name}")
    processor.process(
        video_path=str(video_file),
        keep_intermediate=False
    )
```

### 示例6：自定义配置

```python
from videoclip import VideoClipProcessor
from videoclip.config import get_settings
import os

# 设置环境变量
os.environ["QWEN_MODEL"] = "qwen-flash"  # 使用更快的模型
os.environ["WHISPER_MODEL_SIZE"] = "small"  # 使用更精确的模型

# 获取配置
settings = get_settings()

# 创建处理器
processor = VideoClipProcessor(work_dir="custom_work")
processor.process(video_path="video.mp4")
```

### 示例7：错误处理和日志

```python
import logging
from videoclip import VideoClipProcessor
from videoclip.utils.logger import setup_logging, get_logger

# 设置日志
setup_logging(
    level=logging.INFO,
    log_file="process.log"
)
logger = get_logger(__name__)

try:
    processor = VideoClipProcessor()
    processor.process(video_path="video.mp4")
    logger.info("处理完成")
except Exception as e:
    logger.error(f"处理失败: {e}", exc_info=True)
```

## 扩展示例

### 示例8：创建自定义提取器

```python
from videoclip.extractors.base import BaseExtractor
from pathlib import Path

class CustomExtractor(BaseExtractor):
    def extract(self, input_path: str, output_path: str = None) -> str:
        # 实现自定义提取逻辑
        input_file = Path(input_path)
        if output_path is None:
            output_path = self.output_dir / f"{input_file.stem}_custom.txt"
        
        # 您的处理逻辑
        with open(output_path, 'w') as f:
            f.write("自定义提取结果")
        
        return str(output_path)
```

### 示例9：创建自定义分析器

```python
from videoclip.analyzers.base import BaseAnalyzer
import json
from pathlib import Path

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, input_path: str, output_path: str = None, **kwargs) -> str:
        # 实现自定义分析逻辑
        input_file = Path(input_path)
        if output_path is None:
            output_path = input_file.parent / f"{input_file.stem}_custom.json"
        
        # 您的分析逻辑
        result = {
            "highlights": [
                {
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "text": "示例片段",
                    "reason": "示例原因"
                }
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def load_results(self, results_path: str) -> dict:
        with open(results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
```

## 实用脚本示例

### 示例10：重新生成字幕

```python
from pathlib import Path
from videoclip.extractors import SubtitleExtractor
from videoclip.clippers import VideoClipper
import json

# 加载数据
subtitle_path = Path("work/audio/video_subtitles.json")
highlights_path = Path("work/audio/video_subtitles_highlights.json")

subtitle_extractor = SubtitleExtractor()
subtitle_data = subtitle_extractor.load_subtitles(str(subtitle_path))

with open(highlights_path, 'r', encoding='utf-8') as f:
    highlights_data = json.load(f)

# 重新生成字幕
clipper = VideoClipper(output_dir="work/clips")
highlight = highlights_data["highlights"][0]  # 第一个片段

clip_subtitle = clipper.extract_subtitle_for_clip(
    subtitle_data,
    highlight["start_time"],
    highlight["end_time"]
)

# 保存字幕
srt_path = Path("work/clips/highlight_01_subtitle.srt")
clipper.save_subtitle_srt(clip_subtitle, srt_path)
```

## 相关文档

- [API参考](../api/README.md)
- [扩展开发](../guides/extension.md)
- [快速入门](../guides/quickstart.md)

