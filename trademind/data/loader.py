"""
TradeMind Lite（轻量版）- 数据加载器

本模块包含股票数据加载相关的功能。
"""

import os
import json
import time
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple, Any, Union
import re
from collections import OrderedDict as CollectionsOrderedDict

# 设置日志
logger = logging.getLogger(__name__)

def get_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    获取股票历史数据
    
    参数:
        symbol: 股票代码
        period: 数据周期，如1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: 数据间隔，如1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        
    返回:
        pd.DataFrame: 股票历史数据
    """
    try:
        # 获取更长时间的历史数据，确保有足够的数据进行回测
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty or len(hist) < 100:  # 确保至少有100个交易日的数据
            print(f"⚠️ {symbol} 的历史数据不足，尝试获取最大可用数据")
            # 尝试获取最大可用数据
            hist = stock.history(period="max")
        
        return hist
    except Exception as e:
        logger.error(f"获取 {symbol} 的历史数据时出错: {str(e)}")
        print(f"❌ 获取 {symbol} 的历史数据失败: {str(e)}")
        return pd.DataFrame()

def get_stock_info(symbol: str) -> Dict:
    """
    获取股票信息
    
    参数:
        symbol: 股票代码
        
    返回:
        Dict: 股票信息
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return info
    except Exception as e:
        logger.error(f"获取 {symbol} 的信息时出错: {str(e)}")
        return {}

def convert_stock_code(code: str, market: str = "US") -> str:
    """
    转换股票代码为Yahoo Finance格式
    
    参数:
        code: 原始股票代码
        market: 市场类型，US或HK
        
    返回:
        str: 转换后的股票代码或错误信息
    """
    # 清理代码（去除空格和特殊字符）
    code = code.strip().upper()
    
    # 美股指数转换映射
    index_mapping = {
        '.DJI': '^DJI',
        '.IXIC': '^IXIC',
        '.SPX': '^GSPC',
        '.VIX': '^VIX',
        '.NDX': '^NDX'
    }
    
    # 处理美股
    if market == "US":
        # 处理指数
        if code in index_mapping:
            return index_mapping[code]
        
        # 处理期货合约
        if code.endswith(('main', '2503', '2504', '2505')) or re.match(r'[A-Z]+\d{4}$', code):
            return {"valid": False, "reason": "期货合约不支持导入"}
        
        # 处理富途/MOOMOO格式的美股代码（如US.AAPL）
        if code.startswith('US.'):
            return code[3:]
        
        # 处理雪球格式的美股代码（如$AAPL$）
        if code.startswith('$') and code.endswith('$'):
            return code[1:-1]
        
        # 普通美股代码直接返回
        return code.upper()
    
    # 处理港股
    if market == "HK":
        # 处理恒生指数
        if code == '800000':
            return '^HSI'
        
        # 处理富途/MOOMOO格式的港股代码（如HK.00700）
        if code.startswith('HK.'):
            code = code[3:]
        
        # 处理雪球格式的港股代码（如$00700$）
        if code.startswith('$') and code.endswith('$'):
            code = code[1:-1]
        
        # 移除前导零并添加.HK后缀
        return code.lstrip('0') + '.HK'
    
    return {"valid": False, "reason": "不支持的市场"}

