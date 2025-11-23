"""
主程序入口（向后兼容）
推荐使用: python -m videoclip.cli
"""
import sys

# 向后兼容：导入新架构的CLI
from videoclip.cli.main import main

if __name__ == "__main__":
    main()
