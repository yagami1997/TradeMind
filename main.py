import logging
from core.backtest_manager import BacktestManager
from typing import Optional
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('trading_system.log')
    ]
)

logger = logging.getLogger(__name__)

class TradeMindSystem:
    """TradeMind交易系统主类"""
    
    def __init__(self):
        self.backtest_manager: Optional[BacktestManager] = None
        
    def display_main_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("TradeMind 交易系统")
        print("="*50)
        print("1. 策略回测")
        print("2. 实时交易")
        print("3. 数据分析")
        print("4. 系统设置")
        print("0. 退出系统")
        print("="*50)
        return input("请选择功能: ")
        
    def display_backtest_menu(self):
        """显示回测菜单"""
        print("\n" + "="*50)
        print("策略回测系统")
        print("="*50)
        print("1. 选择策略")
        print("2. 设置回测参数")
        print("3. 执行回测")
        print("4. 查看历史报告")
        print("0. 返回主菜单")
        print("="*50)
        return input("请选择功能: ")
        
    def handle_backtest(self):
        """处理回测相关操作"""
        if not self.backtest_manager:
            self.backtest_manager = BacktestManager()
            
        while True:
            choice = self.display_backtest_menu()
            
            if choice == '1':
                if self.backtest_manager.select_strategy():
                    print("策略选择成功")
                else:
                    print("策略选择失败")
                    
            elif choice == '2':
                if self.backtest_manager.configure_backtest():
                    print("参数配置成功")
                else:
                    print("参数配置失败")
                    
            elif choice == '3':
                if not self.backtest_manager.validate_parameters():
                    print("请先完成策略选择和参数配置")
                    continue
                    
                if self.backtest_manager.run_backtest():
                    print("回测执行完成")
                else:
                    print("回测执行失败")
                    
            elif choice == '4':
                self.backtest_manager.view_reports()
                
            elif choice == '0':
                break
                
    def handle_realtime_trading(self):
        """处理实时交易"""
        print("\n实时交易功能开发中...")
        
    def handle_data_analysis(self):
        """处理数据分析"""
        print("\n数据分析功能开发中...")
        
    def handle_system_settings(self):
        """处理系统设置"""
        print("\n系统设置功能开发中...")
        
    def run(self):
        """运行交易系统"""
        try:
            while True:
                choice = self.display_main_menu()
                
                if choice == '1':
                    self.handle_backtest()
                elif choice == '2':
                    self.handle_realtime_trading()
                elif choice == '3':
                    self.handle_data_analysis()
                elif choice == '4':
                    self.handle_system_settings()
                elif choice == '0':
                    print("\n感谢使用 TradeMind 交易系统，再见！")
                    break
                else:
                    print("\n无效的选择，请重试")
                    
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
        except Exception as e:
            logger.error(f"系统运行错误: {e}")
        finally:
            print("\n正在安全退出系统...")
            # 这里可以添加清理工作
            
def main():
    """程序入口"""
    # 确保必要的目录存在
    os.makedirs("reports/output/backtest", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 运行系统
    system = TradeMindSystem()
    system.run()

if __name__ == "__main__":
    main()
