"""
风险度量模块 (L12 风险度量)
Sharpe · Sortino · 最大回撤(MDD) · VaR · CVaR · Calmar
"""
import numpy as np
import pandas as pd
from scipy import stats

# 年化因子
FREQ_MAP = {"daily": 252, "weekly": 52, "monthly": 12}


def sharpe_ratio(returns: np.ndarray, rf: float = 0.02, freq: str = "daily") -> float:
    """夏普比率 (L12)"""
    annual = FREQ_MAP.get(freq, 252)
    excess = returns - rf / annual
    if np.std(excess) < 1e-10:
        return 0.0
    return np.mean(excess) / np.std(excess) * np.sqrt(annual)


def sortino_ratio(returns: np.ndarray, rf: float = 0.02, freq: str = "daily") -> float:
    """索提诺比率 (只惩罚下行波动)"""
    annual = FREQ_MAP.get(freq, 252)
    excess = returns - rf / annual
    downside = excess[excess < 0]
    if len(downside) == 0 or np.std(downside) < 1e-10:
        return 10.0  # 无下行风险的乐观值
    return np.mean(excess) / np.std(downside) * np.sqrt(annual)


def max_drawdown(returns: np.ndarray) -> tuple:
    """
    最大回撤 (L12)
    返回: (MDD值, 开始位置, 结束位置)
    """
    nav = (1 + returns).cumprod()
    peak = np.maximum.accumulate(nav)
    drawdown = (nav - peak) / peak
    mdd = drawdown.min()
    end_idx = drawdown.argmin()
    start_idx = np.argmax(nav[:end_idx + 1]) if end_idx > 0 else 0
    return mdd, start_idx, end_idx


def var_cvar(returns: np.ndarray, alpha: float = 0.05) -> tuple:
    """
    VaR 和 CVaR (L12)
    Historical 方法
    """
    var = np.percentile(returns, alpha * 100)
    cvar = returns[returns <= var].mean()
    return var, cvar


def calmar_ratio(returns: np.ndarray, rf: float = 0.02, freq: str = "daily") -> float:
    """Calmar 比率 = 年化收益 / |MDD|"""
    annual = FREQ_MAP.get(freq, 252)
    annual_ret = np.mean(returns) * annual
    mdd, _, _ = max_drawdown(returns)
    if abs(mdd) < 1e-10:
        return 10.0
    return annual_ret / abs(mdd)


def win_rate(returns: np.ndarray) -> float:
    """胜率"""
    trades = returns[returns != 0]
    if len(trades) == 0:
        return 0
    return np.mean(trades > 0)


def profit_factor(returns: np.ndarray) -> float:
    """盈亏比"""
    pos = returns[returns > 0].sum() if len(returns[returns > 0]) > 0 else 0
    neg = abs(returns[returns < 0].sum()) if len(returns[returns < 0]) > 0 else 1e-10
    return pos / neg


def annual_return(returns: np.ndarray, freq: str = "daily") -> float:
    """年化收益率"""
    annual = FREQ_MAP.get(freq, 252)
    return np.mean(returns) * annual


def annual_volatility(returns: np.ndarray, freq: str = "daily") -> float:
    """年化波动率"""
    annual = FREQ_MAP.get(freq, 252)
    return np.std(returns) * np.sqrt(annual)


def calc_all_risk_metrics(strategy_ret: np.ndarray, benchmark_ret: np.ndarray = None,
                          rf: float = 0.02, freq: str = "daily") -> dict:
    """
    一站式风险指标计算
    """
    metrics = {
        "annual_return": annual_return(strategy_ret, freq),
        "annual_volatility": annual_volatility(strategy_ret, freq),
        "sharpe_ratio": sharpe_ratio(strategy_ret, rf, freq),
        "sortino_ratio": sortino_ratio(strategy_ret, rf, freq),
        "max_drawdown": max_drawdown(strategy_ret)[0],
        "var_95": var_cvar(strategy_ret, 0.05)[0],
        "cvar_95": var_cvar(strategy_ret, 0.05)[1],
        "calmar_ratio": calmar_ratio(strategy_ret, rf, freq),
        "win_rate": win_rate(strategy_ret),
        "profit_factor": profit_factor(strategy_ret),
        "total_return": (1 + strategy_ret).prod() - 1,
        "n_days": len(strategy_ret),
    }

    # 基准对比
    if benchmark_ret is not None:
        bh_metrics = {
            "bh_annual_return": annual_return(benchmark_ret, freq),
            "bh_sharpe": sharpe_ratio(benchmark_ret, rf, freq),
            "bh_max_drawdown": max_drawdown(benchmark_ret)[0],
            "bh_total_return": (1 + benchmark_ret).prod() - 1,
            "bh_volatility": annual_volatility(benchmark_ret, freq),
        }
        metrics.update(bh_metrics)

        # 相对超额
        metrics["excess_return"] = metrics["total_return"] - metrics["bh_total_return"]
        metrics["excess_annual"] = metrics["annual_return"] - metrics["bh_annual_return"]

    return metrics


