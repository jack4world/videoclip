# 完整教程

VideoClip 的完整使用教程，从基础到高级。

## 目录

1. [准备工作](#准备工作)
2. [基本使用](#基本使用)
3. [高级功能](#高级功能)
4. [最佳实践](#最佳实践)
5. [故障排除](#故障排除)

## 准备工作

### 1. 安装和配置

参考 [安装指南](installation.md) 完成安装和配置。

### 2. 准备视频文件

您可以：
- 使用本地视频文件
- 从 YouTube 下载视频

### 3. 检查配置

```bash
python check_api.py
```

## 基本使用

### 场景1：处理本地视频

```bash
python main.py --video "path/to/video.mp4"
```

**处理流程：**
1. 提取音频
2. 生成字幕
3. 分析精彩片段
4. 裁剪视频并生成字幕

**输出结果：**
- `work/clips/` - 裁剪的视频片段
- `work/audio/` - 字幕和分析结果

### 场景2：从 YouTube 下载并处理

```bash
python main.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

**注意事项：**
- 确保网络连接正常
- 视频下载可能需要一些时间
- 下载的视频会保存在 `work/downloads/`

### 场景3：保留中间文件

```bash
python main.py --video "video.mp4" --keep-intermediate
```

这会保留音频文件，方便后续处理。

## 高级功能

### 自定义分析提示词

#### 方式1：命令行参数

```bash
python main.py \
  --video "video.mp4" \
  --prompt "找出所有关于技术创新的片段"
```

#### 方式2：文件输入

创建 `prompt.txt`：

```text
请分析以下视频字幕，找出所有关于技术创新的内容片段。

要求：
1. 识别出涉及技术创新的片段
2. 每个片段包含时间戳和内容描述
3. 说明为什么这段内容与技术创新相关

字幕内容：
{subtitle_text}

请返回 JSON 格式，包含 highlights 数组。
```

然后使用：

```bash
python main.py --video "video.mp4" --prompt-file prompt.txt
```

### 使用 Python API

```python
from videoclip import VideoClipProcessor

processor = VideoClipProcessor(work_dir="work")
processor.process(
    video_path="video.mp4",
    keep_intermediate=True,
    custom_prompt="找出所有关于人工智能的观点"
)
```

### 单独使用各个模块

```python
from videoclip.extractors import AudioExtractor, SubtitleExtractor
from videoclip.analyzers import ContentAnalyzer
from videoclip.clippers import VideoClipper

# 提取音频
audio_extractor = AudioExtractor()
audio_path = audio_extractor.extract("video.mp4")

# 提取字幕
subtitle_extractor = SubtitleExtractor()
subtitle_path = subtitle_extractor.extract(audio_path)

# 分析内容
analyzer = ContentAnalyzer()
highlights_path = analyzer.analyze(subtitle_path)

# 裁剪视频
clipper = VideoClipper()
highlights_data = analyzer.load_results(highlights_path)
results = clipper.clip_multiple(
    "video.mp4",
    highlights_data["highlights"],
    subtitle_data=subtitle_extractor.load_subtitles(subtitle_path)
)
```

## 最佳实践

### 1. 工作目录管理

为不同项目使用不同的工作目录：

```bash
python main.py --video "video1.mp4" --work-dir "project1"
python main.py --video "video2.mp4" --work-dir "project2"
```

### 2. 提示词优化

- **明确目标**：清楚地说明您想要什么
- **指定数量**：明确需要多少个片段
- **说明标准**：解释什么是"精彩"或"重要"
- **提供示例**：在提示词中给出格式示例

### 3. 文件管理

- 定期清理 `work/` 目录
- 重要结果及时备份
- 使用 `--keep-intermediate` 保留中间文件用于调试

### 4. 性能优化

- 使用较小的 Whisper 模型（`tiny` 或 `base`）加快处理速度
- 使用 `qwen-flash` 模型加快分析速度
- 处理长视频时考虑分段处理

## 故障排除

### 问题1：API 调用失败

**症状：** 提示 API 错误或配额不足

**解决方案：**
1. 检查 `QWEN_API_KEY` 是否正确配置
2. 访问 [DashScope控制台](https://dashscope.console.aliyun.com/) 检查配额
3. 确认使用的是付费账户

### 问题2：字幕提取失败

**症状：** Whisper 模型加载失败或处理出错

**解决方案：**
1. 检查网络连接（首次使用需要下载模型）
2. 尝试使用较小的模型（`tiny` 或 `base`）
3. 检查音频文件是否损坏

### 问题3：视频裁剪失败

**症状：** FFmpeg 错误

**解决方案：**
1. 确认 FFmpeg 已正确安装
2. 检查视频文件格式是否支持
3. 查看错误日志了解详细信息

### 问题4：找不到精彩片段

**症状：** 分析结果为空

**解决方案：**
1. 检查提示词是否合适
2. 尝试使用默认提示词
3. 查看 API 返回的原始内容（启用 DEBUG 日志）

### 问题5：字幕文件没有中文翻译

**症状：** SRT 文件只有英文

**解决方案：**
1. 确认 `QWEN_API_KEY` 已配置
2. 检查 API 配额是否充足
3. 重新生成字幕文件（使用 `scripts/regenerate_subtitle.py`）

## 工作流程示例

### 完整工作流程

```bash
# 1. 检查配置
python check_api.py

# 2. 处理视频
python main.py --video "video.mp4" --keep-intermediate

# 3. 查看结果
ls -lh work/clips/

# 4. 如果需要，重新生成字幕
python scripts/regenerate_subtitle.py 1
```

### 批量处理流程

```python
from pathlib import Path
from videoclip import VideoClipProcessor

processor = VideoClipProcessor()

for video_file in Path("videos").glob("*.mp4"):
    print(f"处理: {video_file.name}")
    processor.process(
        video_path=str(video_file),
        keep_intermediate=False
    )
```

## 下一步

- [API参考](../api/README.md) - 了解 Python API
- [扩展开发](extension.md) - 学习如何扩展功能
- [代码示例](../examples/README.md) - 查看更多示例

## 获取帮助

- 查看 [命令行参考](cli-reference.md)
- 阅读 [常见问题](quickstart.md#常见问题)
- 提交 Issue（如果适用）

