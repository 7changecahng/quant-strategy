"""
单元测试: strategy.py 策略信号与回测
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import numpy as np
import pandas as pd
from strategy import (
    generate_composite_signal, backtest, apply_stop_loss_take_profit,
    ml_signal_enhance, run_full_backtest
)
from indicators import calc_all_indicators


@pytest.fixture
def df_with_indicators():
    """生成带指标的 DataFrame"""
    np.random.seed(42)
    n = 500
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    df = pd.DataFrame({
        "date": dates, "open": close - 0.5, "high": close + 1.5,
        "low": close - 1.5, "close": close,
        "volume": np.random.randint(100000, 1000000, n),
    })
    return calc_all_indicators(df).dropna()


class TestGenerateSignal:
    def test_signal_is_binary(self, df_with_indicators):
        df = generate_composite_signal(df_with_indicators)
        unique = df["signal_raw"].unique()
        assert set(unique).issubset({0, 1})

    def test_signal_in_range(self, df_with_indicators):
        df = generate_composite_signal(df_with_indicators)
        # signal 值在 [0, 1] 之间 (含仓位)
        assert (df["signal"] >= -0.01).all()
        assert (df["signal"] <= 1.01).all()

    def test_position_pct_between_05_and_1(self, df_with_indicators):
        df = generate_composite_signal(df_with_indicators)
        assert (df["position_pct"] >= 0.49).all()
        assert (df["position_pct"] <= 1.01).all()

    def test_short_signal_off_by_default(self, df_with_indicators):
        df = generate_composite_signal(df_with_indicators, enable_short=False)
        assert (df["short_signal"] == 0).all()

    def test_short_signal_when_enabled(self, df_with_indicators):
        df = generate_composite_signal(df_with_indicators, enable_short=True)
        # 应该有 -1 或 0
        unique = df["short_signal"].unique()
        assert set(unique).issubset({0, -1})


class TestBacktest:
    def test_no_future_leakage(self, df_with_indicators):
        """回测第 t 天不应用到第 t+1 天数据"""
        df = generate_composite_signal(df_with_indicators)
        ret = backtest(df["signal"], df["close"])

        # 构造"偷看"版本: 使用未shift的信号
        ret_cheated = np.zeros(len(df))
        for t in range(1, len(df)):
            r = (df["close"].iloc[t] - df["close"].iloc[t-1]) / df["close"].iloc[t-1]
            ret_cheated[t] = df["signal"].iloc[t] * r  # 使用当天信号

        # shift版收益不应等于偷看版
        assert not np.allclose(ret[1:], ret_cheated[1:])

    def test_first_day_zero(self, df_with_indicators):
        df = generate_composite_signal(df_with_indicators)
        ret = backtest(df["signal"], df["close"])
        assert ret[0] == 0.0

    def test_cash_stays_cash(self):
        """空仓期间收益应为0"""
        close = pd.Series([100, 101, 102, 103, 104])
        signal = pd.Series([0, 0, 0, 0, 0])
        ret = backtest(signal, close)
        assert (ret == 0).all()


class TestStopLoss:
    def test_stop_loss_trigger_applied(self, df_with_indicators):
        """止损函数运行不报错"""
        df = generate_composite_signal(df_with_indicators)
        result = apply_stop_loss_take_profit(df)
        assert "signal_sltp" in result.columns
        assert "stop_event" in result.columns
        assert "profit_event" in result.columns

    def test_stop_loss_signal_not_greater_than_original(self, df_with_indicators):
        """止损后信号不能超过原始信号"""
        df = generate_composite_signal(df_with_indicators)
        result = apply_stop_loss_take_profit(df)
        # signal_sltp 要么等于 signal, 要么为0 (被止损)
        valid = result["signal_sltp"].notna() & result["signal"].notna()
        assert (result.loc[valid, "signal_sltp"] <= result.loc[valid, "signal"]).all()


class TestRunFullBacktest:
    def test_returns_dict(self, df_with_indicators):
        result = run_full_backtest(df_with_indicators, "测试")
        assert isinstance(result, dict)
        assert "metrics" in result
        assert "df" in result
        assert "trade_stats" in result

    def test_without_stop_loss(self, df_with_indicators):
        result = run_full_backtest(df_with_indicators, "测试", use_stop_loss=False)
        assert result["metrics"]["sharpe_ratio"] is not None

    def test_with_stop_loss(self, df_with_indicators):
        result = run_full_backtest(df_with_indicators, "测试", use_stop_loss=True)
        assert "sltp_events" in result
