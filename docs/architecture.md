# VideoClip 架构文档

## 概述

VideoClip 是一个基于 AI 的智能视频剪辑工具，采用模块化架构设计，便于扩展和维护。

## 目录结构

```
videoclip/
├── videoclip/              # 主包
│   ├── __init__.py
│   ├── core/              # 核心功能模块
│   │   ├── __init__.py
│   │   └── processor.py   # 主处理器（整合所有功能）
│   ├── extractors/        # 提取器模块
│   │   ├── __init__.py
│   │   ├── base.py        # 提取器基类
│   │   ├── audio.py       # 音频提取器
│   │   ├── subtitle.py    # 字幕提取器
│   │   └── video.py       # 视频下载器
│   ├── analyzers/         # 分析器模块
│   │   ├── __init__.py
│   │   ├── base.py        # 分析器基类
│   │   └── content.py     # 内容分析器
│   ├── clippers/          # 裁剪器模块
│   │   ├── __init__.py
│   │   └── video.py       # 视频裁剪器
│   ├── config/            # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py    # 配置类（单例模式）
│   │   └── constants.py  # 常量定义
│   ├── utils/             # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py      # 日志工具
│   │   └── file_utils.py  # 文件工具
│   └── cli/               # 命令行接口
│       ├── __init__.py
│       └── main.py         # CLI主入口
├── scripts/                # 脚本目录
│   └── regenerate_subtitle.py
├── tests/                  # 测试目录
├── main.py                 # 向后兼容入口
├── setup.py                # 安装配置
├── requirements.txt        # 依赖列表
└── README.md               # 项目说明
```

## 架构设计原则

### 1. 模块化设计
- 每个功能模块独立，职责单一
- 通过基类定义统一接口
- 便于替换和扩展实现

### 2. 配置集中管理
- 所有配置通过 `Settings` 类统一管理
- 支持环境变量和默认值
- 单例模式确保配置一致性

### 3. 依赖注入
- 模块间通过接口交互，降低耦合
- 配置和依赖通过构造函数注入
- 便于测试和模拟

### 4. 日志系统
- 统一的日志接口
- 支持不同日志级别
- 可配置日志输出（控制台/文件）

## 核心模块说明

### 1. Config 模块 (`videoclip.config`)
负责配置管理：
- `Settings`: 单例配置类，统一管理所有配置项
- `constants.py`: 常量定义（文件扩展名、目录名等）

### 2. Extractors 模块 (`videoclip.extractors`)
负责数据提取：
- `BaseExtractor`: 提取器基类，定义统一接口
- `AudioExtractor`: 从视频提取音频
- `SubtitleExtractor`: 从音频提取字幕（使用Whisper）
- `YouTubeDownloader`: 下载YouTube视频

### 3. Analyzers 模块 (`videoclip.analyzers`)
负责内容分析：
- `BaseAnalyzer`: 分析器基类
- `ContentAnalyzer`: 使用Qwen API分析字幕，找出精彩片段

### 4. Clippers 模块 (`videoclip.clippers`)
负责视频裁剪：
- `VideoClipper`: 裁剪视频片段并生成字幕文件

### 5. Core 模块 (`videoclip.core`)
核心处理流程：
- `VideoClipProcessor`: 整合所有模块，实现完整处理流程

### 6. Utils 模块 (`videoclip.utils`)
工具函数：
- `logger.py`: 日志工具
- `file_utils.py`: 文件操作工具

### 7. CLI 模块 (`videoclip.cli`)
命令行接口：
- `main.py`: CLI入口，解析参数并调用处理器

## 使用方式

### 作为Python包使用

```python
from videoclip import VideoClipProcessor

processor = VideoClipProcessor(work_dir="work")
processor.process(
    video_path="video.mp4",
    keep_intermediate=True,
    custom_prompt="自定义提示词"
)
```

### 作为命令行工具使用

```bash
# 使用新架构（推荐）
python -m videoclip.cli --video "video.mp4"

# 向后兼容（旧方式）
python main.py --video "video.mp4"
```

### 安装为系统命令

```bash
pip install -e .
videoclip --video "video.mp4"
```

## 扩展指南

### 添加新的提取器

1. 继承 `BaseExtractor` 基类
2. 实现 `extract()` 方法
3. 在 `extractors/__init__.py` 中导出

### 添加新的分析器

1. 继承 `BaseAnalyzer` 基类
2. 实现 `analyze()` 和 `load_results()` 方法
3. 在 `analyzers/__init__.py` 中导出

### 修改配置

在 `videoclip/config/settings.py` 中添加新的配置项，支持环境变量和默认值。

## 向后兼容性

- 旧的 `main.py` 仍然可用，内部调用新架构
- 旧的模块导入路径仍然支持（通过 `__init__.py` 导出）
- 配置文件格式保持不变

## 测试

```bash
# 运行测试（待实现）
pytest tests/
```

## 未来改进方向

1. 添加单元测试和集成测试
2. 支持更多视频源（Bilibili、Vimeo等）
3. 支持更多字幕格式（ASS、VTT等）
4. 添加Web界面
5. 支持批量处理
6. 添加进度条和更详细的日志

