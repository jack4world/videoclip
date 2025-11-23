# 安装指南

本文档介绍如何安装和配置 VideoClip。

## 系统要求

- Python 3.8 或更高版本
- FFmpeg（用于视频处理）
- 足够的磁盘空间（用于存储视频和音频文件）

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd videoclip
```

或者直接下载项目文件。

### 2. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 确保虚拟环境已激活，然后安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 安装 FFmpeg

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### Windows
1. 访问 [FFmpeg官网](https://ffmpeg.org/download.html)
2. 下载 Windows 版本
3. 解压并添加到系统 PATH

### 5. 配置环境变量

创建 `.env` 文件（在项目根目录）：

```bash
# DashScope API 配置
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# 可选配置
QWEN_MODEL=qwen-plus
QWEN_TEMPERATURE=0.7
QWEN_MAX_TOKENS=2000
WHISPER_MODEL_SIZE=base
WORK_DIR=work
SUBTITLE_MAX_CHARS=15
```

### 6. 验证安装

```bash
# 检查 API 配置
python check_api.py

# 测试导入
python -c "from videoclip import VideoClipProcessor; print('✓ 安装成功')"
```

## 安装为系统命令（可选）

```bash
pip install -e .
```

安装后可以直接使用：

```bash
videoclip --video "path/to/video.mp4"
```

## 常见问题

### Q: 如何获取 QWEN_API_KEY？

A: 
1. 访问 [DashScope控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录账号
3. 创建 API Key
4. 将 API Key 添加到 `.env` 文件

### Q: FFmpeg 安装失败怎么办？

A: 请参考 [FFmpeg官方文档](https://ffmpeg.org/download.html) 或使用包管理器安装。

### Q: Whisper 模型下载很慢？

A: Whisper 模型会在首次使用时自动下载。如果下载慢，可以考虑：
- 使用代理
- 手动下载模型文件
- 使用较小的模型（如 `tiny` 或 `base`）

## 下一步

安装完成后，请查看：
- [快速入门](quickstart.md) - 开始使用 VideoClip
- [配置说明](../config.md) - 了解详细配置选项

