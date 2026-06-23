"""
参数优化模块 (L11 回测优化 + L5 sklearn 网格搜索)
对 MA/RSI/布林带参数进行网格搜索，找到最优组合
"""
import numpy as np
import pandas as pd
import os
import json
import itertools
from datetime import datetime
from sklearn.model_selection import TimeSeriesSplit


def load_config():
    """加载配置文件"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def param_grid_search(stock_data: pd.DataFrame,
                      param_grid: dict,
                      objective: str = "sharpe_ratio",
                      cv_folds: int = 5) -> list:
    """
    网格搜索最优参数 (时序交叉验证)
    
    Args:
        stock_data: 股票日线数据 (需包含 close, high, low, volume)
        param_grid: 参数网格, 如 {"ma_fast": [3,5,8], "ma_slow": [15,20,25]}
        objective: 优化目标 "sharpe_ratio" / "sortino_ratio" / "calmar_ratio" / "total_return"
        cv_folds: 交叉验证折数
    
    Returns:
        按目标排序的参数组合列表
    """
    from indicators import calc_all_indicators
    from risk_metrics import calc_all_risk_metrics

    # 生成所有参数组合
    keys = list(param_grid.keys())
    combinations = [dict(zip(keys, vals)) for vals in itertools.product(*param_grid.values())]

    results = []
    total = len(combinations)

    print(f"\n🔍 网格搜索: {total} 种参数组合, {cv_folds} 折交叉验证")
    print(f"   优化目标: {objective}")

    # 预处理: 计算所有指标 (只算一次)
    df_full = calc_all_indicators(stock_data).dropna()
    if len(df_full) < 120:
        print(f"   ⚠ 数据不足 (仅 {len(df_full)} 行), 至少需要 120 行")
        return []

    close_all = df_full["close"].values
    n = len(df_full)

    for i, params in enumerate(combinations):
        # 用当前参数覆盖指标 (仅覆盖变化的)
        df = df_full.copy()
        ma_fast = params.get("ma_fast", 5)
        ma_slow = params.get("ma_slow", 20)

        df["ma5"] = df["close"].rolling(window=ma_fast).mean()
        df["ma20"] = df["close"].rolling(window=ma_slow).mean()

        # 生成信号
        df["sig_trend"] = (df["ma5"] > df["ma20"]).astype(int)
        df["sig_momentum"] = (df["macd_hist"] > 0).astype(int)

        rsi_thresh = params.get("rsi_threshold", 70)
        df["sig_rsi"] = (df["rsi"] < rsi_thresh).astype(int)
        df["sig_bb"] = (df["close"] > df["bb_lower"]).astype(int)
        df["sig_volume"] = (df["volume_ratio"] > 0.7).astype(int)

        df["signal_raw"] = (
            (df["sig_trend"] == 1) & (df["sig_momentum"] == 1) &
            (df["sig_rsi"] == 1) & (df["sig_bb"] == 1) & (df["sig_volume"] == 1)
        ).astype(int)
        df["signal"] = df["signal_raw"]
        df = df.dropna()

        if len(df) < 60:
            results.append({**params, "score": -999, "status": "data_insufficient"})
            continue

        # 时序交叉验证回测 (使用 df 自身的 close 和 signal)
        cv_scores = []
        fold_size = len(df) // (cv_folds + 1)

        for fold in range(cv_folds):
            train_end = (fold + 1) * fold_size
            test_end = min((fold + 2) * fold_size, len(df))
            test_close = df["close"].values[train_end:test_end]
            test_signal = df["signal"].values[train_end:test_end]

            if len(test_close) < 30:
                continue

            # 回测 (简单版本: 无手续费)
            ret = np.zeros(len(test_close))
            for t in range(1, len(test_close)):
                r = (test_close[t] - test_close[t-1]) / (test_close[t-1] + 1e-10)
                ret[t] = test_signal[t] * r

            metrics = calc_all_risk_metrics(ret, None)
            cv_scores.append(metrics.get(objective, 0))

        avg_score = np.mean(cv_scores) if cv_scores else -999
        params["score"] = round(float(avg_score), 4)
        params["cv_scores"] = [round(float(s), 4) for s in cv_scores]
        params["status"] = "ok"

        if (i + 1) % max(1, total // 10) == 0 or i == total - 1:
            print(f"   进度: {i+1}/{total}, 当前最优: {max(results, key=lambda x: x['score'])['score']:.4f}")

        results.append(params)

    # 按目标排序 (越大越好)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def run_optimization(code: str = "600519", name: str = "贵州茅台") -> dict:
    """
    对指定标的运行完整参数优化
    """
    from data_fetcher import load_from_sqlite, TARGET_STOCKS

    cfg = load_config()
    opt_cfg = cfg["optimization"]

    # 构建参数网格
    param_grid = {
        "ma_fast": opt_cfg.get("ma_fast_range", [3, 5, 8, 10]),
        "ma_slow": opt_cfg.get("ma_slow_range", [15, 20, 25, 30]),
        "rsi_threshold": opt_cfg.get("rsi_threshold_range", [60, 65, 70, 75, 80]),
    }
    objective = opt_cfg.get("objective", "sharpe_ratio")
    cv_folds = opt_cfg.get("cv_folds", 5)

    print(f"\n{'='*60}")
    print(f"  参数优化: {name} ({code})")
    print(f"{'='*60}")

    # 加载数据
    try:
        df = load_from_sqlite(f"stock_{code}")
        print(f"  数据: {len(df)} 行")
    except Exception:
        print(f"  ⚠ 数据库无数据, 使用模拟数据")
        np.random.seed(42)
        n = 500
        dates = pd.date_range("2022-01-01", periods=n, freq="B")
        close = 100 + np.cumsum(np.random.randn(n) * 2)
        df = pd.DataFrame({
            "date": dates, "open": close - 0.5, "high": close + 1.5,
            "low": close - 1.5, "close": close,
            "volume": np.random.randint(100000, 1000000, n)
        })

    # 运行网格搜索
    results = param_grid_search(df, param_grid, objective, cv_folds)

    if not results:
        print("  ❌ 无有效结果")
        return {}

    # 输出最优
    best = results[0]
    print(f"\n  🏆 最优参数 (按 {objective}):")
    for k, v in best.items():
        if k not in ("score", "cv_scores", "status"):
            print(f"     {k}: {v}")
    print(f"     {objective}: {best['score']}")

    # 保存结果
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "optimizer")
    os.makedirs(out_dir, exist_ok=True)

    # 保存完整结果
    with open(os.path.join(out_dir, f"optimization_{code}.json"), "w", encoding="utf-8") as f:
        json.dump({
            "code": code, "name": name, "objective": objective,
            "cv_folds": cv_folds, "total_combinations": len(results),
            "timestamp": datetime.now().isoformat(),
            "results": results[:20]  # 保存前20条
        }, f, ensure_ascii=False, indent=2)

    # 保存 CSV 汇总
    summary_rows = []
    for r in results[:20]:
        row = {k: v for k, v in r.items() if k not in ("cv_scores", "status")}
        summary_rows.append(row)
    pd.DataFrame(summary_rows).to_csv(
        os.path.join(out_dir, f"optimization_{code}.csv"),
        index=False, encoding="utf-8-sig")

    print(f"\n  结果已保存至: {out_dir}")
    return best


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("  参数优化模块")
    print("=" * 60)

    # 对茅台进行参数优化演示
    run_optimization("600519", "贵州茅台")
