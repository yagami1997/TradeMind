"""
TradeMind Lite - 用户界面包

本包提供TradeMind Lite的用户界面模块，包括命令行界面和Web界面。
"""

__version__ = "0.3.1"

from .cli import run_cli
from .web import run_web_server

__all__ = ['run_cli', 'run_web_server'] 