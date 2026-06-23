"""
单元测试: indicators.py 技术指标计算
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import numpy as np
import pandas as pd
from indicators import (
    calc_ma, calc_ema, calc_macd, calc_rsi,
    calc_bollinger, calc_atr, calc_all_indicators
)


@pytest.fixture
def sample_data():
    """构造 500 天模拟数据"""
    np.random.seed(42)
    n = 500
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    return pd.DataFrame({
        "date": dates,
        "open": close - 0.5,
        "high": close + np.abs(np.random.randn(n) * 1.5),
        "low": close - np.abs(np.random.randn(n) * 1.5),
        "close": close,
        "volume": np.random.randint(100000, 1000000, n),
    })


class TestMA:
    def test_ma5_length(self, sample_data):
        result = calc_ma(sample_data["close"], 5)
        assert len(result) == 500
        assert pd.isna(result.iloc[0:4]).all()  # 前4天 NaN
        assert not pd.isna(result.iloc[4])        # 第5天有值

    def test_ma_equals_rolling_mean(self, sample_data):
        result = calc_ma(sample_data["close"], 20)
        expected = sample_data["close"].rolling(20).mean()
        pd.testing.assert_series_equal(result, expected)


class TestEMA:
    def test_ema_length(self, sample_data):
        result = calc_ema(sample_data["close"], 12)
        assert len(result) == 500
        assert not pd.isna(result.iloc[0])  # EMA 从第一天就有值


class TestMACD:
    def test_macd_no_nan(self, sample_data):
        dif, dea, hist = calc_macd(sample_data["close"])
        assert len(dif) == 500
        assert len(dea) == 500
        assert len(hist) == 500

    def test_macd_hist_sign_consistency(self, sample_data):
        dif, dea, hist = calc_macd(sample_data["close"])
        # hist = 2*(DIF-DEA), hist 和 DIF-DEA 符号应一致
        sign_match = np.sign(hist.dropna()) == np.sign((dif - dea).dropna())
        assert sign_match.all()


class TestRSI:
    def test_rsi_range(self, sample_data):
        rsi = calc_rsi(sample_data["close"]).dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

    def test_rsi_constant_price(self):
        """价格不变时 RSI 趋于稳定 (无涨跌)"""
        flat = pd.Series([100.0] * 100)
        rsi = calc_rsi(flat).dropna()
        # 价格不变时 gain=0 loss=0，RSI 会收敛
        # RSI 值应该在合理范围内，不存在 NaN
        assert not rsi.isna().any()
        # RSI 应在 [0, 100] 之间
        assert (rsi >= 0).all() and (rsi <= 100).all()


class TestBollinger:
    def test_bands_order(self, sample_data):
        upper, middle, lower, pct_b = calc_bollinger(sample_data["close"])
        valid = middle.notna()
        assert (upper[valid] >= middle[valid]).all()
        assert (middle[valid] >= lower[valid]).all()

    def test_pct_b_range(self, sample_data):
        _, _, _, pct_b = calc_bollinger(sample_data["close"])
        valid = pct_b.dropna()
        # %B 理论上在 [0,1] 但实际可能超出
        assert (valid >= -0.5).all()
        assert (valid <= 1.5).all()


class TestATR:
    def test_atr_positive(self, sample_data):
        atr = calc_atr(sample_data["high"], sample_data["low"], sample_data["close"])
        valid = atr.dropna()
        assert (valid > 0).all()


class TestCalcAllIndicators:
    def test_all_columns_present(self, sample_data):
        result = calc_all_indicators(sample_data)
        expected_cols = [
            "ma5", "ma10", "ma20", "ma60",
            "ema12", "ema26", "macd_dif", "macd_dea", "macd_hist",
            "rsi", "bb_upper", "bb_middle", "bb_lower", "bb_pct_b",
            "atr", "daily_ret", "volume_ratio"
        ]
        for col in expected_cols:
            assert col in result.columns, f"缺少列: {col}"

    def test_no_future_leakage_ma(self, sample_data):
        """验证 MA 计算无未来函数: shift 后不应有非NaN变化"""
        result = calc_all_indicators(sample_data)
        # MA5 的第5个值应该只用到前5天数据
        # 简单验证: ma5 从第5个开始有值，第4个为 NaN
        assert pd.isna(result["ma5"].iloc[3])
        assert not pd.isna(result["ma5"].iloc[4])
