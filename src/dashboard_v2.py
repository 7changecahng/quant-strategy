"""
量化策略 Dashboard v2 (轻量版)
从预计算数据加载，实时参数调节回测
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

from data_fetcher import TARGET_STOCKS
from indicators import calc_all_indicators
from strategy import backtest, apply_stop_loss_take_profit

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "output")
DASHBOARD_DIR = os.path.join(OUTPUT, "dashboard")

st.set_page_config(
    page_title="多因子量化策略平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 加载预计算数据 ===
@st.cache_data
def load_nav_data(code: str) -> pd.DataFrame:
    """加载预计算净值曲线数据"""
    path = os.path.join(DASHBOARD_DIR, f"nav_curve_{code}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        return df
    return None

@st.cache_data
def load_all_metrics() -> pd.DataFrame:
    """加载全标汇总指标"""
    path = os.path.join(DASHBOARD_DIR, "all_metrics_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

@st.cache_data
def load_raw_from_db(code: str) -> pd.DataFrame:
    """从 SQLite 加载原始数据用于重算"""
    from data_fetcher import load_from_sqlite
    try:
        df = load_from_sqlite(f"stock_{code}")
        if df is not None and len(df) > 60:
            df["date"] = pd.to_datetime(df["date"])
            return df
    except Exception:
        pass
    # 模拟数据
    np.random.seed(hash(code) % 10000)
    n = 500
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    df = pd.DataFrame({
        "date": dates, "open": close - 0.5, "high": close + 1.5,
        "low": close - 1.5, "close": close,
        "volume": np.random.randint(100000, 1000000, n),
    })
    return df


# === 侧边栏 ===
with st.sidebar:
    st.markdown("## 📈 量化策略平台")
    st.markdown("---")

    stock_options = {f"{n}({c})": c for c, n in TARGET_STOCKS.items()}
    selected_label = st.selectbox("选择标的", list(stock_options.keys()), index=0)
    code = stock_options[selected_label]
    name = selected_label.split("(")[0]

    st.markdown("---")
    mode = st.radio("数据模式", ["预计算数据 (快速)", "实时重算 (可调参数)"], index=0)

    if mode == "实时重算 (可调参数)":
        st.subheader("⚙️ 策略参数")
        ma_fast = st.slider("MA 快线", 3, 30, 5, 1)
        ma_slow = st.slider("MA 慢线", 10, 120, 20, 1)
        rsi_threshold = st.slider("RSI 阈值", 50, 90, 70, 1)
        rsi_cut = st.slider("RSI 减仓起点", 50, 80, 60, 1)
        use_stop = st.checkbox("启用止损止盈", value=False)
    else:
        ma_fast, ma_slow, rsi_threshold, rsi_cut = 5, 20, 70, 60
        use_stop = False

    st.markdown("---")
    st.caption("💡 预计算模式加载快\n⚙ 实时模式支持调参数")


# === 主内容区 ===
st.title(f"📊 {name} ({code}) 量化策略分析")
st.markdown("*基于 MA/MACD/RSI/布林带 的多因子复合择时策略*")

# --- 模式1: 预计算数据快速展示 ---
if mode.startswith("预计算"):
    df = load_nav_data(code)
    all_m = load_all_metrics()

    if df is None:
        st.warning(f"无预计算数据, 切换到实时模式")
        mode = "实时重算"

if mode.startswith("预计算") and df is not None:
    # 指标卡
    row = all_m[all_m["code"] == code] if all_m is not None else None
    if row is not None and len(row) > 0:
        r = row.iloc[0]
        cols = st.columns(4)
        cols[0].metric("年化收益", r["annual_return"])
        cols[1].metric("夏普比率", r["sharpe"])
        cols[2].metric("最大回撤", r["mdd"])
        cols[3].metric("胜率", r["win_rate"])

    # 净值曲线
    st.markdown("### 净值曲线")
    nav_data = pd.DataFrame({
        "策略净值": df["nav_strategy"].values,
        "买入持有": df["nav_benchmark"].values,
    })
    st.line_chart(nav_data, height=350, use_container_width=True)

    # 回撤曲线
    st.markdown("### 回撤曲线")
    dd_s = df["nav_strategy"] / df["nav_strategy"].cummax() - 1
    dd_b = df["nav_benchmark"] / df["nav_benchmark"].cummax() - 1
    dd_data = pd.DataFrame({
        "策略回撤": dd_s.values,
        "基准回撤": dd_b.values,
    })
    st.line_chart(dd_data, height=250, use_container_width=True)

    # 信号统计
    pos_days = int(df["signal_raw"].sum())
    total_days = len(df)
    st.info(f"📊 持仓 {pos_days}/{total_days} 天 ({pos_days/total_days:.1%})")

    # RSI 曲线
    st.markdown("### RSI 指标")
    st.line_chart(df.set_index("date")["rsi"], height=200, use_container_width=True)

    # 数据预览
    with st.expander("查看原始数据"):
        st.dataframe(df.tail(20), use_container_width=True)

else:
    # --- 模式2: 实时重算 ---
    with st.spinner("加载数据并计算中..."):
        df_raw = load_raw_from_db(code)

    if df_raw is None or len(df_raw) < 60:
        st.error("数据不足")
        st.stop()

    # 计算指标
    df = calc_all_indicators(df_raw)

    # 用用户参数复写
    df["ma5"] = df["close"].rolling(window=ma_fast).mean()
    df["ma20"] = df["close"].rolling(window=ma_slow).mean()

    df["sig_trend"] = (df["ma5"] > df["ma20"]).astype(int)
    df["sig_momentum"] = (df["macd_hist"] > 0).astype(int)
    df["sig_rsi"] = (df["rsi"] < rsi_threshold).astype(int)
    df["sig_bb"] = (df["close"] > df["bb_lower"]).astype(int)
    df["sig_volume"] = (df["volume_ratio"] > 0.7).astype(int)

    df["signal_raw"] = (
        (df["sig_trend"] == 1) &
        (df["sig_momentum"] == 1) &
        (df["sig_rsi"] == 1) &
        (df["sig_bb"] == 1) &
        (df["sig_volume"] == 1)
    ).astype(int)

    # 仓位管理
    df["position_pct"] = 1.0
    mask_high = df["rsi"] > rsi_cut
    df.loc[mask_high, "position_pct"] = np.maximum(
        0.5, 1.0 - (df.loc[mask_high, "rsi"] - rsi_cut) / (100 - rsi_cut)
    )
    df["signal"] = df["signal_raw"] * df["position_pct"]
    df = df.dropna()

    if len(df) < 30:
        st.error("有效数据不足")
        st.stop()

    # 风控
    if use_stop:
        df = apply_stop_loss_take_profit(df, -0.08, 0.25, -0.06)
        signal_bt = df["signal_sltp"]
    else:
        signal_bt = df["signal"]
        df["signal_sltp"] = df["signal"]
        df["stop_event"] = 0
        df["profit_event"] = 0
        df["trail_event"] = 0

    # 回测
    sr = backtest(signal_bt, df["close"], fee=0.0005)
    bh = df["close"].pct_change().fillna(0).values
    df["nav_strategy"] = (1 + sr).cumprod()
    df["nav_benchmark"] = (1 + bh).cumprod()

    # 手动计算核心指标
    total_ret = sr.sum()
    annual_ret = total_ret / len(sr) * 252
    volatility = np.std(sr) * np.sqrt(252)
    sharpe = (annual_ret - 0.02) / volatility if volatility > 0 else 0
    dd = (df["nav_strategy"] / df["nav_strategy"].cummax() - 1).min()
    win_rate = (sr > 0).mean()

    # 指标卡
    cols = st.columns(5)
    cols[0].metric("年化收益", f"{annual_ret:.2%}")
    cols[1].metric("年化波动", f"{volatility:.2%}")
    cols[2].metric("夏普比率", f"{sharpe:.2f}")
    cols[3].metric("最大回撤", f"{dd:.2%}")
    cols[4].metric("胜率", f"{win_rate:.2%}")

    # 净值曲线
    st.markdown("### 净值曲线对比")
    nav_df = pd.DataFrame({
        "策略净值": df["nav_strategy"].values,
        "买入持有": df["nav_benchmark"].values,
    })
    st.line_chart(nav_df, height=350, use_container_width=True)

    # 回撤
    st.markdown("### 回撤曲线")
    dd_s = df["nav_strategy"] / df["nav_strategy"].cummax() - 1
    dd_b = df["nav_benchmark"] / df["nav_benchmark"].cummax() - 1
    st.line_chart(pd.DataFrame({
        "策略回撤": dd_s.values,
        "基准回撤": dd_b.values,
    }), height=250, use_container_width=True)

    # 价格 + MA
    st.markdown("### 价格 & 均线")
    price_df = pd.DataFrame({
        "收盘价": df["close"].values,
        f"MA{ma_fast}": df["ma5"].values,
        f"MA{ma_slow}": df["ma20"].values,
    })
    st.line_chart(price_df, height=300, use_container_width=True)

    # 指标面板
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### MACD")
        macd_df = pd.DataFrame({
            "MACD柱": df["macd_hist"].values,
        })
        st.bar_chart(macd_df, height=200, use_container_width=True)

    with col_r:
        st.markdown("### RSI")
        st.line_chart(df.set_index("date")["rsi"], height=200, use_container_width=True)

    # 交易统计
    pos_days = int(df["signal_raw"].sum())
    total_days = len(df)
    changes = df["signal_raw"].diff().fillna(0)
    buy_times = int((changes == 1).sum())

    st.info(f"📊 持仓 {pos_days}/{total_days} 天 ({pos_days/total_days:.1%}) · 开仓 {buy_times} 次")

st.markdown("---")
st.caption("📈 多因子量化策略分析平台 · Streamlit · 防未来函数")
