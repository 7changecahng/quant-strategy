"""
单元测试: risk_metrics.py 风险指标
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import numpy as np
from risk_metrics import (
    sharpe_ratio, sortino_ratio, max_drawdown, var_cvar,
    calmar_ratio, win_rate, profit_factor, annual_return,
    annual_volatility, calc_all_risk_metrics, calc_trade_stats
)


@pytest.fixture
def positive_returns():
    """始终正收益"""
    np.random.seed(42)
    return np.abs(np.random.normal(0.001, 0.01, 500))


@pytest.fixture
def mixed_returns():
    """正常混合收益"""
    np.random.seed(42)
    return np.random.normal(0.0005, 0.015, 500)


@pytest.fixture
def negative_returns():
    """亏损序列"""
    np.random.seed(42)
    return -np.abs(np.random.normal(0.001, 0.01, 500))


class TestSharpeRatio:
    def test_positive_returns_positive_sharpe(self, positive_returns):
        sr = sharpe_ratio(positive_returns)
        assert sr > 0

    def test_negative_returns_negative_sharpe(self, negative_returns):
        sr = sharpe_ratio(negative_returns)
        assert sr < 0

    def test_zero_returns(self):
        zero = np.zeros(100)
        sr = sharpe_ratio(zero)
        assert sr == 0.0


class TestMaxDrawdown:
    def test_mdd_on_uptrend(self):
        """单边上涨: nav 应该无回撤或回撤很小"""
        prices = np.linspace(100, 200, 500)
        ret = np.diff(prices) / prices[:-1]
        mdd, _, _ = max_drawdown(ret)
        assert abs(mdd) < 1e-10

    def test_mdd_on_crash(self):
        """先涨后跌: 应有明显回撤"""
        nav = np.ones(200)
        nav[:100] = np.linspace(1, 2, 100)  # 涨到2
        nav[100:] = np.linspace(2, 0.5, 100)  # 跌到0.5
        ret = np.diff(nav) / nav[:-1]
        ret = np.insert(ret, 0, 0)
        mdd, _, _ = max_drawdown(ret)
        assert mdd < -0.5  # 至少跌50%


class TestVaRCVaR:
    def test_var_cvar_order(self, mixed_returns):
        """CVaR 应该比 VaR 更极端 (更负)"""
        var, cvar = var_cvar(mixed_returns, alpha=0.05)
        assert cvar <= var  # CVaR 是尾部均值, 比 VaR 更差

    def test_var_95_negative_for_normal(self, mixed_returns):
        var, _ = var_cvar(mixed_returns, alpha=0.05)
        assert var < 0  # 正常市场 VaR 为负


class TestWinRate:
    def test_all_wins(self):
        wins = np.array([0.01] * 100)
        assert win_rate(wins) == 1.0

    def test_mixed(self, mixed_returns):
        wr = win_rate(mixed_returns)
        assert 0 <= wr <= 1


class TestProfitFactor:
    def test_all_wins_large_pf(self, positive_returns):
        pf = profit_factor(positive_returns)
        assert pf > 5

    def test_all_losses(self, negative_returns):
        pf = profit_factor(negative_returns)
        assert pf == 0.0


class TestCalcAllRiskMetrics:
    def test_all_keys_present(self, mixed_returns):
        m = calc_all_risk_metrics(mixed_returns)
        required = [
            "annual_return", "annual_volatility", "sharpe_ratio",
            "sortino_ratio", "max_drawdown", "var_95", "cvar_95",
            "calmar_ratio", "win_rate", "profit_factor", "total_return"
        ]
        for k in required:
            assert k in m, f"缺少: {k}"

    def test_with_benchmark(self, mixed_returns):
        bh = np.random.normal(0.0003, 0.012, 500)
        m = calc_all_risk_metrics(mixed_returns, bh)
        assert "bh_total_return" in m
        assert "excess_return" in m
        assert "bh_sharpe" in m


class TestTradeStats:
    def test_trade_stats_keys(self):
        import pandas as pd
        signal = pd.Series([0, 1, 1, 1, 0, 0, 1, 1, 0] * 50)
        ts = calc_trade_stats(signal)
        assert "total_trades" in ts
        assert "entries" in ts
        assert "exits" in ts
        assert "position_ratio" in ts
        assert ts["position_ratio"] > 0
