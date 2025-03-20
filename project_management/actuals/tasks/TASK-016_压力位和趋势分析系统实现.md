# TASK-016: 压力位和趋势分析系统实现

## 基本信息

- **任务ID**: TASK-016
- **任务名称**: 压力位和趋势分析系统实现
- **负责人**: Yagami
- **开始日期**: 2025-03-20
- **计划完成日期**: 2025-03-25
- **实际完成日期**: -
- **状态**: 🚀 进行中
- **优先级**: 高
- **难度**: 高
- **预计工时**: 24小时
- **实际工时**: -

*生成时间：2025-03-20 00:05:40 PDT*

## 任务描述

实现基于经典技术分析理论的压力位识别和趋势判定系统，包括Fibonacci回调位、Market Profile理论和Dow Theory等核心分析方法。同时设计并实现个股分析卡片，展示压力位分布和趋势状态信息。

## 任务目标

1. 实现压力位识别系统，包括：
   - Fibonacci回调位计算
   - 历史价格分布密度分析
   - 移动平均线支撑压力系统

2. 实现趋势判定系统，包括：
   - Dow Theory核心原则实现
   - ADX趋势强度指标
   - 趋势线自动识别

3. 设计并实现个股分析卡片UI
4. 集成到现有的分析系统中

## 实现细节

### 1. 压力位识别系统（pressure_points.py）

```python
class PressurePointAnalyzer:
    def __init__(self, price_data: pd.DataFrame):
        """
        初始化压力位分析器
        
        参数:
            price_data: 包含OHLCV数据的DataFrame
        """
        self.price_data = price_data
        self.fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.ma_periods = [20, 50, 200]
    
    def calculate_fibonacci_levels(self, trend_high: float, trend_low: float) -> Dict[float, float]:
        """
        计算Fibonacci回调位
        
        参数:
            trend_high: 趋势高点
            trend_low: 趋势低点
            
        返回:
            Dict: Fibonacci水平位对应的价格
        """
        price_range = trend_high - trend_low
        return {
            level: trend_high - price_range * level
            for level in self.fib_levels
        }
    
    def analyze_price_distribution(self, window: int = 20) -> List[Dict]:
        """
        基于Market Profile理论分析价格分布
        
        参数:
            window: 分析窗口大小
            
        返回:
            List[Dict]: 主要价格区域及其强度
        """
        # 实现价格分布密度分析
        pass
    
    def get_ma_support_resistance(self) -> Dict[str, float]:
        """
        计算移动平均线支撑压力位
        
        返回:
            Dict: 各周期均线位置
        """
        ma_levels = {}
        for period in self.ma_periods:
            ma = self.price_data['Close'].rolling(window=period).mean()
            ma_levels[f'MA{period}'] = ma.iloc[-1]
        return ma_levels
```

### 2. 趋势判定系统（trend_analysis.py）

```python
class TrendAnalyzer:
    def __init__(self, price_data: pd.DataFrame):
        """
        初始化趋势分析器
        
        参数:
            price_data: 包含OHLCV数据的DataFrame
        """
        self.price_data = price_data
        self.adx_period = 14
        self.trend_threshold = 25  # ADX趋势强度阈值
    
    def calculate_adx(self) -> Tuple[float, float, float]:
        """
        计算ADX及方向指标
        
        返回:
            Tuple[float, float, float]: (ADX, +DI, -DI)
        """
        # 实现ADX计算
        pass
    
    def identify_trend_lines(self) -> Dict:
        """
        识别主要趋势线
        
        返回:
            Dict: 包含支撑和阻力趋势线参数
        """
        # 实现趋势线识别
        pass
    
    def analyze_dow_theory(self) -> Dict[str, str]:
        """
        基于Dow Theory分析趋势
        
        返回:
            Dict: 包含主要趋势和次要趋势的判断
        """
        # 实现Dow Theory分析
        pass
```

### 3. 个股分析卡片UI实现

在`trademind/ui/templates/stock_card.html`中添加新的分析卡片组件：

```html
<div class="analysis-card">
    <!-- 趋势研判面板 -->
    <div class="trend-panel">
        <h3>趋势研判</h3>
        <div class="trend-info">
            <div class="trend-status">
                <span class="trend-direction {{ trend_class }}">
                    趋势：{{ trend_direction }} {{ trend_arrow }}
                </span>
                <div class="trend-strength">
                    强度：<div class="strength-bar">
                        <div class="strength-value" style="width: {{ strength }}%"></div>
                    </div>
                    {{ strength }}%
                </div>
            </div>
        </div>
        
        <!-- 价格区间 -->
        <div class="price-levels">
            <div class="resistance-level">
                阻力: ${{ resistance_price }} ({{ resistance_source }})
            </div>
            <div class="current-price">
                现价: ${{ current_price }}
            </div>
            <div class="support-level">
                支撑: ${{ support_price }} ({{ support_source }})
            </div>
        </div>
        
        <!-- 操作建议 -->
        <div class="action-zone">
            <h4>建议操作区间</h4>
            <div class="buy-zone">
                买入: ${{ buy_zone_low }} ~ ${{ buy_zone_high }}
            </div>
            <div class="stop-loss">
                止损: ${{ stop_loss }}
            </div>
        </div>
    </div>
</div>
```

添加对应的CSS样式：

```css
.trend-panel {
    padding: 15px;
    border-radius: 8px;
    background: #f8f9fa;
    margin: 10px 0;
}

.trend-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 15px;
}

.trend-up {
    color: #00a960;
}

.trend-down {
    color: #ff4d4f;
}

.trend-neutral {
    color: #666;
}

.strength-bar {
    display: inline-block;
    width: 100px;
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    margin: 0 8px;
}

.strength-value {
    height: 100%;
    background: linear-gradient(90deg, #00a960, #52c41a);
    border-radius: 3px;
    transition: width 0.3s;
}

.price-levels {
    margin: 15px 0;
    padding: 10px;
    background: #fff;
    border-radius: 4px;
}

.action-zone {
    margin-top: 15px;
    padding: 10px;
    background: #fff;
    border-radius: 4px;
}
```

在`trademind/ui/web.py`中添加数据处理逻辑：

```python
def prepare_trend_analysis(analyzer_result: Dict) -> Dict:
    """
    准备趋势分析数据用于UI展示
    
    参数:
        analyzer_result: 分析器返回的原始结果
        
    返回:
        Dict: 处理后的UI展示数据
    """
    trend_direction = analyzer_result['trend_analysis']['direction']
    trend_strength = analyzer_result['trend_analysis']['strength']
    
    # 设置趋势方向的样式类和箭头
    trend_class = {
        'up': 'trend-up',
        'down': 'trend-down',
        'neutral': 'trend-neutral'
    }.get(trend_direction, 'trend-neutral')
    
    trend_arrow = {
        'up': '↑',
        'down': '↓',
        'neutral': '→'
    }.get(trend_direction, '→')
    
    # 获取关键价位
    price_levels = analyzer_result['pressure_points']
    
    return {
        'trend_direction': trend_direction,
        'trend_class': trend_class,
        'trend_arrow': trend_arrow,
        'strength': trend_strength,
        'resistance_price': price_levels['resistance']['price'],
        'resistance_source': price_levels['resistance']['source'],
        'support_price': price_levels['support']['price'],
        'support_source': price_levels['support']['source'],
        'current_price': analyzer_result['current_price'],
        'buy_zone_low': price_levels['buy_zone']['low'],
        'buy_zone_high': price_levels['buy_zone']['high'],
        'stop_loss': price_levels['stop_loss']
    }
```

### 4. 系统集成

在`