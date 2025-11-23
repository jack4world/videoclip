# 命令行参考

VideoClip 命令行工具的完整参考文档。

## 基本语法

```bash
python main.py [选项]
# 或
python -m videoclip.cli [选项]
```

## 必需参数

必须提供以下参数之一：

### `--url URL`
YouTube 视频 URL

```bash
python main.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### `--video PATH`
本地视频文件路径

```bash
python main.py --video "path/to/video.mp4"
```

## 可选参数

### `--work-dir DIR`
指定工作目录（默认: `work`）

```bash
python main.py --video "video.mp4" --work-dir "my_work"
```

### `--keep-intermediate`
保留中间文件（音频文件等）

```bash
python main.py --video "video.mp4" --keep-intermediate
```

**注意**：字幕文件和精彩片段分析结果始终会被保留。

### `--prompt TEXT`
自定义分析提示词

```bash
python main.py --video "video.mp4" --prompt "找出所有关于技术创新的片段"
```

提示词中可以使用的占位符：
- `{subtitle_text}` - 字幕内容

### `--prompt-file PATH`
从文件读取自定义提示词

```bash
python main.py --video "video.mp4" --prompt-file prompt.txt
```

### `--log-level LEVEL` (仅新架构)
设置日志级别（DEBUG, INFO, WARNING, ERROR）

```bash
python -m videoclip.cli --video "video.mp4" --log-level DEBUG
```

### `--log-file PATH` (仅新架构)
指定日志文件路径

```bash
python -m videoclip.cli --video "video.mp4" --log-file logs/app.log
```

## 示例

### 基本使用

```bash
# 处理本地视频
python main.py --video "video.mp4"

# 从YouTube下载并处理
python main.py --url "https://www.youtube.com/watch?v=example"
```

### 高级使用

```bash
# 保留所有中间文件
python main.py --video "video.mp4" --keep-intermediate

# 使用自定义提示词
python main.py \
  --video "video.mp4" \
  --prompt "找出所有关于人工智能的观点片段"

# 从文件读取提示词
python main.py \
  --video "video.mp4" \
  --prompt-file my_prompt.txt \
  --work-dir custom_work

# 使用新架构（带日志）
python -m videoclip.cli \
  --video "video.mp4" \
  --log-level INFO \
  --log-file logs/process.log
```

## 环境变量

可以通过环境变量设置默认值：

```bash
export WORK_DIR=my_work
export QWEN_API_KEY=your_key
python main.py --video "video.mp4"
```

## 退出代码

- `0` - 成功
- `1` - 错误

## 获取帮助

```bash
python main.py --help
python -m videoclip.cli --help
```

## 相关文档

- [快速入门](quickstart.md)
- [完整教程](tutorial.md)
- [配置说明](../config.md)

