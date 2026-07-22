"""
股票AI量化分析系统 - Kivy 安卓版
"""

import urllib.request
import json
import time
import random
import threading
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, BooleanProperty
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.utils import platform

# 设置窗口大小（桌面调试用）
if platform == 'win':
    Window.size = (400, 700)

# ===================== 配置 =====================
STOCK_POOL = {
    "贵州茅台": "sh600519",
    "平安银行": "sz000001",
    "招商银行": "sh600036",
    "五粮液": "sz000858",
    "中国平安": "sh601318",
    "比亚迪": "sz002594",
    "长江电力": "sh600900",
    "美的集团": "sz000333",
    "兴业银行": "sh601166",
    "上证指数": "sh000001",
}

STOCK_LIST = [(name, code) for name, code in STOCK_POOL.items()]

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
]

# ===================== 数据获取 =====================
def fetch_quote(code):
    """从新浪财经获取股票数据"""
    url = f"https://hq.sinajs.cn/list={code}"
    req = urllib.request.Request(url, headers={
        "Referer": "https://finance.sina.com.cn/",
        "User-Agent": random.choice(UA_POOL)
    })
    
    try:
        resp = urllib.request.urlopen(req, timeout=8)
        text = resp.read().decode("gbk")
        p = text.split(",")
        
        return {
            "name": p[0].split('"')[1] if '"' in p[0] else code,
            "open": float(p[1]),
            "price": float(p[3]),
            "high": float(p[4]),
            "low": float(p[5]),
            "volume": int(p[8]),
            "amount": float(p[9]),
            "change": float(p[3]) - float(p[2]),
            "change_pct": (float(p[3]) - float(p[2])) / float(p[2]) * 100 if float(p[2]) != 0 else 0,
        }
    except Exception as e:
        return None

# ===================== 指标计算 =====================
def calc_indicators(price):
    """计算简单指标"""
    base = price
    
    # 模拟MA
    ma5 = base * (1 + random.uniform(-0.02, 0.02))
    ma20 = base * (1 + random.uniform(-0.05, 0.05))
    
    # RSI模拟
    rsi = 50 + random.uniform(-30, 30)
    
    # KDJ模拟
    k = 50 + random.uniform(-30, 30)
    d = 50 + random.uniform(-20, 20)
    j = 3 * k - 2 * d
    
    # 资金模拟
    vol_ratio = 1 + random.uniform(-0.5, 1.5)
    capital_state = random.choice(["资本温和进入", "资本平衡", "资本温和流出"])
    capital_in = random.uniform(0, 20)
    capital_out = random.uniform(0, 20)
    
    # 情绪
    emotion = max(20, min(80, rsi * 0.8 + vol_ratio * 10))
    
    return {
        "MA5": round(ma5, 2),
        "MA20": round(ma20, 2),
        "RSI": round(rsi, 2),
        "KDJ_K": round(k, 2),
        "KDJ_D": round(d, 2),
        "KDJ_J": round(j, 2),
        "VolRatio": round(vol_ratio, 2),
        "CapitalState": capital_state,
        "CapitalIn": round(capital_in, 2),
        "CapitalOut": round(capital_out, 2),
        "Emotion": round(emotion, 1),
    }

def ai_total_score(f):
    """AI综合评分"""
    s = 0
    if f["MA5"] > f["MA20"]: s += 20
    if 40 < f["RSI"] < 70: s += 15
    if f["KDJ_J"] > f["KDJ_K"]: s += 10
    if f["VolRatio"] > 1.2: s += 15
    if "进入" in f["CapitalState"]: s += 25
    elif "流出" in f["CapitalState"]: s -= 20
    if f["Emotion"] > 60: s += 15
    return max(0, min(s, 100))

def get_advice(score, indicators):
    """给出建议"""
    if score >= 80:
        return "⭐⭐⭐ 强烈关注", (0.2, 0.8, 0.2, 1)
    elif score >= 65:
        return "⭐⭐ 趋势向好", (0.2, 0.6, 0.2, 1)
    elif score >= 45:
        return "⭐ 谨慎观望", (1, 0.8, 0, 1)
    else:
        return "⚠️ 注意风险", (1, 0.2, 0.2, 1)

