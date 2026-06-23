"""
技术指标计算模块 (L10 金融指标)
MA · MACD · RSI · 布林带 · ATR
严格向量化,无循环,防未来函数
"""
import numpy as np
import pandas as pd


def calc_ma(close: pd.Series, window: int) -> pd.Series:
    """简单移动均线 (L10)"""
    return close.rolling(window=window).mean()


def calc_ema(close: pd.Series, window: int) -> pd.Series:
    """指数移动均线"""
    return close.ewm(span=window, adjust=False).mean()


def calc_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    MACD 指标 (L10)
    返回: MACD线(DIF), 信号线(DEA), 柱状图(HIST)
    """
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = 2 * (dif - dea)
    return dif, dea, hist


def calc_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """
    RSI 相对强弱指标 (L10)
    RSI = 100 - 100/(1 + RS)
    RS = 平均涨幅 / 平均跌幅
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()  # Wilder 平滑
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)  # 防除零
    rsi = 100 - 100 / (1 + rs)
    return rsi


def calc_bollinger(close: pd.Series, window: int = 20, n_std: float = 2.0):
    """
    布林带 (L10)
    返回: 上轨, 中轨, 下轨, 带宽百分比(%B)
    """
    middle = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = middle + n_std * std
    lower = middle - n_std * std
    # %B = (价格-下轨) / (上轨-下轨)
    pct_b = (close - lower) / (upper - lower + 1e-10)
    return upper, middle, lower, pct_b


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """ATR 平均真实波幅"""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/window, adjust=False).mean()


def calc_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    一次性计算所有技术指标 (向量化,批量操作)
    """
    df = df.copy()
    close = df["close"]
    high = df["high"]
    low = df["low"]

    # MA
    df["ma5"] = calc_ma(close, 5)
    df["ma10"] = calc_ma(close, 10)
    df["ma20"] = calc_ma(close, 20)
    df["ma60"] = calc_ma(close, 60)

    # EMA
    df["ema12"] = calc_ema(close, 12)
    df["ema26"] = calc_ema(close, 26)

    # MACD
    df["macd_dif"], df["macd_dea"], df["macd_hist"] = calc_macd(close)

    # RSI
    df["rsi"] = calc_rsi(close, 14)

    # 布林带
    df["bb_upper"], df["bb_middle"], df["bb_lower"], df["bb_pct_b"] = calc_bollinger(close)

    # ATR
    df["atr"] = calc_atr(high, low, close)

    # 日收益率
    df["daily_ret"] = close.pct_change()

    # 成交量指标
    df["volume_ma5"] = df["volume"].rolling(5).mean()
    df["volume_ratio"] = df["volume"] / (df["volume_ma5"] + 1e-10)

    return df


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    sys.stdout.reconfigure(encoding='utf-8')

    # 生成模拟数据并计算所有指标，保存到 output/indicators/
    np.random.seed(42)
    n = 500
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n) * 1.5)
    low = close - np.abs(np.random.randn(n) * 1.5)
    vol = np.random.randint(100000, 1000000, n)

    demo_df = pd.DataFrame({"date": dates, "open": close - 0.5, "high": high,
                            "low": low, "close": close, "volume": vol})
    result = calc_all_indicators(demo_df)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "indicators")
    os.makedirs(out_dir, exist_ok=True)

    # 保存指标计算结果
    result[["date", "close", "ma5", "ma10", "ma20", "ma60",
            "macd_dif", "macd_dea", "macd_hist", "rsi",
            "bb_upper", "bb_middle", "bb_lower", "bb_pct_b",
            "atr", "daily_ret", "volume_ratio"]].tail(200).to_csv(
        os.path.join(out_dir, "indicators_demo.csv"), index=False, encoding="utf-8-sig")

    # 保存函数清单
    func_list = [f for f in dir() if f.startswith("calc_")]
    with open(os.path.join(out_dir, "function_list.txt"), "w", encoding="utf-8") as f:
        f.write("indicators.py 可用函数:\n")
        for name in func_list:
            f.write(f"  - {name}\n")

    print(f"✅ 指标计算模块运行成功")
    print(f"  可用函数: {func_list}")
    print(f"  结果已保存至: {out_dir}")
    print(f"    - indicators_demo.csv ({len(result)} 行)")
    print(f"    - function_list.txt")
