# 配置说明

## API 配置

### API 配置

本项目使用以下服务：
1. **Whisper（本地）** - 用于语音识别和字幕提取（本地运行，无需 API）
2. **Qwen-Flash/Qwen-Plus** - 用于内容分析和精彩片段识别（需要 DashScope API）

### 环境变量设置

创建 `.env` 文件（参考 `.env.example`）：

```bash
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
```

### 获取 API Key

1. 访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/)
2. 注册/登录账号
3. **付费账户设置**：
   - 免费账户有配额限制，可能无法处理长视频
   - 建议使用付费账户以获得更多配额和更好的服务
   - 在 DashScope 控制台充值并开通付费服务
4. 创建 API Key
5. 将 API Key 填入 `.env` 文件

### 付费账户优势

- ✅ 更高的 API 调用配额
- ✅ 可以处理更长的音频/视频文件
- ✅ 更快的响应速度
- ✅ 更好的服务稳定性

**注意**：如果遇到 "Free allocated quota exceeded" 错误，说明免费配额已用完，需要：
1. 升级到付费账户
2. 或等待配额重置（通常按天或按月）

### API 端点调整

由于 Qwen API 可能更新，如果遇到 API 调用错误，请：

1. 查看 [Qwen 官方文档](https://help.aliyun.com/zh/model-studio/)
2. 检查以下文件中的 API 端点：
   - `subtitle_extractor.py` - 字幕提取 API
   - `content_analyzer.py` - 内容分析 API
3. 根据文档更新：
   - API 端点 URL
   - 请求参数格式
   - 模型名称

### 模型配置

当前代码中使用的模型：

- **ASR 模型**: Whisper（本地模型，在 `subtitle_extractor.py` 中）
  - 默认模型: `base`（平衡速度和精度）
  - 可选模型: `tiny`（最快）、`small`（较好精度）、`medium`（高精度）、`large`（最高精度）
  - 优势: 本地运行，无需 API 调用，无配额限制
  - 注意: 首次使用会自动下载模型文件
- **分析模型**: `qwen-plus` (在 `content_analyzer.py` 中)
  - 其他可选模型: `qwen-max`（更高精度）、`qwen-flash`（更快速度）
  - 需要 DashScope API Key

如果使用其他模型，请修改相应的代码文件。

## 系统依赖

### FFmpeg

视频和音频处理需要 FFmpeg：

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
1. 下载 FFmpeg: https://ffmpeg.org/download.html
2. 解压并添加到系统 PATH

### Python 版本

建议使用 Python 3.8 或更高版本。

## 视频编码说明

### 音视频同步

视频裁剪功能使用重新编码方式（而非流复制）来确保音视频精确同步：
- **编码器**: H.264 (libx264) 视频编码器 + AAC 音频编码器
- **质量设置**: CRF=23（平衡质量和速度）
- **编码预设**: medium（平衡编码速度和质量）
- **优化**: 启用 faststart 标志，便于流式播放

### 编码参数说明

- **CRF (Constant Rate Factor)**: 恒定质量因子
  - 18: 高质量（文件较大，处理较慢）
  - 23: 平衡模式（默认，推荐）
  - 28: 快速模式（文件较小，处理较快）

- **编码预设 (Preset)**:
  - slow: 最高质量，最慢速度
  - medium: 平衡模式（默认）
  - fast: 较快速度，质量略低

**注意**: 重新编码会增加处理时间，但能保证音视频精确同步，避免使用流复制时可能出现的时间戳不匹配问题。

## 使用示例

```bash
# 基本使用
python main.py --url "https://www.youtube.com/watch?v=example"

# 保留中间文件（用于调试）
python main.py --url "https://www.youtube.com/watch?v=example" --keep-intermediate

# 指定工作目录
python main.py --url "https://www.youtube.com/watch?v=example" --work-dir my_work
```

