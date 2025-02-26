import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime

class WatchlistManager:
    """观察列表管理器：管理多个股票观察列表"""
    
    def __init__(self):
        """初始化观察列表管理器"""
        self.setup_logging()
        self.setup_paths()
        self.load_watchlists()
        
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(
            "logs/watchlist_manager.log", 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
        
    def setup_paths(self):
        """设置路径"""
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.watchlist_file = self.config_dir / "watchlists.json"
        
    def load_watchlists(self):
        """加载观察列表"""
        try:
            if not self.watchlist_file.exists():
                self._create_default_watchlists()
                
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                self.watchlists = json.load(f)
                
            self.logger.info(f"已加载 {len(self.watchlists)} 个观察列表")
            
        except Exception as e:
            self.logger.error(f"加载观察列表时出错: {str(e)}")
            self.watchlists = {}
            
    def _create_default_watchlists(self):
        """创建默认观察列表"""
        default_lists = {
            "美股科技": {
                "AAPL": "苹果",
                "MSFT": "微软",
                "GOOGL": "谷歌",
                "AMZN": "亚马逊",
                "META": "Meta",
                "NVDA": "英伟达",
                "TSLA": "特斯拉"
            },
            "中概股": {
                "BABA": "阿里巴巴",
                "PDD": "拼多多",
                "JD": "京东",
                "BIDU": "百度",
                "NIO": "蔚来",
                "XPEV": "小鹏汽车",
                "LI": "理想汽车"
            },
            "新能源": {
                "TSLA": "特斯拉",
                "NIO": "蔚来",
                "XPEV": "小鹏汽车",
                "LI": "理想汽车",
                "RIVN": "Rivian",
                "LCID": "Lucid"
            }
        }
        
        with open(self.watchlist_file, 'w', encoding='utf-8') as f:
            json.dump(default_lists, f, ensure_ascii=False, indent=4)
            
        self.logger.info("已创建默认观察列表")
        
    def save_watchlists(self):
        """保存观察列表"""
        try:
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(self.watchlists, f, ensure_ascii=False, indent=4)
            self.logger.info("观察列表已保存")
        except Exception as e:
            self.logger.error(f"保存观察列表时出错: {str(e)}")
            
    def get_watchlist(self, name: str) -> List[str]:
        """
        获取指定观察列表的股票代码
        
        Args:
            name (str): 观察列表名称
            
        Returns:
            List[str]: 股票代码列表
        """
        try:
            if name not in self.watchlists:
                self.logger.error(f"观察列表 {name} 不存在")
                return []
            return list(self.watchlists[name].keys())
        except Exception as e:
            self.logger.error(f"获取观察列表时出错: {str(e)}")
            return []
            
    def get_stock_name(self, list_name: str, symbol: str) -> str:
        """
        获取股票的中文名称
        
        Args:
            list_name (str): 观察列表名称
            symbol (str): 股票代码
            
        Returns:
            str: 股票名称
        """
        try:
            return self.watchlists[list_name].get(symbol, symbol)
        except Exception as e:
            self.logger.error(f"获取股票名称时出错: {str(e)}")
            return symbol
            
    def add_watchlist(self, name: str, stocks: Dict[str, str]) -> bool:
        """
        添加新的观察列表
        
        Args:
            name (str): 观察列表名称
            stocks (Dict[str, str]): 股票代码到名称的映射
            
        Returns:
            bool: 是否添加成功
        """
        try:
            name = self._validate_watchlist_name(name)
            if name in self.watchlists:
                self.logger.warning(f"观察列表 {name} 已存在，将被覆盖")
            self.watchlists[name] = stocks
            self.save_watchlists()
            return True
        except Exception as e:
            self.logger.error(f"添加观察列表时出错: {str(e)}")
            return False
            
    def remove_watchlist(self, name: str) -> bool:
        """
        删除观察列表
        
        Args:
            name (str): 观察列表名称
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if name not in self.watchlists:
                self.logger.error(f"观察列表 {name} 不存在")
                return False
            del self.watchlists[name]
            self.save_watchlists()
            return True
        except Exception as e:
            self.logger.error(f"删除观察列表时出错: {str(e)}")
            return False
            
    def add_stock(self, list_name: str, symbol: str, name: str) -> bool:
        """
        向观察列表添加股票
        
        Args:
            list_name (str): 观察列表名称
            symbol (str): 股票代码
            name (str): 股票名称
            
        Returns:
            bool: 是否添加成功
        """
        try:
            symbol = self._validate_symbol(symbol)
            if list_name not in self.watchlists:
                self.logger.error(f"观察列表 {list_name} 不存在")
                return False
            self.watchlists[list_name][symbol] = name
            self.save_watchlists()
            return True
        except Exception as e:
            self.logger.error(f"添加股票时出错: {str(e)}")
            return False
            
    def remove_stock(self, list_name: str, symbol: str) -> bool:
        """
        从观察列表删除股票
        
        Args:
            list_name (str): 观察列表名称
            symbol (str): 股票代码
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if list_name not in self.watchlists:
                self.logger.error(f"观察列表 {list_name} 不存在")
                return False
            if symbol not in self.watchlists[list_name]:
                self.logger.error(f"股票 {symbol} 不在观察列表中")
                return False
            del self.watchlists[list_name][symbol]
            self.save_watchlists()
            return True
        except Exception as e:
            self.logger.error(f"删除股票时出错: {str(e)}")
            return False
            
    def get_all_watchlists(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有观察列表
        
        Returns:
            Dict[str, Dict[str, str]]: 所有观察列表
        """
        return self.watchlists
        
    def get_watchlist_names(self) -> List[str]:
        """
        获取所有观察列表名称
        
        Returns:
            List[str]: 观察列表名称列表
        """
        return list(self.watchlists.keys())

    def _validate_symbol(self, symbol: str) -> str:
        """验证并标准化股票代码"""
        try:
            # 去除空白字符
            symbol = symbol.strip().upper()
            
            # 基本格式验证
            if not symbol or not symbol.isalnum():
                raise ValueError(f"无效的股票代码格式: {symbol}")
            
            return symbol
        except Exception as e:
            self.logger.error(f"股票代码验证失败: {str(e)}")
            raise

    def _validate_watchlist_name(self, name: str) -> str:
        """验证观察列表名称"""
        try:
            name = name.strip()
            if not name:
                raise ValueError("观察列表名称不能为空")
            return name
        except Exception as e:
            self.logger.error(f"观察列表名称验证失败: {str(e)}")
            raise

    def batch_add_stocks(self, list_name: str, stocks: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        批量添加股票
        
        Returns:
            Tuple[bool, List[str]]: (是否全部成功, 失败的股票列表)
        """
        try:
            list_name = self._validate_watchlist_name(list_name)
            if list_name not in self.watchlists:
                self.logger.error(f"观察列表 {list_name} 不存在")
                return False, list(stocks.keys())
            
            failed_symbols = []
            for symbol, name in stocks.items():
                try:
                    symbol = self._validate_symbol(symbol)
                    self.watchlists[list_name][symbol] = name
                except Exception as e:
                    failed_symbols.append(symbol)
                    self.logger.warning(f"添加股票失败 {symbol}: {str(e)}")
                
            self.save_watchlists()
            return len(failed_symbols) == 0, failed_symbols
        
        except Exception as e:
            self.logger.error(f"批量添加股票时出错: {str(e)}")
            return False, list(stocks.keys())

    def backup_watchlists(self) -> bool:
        """备份观察列表"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.config_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"watchlists_{timestamp}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.watchlists, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"观察列表已备份到: {backup_file}")
            return True
        except Exception as e:
            self.logger.error(f"备份观察列表时出错: {str(e)}")
            return False

    def restore_from_backup(self, backup_file: str) -> bool:
        """从备份恢复"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                self.logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                watchlists = json.load(f)
            
            # 验证备份数据
            if not isinstance(watchlists, dict):
                raise ValueError("无效的备份文件格式")
            
            # 创建当前配置的备份
            self.backup_watchlists()
            
            # 恢复数据
            self.watchlists = watchlists
            self.save_watchlists()
            
            self.logger.info(f"已从备份文件恢复: {backup_file}")
            return True
        except Exception as e:
            self.logger.error(f"恢复备份时出错: {str(e)}")
            return False

if __name__ == "__main__":
    try:
        manager = WatchlistManager()
        
        print("\n=== 观察列表管理器测试 ===")
        
        # 测试获取所有观察列表
        watchlists = manager.get_all_watchlists()
        print("\n1. 当前所有观察列表:")
        for name, stocks in watchlists.items():
            print(f"  {name}: {len(stocks)}支股票")
            
        # 测试添加新的观察列表
        new_list = {
            "AAPL": "苹果公司",
            "GOOGL": "谷歌公司"
        }
        print("\n2. 添加新的观察列表 '我的关注'")
        if manager.add_watchlist("我的关注", new_list):
            print("  添加成功")
            
        # 测试批量添加股票
        more_stocks = {
            "MSFT": "微软公司",
            "AMZN": "亚马逊公司",
            "NVDA": "英伟达公司"
        }
        print("\n3. 批量添加股票到 '我的关注'")
        success, failed = manager.batch_add_stocks("我的关注", more_stocks)
        if success:
            print("  全部添加成功")
        else:
            print(f"  部分添加失败: {failed}")
            
        # 测试备份
        print("\n4. 创建备份")
        if manager.backup_watchlists():
            print("  备份成功")
            
        # 获取并显示最终结果
        my_list = manager.get_watchlist("我的关注")
        print("\n5. 我的关注列表最终内容:")
        print(f"  股票代码: {my_list}")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
    finally:
        print("\n=== 测试完成 ===")
