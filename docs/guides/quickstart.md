# 快速入门

5分钟快速上手 VideoClip！

## 前提条件

- 已完成安装（参考 [安装指南](installation.md)）
- 已配置 `QWEN_API_KEY`

## 基本使用

### 方式1：处理已下载的视频文件

```bash
python main.py --video "path/to/your/video.mp4"
```

### 方式2：从 YouTube 下载并处理

```bash
python main.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 方式3：使用新架构（推荐）

```bash
python -m videoclip.cli --video "path/to/your/video.mp4"
```

## 处理流程

VideoClip 会自动执行以下步骤：

1. **提取音频** - 从视频中提取音频文件
2. **提取字幕** - 使用 Whisper 生成字幕和时间戳
3. **分析内容** - 使用 AI 找出精彩片段
4. **裁剪视频** - 自动裁剪精彩片段并生成字幕

## 输出结果

处理完成后，您会在 `work/` 目录下找到：

```
work/
├── downloads/          # 下载的视频（如果从YouTube下载）
├── audio/              # 音频和字幕文件
│   ├── video_subtitles.json
│   └── video_subtitles_highlights.json
└── clips/              # 裁剪的视频片段
    ├── highlight_01_xxx.mp4
    ├── highlight_01_xxx_subtitle.srt
    └── highlight_01_xxx_subtitle.json
```

## 常用选项

### 保留中间文件

```bash
python main.py --video "video.mp4" --keep-intermediate
```

### 使用自定义提示词

```bash
python main.py --video "video.mp4" --prompt "找出所有关于技术创新的片段"
```

### 从文件读取提示词

```bash
python main.py --video "video.mp4" --prompt-file prompt.txt
```

## 示例

### 示例1：处理本地视频

```bash
python main.py --video "work/downloads/my_video.mp4"
```

### 示例2：处理YouTube视频并保留中间文件

```bash
python main.py --url "https://www.youtube.com/watch?v=example" --keep-intermediate
```

### 示例3：使用自定义提示词

```bash
python main.py \
  --video "video.mp4" \
  --prompt "请找出所有关于人工智能未来发展的观点片段"
```

## 下一步

- [完整教程](tutorial.md) - 了解更多功能
- [命令行参考](cli-reference.md) - 查看所有选项
- [自定义提示词](custom-prompts.md) - 学习编写提示词

## 获取帮助

```bash
python main.py --help
```

或

```bash
python -m videoclip.cli --help
```