def convert_index_code(code: str) -> str:
    """
    将常见指数代码和期货合约代码转换为YFinance可识别的格式
    
    参数:
        code: 原始代码
        
    返回:
        str: 转换后的代码
    """
    # 如果代码已经是YFinance格式，直接返回
    if code.startswith('^'):
        return code
        
    # 常见指数代码映射
    index_mapping = {
        # 美国指数
        ".DJI": "^DJI",     # 道琼斯工业平均指数
        ".IXIC": "^IXIC",   # 纳斯达克综合指数
        ".SPX": "^GSPC",    # 标普500指数
        ".VIX": "^VIX",     # VIX波动率指数
        ".NDX": "^NDX",     # 纳斯达克100指数
        ".RUT": "^RUT",     # 罗素2000指数
        "SPX": "^GSPC",     # 标普500指数简写
        "DJI": "^DJI",      # 道指简写
        "IXIC": "^IXIC",    # 纳指简写
        "VIX": "^VIX",      # VIX简写
        "NDX": "^NDX",      # 纳指100简写
        
        # 国际指数
        ".FTSE": "^FTSE",   # 英国富时100指数
        ".N225": "^N225",   # 日经225指数
        ".HSI": "^HSI",     # 恒生指数
        ".SSEC": "^SSEC",   # 上证综指
        ".SZSC": "^SZSC",   # 深证成指
        
        # 债券收益率
        ".TNX": "^TNX",     # 10年期美国国债收益率
        ".TYX": "^TYX",     # 30年期美国国债收益率
        
        # 商品
        "GCMAIN": "GC=F",   # 黄金期货
        "SIMAIN": "SI=F",   # 白银期货
        "CLMAIN": "CL=F",   # 原油期货
        "NGMAIN": "NG=F",   # 天然气期货
    }
    
    # 检查是否在映射表中
    if code in index_mapping:
        return index_mapping[code]
    
    # 处理期货合约代码
    # 例如：ES2503 -> ES=F (标普500期货)
    # 例如：NQ2503 -> NQ=F (纳斯达克期货)
    # 例如：GC2504 -> GC=F (黄金期货)
    futures_pattern = re.compile(r'^([A-Z]{2})(\d{4})$')
    match = futures_pattern.match(code)
    if match:
        futures_code = match.group(1)
        # 常见期货代码映射
        futures_mapping = {
            "ES": "ES=F",  # 标普500期货
            "NQ": "NQ=F",  # 纳斯达克期货
            "YM": "YM=F",  # 道琼斯期货
            "GC": "GC=F",  # 黄金期货
            "SI": "SI=F",  # 白银期货
            "CL": "CL=F",  # 原油期货
            "NG": "NG=F",  # 天然气期货
            "ZB": "ZB=F",  # 30年期美国国债期货
            "ZN": "ZN=F",  # 10年期美国国债期货
            "ZF": "ZF=F",  # 5年期美国国债期货
            "ZT": "ZT=F",  # 2年期美国国债期货
            "HG": "HG=F",  # 铜期货
            "PL": "PL=F",  # 铂金期货
            "PA": "PA=F",  # 钯金期货
            "ZC": "ZC=F",  # 玉米期货
            "ZS": "ZS=F",  # 大豆期货
            "ZW": "ZW=F",  # 小麦期货
            "KC": "KC=F",  # 咖啡期货
            "CT": "CT=F",  # 棉花期货
            "SB": "SB=F",  # 糖期货
            "CC": "CC=F",  # 可可期货
            "OJ": "OJ=F",  # 橙汁期货
            "LB": "LB=F",  # 木材期货
        }
        if futures_code in futures_mapping:
            return futures_mapping[futures_code]
    
    # 如果不在映射表中但以点开头，尝试转换为^格式
    if code.startswith("."):
        return "^" + code[1:]
    
    # 返回原始代码
    return code

