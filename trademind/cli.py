import sys

def show_main_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("                    TradeMind Lite 主菜单")
    print("="*60 + "\n")
    
    menu_items = [
        ("1", "命令行模式", "交互式命令行界面，适合脚本操作"),
        ("2", "Web模式", "图形化Web界面，提供完整功能"),
        ("q", "退出程序", "结束程序运行")
    ]
    
    # 计算最长的选项长度，用于对齐
    max_option_len = max(len(item[0]) for item in menu_items)
    max_name_len = max(len(item[1]) for item in menu_items)
    
    # 打印菜单项
    print("  选项" + " " * (max_option_len-2) + "    功能" + " " * (max_name_len-2) + "    描述")
    print("  " + "-"*56)  # 分隔线
    
    for option, name, desc in menu_items:
        # 使用f-string和固定宽度确保对齐
        print(f"  {option:<{max_option_len}}    {name:<{max_name_len}}    {desc}")
    
    print("\n" + "="*60)
    
    while True:
        choice = input("\n请选择操作 [1/2/q]: ").strip().lower()
        if choice in ['1', '2', 'q']:
            return choice
        print("无效的选择，请重试")

if __name__ == "__main__":
    try:
        while True:
            choice = show_main_menu()
            
            if choice == 'q':
                print("\n感谢使用 TradeMind Lite！")
                break
            elif choice == '1':
                # 命令行模式
                from trademind.ui.cli import run_cli
                run_cli()
            elif choice == '2':
                # Web模式
                from trademind.ui.web import run_web_server
                run_web_server(port=3336)
                
    except KeyboardInterrupt:
        print("\n\n程序已终止")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
        sys.exit(1) 