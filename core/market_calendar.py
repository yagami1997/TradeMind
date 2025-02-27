"""
市场日历管理
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import pandas as pd
import pandas_market_calendars as mcal
from zoneinfo import ZoneInfo

from .market_types import Exchange, ExchangeType

class MarketCalendar:
    """市场日历管理"""
    
    # 交易所日历映射
    CALENDAR_MAPPING = {
        ExchangeType.NYSE.value: "NYSE",
        ExchangeType.NASDAQ.value: "NASDAQ",
        ExchangeType.LSE.value: "LSE",
        ExchangeType.JPX.value: "JPX",
        ExchangeType.HKEx.value: "HKEX",
        # A股使用上交所日历
        ExchangeType.SSE.value: "SSE",
        ExchangeType.SZSE.value: "SSE"
    }
    
    _calendars = {}
    
    @classmethod
    def get_calendar(cls, exchange: str):
        """获取交易所日历"""
        if exchange not in cls._calendars:
            calendar_name = cls.CALENDAR_MAPPING.get(exchange)
            if not calendar_name:
                raise ValueError(f"未支持的交易所日历: {exchange}")
            cls._calendars[exchange] = mcal.get_calendar(calendar_name)
        return cls._calendars[exchange]
    
    @classmethod
    def is_trading_day(cls, exchange: str, check_date: Optional[date] = None) -> bool:
        """检查是否为交易日"""
        if check_date is None:
            check_date = date.today()
            
        calendar = cls.get_calendar(exchange)
        schedule = calendar.schedule(start_date=check_date, end_date=check_date)
        return not schedule.empty
    
    @classmethod
    def get_trading_days(cls, 
                        exchange: str,
                        start_date: date,
                        end_date: date) -> List[date]:
        """获取交易日列表"""
        calendar = cls.get_calendar(exchange)
        schedule = calendar.schedule(start_date=start_date, end_date=end_date)
        return schedule.index.date.tolist()
    
    @classmethod
    def get_next_trading_day(cls, 
                           exchange: str,
                           from_date: Optional[date] = None) -> Optional[date]:
        """获取下一个交易日"""
        if from_date is None:
            from_date = date.today()
            
        calendar = cls.get_calendar(exchange)
        schedule = calendar.schedule(
            start_date=from_date,
            end_date=from_date + pd.Timedelta(days=10)
        )
        
        if schedule.empty:
            return None
            
        next_dates = schedule.index.date
        for next_date in next_dates:
            if next_date > from_date:
                return next_date
        return None
    
    @classmethod
    def get_previous_trading_day(cls,
                               exchange: str,
                               from_date: Optional[date] = None) -> Optional[date]:
        """获取上一个交易日"""
        if from_date is None:
            from_date = date.today()
            
        calendar = cls.get_calendar(exchange)
        schedule = calendar.schedule(
            start_date=from_date - pd.Timedelta(days=10),
            end_date=from_date
        )
        
        if schedule.empty:
            return None
            
        prev_dates = schedule.index.date
        for prev_date in reversed(prev_dates):
            if prev_date < from_date:
                return prev_date
        return None
    
    @classmethod
    def get_trading_hours(cls, 
                         exchange: str,
                         for_date: Optional[date] = None) -> Dict[str, Dict[str, datetime]]:
        """获取指定日期的交易时间"""
        if for_date is None:
            for_date = date.today()
            
        config = Exchange.get_config(exchange)
        timezone = ZoneInfo(config["timezone"])
        trading_hours = config["trading_hours"]
        
        result = {}
        for period, times in trading_hours.items():
            if times:  # 某些市场可能没有 pre/post market
                start_time = datetime.strptime(times["start"], "%H:%M").time()
                end_time = datetime.strptime(times["end"], "%H:%M").time()
                
                result[period] = {
                    "start": datetime.combine(for_date, start_time).replace(tzinfo=timezone),
                    "end": datetime.combine(for_date, end_time).replace(tzinfo=timezone)
                }
                
        return result 
    
    @classmethod
    def get_market_status(cls, exchange: str) -> Dict[str, Any]:
        """获取市场当前状态
        
        Args:
            exchange: 交易所代码
            
        Returns:
            Dict[str, Any]: 包含市场状态信息的字典
        """
        now = datetime.now()
        trading_hours = cls.get_trading_hours(exchange)
        is_trading_day = cls.is_trading_day(exchange)
        
        status = {
            "exchange": exchange,
            "current_time": now.isoformat(),
            "is_trading_day": is_trading_day,
            "next_trading_day": cls.get_next_trading_day(exchange),
            "trading_periods": {}
        }
        
        if is_trading_day:
            for period, times in trading_hours.items():
                if times:
                    period_status = {
                        "is_active": times["start"] <= now <= times["end"],
                        "start_time": times["start"].isoformat(),
                        "end_time": times["end"].isoformat()
                    }
                    status["trading_periods"][period] = period_status
                    
        return status
        
    @classmethod
    def get_trading_breaks(cls, exchange: str) -> List[Dict[str, datetime]]:
        """获取交易休息时间
        
        Args:
            exchange: 交易所代码
            
        Returns:
            List[Dict[str, datetime]]: 交易休息时间列表
        """
        config = Exchange.get_config(exchange)
        trading_hours = config["trading_hours"]
        timezone = ZoneInfo(config["timezone"])
        today = date.today()
        
        breaks = []
        # 处理午休时间
        if "morning" in trading_hours and "afternoon" in trading_hours:
            morning_end = datetime.combine(
                today,
                datetime.strptime(trading_hours["morning"]["end"], "%H:%M").time()
            ).replace(tzinfo=timezone)
            
            afternoon_start = datetime.combine(
                today,
                datetime.strptime(trading_hours["afternoon"]["start"], "%H:%M").time()
            ).replace(tzinfo=timezone)
            
            breaks.append({
                "start": morning_end,
                "end": afternoon_start
            })
            
        return breaks
        
    @classmethod
    def get_trading_sessions(cls, exchange: str, for_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """获取交易时段信息
        
        Args:
            exchange: 交易所代码
            for_date: 指定日期，默认为今天
            
        Returns:
            List[Dict[str, Any]]: 交易时段列表
        """
        if for_date is None:
            for_date = date.today()
            
        if not cls.is_trading_day(exchange, for_date):
            return []
            
        trading_hours = cls.get_trading_hours(exchange, for_date)
        sessions = []
        
        for period, times in trading_hours.items():
            if times:
                session = {
                    "name": period,
                    "start": times["start"],
                    "end": times["end"],
                    "duration": (times["end"] - times["start"]).total_seconds() / 3600  # 小时
                }
                sessions.append(session)
                
        return sessions 