def validate_stock_code(code: str, translate: bool = True) -> dict:
    """
    验证股票代码是否有效，并返回相关信息
    
    参数:
        code: 股票代码
        translate: 是否翻译股票名称为中文
        
    返回:
        dict: 包含验证结果的字典
    """
    try:
        # 去除空格和特殊字符
        code = code.strip().upper()
        
        # 如果代码为空，返回错误
        if not code:
            return {
                "code": "",
                "valid": False,
                "error": "股票代码不能为空"
            }
        
        # 检查是否为期货合约代码（如ES2503, NQ2503等）
        futures_pattern = re.compile(r'^([A-Z]{2})(\d{4})$')
        if futures_pattern.match(code):
            return {
                "code": code,
                "valid": False,
                "error": f"不支持期货合约代码，请使用普通股票代码"
            }
        
        # 检查是否为期货或期权
        if any(pattern in code for pattern in ["/", "=F", "-C", "-P"]):
            contract_type = "期货" if any(pattern in code for pattern in ["/", "=F"]) else "期权"
            return {
                "code": code,
                "valid": False,
                "error": f"不支持{contract_type}合约，请输入普通股票代码"
            }
            
        # 检查是否为港股代码格式（纯数字或数字.HK）
        if code.isdigit() and len(code) <= 5:
            return {
                "code": code,
                "valid": False,
                "error": "不支持的市场代码，请输入美股代码"
            }
            
        if code.endswith('.HK'):
            return {
                "code": code,
                "valid": False,
                "error": "不支持的市场代码，请输入美股代码"
            }
        
        # 转换指数代码
        yf_code = convert_index_code(code)
        
        # 如果转换后的代码包含"=F"，说明是期货代码
        if "=F" in yf_code:
            return {
                "code": code,
                "valid": False,
                "error": f"不支持期货合约，请输入普通股票代码"
            }
        
        # 尝试获取股票信息
        try:
            stock_info = yf.Ticker(yf_code).info
            
            # 检查是否获取到有效信息
            if "symbol" not in stock_info or stock_info.get("regularMarketPrice") is None:
                return {
                    "code": code,
                    "valid": False,
                    "error": "无法获取股票信息，请检查代码是否正确"
                }
            
            # 检查市场类型
            market_type = stock_info.get("quoteType", "").lower()
            if market_type not in ["equity", "etf", "index"]:
                return {
                    "code": code,
                    "valid": False,
                    "error": f"不支持的市场类型: {market_type}，仅支持股票、ETF和指数"
                }
            
            # 获取股票名称
            english_name = stock_info.get("shortName", "") or stock_info.get("longName", "")
            
            # 获取中文名称（如果需要）
            chinese_name = ""
            if translate and english_name:
                chinese_name = get_chinese_name(code, english_name)
            
            # 构建结果
            result = {
                "code": code,
                "yf_code": yf_code if yf_code != code else None,  # 如果代码被转换，记录YF代码
                "valid": True,
                "name": chinese_name if chinese_name and translate else english_name,
                "english_name": english_name,
                "price": stock_info.get("regularMarketPrice", 0),
                "currency": stock_info.get("currency", "USD"),
                "market_type": market_type
            }
            
            return result
        except Exception as e:
            error_msg = str(e)
            
            # 处理常见错误
            if "No data found" in error_msg or "404" in error_msg:
                return {
                    "code": code,
                    "valid": False,
                    "error": f"无法识别的股票代码: {code}"
                }
            elif "NoneType" in error_msg:
                return {
                    "code": code,
                    "valid": False,
                    "error": f"获取股票数据时出错: 数据格式不正确"
                }
            else:
                return {
                    "code": code,
                    "valid": False,
                    "error": f"获取股票数据时出错: {error_msg[:100]}"
                }
    
    except Exception as e:
        return {
            "code": code,
            "valid": False,
            "error": f"验证股票代码时出错: {str(e)[:100]}"
        }

def get_chinese_name(symbol: str, english_name: str) -> str:
    """
    获取股票的中文名称，但不再使用硬编码的映射表
    
    参数:
        symbol: 股票代码
        english_name: 英文名称
        
    返回:
        str: 中文名称，如果没有则返回英文名称
    """
    # 尝试根据股票类型和名称特征进行翻译
    if symbol.startswith('^'):  # 指数
        if "Composite" in english_name:
            return english_name.replace("Composite", "综合") + "指数"
        elif "Index" in english_name:
            return english_name.replace("Index", "") + "指数"
        else:
            return english_name + "指数"
    
    # 尝试翻译ETF
    if "ETF" in english_name or "Fund" in english_name:
        # 提取ETF的主要特征
        if "S&P 500" in english_name:
            return "标普500" + ("ETF" if "ETF" in english_name else "基金")
        elif "NASDAQ" in english_name or "Nasdaq" in english_name:
            return "纳斯达克" + ("ETF" if "ETF" in english_name else "基金")
        elif "Technology" in english_name:
            return "科技行业" + ("ETF" if "ETF" in english_name else "基金")
        elif "Energy" in english_name:
            return "能源行业" + ("ETF" if "ETF" in english_name else "基金")
        elif "Financial" in english_name:
            return "金融行业" + ("ETF" if "ETF" in english_name else "基金")
        elif "Health" in english_name:
            return "医疗健康" + ("ETF" if "ETF" in english_name else "基金")
        elif "Consumer" in english_name:
            if "Staples" in english_name:
                return "必需消费品" + ("ETF" if "ETF" in english_name else "基金")
            elif "Discretionary" in english_name:
                return "非必需消费品" + ("ETF" if "ETF" in english_name else "基金")
            else:
                return "消费品" + ("ETF" if "ETF" in english_name else "基金")
    
    # 不再使用硬编码的中文名称映射，直接返回英文名称
    return english_name