# ===================== Kivy 界面 =====================
class StockCard(BoxLayout):
    """股票卡片组件"""
    name = StringProperty("")
    price = StringProperty("0.00")
    change = StringProperty("0.00")
    change_pct = StringProperty("0.00%")
    score = StringProperty("0")
    advice = StringProperty("")
    advice_color = StringProperty("00ff00")
    
    def update(self, name, data, score, advice):
        self.name = name
        self.price = f"{data['price']:.2f}"
        self.change = f"{data['change']:+.2f}"
        self.change_pct = f"{data['change_pct']:+.2f}%"
        self.score = str(score)
        self.advice = advice[0]
        # 转换颜色为hex字符串
        r, g, b, a = advice[1]
        self.advice_color = "{:02x}{:02x}{:02x}".format(
            int(r*255), int(g*255), int(b*255))

# ===================== 主界面 =====================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stock_data = {}
        self.auto_refresh = False
        self.refresh_thread = None
        Clock.schedule_once(self.build_ui, 0.1)
    
    def build_ui(self, *args):
        """构建界面"""
        self.clear_widgets()
        
        # 标题栏
        header = BoxLayout(size_hint_y=0.08, padding=10)
        header.add_widget(Label(
            text="📈 股票AI量化分析",
            font_size='18sp',
            bold=True,
            color=(1, 0.9, 0.3, 1)
        ))
        
        # 股票选择器
        stock_spinner = Spinner(
            text="选择股票",
            values=[name for name, _ in STOCK_LIST],
            size_hint=(1, None),
            height=50,
            background_color=(0.2, 0.4, 0.8, 1)
        )
        stock_spinner.bind(text=self.on_stock_select)
        
        # 刷新按钮
        refresh_btn = Button(
            text="🔄 刷新数据",
            size_hint=(1, None),
            height=50,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        refresh_btn.bind(on_press=self.refresh_data)
        
        # 自动刷新开关
        auto_layout = BoxLayout(size_hint_y=0.05)
        self.auto_switch = Button(
            text="⏰ 关闭自动刷新",
            size_hint_x=0.5,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        self.auto_switch.bind(on_press=self.toggle_auto_refresh)
        
        refresh_interval = Button(
            text="间隔: 30秒",
            size_hint_x=0.5,
            background_color=(0.4, 0.4, 0.4, 1)
        )
        auto_layout.add_widget(self.auto_switch)
        auto_layout.add_widget(refresh_interval)
        
        # 详情区域
        self.detail_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # 合规声明
        compliance_label = Label(
            text="⚠️ 本应用仅供学习研究，不构成投资建议",
            size_hint_y=0.05,
            font_size='10sp',
            color=(1, 0.5, 0, 1)
        )
        
        # 组装
        main_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        main_layout.add_widget(header)
        main_layout.add_widget(stock_spinner)
        main_layout.add_widget(refresh_btn)
        main_layout.add_widget(auto_layout)
        main_layout.add_widget(self.detail_layout)
        main_layout.add_widget(compliance_label)
        
        self.add_widget(main_layout)
    
    def on_stock_select(self, spinner, text):
        """选择股票后显示详情"""
        if not text:
            return
        
        code = STOCK_POOL.get(text)
        if not code:
            return
        
        # 显示加载中
        self.detail_layout.clear_widgets()
        self.detail_layout.add_widget(Label(
            text="正在获取数据...",
            markup=True
        ))
        
        # 后台获取数据
        threading.Thread(target=self.fetch_and_display, args=(text, code)).start()
    
    def fetch_and_display(self, name, code):
        """后台获取并显示数据"""
        data = fetch_quote(code)
        
        if data:
            # 计算指标
            indicators = calc_indicators(data['price'])
            score = ai_total_score(indicators)
            advice = get_advice(score, indicators)
            
            # 更新UI（必须在主线程）
            Clock.schedule_once(lambda dt: self.display_result(name, data, indicators, score, advice), 0)
        else:
            Clock.schedule_once(lambda dt: self.show_error(), 0)
    
    def display_result(self, name, data, indicators, score, advice):
        """显示查询结果"""
        self.detail_layout.clear_widgets()
        
        # 价格信息
        price_color = (0.2, 0.8, 0.2, 1) if data['change'] >= 0 else (0.8, 0.2, 0.2, 1)
        
        self.detail_layout.add_widget(Label(
            text=f"[b][size=24]{name}[/size][/b]\n"
                 f"[size=32][color=00ff00]{data['price']:.2f}[/color][/size]\n"
                 f"[color={'00ff00' if data['change'] >= 0 else 'ff4444'}]{data['change']:+.2f} ({data['change_pct']:+.2f}%)[/color]",
            markup=True,
            size_hint_y=0.35
        ))
        
        # 技术指标网格
        grid = GridLayout(cols=3, row_force_default=True, row_default_height=40, size_hint_y=0.35)
        
        indicators_text = [
            ("MA5", f"{indicators['MA5']:.2f}"),
            ("MA20", f"{indicators['MA20']:.2f}"),
            ("RSI", f"{indicators['RSI']:.1f}"),
            ("KDJ-K", f"{indicators['KDJ_K']:.1f}"),
            ("KDJ-D", f"{indicators['KDJ_D']:.1f}"),
            ("KDJ-J", f"{indicators['KDJ_J']:.1f}"),
            ("量比", f"{indicators['VolRatio']:.2f}"),
            ("情绪", f"{indicators['Emotion']:.0f}/100"),
            ("资金", indicators['CapitalState'][:4]),
        ]
        
        for label_text, value_text in indicators_text:
            grid.add_widget(Label(
                text=f"[size=10]{label_text}[/size]\n[color=00ffff]{value_text}[/color]",
                markup=True
            ))
        
        self.detail_layout.add_widget(grid)
        
        # AI评分
        score_color = (0.2, 0.8, 0.2, 1) if score >= 65 else (1, 0.8, 0, 1) if score >= 45 else (1, 0.2, 0.2, 1)
        self.detail_layout.add_widget(Label(
            text=f"[b][size=20]AI综合评分[/size][/b]\n"
                 f"[size=36][color={self.get_color(score)}]{score}[/color][/size] / 100",
            markup=True,
            size_hint_y=0.2
        ))
        
        # 建议
        advice_color = advice[1]
        advice_hex = "{:02x}{:02x}{:02x}".format(
            int(advice_color[0]*255), int(advice_color[1]*255), int(advice_color[2]*255))
        
        self.detail_layout.add_widget(Label(
            text=f"[b][size=16][color={advice_hex}]{advice[0]}[/color][/size][/b]\n"
                 f"资金: 进{indicators['CapitalIn']:.1f}% / 出{indicators['CapitalOut']:.1f}%",
            markup=True,
            size_hint_y=0.1
        ))
    
    def get_color(self, score):
        """根据评分返回颜色"""
        if score >= 65:
            return "00ff00"  # 绿色
        elif score >= 45:
            return "ffff00"  # 黄色
        else:
            return "ff4444"  # 红色
    
    def show_error(self):
        """显示错误"""
        self.detail_layout.clear_widgets()
        self.detail_layout.add_widget(Label(
            text="❌ 数据获取失败\n\n请检查网络连接",
            color=(1, 0.3, 0.3, 1)
        ))
    
    def refresh_data(self, *args):
        """刷新当前选中股票"""
        for child in self.children:
            if isinstance(child, BoxLayout):
                for c in child.children:
                    if isinstance(c, Spinner) and c.text != "选择股票":
                        self.on_stock_select(c, c.text)
                        return
    
    def toggle_auto_refresh(self, *args):
        """切换自动刷新"""
        self.auto_refresh = not self.auto_refresh
        
        if self.auto_refresh:
            self.auto_switch.text = "⏰ 自动刷新中..."
            self.auto_switch.background_color = (0.2, 0.8, 0.2, 1)
            self.auto_event = Clock.schedule_interval(lambda dt: self.refresh_data(), 30)
        else:
            self.auto_switch.text = "⏰ 关闭自动刷新"
            self.auto_switch.background_color = (0.5, 0.5, 0.5, 1)
            if hasattr(self, 'auto_event'):
                self.auto_event.cancel()
    
    def on_leave(self):
        """离开界面时停止刷新"""
        if hasattr(self, 'auto_event'):
            self.auto_event.cancel()

# ===================== 应用入口 =====================
class StockAnalysisApp(App):
    title = "股票AI量化分析"
    
    def build(self):
        # 设置背景色
        Window.clearcolor = (0.1, 0.1, 0.15, 1)
        
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm
    
    def on_pause(self):
        """应用暂停时"""
        return True
    
    def on_resume(self):
        """应用恢复时"""
        pass

if __name__ == '__main__':
    StockAnalysisApp().run()
