import json
from pathlib import Path
from typing import List, Dict

class WatchlistManager:
    def __init__(self):
        self.config_path = Path("config/watchlists.json")
        self.watchlists = self._load_watchlists()
    
    def _load_watchlists(self) -> Dict[str, List[str]]:
        """加载自选股配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                raise FileNotFoundError("配置文件不存在")
        except Exception as e:
            print(f"加载配置文件时出错: {str(e)}")
            return {}
    
    def save_watchlists(self) -> None:
        """保存自选股配置到文件"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.watchlists, f, indent=4)
        except Exception as e:
            print(f"保存配置文件时出错: {str(e)}")
    
    def get_group_symbols(self, group_name: str) -> List[str]:
        """获取指定分组的所有股票代码"""
        return self.watchlists.get(group_name, [])
    
    def get_all_symbols(self) -> List[str]:
        """获取所有股票代码"""
        all_symbols = []
        for symbols in self.watchlists.values():
            all_symbols.extend(symbols)
        return list(set(all_symbols))  # 去重
    
    def add_symbol(self, group_name: str, symbol: str) -> bool:
        """添加股票到指定分组"""
        if group_name not in self.watchlists:
            self.watchlists[group_name] = []
        
        if symbol not in self.watchlists[group_name]:
            self.watchlists[group_name].append(symbol)
            self.save_watchlists()
            return True
        return False
    
    def remove_symbol(self, group_name: str, symbol: str) -> bool:
        """从指定分组删除股票"""
        if group_name in self.watchlists and symbol in self.watchlists[group_name]:
            self.watchlists[group_name].remove(symbol)
            self.save_watchlists()
            return True
        return False

# 测试代码
if __name__ == "__main__":
    # 创建WatchlistManager实例
    manager = WatchlistManager()
    
    # 测试获取所有股票
    print("所有股票:")
    print(manager.get_all_symbols())
    
    # 测试获取特定分组的股票
    print("\n我的精选股票:")
    print(manager.get_group_symbols("我的精选"))
    
    # 测试添加新股票
    print("\n添加新股票:")
    success = manager.add_symbol("我的精选", "NFLX")
    print(f"添加NFLX: {'成功' if success else '失败'}")
    
    # 再次显示分组股票
    print("\n更新后的我的精选股票:")
    print(manager.get_group_symbols("我的精选"))