def batch_validate_stock_codes(codes: List[str], market: str = "US", translate: bool = False) -> List[Dict]:
    """
    批量验证股票代码
    
    参数:
        codes: 股票代码列表
        market: 市场类型，仅支持US
        translate: 是否翻译股票名称为中文
        
    返回:
        List[Dict]: 验证结果列表
    """
    if not codes:
        logger.warning("批量验证股票代码时收到空列表")
        return []
    
    logger.info(f"开始批量验证 {len(codes)} 个股票代码，市场: US, 翻译: {translate}")
    results = []
    
    for code in codes:
        try:
            # 跳过空代码
            if not code or not code.strip():
                logger.warning("跳过空股票代码")
                results.append({
                    "code": "",
                    "valid": False,
                    "error": "股票代码不能为空"
                })
                continue
                
            # 验证单个股票代码
            logger.debug(f"验证股票代码: {code}")
            result = validate_stock_code(code, translate=translate)
            results.append(result)
            
            # 记录验证结果
            if result.get("valid", False):
                logger.debug(f"股票代码 {code} 验证有效")
            else:
                logger.debug(f"股票代码 {code} 验证无效: {result.get('error', '未知错误')}")
                
        except Exception as e:
            logger.error(f"验证股票代码 {code} 时出错: {str(e)}", exc_info=True)
            results.append({
                "code": code,
                "valid": False,
                "error": f"验证出错: {str(e)}"
            })
    
    # 记录验证结果统计
    valid_count = sum(1 for r in results if r.get("valid", False))
    logger.info(f"批量验证完成: 总计 {len(results)}, 有效 {valid_count}, 无效 {len(results) - valid_count}")
    
    return results

def parse_stock_text(text: str) -> List[str]:
    """
    解析股票文本，支持多种格式
    
    参数:
        text: 股票文本
        
    返回:
        List[str]: 解析出的股票代码列表
    """
    if not text:
        return []
    
    # 替换常见分隔符为空格
    text = re.sub(r'[,\t\n]+', ' ', text)
    
    # 分割并过滤空字符串
    codes = []
    for item in text.split():
        # 提取可能的股票代码
        # 支持多种格式：普通代码、富途格式(US.AAPL)、雪球格式($AAPL$)等
        code = item.strip()
        if code:
            codes.append(code)
    
    return codes

def update_watchlists_file(stocks: List[Dict], group_name: str = None) -> bool:
    """
    更新watchlists.json文件，支持用户指定分类
    
    参数:
        stocks: 股票列表，每个股票为一个字典，包含symbol, name等信息
        group_name: 分组名称，如果提供则所有股票放入该分组，否则放入默认分组
        
    返回:
        bool: 是否成功更新
    """
    try:
        # 读取现有的watchlists.json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'watchlists.json')
        
        # 确保使用OrderedDict保持顺序
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                watchlists = json.load(f, object_pairs_hook=CollectionsOrderedDict)
        else:
            watchlists = CollectionsOrderedDict()
        
        # 备份原文件
        if os.path.exists(config_path):
            backup_path = config_path + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(watchlists, f, ensure_ascii=False, indent=4, sort_keys=False)
        
        # 使用指定的分组名称
        target_group = group_name or "自选股"
        
        # 确保分组存在
        if target_group not in watchlists:
            watchlists[target_group] = CollectionsOrderedDict()
        
        # 添加股票到分组
        for stock in stocks:
            if stock.get('valid', False):
                symbol = stock.get('converted', stock.get('symbol', ''))
                name = stock.get('name', symbol)
                if symbol:
                    watchlists[target_group][symbol] = name
        
        # 写入更新后的文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(watchlists, f, ensure_ascii=False, indent=4, sort_keys=False)
            
        return True
    except Exception as e:
        logger.error(f"更新watchlists.json文件时出错: {str(e)}")
        return False

