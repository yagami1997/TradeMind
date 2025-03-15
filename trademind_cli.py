#!/usr/bin/env python3
"""
TradeMind Lite - 命令行入口点

本脚本是TradeMind Lite的命令行入口点，用于启动命令行界面。
"""

import sys
from trademind.ui import run_cli

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n\n程序已终止")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
        sys.exit(1) 