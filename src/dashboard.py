"""
Streamlit 交互式 Dashboard (L13)
多因子量化策略回测与分析平台
支持 Plotly 交互图表 + 静态报告导出
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from data_fetcher import TARGET_STOCKS, fetch_stock_daily, BENCHMARK, fetch_index_daily
from indicators import calc_all_indicators
from strategy import generate_composite_signal, backtest, apply_stop_loss_take_profit
from risk_metrics import calc_all_risk_metrics, format_metrics_report, max_drawdown

# --- 页面配置 ---
st.set_page_config(
    page_title="多因子量化策略平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 缓存 ---
@st.cache_data(ttl=3600)
def load_stock_data(code: str):
    """从 SQLite 加载个股数据，无数据时生成模拟数据"""
    from data_fetcher import load_from_sqlite
    try:
        df = load_from_sqlite(f"stock_{code}")
        if df is not None and len(df) > 60:
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            cols_lower = [c.lower() for c in df.columns]
            if "name" not in cols_lower:
                df["name"] = TARGET_STOCKS.get(code, "")
            return df
    except Exception:
        pass
    # 无数据 → 生成模拟数据
    np.random.seed(hash(code) % 10000)
    n = 500
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    df = pd.DataFrame({
        "date": dates, "open": close - 0.5, "high": close + 1.5,
        "low": close - 1.5, "close": close,
        "volume": np.random.randint(100000, 1000000, n),
    })
    df["code"] = code
    df["name"] = TARGET_STOCKS.get(code, "")
    return df

@st.cache_data(ttl=3600)
def load_benchmark():
    """加载基准指数，失败时用贵州茅台收盘价做近似基准"""
    from data_fetcher import load_from_sqlite
    try:
        df = load_from_sqlite("benchmark_hs300")
        if df is not None and len(df) > 60:
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            return df
    except Exception:
        pass
    # 基准也失败时，用贵州茅台数据做近似
    try:
        return load_stock_data("600519")
    except Exception:
        return pd.DataFrame()


# --- 侧边栏 ---
with st.sidebar:
    st.markdown("## 📈")
    st.title("📈 量化策略平台")
    st.markdown("---")

    st.subheader("🎯 参数配置")

    # 选择标的
    stock_options = {f"{name}({code})": code for code, name in TARGET_STOCKS.items()}
    selected_label = st.selectbox(
        "选择标的",
        list(stock_options.keys()),
        index=0
    )
    selected_code = stock_options[selected_label]
    selected_name = selected_label.split("(")[0]

    st.markdown("---")
    st.subheader("⚙️ 策略参数")

    # 可调参数
    ma_fast = st.slider("MA 快线", 3, 30, 5, 1)
    ma_slow = st.slider("MA 慢线", 10, 120, 20, 1)
    rsi_threshold = st.slider("RSI 阈值", 50, 90, 70, 1)
    rsi_position_cut = st.slider("RSI 减仓起点", 50, 80, 60, 1)
    fee_bps = st.slider("手续费(万份之)", 0.0, 5.0, 0.5, 0.1) / 10000
    use_volume_filter = st.checkbox("成交量过滤", value=True)
    use_bb_filter = st.checkbox("布林带过滤", value=True)

    st.markdown("---")
    st.subheader("📅 回测区间")
    start_date = st.date_input("开始日期", pd.to_datetime("2022-01-01"))
    end_date = st.date_input("结束日期", pd.to_datetime("2025-12-31"))

    st.markdown("---")
    st.subheader("🛡️ 风控设置")
    use_stop_loss = st.checkbox("启用止损止盈", value=False)
    stop_loss_pct = st.slider("固定止损", -25.0, -1.0, -8.0, 0.5) / 100 if use_stop_loss else -0.08
    take_profit_pct = st.slider("固定止盈", 5.0, 50.0, 25.0, 0.5) / 100 if use_stop_loss else 0.25
    trailing_stop_pct = st.slider("追踪止损", -15.0, -1.0, -6.0, 0.5) / 100 if use_stop_loss else -0.06

    st.markdown("---")
    st.caption("💡 提示: 修改参数后自动重新计算\n"
               "⚠ 所有信号使用 shift(1) 防未来函数")


def main():
    """Dashboard 主逻辑"""
    st.title(f"📊 {selected_name} 多因子择时策略分析")
    st.markdown(f"*基于 MA/MACD/RSI/布林带 的复合信号 + 动态仓位管理*")

    # 加载数据
    with st.spinner("加载数据中..."):
        df_raw = load_stock_data(selected_code)
        bench_raw = load_benchmark()

    if df_raw.empty:
        st.error("无数据,请检查网络连接")
        st.stop()

    # 预处理
    df_raw["date"] = pd.to_datetime(df_raw["date"])
    mask = (df_raw["date"] >= pd.to_datetime(start_date)) & (df_raw["date"] <= pd.to_datetime(end_date))
    df = df_raw[mask].copy().reset_index(drop=True)

    if len(df) < 60:
        st.error(f"数据不足 ({len(df)} 天),至少需要 60 天")
        st.stop()

    # --- 计算指标 ---
    df = calc_all_indicators(df)

    # --- 用用户参数复写关键指标 ---
    df["ma5"] = df["close"].rolling(window=ma_fast).mean()
    df["ma20"] = df["close"].rolling(window=ma_slow).mean()

    # 调整信号规则适配用户参数
    df["sig_trend"] = (df["ma5"] > df["ma20"]).astype(int)
    df["sig_momentum"] = (df["macd_hist"] > 0).astype(int)
    df["sig_rsi"] = (df["rsi"] < rsi_threshold).astype(int)
    df["sig_bb"] = (df["close"] > df["bb_lower"]).astype(int) if use_bb_filter else pd.Series(1, index=df.index)
    df["sig_volume"] = (df["volume_ratio"] > 0.7).astype(int) if use_volume_filter else pd.Series(1, index=df.index)

    df["signal_raw"] = (
        (df["sig_trend"] == 1) &
        (df["sig_momentum"] == 1) &
        (df["sig_rsi"] == 1) &
        (df["sig_bb"] == 1) &
        (df["sig_volume"] == 1)
    ).astype(int)

    # 仓位管理
    df["position_pct"] = 1.0
    mask_high = df["rsi"] > rsi_position_cut
    df.loc[mask_high, "position_pct"] = np.maximum(0.5, 1.0 - (df.loc[mask_high, "rsi"] - rsi_position_cut) / (100 - rsi_position_cut))
    df["signal"] = df["signal_raw"] * df["position_pct"]
    df = df.dropna()

    if len(df) < 30:
        st.error("有效数据不足(去除NaN后),请调整日期范围")
        st.stop()

    # --- 回测 ---
    if use_stop_loss:
        df = apply_stop_loss_take_profit(df, stop_loss_pct, take_profit_pct, trailing_stop_pct)
        signal_for_bt = df["signal_sltp"]
    else:
        signal_for_bt = df["signal"]
        df["signal_sltp"] = df["signal"]
        df["stop_event"] = 0
        df["profit_event"] = 0
        df["trail_event"] = 0

    strategy_ret = backtest(signal_for_bt, df["close"], fee=fee_bps)
    buy_hold_ret = df["close"].pct_change().fillna(0).values
    df["nav_strategy"] = (1 + strategy_ret).cumprod()
    df["nav_benchmark"] = (1 + buy_hold_ret).cumprod()
    metrics = calc_all_risk_metrics(strategy_ret, buy_hold_ret)

    # === 仪表盘布局 ===

    # --- 第一行: 关键指标卡 ---
    st.markdown("### 📈 核心指标")
    cols = st.columns(6)
    metrics_display = [
        ("累计收益", f"{metrics['total_return']:.2%}", f"{metrics['bh_total_return']:.2%}" if 'bh_total_return' in metrics else "-"),
        ("年化收益", f"{metrics['annual_return']:.2%}", f"{metrics['bh_annual_return']:.2%}" if 'bh_annual_return' in metrics else "-"),
        ("夏普比率", f"{metrics['sharpe_ratio']:.2f}", f"{metrics['bh_sharpe']:.2f}" if 'bh_sharpe' in metrics else "-"),
        ("最大回撤", f"{metrics['max_drawdown']:.2%}", f"{metrics['bh_max_drawdown']:.2%}" if 'bh_max_drawdown' in metrics else "-"),
        ("胜率", f"{metrics['win_rate']:.2%}", "-"),
        ("超额收益", f"{metrics.get('excess_return', 0):.2%}", "-"),
    ]

    for i, (label, val, bench) in enumerate(metrics_display):
        with cols[i]:
            is_good = True
            if label == "最大回撤":
                is_good = float(val.strip('%')) < float(bench.strip('%')) if bench != '-' else True
                color = "#1E7A4A" if is_good else "#B83020"
            else:
                color = "#1E7A4A" if float(val.strip('%').replace('f','').replace('%','')) > 0 else "#B83020"
            st.metric(label=label, value=val, delta=f"基准 {bench}" if bench != "-" else None)

    # --- 第二行: 净值曲线 (Plotly 交互式) ---
    st.markdown("### 📉 净值曲线对比")
    try:
        import plotly.graph_objects as go
        fig_nav = go.Figure()
        fig_nav.add_trace(go.Scatter(
            x=df["date"], y=df["nav_strategy"], name="策略净值",
            line=dict(color="#3366CC", width=2), mode="lines"
        ))
        fig_nav.add_trace(go.Scatter(
            x=df["date"], y=df["nav_benchmark"], name="买入持有",
            line=dict(color="#999999", width=1.5, dash="dash"), mode="lines"
        ))
        # 标注开仓区间
        buy_idx = df[df["signal_raw"] == 1].index
        if len(buy_idx) > 0:
            fig_nav.add_trace(go.Scatter(
                x=df.loc[buy_idx, "date"], y=df.loc[buy_idx, "nav_strategy"],
                mode="markers", name="持仓区间",
                marker=dict(color="rgba(102,187,106,0.3)", size=3)
            ))
        fig_nav.update_layout(
            height=400, margin=dict(l=20, r=20, t=10, b=20),
            hovermode="x unified", legend=dict(orientation="h", y=1.1),
            xaxis_title="日期", yaxis_title="净值"
        )
        st.plotly_chart(fig_nav, use_container_width=True)
    except ImportError:
        nav_chart_data = pd.DataFrame({
            "策略净值": df["nav_strategy"].values,
            "买入持有": df["nav_benchmark"].values,
        }, index=df["date"])
        st.line_chart(nav_chart_data, height=400, use_container_width=True)

    # --- 第三行: 回撤曲线 (Plotly) ---
    st.markdown("### 📉 回撤曲线")
    dd_strategy = (df["nav_strategy"] / df["nav_strategy"].cummax() - 1)
    dd_bench = (df["nav_benchmark"] / df["nav_benchmark"].cummax() - 1)
    try:
        import plotly.graph_objects as go
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=df["date"], y=dd_strategy, name="策略回撤",
            line=dict(color="#E74C3C", width=2), fill="tozeroy",
            fillcolor="rgba(231,76,60,0.1)"
        ))
        fig_dd.add_trace(go.Scatter(
            x=df["date"], y=dd_bench, name="基准回撤",
            line=dict(color="#999999", width=1, dash="dot")
        ))
        fig_dd.update_layout(
            height=280, margin=dict(l=20, r=20, t=10, b=20),
            hovermode="x unified", legend=dict(orientation="h", y=1.1),
            yaxis_tickformat=".1%"
        )
        st.plotly_chart(fig_dd, use_container_width=True)
    except ImportError:
        dd_data = pd.DataFrame({
            "策略回撤": dd_strategy.values,
            "基准回撤": dd_bench.values,
        }, index=df["date"])
        st.line_chart(dd_data, height=250, use_container_width=True)

    # --- 第四行: 信号与仓位 ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🎯 信号分布")
        try:
            import plotly.graph_objects as go
            fig_sig = go.Figure()
            fig_sig.add_trace(go.Scatter(
                x=df["date"], y=df["close"], name="收盘价",
                line=dict(color="#3366CC", width=2)
            ))
            fig_sig.add_trace(go.Scatter(
                x=df["date"], y=df["ma5"], name=f"MA{ma_fast}",
                line=dict(color="#E67E22", width=1, dash="dot")
            ))
            fig_sig.add_trace(go.Scatter(
                x=df["date"], y=df["ma20"], name=f"MA{ma_slow}",
                line=dict(color="#8E44AD", width=1, dash="dash")
            ))
            # 标注开仓区间
            if use_stop_loss:
                stop_points = df[df["stop_event"] == 1]
                if len(stop_points) > 0:
                    fig_sig.add_trace(go.Scatter(
                        x=stop_points["date"], y=stop_points["close"],
                        mode="markers", name="止损",
                        marker=dict(color="red", size=8, symbol="x")
                    ))
            fig_sig.update_layout(
                height=320, margin=dict(l=20, r=20, t=10, b=20),
                hovermode="x unified", legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_sig, use_container_width=True)
        except ImportError:
            signal_data = pd.DataFrame({
                "收盘价": df["close"].values,
                "MA快线": df["ma5"].values,
                "MA慢线": df["ma20"].values,
            }, index=df["date"])
            st.line_chart(signal_data, height=300, use_container_width=True)

        # 信号统计
        pos_days = df["signal_raw"].sum()
        total_days = len(df)
        n_stops = int(df["stop_event"].sum()) if "stop_event" in df.columns else 0
        n_profits = int(df["profit_event"].sum()) if "profit_event" in df.columns else 0
        st.info(f"📊 仓位统计: 持仓 {pos_days}/{total_days} 天 "
                f"({pos_days/total_days:.1%}) · "
                f"开仓 {df['signal_raw'].diff().eq(1).sum()} 次"
                + (f" · 止损 {n_stops} 次 · 止盈 {n_profits} 次" if use_stop_loss else ""))

    with col_right:
        st.markdown("### 🔬 技术指标面板")
        show_indicator = st.selectbox(
            "选择指标",
            ["MACD", "RSI", "布林带 %B", "成交量比"]
        )

        try:
            import plotly.graph_objects as go
            fig_ind = go.Figure()

            if show_indicator == "MACD":
                fig_ind.add_trace(go.Scatter(
                    x=df["date"], y=df["macd_dif"], name="MACD DIF",
                    line=dict(color="#3366CC", width=1.5)
                ))
                fig_ind.add_trace(go.Scatter(
                    x=df["date"], y=df["macd_dea"], name="MACD DEA",
                    line=dict(color="#E67E22", width=1)
                ))
                fig_ind.add_trace(go.Bar(
                    x=df["date"], y=df["macd_hist"], name="MACD HIST",
                    marker_color=df["macd_hist"].apply(
                        lambda x: "rgba(231,76,60,0.6)" if x < 0 else "rgba(46,204,113,0.6)"
                    )
                ))
            elif show_indicator == "RSI":
                fig_ind.add_trace(go.Scatter(
                    x=df["date"], y=df["rsi"], name="RSI(14)",
                    line=dict(color="#8E44AD", width=1.5), fill="tozeroy",
                    fillcolor="rgba(142,68,173,0.1)"
                ))
                fig_ind.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5,
                                  annotation_text="超买70")
                fig_ind.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5,
                                  annotation_text="超卖30")
            elif show_indicator == "布林带 %B":
                fig_ind.add_trace(go.Scatter(
                    x=df["date"], y=df["bb_pct_b"], name="%B",
                    line=dict(color="#2C3E50", width=1.5), fill="tozeroy",
                    fillcolor="rgba(44,62,80,0.1)"
                ))
                fig_ind.add_hline(y=1, line_dash="dash", line_color="red", opacity=0.5)
                fig_ind.add_hline(y=0, line_dash="dash", line_color="green", opacity=0.5)
            else:
                fig_ind.add_trace(go.Scatter(
                    x=df["date"], y=df["volume_ratio"], name="量比",
                    line=dict(color="#D35400", width=1.5), fill="tozeroy",
                    fillcolor="rgba(211,84,0,0.1)"
                ))
                fig_ind.add_hline(y=1, line_dash="dash", line_color="gray", opacity=0.5)

            fig_ind.update_layout(
                height=320, margin=dict(l=20, r=20, t=10, b=20),
                hovermode="x unified", legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_ind, use_container_width=True)
        except ImportError:
            if show_indicator == "MACD":
                indicator_data = pd.DataFrame({
                    "MACD DIF": df["macd_dif"].values,
                    "MACD DEA": df["macd_dea"].values,
                    "MACD HIST": df["macd_hist"].values,
                }, index=df["date"])
            elif show_indicator == "RSI":
                indicator_data = pd.DataFrame({
                    "RSI(14)": df["rsi"].values,
                }, index=df["date"])
            elif show_indicator == "布林带 %B":
                indicator_data = pd.DataFrame({
                    "%B": df["bb_pct_b"].values,
                }, index=df["date"])
            else:
                indicator_data = pd.DataFrame({
                    "量比": df["volume_ratio"].values,
                }, index=df["date"])
            st.line_chart(indicator_data, height=300, use_container_width=True)

    # --- 交易明细 ---
    st.markdown("### 📋 风险指标明细")

    tab1, tab2, tab3 = st.tabs(["风险指标", "交易统计", "原始数据"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("策略指标")
            risk_df = pd.DataFrame({
                "指标": ["年化收益率", "年化波动率", "夏普比率", "索提诺比率",
                        "最大回撤", "VaR(95%)", "CVaR(95%)", "Calmar比率",
                        "胜率", "盈亏比"],
                "数值": [
                    f"{metrics['annual_return']:.2%}",
                    f"{metrics['annual_volatility']:.2%}",
                    f"{metrics['sharpe_ratio']:.2f}",
                    f"{metrics['sortino_ratio']:.2f}",
                    f"{metrics['max_drawdown']:.2%}",
                    f"{metrics['var_95']:.4f}",
                    f"{metrics['cvar_95']:.4f}",
                    f"{metrics['calmar_ratio']:.2f}",
                    f"{metrics['win_rate']:.2%}",
                    f"{metrics['profit_factor']:.2f}",
                ]
            })
            st.dataframe(risk_df, use_container_width=True, hide_index=True)

        with col_b:
            st.subheader("基准对比")
            if "bh_total_return" in metrics:
                bench_df = pd.DataFrame({
                    "指标": ["年化收益率", "累计收益", "夏普比率", "最大回撤", "年化波动率"],
                    "数值": [
                        f"{metrics['bh_annual_return']:.2%}",
                        f"{metrics['bh_total_return']:.2%}",
                        f"{metrics['bh_sharpe']:.2f}",
                        f"{metrics['bh_max_drawdown']:.2%}",
                        f"{metrics['bh_volatility']:.2%}",
                    ]
                })
                st.dataframe(bench_df, use_container_width=True, hide_index=True)

                # 超额对比
                st.subheader("超额分析")
                excess_df = pd.DataFrame({
                    "对比项": ["累计超额收益", "年化超额收益"],
                    "数值": [
                        f"{metrics['excess_return']:.2%}",
                        f"{metrics['excess_annual']:.2%}",
                    ]
                })
                st.dataframe(excess_df, use_container_width=True, hide_index=True)

    with tab2:
        # 交易统计
        signal_changes = df["signal_raw"].diff().fillna(0)
        buy_signals = df[signal_changes == 1]
        sell_signals = df[signal_changes == -1]

        st.subheader(f"交易记录 (共 {len(buy_signals)} 笔)")
        trades_list = []
        for i, (_, buy_row) in enumerate(buy_signals.iterrows()):
            trade = {
                "序号": i + 1,
                "买入日期": buy_row["date"].strftime("%Y-%m-%d"),
                "买入价": f"{buy_row['close']:.2f}",
                "RSI(买)": f"{buy_row['rsi']:.1f}",
            }
            # 找对应卖出
            after_buy = sell_signals[sell_signals.index > buy_row.name]
            if len(after_buy) > 0:
                sell_row = after_buy.iloc[0]
                trade["卖出日期"] = sell_row["date"].strftime("%Y-%m-%d")
                trade["卖出价"] = f"{sell_row['close']:.2f}"
                trade["收益率"] = f"{(sell_row['close']/buy_row['close']-1)*100:+.2f}%"
                trade["持有天数"] = (sell_row["date"] - buy_row["date"]).days
            else:
                trade["卖出日期"] = "持仓中"
                trade["卖出价"] = "-"
                trade["收益率"] = "-"
                trade["持有天数"] = "-"
            trades_list.append(trade)

        if trades_list:
            st.dataframe(pd.DataFrame(trades_list), use_container_width=True, hide_index=True)

    with tab3:
        st.dataframe(df[[
            "date", "close", "ma5", "ma20", "macd_hist", "rsi",
            "bb_pct_b", "volume_ratio", "signal_raw", "signal"
        ]].tail(50), use_container_width=True)

    # --- 底部 ---
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#9A8878;font-size:12px'>"
        "📈 多因子量化策略分析平台 · Python + Streamlit · "
        "信号使用 shift(1) 严格防未来函数 · "
        "涵盖课程 L3-L13 核心知识"
        "</div>",
        unsafe_allow_html=True
    )

def export_static_report(code="600519", name="贵州茅台"):
    """离线导出静态回测报告（不启动 Streamlit）"""
    import json
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "dashboard")
    os.makedirs(out_dir, exist_ok=True)

    from data_fetcher import load_from_sqlite

    try:
        df_raw = load_from_sqlite(f"stock_{code}")
    except Exception:
        np.random.seed(42)
        n = 500
        dates = pd.date_range("2022-01-01", periods=n, freq="B")
        close = 100 + np.cumsum(np.random.randn(n) * 2)
        df_raw = pd.DataFrame({
            "date": dates, "open": close - 0.5, "high": close + 1.5,
            "low": close - 1.5, "close": close,
            "volume": np.random.randint(100000, 1000000, n)
        })
        print("  ⚠ 数据库无数据，使用模拟数据")

    df_raw["date"] = pd.to_datetime(df_raw["date"])
    df = calc_all_indicators(df_raw)
    df = generate_composite_signal(df)
    df = df.dropna()

    if len(df) < 30:
        print("  数据不足")
        return

    strategy_ret = backtest(df["signal"], df["close"])
    buy_hold_ret = df["close"].pct_change().fillna(0).values
    df["nav_strategy"] = (1 + strategy_ret).cumprod()
    df["nav_benchmark"] = (1 + buy_hold_ret).cumprod()
    metrics = calc_all_risk_metrics(strategy_ret, buy_hold_ret)

    # 保存净值曲线
    df[["date", "close", "nav_strategy", "nav_benchmark", "signal_raw", "rsi", "macd_hist"]].to_csv(
        os.path.join(out_dir, f"nav_curve_{code}.csv"), index=False, encoding="utf-8-sig")

    # 保存指标 JSON
    def convert(o):
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, (np.integer,)): return int(o)
        raise TypeError

    with open(os.path.join(out_dir, f"metrics_{code}.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, default=convert)

    # 保存策略参数
    params = {
        "code": code, "name": name, "n_days": len(df),
        "ma_fast": 5, "ma_slow": 20, "rsi_threshold": 70,
        "rsi_position_cut": 60, "fee_bps": 0.0005,
        "use_volume_filter": True, "use_bb_filter": True,
    }
    with open(os.path.join(out_dir, "params.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    print(f"  {name} ({code})")
    print(f"    年化收益: {metrics['annual_return']:.2%}")
    print(f"    夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"    最大回撤: {metrics['max_drawdown']:.2%}")
    return metrics


if __name__ == "__main__":
    # 检查是否以 streamlit 运行
    if "STREAMLIT_RUNTIME" in os.environ or "streamlit" in sys.argv[0].lower():
        main()
    else:
        # 命令行模式：导出所有标的的静态报告
        sys.stdout.reconfigure(encoding='utf-8')
        out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "dashboard")
        os.makedirs(out_dir, exist_ok=True)

        print("=" * 50)
        print("  Dashboard 静态报告导出")
        print("=" * 50)

        all_metrics = {}
        for code, name in TARGET_STOCKS.items():
            try:
                m = export_static_report(code, name)
                if m:
                    all_metrics[code] = {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
                                         for k, v in m.items()}
            except Exception as e:
                print(f"  ❌ {name}({code}) 失败: {e}")

        # 汇总表
        if all_metrics:
            rows = []
            for code, m in all_metrics.items():
                rows.append({
                    "code": code,
                    "name": TARGET_STOCKS.get(code, ""),
                    "annual_return": f"{m['annual_return']:.2%}",
                    "sharpe": f"{m['sharpe_ratio']:.2f}",
                    "mdd": f"{m['max_drawdown']:.2%}",
                    "win_rate": f"{m['win_rate']:.2%}",
                })
            pd.DataFrame(rows).to_csv(os.path.join(out_dir, "all_metrics_summary.csv"),
                                     index=False, encoding="utf-8-sig")
            print(f"\n✅ 所有报告已导出至: {out_dir}")