def import_stocks_to_watchlist(user_id: str, stocks: List[Dict], group_name: str = "", auto_categories: bool = False, clear_existing: bool = False, translate: bool = False) -> Dict:
    """
    导入股票到自选股列表
    
    参数:
        user_id: 用户ID
        stocks: 股票列表，每个股票是一个字典，包含code和name
        group_name: 分组名称，如果不指定则使用默认分组
        auto_categories: 是否自动分类(此参数已不再使用自动分类逻辑，仅为保持API兼容)
        clear_existing: 是否清空现有列表
        translate: 是否翻译股票名称
        
    返回:
        Dict: 导入结果
    """
    try:
        # 获取现有的自选股列表
        user_watchlists = get_user_watchlists(user_id) if not clear_existing else CollectionsOrderedDict()
        
        # 使用指定的分组名称
        target_group = group_name or "自选股"
        
        # 确保分组存在
        if target_group not in user_watchlists:
            user_watchlists[target_group] = CollectionsOrderedDict()
        
        # 统计导入结果
        imported_count = 0
        skipped_count = 0
        invalid_count = 0
        
        # 过滤有效的股票
        valid_stocks = [s for s in stocks if s.get('valid', True)]
        
        # 添加股票到分组
        for stock in valid_stocks:
            stock_code = stock.get('code', '')
            if not stock_code:
                continue
            
            # 使用简单字符串格式保存股票名称
            stock_name = stock.get('name', '')
            
            # 如果需要翻译，并且名称是英文，尝试翻译
            if translate and stock_name and is_english_name(stock_name):
                # 获取股票代码（确保是Yahoo Finance格式）
                yf_code = stock.get('yf_code', stock_code)
                
                # 尝试获取中文名称
                try:
                    # 使用validate_stock_code函数获取中文名称
                    validation_result = validate_stock_code(yf_code, translate=True)
                    if validation_result.get('valid') and validation_result.get('name'):
                        stock_name = validation_result.get('name')
                except Exception as e:
                    logger.warning(f"翻译股票名称失败: {stock_code} - {e}")
            
            # 获取股票类型
            market_type = stock.get('market_type', 'equity').lower()
            
            # 确保指数代码使用正确的格式
            if stock_code.startswith('.') or (market_type == 'index' and not stock_code.startswith('^')):
                # 使用convert_index_code函数转换指数代码
                stock_code = convert_index_code(stock_code)
            
            # 添加到分组
            user_watchlists[target_group][stock_code] = stock_name
            
            imported_count += 1
        
        # 保存更新后的自选股列表
        save_user_watchlists(user_id, user_watchlists)
        
        # 返回结果
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'invalid': invalid_count,
            'watchlists': user_watchlists
        }
    
    except Exception as e:
        logger.error(f"导入股票到自选股列表出错: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_user_watchlists(user_id: str) -> Dict:
    """获取用户的自选股列表"""
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # 获取用户配置目录
        user_config_dir = os.path.join(project_root, 'config', 'users', user_id)
        
        # 确保目录存在
        os.makedirs(user_config_dir, exist_ok=True)
        
        # 自选股文件路径
        watchlists_file = os.path.join(user_config_dir, 'watchlists.json')
        
        # 如果用户特定的文件不存在，返回空字典
        if not os.path.exists(watchlists_file):
            return CollectionsOrderedDict()
        
        # 直接读取JSON文件，确保严格保持JSON中的顺序
        with open(watchlists_file, 'r', encoding='utf-8') as f:
            # 使用object_pairs_hook=OrderedDict参数确保保持JSON中的顺序
            watchlists_data = json.load(f, object_pairs_hook=CollectionsOrderedDict)
            
            # 确保每个分组内的股票也使用OrderedDict并保持原始顺序
            ordered_data = CollectionsOrderedDict()
            for group_name, stocks in watchlists_data.items():
                # 直接使用OrderedDict保持原始顺序，不排序
                ordered_data[group_name] = CollectionsOrderedDict(stocks)
            
            # 记录读取到的顺序，帮助调试
            logger.debug(f"读取到的分组顺序: {list(ordered_data.keys())}")
            for group, stocks in ordered_data.items():
                logger.debug(f"  分组 '{group}' 的股票顺序: {list(stocks.keys())}")
            
            return ordered_data
    
    except Exception as e:
        logger.exception(f"获取用户自选股列表时出错: {str(e)}")
        return CollectionsOrderedDict()

def save_user_watchlists(user_id: str, watchlists: Dict) -> bool:
    """保存用户的自选股列表"""
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # 获取用户配置目录
        user_config_dir = os.path.join(project_root, 'config', 'users', user_id)
        
        # 构建文件路径
        file_path = os.path.join(user_config_dir, 'watchlists.json')
        
        # 确保目录存在
        os.makedirs(user_config_dir, exist_ok=True)
        
        # 使用 OrderedDict 保存数据，确保顺序一致性
        ordered_watchlists = CollectionsOrderedDict()
        
        # 严格按照传入的顺序添加分组和股票，不做任何排序
        for group_name, stocks in watchlists.items():
            # 如果股票不是 OrderedDict 类型，转换为 OrderedDict
            if not isinstance(stocks, CollectionsOrderedDict):
                ordered_watchlists[group_name] = CollectionsOrderedDict(stocks)
            else:
                ordered_watchlists[group_name] = stocks
        
        # 记录将要保存的顺序，帮助调试
        logger.debug(f"将要保存的分组顺序: {list(ordered_watchlists.keys())}")
        for group, stocks in ordered_watchlists.items():
            logger.debug(f"  分组 '{group}' 的股票顺序: {list(stocks.keys())}")
        
        # 直接保存文件，使用 OrderedDict 确保顺序
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 使用 sort_keys=False 确保不会对键进行排序
                json.dump(ordered_watchlists, f, ensure_ascii=False, indent=4, sort_keys=False)
            
            logger.info(f"成功保存自选股列表到文件: {file_path}")
            return True
            
        except Exception as write_error:
            logger.error(f"写入自选股文件失败: {str(write_error)}")
            
            # 尝试使用临时文件
            try:
                temp_file = file_path + '.temp'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    # 使用 sort_keys=False 确保不会对键进行排序
                    json.dump(ordered_watchlists, f, ensure_ascii=False, indent=4, sort_keys=False)
                logger.info(f"已写入临时文件: {temp_file}")
                
                # 尝试重命名临时文件
                os.replace(temp_file, file_path)
                logger.info(f"已将临时文件重命名为正式文件")
                return True
            except Exception as temp_error:
                logger.error(f"使用临时文件保存失败: {str(temp_error)}")
                return False
    
    except Exception as e:
        logger.exception(f"保存用户自选股列表时出错: {str(e)}")
        return False

def is_english_name(name: str) -> bool:
    """
    判断股票名称是否为英文
    
    参数:
        name: 股票名称
        
    返回:
        bool: 是否为英文名称
    """
    if not name:
        return False
    
    # 检查是否包含中文字符
    for char in name:
        if '\u4e00' <= char <= '\u9fff':
            return False
    
    # 如果不包含中文字符，且包含英文字母，则认为是英文名称
    return any(c.isalpha() for c in name) 