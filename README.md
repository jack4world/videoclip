# VideoClip - 智能视频剪辑工具

一个基于 AI 的智能视频剪辑工具，可以自动从 YouTube 视频中提取精彩片段。

📚 **[查看完整文档](docs/README.md)** | 🚀 **[快速开始](docs/guides/quickstart.md)** | 📖 **[API参考](docs/api/README.md)**

## 功能特性

1. **YouTube 视频下载** - 下载 YouTube 视频为 MP4 格式
2. **音频提取** - 从视频中提取音频文件
3. **字幕提取** - 使用本地 Whisper 模型提取字幕和时间戳（无需 API，无配额限制）
4. **精彩内容分析** - 使用 Qwen-Plus/Qwen-Flash 分析字幕，找出精彩观点和时间戳
5. **视频裁剪** - 根据时间戳自动裁剪视频片段
6. **字幕对应** - 为每个裁剪的视频片段自动生成对应的字幕文件（SRT 和 JSON 格式），确保视频与字幕一一对应

## 安装

### 1. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 2. 安装依赖

```bash
# 确保虚拟环境已激活，然后安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 安装 FFmpeg

确保已安装 ffmpeg：
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# 下载 ffmpeg 并添加到 PATH
```

## 配置

创建 `.env` 文件并配置 API 密钥：

```
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://api.example.com  # Qwen API 基础 URL
```

## 使用方法

**注意**：使用前请确保已激活虚拟环境：
```bash
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
```

### 基本使用

#### 方式一：从 YouTube 下载并处理

```bash
python main.py --url <youtube_url>
```

#### 方式二：处理已下载的视频文件

```bash
python main.py --video <视频文件路径>
```

例如：
```bash
python main.py --video "downloads/my_video.mp4"
python main.py --video "/Users/jackwang/Videos/video.mp4"
```

### 高级选项

```bash
# 保留中间文件（音频文件等）
# 注意：字幕文件和精彩片段分析结果始终会被保存，不受此选项影响
python main.py --url <youtube_url> --keep-intermediate
python main.py --video <视频路径> --keep-intermediate

# 使用自定义提示词进行分析
python main.py --url <youtube_url> --prompt "你的自定义提示词"
python main.py --video <视频路径> --prompt "你的自定义提示词"

# 从文件读取自定义提示词
python main.py --url <youtube_url> --prompt-file prompt.txt
python main.py --video <视频路径> --prompt-file prompt.txt

# 指定工作目录
python main.py --url <youtube_url> --work-dir my_work
python main.py --video <视频路径> --work-dir my_work
```

### 自定义提示词

默认情况下，程序会使用内置的提示词来分析字幕内容。你也可以提供自定义提示词来满足特定需求：

- **命令行参数**：使用 `--prompt` 直接输入提示词
- **文件输入**：使用 `--prompt-file` 从文件读取提示词

在自定义提示词中，可以使用 `{subtitle_text}` 占位符来插入字幕内容。如果没有使用占位符，字幕内容会自动追加到提示词末尾。

示例提示词文件 (`prompt.txt`)：
```
请分析以下视频字幕，找出所有关于技术创新的内容片段。

要求：
1. 识别出所有涉及技术创新的片段
2. 每个片段需要包含开始时间、结束时间和内容描述

字幕内容：
{subtitle_text}

请返回 JSON 格式，包含 highlights 数组。
```

## 输出文件说明

处理完成后，会生成以下文件：

### 视频片段
- 位置：`work/clips/` 目录
- 格式：MP4
- 命名：`highlight_01_[内容描述].mp4`

### 字幕文件（每个视频片段都有对应的字幕）
- **SRT 格式**：`highlight_01_[内容描述]_subtitle.srt` - 中英文双语字幕格式
  - 每行字幕最多 12-15 个字符
  - 第一行显示英文，第二行显示中文
  - 可在视频播放器中显示（如 VLC、PotPlayer 等）
- **JSON 格式**：`highlight_01_[内容描述]_subtitle.json` - 包含详细的时间戳和分段信息

### 完整字幕和分析文件
- **完整字幕**：`work/audio/[视频名]_subtitles.json` - 原始视频的完整字幕
- **精彩片段分析**：`work/audio/[视频名]_highlights.json` - AI 分析出的精彩片段列表

### 字幕对应关系

每个裁剪的视频片段都会自动生成对应的字幕文件：
- ✅ 视频片段的时间戳已调整为从 0 开始（相对于片段开始时间）
- ✅ SRT 格式为中英文双语字幕：
  - 每行字幕最多 12-15 个字符（智能分割）
  - 第一行显示英文原文（自动修正错别字）
  - 第二行显示中文翻译（使用 Qwen API 自动翻译）
  - 文字校验：翻译过程中会自动检测并修正明显的错别字和拼写错误
  - 可直接用于视频播放器（如 VLC、PotPlayer 等）
- ✅ JSON 格式包含详细的分段和单词级别的时间戳信息
- ✅ 文件名一一对应，便于管理和使用

**注意**：
- 双语字幕和文字校验功能需要配置 `QWEN_API_KEY`
- 如果未配置 API Key，将只生成英文字幕（不进行错别字修正）
- 翻译过程中会自动修正原文中的明显错别字和拼写错误

### 视频编码与音视频同步

视频裁剪使用重新编码方式（H.264 + AAC）以确保音视频精确同步：
- ✅ 精确的时间戳对齐，避免音视频不同步问题
- ✅ 使用 CRF=23 平衡质量和文件大小
- ✅ 启用 faststart 优化，便于流式播放
- ⚠️ 注意：重新编码会增加处理时间，但能保证最佳同步效果

**示例**：
```
work/clips/
├── highlight_01_技术创新_subtitle.srt      ← 片段1的字幕（SRT）
├── highlight_01_技术创新_subtitle.json      ← 片段1的字幕（JSON）
├── highlight_01_技术创新.mp4               ← 片段1的视频
├── highlight_02_市场分析_subtitle.srt      ← 片段2的字幕（SRT）
├── highlight_02_市场分析_subtitle.json      ← 片段2的字幕（JSON）
└── highlight_02_市场分析.mp4               ← 片段2的视频
```

## 项目结构

```
videoclip/
├── main.py                 # 主程序入口
├── downloader.py           # YouTube 视频下载模块
├── audio_extractor.py      # 音频提取模块
├── subtitle_extractor.py   # 字幕提取模块（Whisper 本地模型）
├── content_analyzer.py     # 内容分析模块（Qwen-Flash）
├── video_clipper.py        # 视频裁剪模块（包含字幕生成功能）
├── requirements.txt        # 依赖包
└── README.md              # 项目说明
```

