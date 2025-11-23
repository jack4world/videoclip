# 文件命名规范

本文档说明 VideoClip 项目的文件命名规范。

## Python 文件命名

### 规范
- 使用 `snake_case`（小写字母 + 下划线）
- 文件名应该清晰描述文件内容
- 避免使用缩写，除非是广泛认可的（如 `api`, `cli`）

### 示例
✅ **正确：**
- `audio_extractor.py`
- `subtitle_extractor.py`
- `content_analyzer.py`
- `video_clipper.py`
- `file_utils.py`
- `check_api.py`
- `test_api.py`

❌ **错误：**
- `AudioExtractor.py` (不应使用大写)
- `subtitle-extractor.py` (不应使用连字符)
- `fileUtils.py` (不应使用驼峰命名)

## 文档文件命名

### 规范
- Markdown 文件使用 `kebab-case`（小写字母 + 连字符）
- 特殊文件可以使用标准命名（如 `README.md`, `CHANGELOG.md`）
- 文件名应该清晰描述文档内容

### 示例
✅ **正确：**
- `README.md` (标准命名)
- `installation.md`
- `quickstart.md`
- `cli-reference.md`
- `custom-prompts.md`
- `api-reference.md`

❌ **错误：**
- `Installation.md` (不应使用大写)
- `CLI_Reference.md` (不应使用下划线和大写)
- `customPrompts.md` (不应使用驼峰命名)

## 目录命名

### 规范
- 使用小写字母
- 多个单词使用连字符分隔（kebab-case）
- 避免使用下划线

### 示例
✅ **正确：**
- `videoclip/`
- `docs/`
- `scripts/`
- `tests/`
- `docs/guides/`
- `docs/api/`

❌ **错误：**
- `VideoClip/` (不应使用大写)
- `docs/Guides/` (不应使用大写)
- `docs/api_reference/` (不应使用下划线)

## 配置文件命名

### 规范
- 使用小写字母
- 使用点号分隔扩展名
- 特殊配置文件可以使用标准命名

### 示例
✅ **正确：**
- `.env`
- `setup.py`
- `requirements.txt`
- `pyproject.toml`
- `.gitignore`

## 特殊文件命名

### 标准命名（保持原样）
- `README.md` - 项目说明
- `CHANGELOG.md` - 更新日志
- `LICENSE` - 许可证
- `setup.py` - 安装配置
- `requirements.txt` - 依赖列表

## 当前项目命名检查

### Python 文件
✅ 所有 Python 文件都符合 `snake_case` 规范

### 文档文件
⚠️ 需要统一：
- `ARCHITECTURE.md` → `architecture.md`
- `CLEANUP_SUMMARY.md` → `cleanup-summary.md`
- `REFACTORING_SUMMARY.md` → `refactoring-summary.md`
- `INDEX.md` → `index.md`
- `CONFIG.md` → `config.md` 或 `configuration.md`

### 目录
✅ 所有目录都符合小写规范

## 命名检查清单

- [ ] Python 文件使用 `snake_case`
- [ ] 文档文件使用 `kebab-case`
- [ ] 目录使用小写字母
- [ ] 文件名清晰描述内容
- [ ] 避免使用缩写（除非广泛认可）
- [ ] 保持命名一致性

