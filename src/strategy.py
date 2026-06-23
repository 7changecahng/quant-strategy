"""
策略与回测模块 (L11 策略回测 + L5 sklearn)
复合多因子择时策略 + 止损止盈 + 严格回测引擎
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit  # L5: 时序交叉验证
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score


def generate_composite_signal(df: pd.DataFrame,
                               ma_fast: int = 5, ma_slow: int = 20,
                               rsi_threshold: float = 70, rsi_oversold: float = 30,
                               use_volume: bool = True, use_bb: bool = True,
                               enable_short: bool = False) -> pd.DataFrame:
    """
    复合信号生成 (L10+L11 综合)
    五层 AND 组合 + 动态仓位管理 + 做空信号

    信号规则:
    - 趋势层: MA快线 > MA慢线 (短期趋势向上)
    - 动能层: MACD_hist > 0 (动能为正)
    - 超买超卖: RSI < 阈值 (未超买才开仓)
    - 布林带: close > bb_lower (价格不在下轨之下)
    - 成交量: 量比 > 0.7 (量价配合)

    仓位 = 基础仓位 × RSI修正因子
    支持做空信号 (可选)
    """
    df = df.copy()

    # --- 趋势信号: MA金叉 ---
    df["sig_trend"] = (df["ma5"] > df["ma20"]).astype(int)

    # --- 动能信号: MACD ---
    df["sig_momentum"] = (df["macd_hist"] > 0).astype(int)

    # --- 超买过滤: RSI ---
    df["sig_rsi"] = (df["rsi"] < rsi_threshold).astype(int)

    # --- 布林带确认 ---
    df["sig_bb"] = (df["close"] > df["bb_lower"]).astype(int) if use_bb else pd.Series(1, index=df.index)

    # --- 成交量确认 (量价配合) ---
    df["sig_volume"] = (df["volume_ratio"] > 0.7).astype(int) if use_volume else pd.Series(1, index=df.index)

    # --- 复合信号 (ALL AND) ---
    df["signal_raw"] = (
        (df["sig_trend"] == 1) &
        (df["sig_momentum"] == 1) &
        (df["sig_rsi"] == 1) &
        (df["sig_bb"] == 1) &
        (df["sig_volume"] == 1)
    ).astype(int)

    # --- 做空信号 (可选) ---
    df["short_signal"] = 0
    if enable_short:
        # 做空条件: RSI超买 + MACD死叉 + 跌破MA20
        df["short_signal"] = (
            (df["rsi"] > rsi_threshold) &
            (df["macd_hist"] < 0) &
            (df["close"] < df["ma20"]) &
            (df["sig_bb"] == 0)
        ).astype(int) * -1  # -1 表示做空

    # --- 仓位管理: RSI 越高仓位越低 (过热减仓) ---
    df["position_pct"] = 1.0
    # RSI > 60 逐步减仓到 50%
    mask_high = df["rsi"] > 60
    df.loc[mask_high, "position_pct"] = np.maximum(
        0.5,
        1.0 - (df.loc[mask_high, "rsi"] - 60) / 40
    )

    # 最终仓位 = (做多信号 - 做空信号) × 仓位百分比
    df["signal"] = (df["signal_raw"] + df["short_signal"]) * df["position_pct"]

    return df


def apply_stop_loss_take_profit(df: pd.DataFrame,
                                 stop_loss_pct: float = -0.08,
                                 take_profit_pct: float = 0.25,
                                 trailing_stop_pct: float = -0.06) -> pd.DataFrame:
    """
    止损止盈机制 (动态追踪止损)
    - 固定止损: 单笔亏损超过 stop_loss_pct 平仓
    - 固定止盈: 单笔盈利超过 take_profit_pct 平仓
    - 追踪止损: 从最高点回撤超过 trailing_stop_pct 平仓
    """
    df = df.copy()
    n = len(df)
    df["signal_sltp"] = df["signal"].copy()
    df["stop_event"] = 0
    df["profit_event"] = 0
    df["trail_event"] = 0

    in_position = False
    entry_price = 0.0
    max_price = 0.0

    for t in range(n):
        if not in_position and df["signal"].iloc[t] > 0:
            # 开仓
            in_position = True
            entry_price = df["close"].iloc[t]
            max_price = entry_price

        elif in_position:
            current_price = df["close"].iloc[t]
            pnl_pct = (current_price - entry_price) / (entry_price + 1e-10)

            # 更新最高价
            if current_price > max_price:
                max_price = current_price

            # 固定止损
            if pnl_pct <= stop_loss_pct:
                df.loc[df.index[t], "signal_sltp"] = 0
                df.loc[df.index[t], "stop_event"] = 1
                in_position = False

            # 固定止盈
            elif pnl_pct >= take_profit_pct:
                df.loc[df.index[t], "signal_sltp"] = 0
                df.loc[df.index[t], "profit_event"] = 1
                in_position = False

            # 追踪止损 (从最高点回撤)
            elif (current_price - max_price) / (max_price + 1e-10) <= trailing_stop_pct:
                df.loc[df.index[t], "signal_sltp"] = 0
                df.loc[df.index[t], "trail_event"] = 1
                in_position = False

            # 信号平仓 (原始信号变0)
            elif df["signal"].iloc[t] <= 0:
                in_position = False

    return df


def backtest(signal: pd.Series, close: pd.Series, fee: float = 0.0005) -> np.ndarray:
    """
    回测引擎 (L11 核心)
    严格 shift(1) 防未来函数
    fee: 单边手续费 (万五)
    """
    n = len(close)
    # ⚠ 关键: shift(1) 避免未来函数
    position = np.roll(signal.values, 1)
    position[0] = 0

    ret = np.zeros(n)
    for t in range(1, n):
        # 当日收益率
        r = (close.iloc[t] - close.iloc[t - 1]) / (close.iloc[t - 1] + 1e-10)
        ret[t] = position[t] * r

        # 仓位变化时扣手续费
        if abs(position[t] - position[t - 1]) > 1e-8:
            ret[t] -= fee * abs(position[t] - position[t - 1])

    return ret


def ml_signal_enhance(df: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    """
    ML增强信号 (L5 sklearn)
    用 LogisticRegression 预测次日涨跌, 辅助过滤
    """
    df = df.copy()

    # 特征
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_5"] = df["close"].pct_change(5)
    df["ret_20"] = df["close"].pct_change(20)
    df["vol_ret"] = df["volume"].pct_change(5)

    # 标签: 次日涨跌
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

    feature_cols = ["ret_1", "ret_5", "ret_20", "vol_ret", "rsi", "macd_hist", "bb_pct_b"]
    df_clean = df.dropna(subset=feature_cols + ["target"])

    if len(df_clean) < 120:
        df["ml_signal"] = 1  # 数据不足, 默认全部通过
        return df

    # 时序交叉验证分训练/测试
    tscv = TimeSeriesSplit(n_splits=5)
    X = df_clean[feature_cols].values
    y = df_clean["target"].values

    scaler = StandardScaler()
    model = LogisticRegression(max_iter=1000, class_weight="balanced")

    # 取最后一批训练
    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model.fit(X_train_s, y_train)

    # 全量预测
    X_all_s = scaler.fit_transform(X)
    df_clean["ml_pred"] = model.predict(X_all_s)
    acc = accuracy_score(y, df_clean["ml_pred"])
    print(f"  ML 准确率: {acc:.2%}")

    # 合并回原数据
    df = df.merge(df_clean[["ml_pred"]], how="left", left_index=True, right_index=True)
    df["ml_signal"] = df["ml_pred"].fillna(1).astype(int)

    return df


def run_full_backtest(stock_data: pd.DataFrame, stock_name: str = "",
                      use_stop_loss: bool = True,
                      stop_loss_pct: float = -0.08,
                      take_profit_pct: float = 0.25,
                      trailing_stop_pct: float = -0.06,
                      **signal_kwargs) -> dict:
    """
    完整回测流程:
    指标 → 信号 → 止损止盈 → 回测 → 风险指标

    Args:
        stock_data: 股票日线 DataFrame
        stock_name: 标的名称
        use_stop_loss: 是否使用止损止盈
        stop_loss_pct: 固定止损比例
        take_profit_pct: 固定止盈比例
        trailing_stop_pct: 追踪止损比例
        **signal_kwargs: 传递给 generate_composite_signal 的参数
    """
    from indicators import calc_all_indicators
    from risk_metrics import calc_all_risk_metrics, calc_trade_stats

    # 1. 计算指标
    df = calc_all_indicators(stock_data)
    df = df.dropna()

    # 2. 信号生成
    df = generate_composite_signal(df, **signal_kwargs)

    # 3. 止损止盈 (可选)
    sltp_events = {"stops": 0, "profits": 0, "trails": 0}
    if use_stop_loss:
        df = apply_stop_loss_take_profit(df, stop_loss_pct, take_profit_pct, trailing_stop_pct)
        signal_for_bt = df["signal_sltp"]
        sltp_events["stops"] = int(df["stop_event"].sum())
        sltp_events["profits"] = int(df["profit_event"].sum())
        sltp_events["trails"] = int(df["trail_event"].sum())
    else:
        signal_for_bt = df["signal"]

    # 4. 回测
    strategy_ret = backtest(signal_for_bt, df["close"])

    # 5. 买入持有基准
    buy_hold_ret = df["close"].pct_change().fillna(0).values

    # 6. 净值曲线
    df["nav_strategy"] = (1 + strategy_ret).cumprod()
    df["nav_benchmark"] = (1 + buy_hold_ret).cumprod()

    # 7. 风险指标
    metrics = calc_all_risk_metrics(strategy_ret, buy_hold_ret, freq="daily")

    # 8. 交易统计
    trade_stats = calc_trade_stats(df["signal_raw"])
    trade_stats.update(sltp_events)

    # 9. 信号统计
    signal_periods = df["signal_raw"].sum()
    total_periods = len(df)
    signal_ratio = signal_periods / total_periods if total_periods > 0 else 0

    return {
        "name": stock_name,
        "df": df,
        "strategy_ret": strategy_ret,
        "buy_hold_ret": buy_hold_ret,
        "metrics": metrics,
        "trade_stats": trade_stats,
        "signal_ratio": signal_ratio,
        "n_days": len(df),
        "sltp_events": sltp_events,
    }


if __name__ == "__main__":
    import sys
    import os
    import json
    sys.path.insert(0, os.path.dirname(__file__))
    sys.stdout.reconfigure(encoding='utf-8')

    # 用模拟数据跑完整回测并保存结果
    np.random.seed(42)
    n = 500
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    demo_df = pd.DataFrame({
        "date": dates, "open": close - 0.5, "high": close + 1.5,
        "low": close - 1.5, "close": close, "volume": np.random.randint(100000, 1000000, n)
    })

    result = run_full_backtest(demo_df, "演示标的")
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "strategy")
    os.makedirs(out_dir, exist_ok=True)

    # 保存回测摘要
    summary = {
        "name": result["name"],
        "n_days": result["n_days"],
        "signal_ratio": float(result["signal_ratio"]),
        "metrics": {k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                    for k, v in result["metrics"].items()},
        "trade_stats": {k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                        for k, v in result["trade_stats"].items()}
    }
    with open(os.path.join(out_dir, "backtest_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 保存净值曲线
    nav_df = result["df"][["date", "nav_strategy", "nav_benchmark", "signal_raw", "close"]].tail(200)
    nav_df.to_csv(os.path.join(out_dir, "nav_curve.csv"), index=False, encoding="utf-8-sig")

    print(f"✅ 策略回测模块运行成功")
    print(f"  可用函数: generate_composite_signal, backtest, ml_signal_enhance, run_full_backtest")
    print(f"  年化收益: {result['metrics']['annual_return']:.2%}, 夏普: {result['metrics']['sharpe_ratio']:.2f}")
    print(f"  结果已保存至: {out_dir}")