def calc_trade_stats(signal_raw: pd.Series) -> dict:
    """
    交易统计
    """
    changes = signal_raw.diff().fillna(0)
    entries = (changes == 1).sum()
    exits = (changes == -1).sum()
    total_trades = min(entries, exits)

    # 持仓天数
    in_position = signal_raw.sum()
    total_days = len(signal_raw)
    position_ratio = in_position / total_days if total_days > 0 else 0

    return {
        "total_trades": int(total_trades),
        "entries": int(entries),
        "exits": int(exits),
        "position_days": int(in_position),
        "position_ratio": position_ratio,
        "avg_holding_period": in_position / total_trades if total_trades > 0 else 0,
    }


def format_metrics_report(metrics: dict) -> str:
    """格式化输出风险指标报告"""
    lines = []
    lines.append("=" * 55)
    lines.append("  风险指标报告 (Risk Metrics Report)")
    lines.append("=" * 55)
    lines.append(f"  年化收益率:     {metrics['annual_return']:>8.2%}")
    lines.append(f"  年化波动率:     {metrics['annual_volatility']:>8.2%}")
    lines.append(f"  累计收益:       {metrics['total_return']:>8.2%}")
    lines.append(f"  夏普比率:       {metrics['sharpe_ratio']:>8.2f}")
    lines.append(f"  索提诺比率:     {metrics['sortino_ratio']:>8.2f}")
    lines.append(f"  最大回撤:       {metrics['max_drawdown']:>8.2%}")
    lines.append(f"  VaR(95%):       {metrics['var_95']:>8.4f}")
    lines.append(f"  CVaR(95%):      {metrics['cvar_95']:>8.4f}")
    lines.append(f"  Calmar 比率:    {metrics['calmar_ratio']:>8.2f}")
    lines.append(f"  胜率:           {metrics['win_rate']:>8.2%}")
    lines.append(f"  盈亏比:         {metrics['profit_factor']:>8.2f}")

    if "bh_total_return" in metrics:
        lines.append("-" * 55)
        lines.append("  基准对比 (买入持有沪深300):")
        lines.append(f"  基准累计收益:   {metrics['bh_total_return']:>8.2%}")
        lines.append(f"  超额收益:       {metrics['excess_return']:>8.2%}")
        lines.append(f"  基准夏普:       {metrics['bh_sharpe']:>8.2f}")
        lines.append(f"  基准最大回撤:   {metrics['bh_max_drawdown']:>8.2%}")
    lines.append("=" * 55)
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    np.random.seed(42)
    fake_ret = np.random.normal(0.0005, 0.015, 500)
    bh_ret = np.random.normal(0.0003, 0.012, 500)
    m = calc_all_risk_metrics(fake_ret, bh_ret)
    report = format_metrics_report(m)
    print(report)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "risk_metrics")
    os.makedirs(out_dir, exist_ok=True)

    # 保存文本报告
    with open(os.path.join(out_dir, "risk_report.txt"), "w", encoding="utf-8") as f:
        f.write(report)

    # 保存 JSON 指标
    import json
    def convert(o):
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, np.ndarray): return o.tolist()
        raise TypeError
    with open(os.path.join(out_dir, "risk_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2, default=convert)

    # 保存交易统计
    signal = pd.Series((np.random.randn(500) > 0).astype(int))
    ts = calc_trade_stats(signal)
    with open(os.path.join(out_dir, "trade_stats.json"), "w", encoding="utf-8") as f:
        json.dump(ts, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存至: {out_dir}")
