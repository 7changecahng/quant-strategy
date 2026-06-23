"""
主回测运行脚本 —— 一键跑完所有标的
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from data_fetcher import TARGET_STOCKS, run_data_pipeline, load_from_sqlite
from strategy import run_full_backtest
from risk_metrics import format_metrics_report, calc_all_risk_metrics
import json


def run_all_stocks():
    """对全部标的运行回测"""
    # 1. 确保数据存在
    print("📦 检查数据...")
    try:
        conn_check = load_from_sqlite("stock_600519")
        print("  数据已存在,跳过下载")
    except Exception:
        print("  数据不存在,开始下载...")
        run_data_pipeline()

    # 2. 逐个回测
    results = {}
    all_summary = []

    print("\n🚀 开始批量回测...")
    for code, name in TARGET_STOCKS.items():
        print(f"\n--- {name} ({code}) ---")
        try:
            try:
                df = load_from_sqlite(f"stock_{code}")
                if df.empty:
                    raise Exception("空数据")
            except Exception:
                # 数据不存在时使用模拟数据演示
                print(f"  ⚠ 数据库无数据, 使用模拟数据演示")
                np.random.seed(hash(code) % 10000)
                n = 500
                dates = pd.date_range("2022-01-01", periods=n, freq="B")
                close = 100 + np.cumsum(np.random.randn(n) * 2)
                df = pd.DataFrame({
                    "date": dates, "open": close - 0.5, "high": close + 1.5,
                    "low": close - 1.5, "close": close,
                    "volume": np.random.randint(100000, 1000000, n)
                })

            result = run_full_backtest(df, name)
            results[code] = result
            metrics = result["metrics"]

            summary = {
                "code": code,
                "name": name,
                "total_return": f"{metrics['total_return']:.2%}",
                "annual_return": f"{metrics['annual_return']:.2%}",
                "sharpe": f"{metrics['sharpe_ratio']:.2f}",
                "mdd": f"{metrics['max_drawdown']:.2%}",
                "win_rate": f"{metrics['win_rate']:.2%}",
                "signal_ratio": f"{result['signal_ratio']:.1%}",
            }

            if "excess_return" in metrics:
                summary["excess_return"] = f"{metrics['excess_return']:.2%}"

            all_summary.append(summary)
            print(format_metrics_report(metrics))

        except Exception as e:
            print(f"  ❌ 回测失败: {e}")
            import traceback
            traceback.print_exc()

    # 3. 输出汇总表
    print("\n\n" + "=" * 80)
    print("  📊 全标回测汇总")
    print("=" * 80)
    summary_df = pd.DataFrame(all_summary)
    print(summary_df.to_string(index=False))

    # 保存到原路径
    summary_df.to_csv(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "summary.csv"), index=False)

    # 4. 保存完整结果(JSON)
    save_results = {}
    for code, r in results.items():
        save_results[code] = {
            "name": r["name"],
            "metrics": {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
                        for k, v in r["metrics"].items()},
            "signal_ratio": float(r["signal_ratio"]),
            "n_days": r["n_days"],
        }
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "results.json"), "w", encoding="utf-8") as f:
        json.dump(save_results, f, ensure_ascii=False, indent=2)

    # 5. 额外保存到 output/run_backtest/ （新目录）
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "run_backtest")
    os.makedirs(out_dir, exist_ok=True)

    summary_df.to_csv(os.path.join(out_dir, "summary.csv"), index=False, encoding="utf-8-sig")
    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(save_results, f, ensure_ascii=False, indent=2)

    # 为每只股票保存详细回测数据
    for code, r in results.items():
        stock_dir = os.path.join(out_dir, f"stock_{code}")
        os.makedirs(stock_dir, exist_ok=True)

        df = r["df"]
        # 净值曲线 + 信号
        nav_cols = ["date", "close", "nav_strategy", "nav_benchmark",
                    "signal_raw", "signal", "rsi", "macd_hist", "bb_pct_b"]
        available = [c for c in nav_cols if c in df.columns]
        df[available].to_csv(os.path.join(stock_dir, "backtest_detail.csv"),
                            index=False, encoding="utf-8-sig")

        # 单个股票指标
        with open(os.path.join(stock_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(save_results[code], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 全部回测完成,结果已保存")
    print(f"  输出目录: {out_dir}")
    return results


def run_oos_validation(oos_end_date: str = "2025-12-31",
                       train_end_date: str = "2024-12-31") -> pd.DataFrame:
    """
    样本外验证 (Out-of-Sample Validation)

    将数据按时间切分为:
      - 样本内 (In-Sample): 数据起始日 → train_end_date
      - 样本外 (Out-of-Sample): train_end_date 次日 → oos_end_date

    分别回测并对比指标衰减，验证策略是否过拟合。

    返回: 对比表 DataFrame
    """
    print("\n" + "=" * 80)
    print("  🔬 样本外验证 (Out-of-Sample Test)")
    print(f"  训练期: ~{train_end_date}  |  测试期: {train_end_date} ~ {oos_end_date}")
    print("=" * 80)

    train_end_dt = pd.Timestamp(train_end_date)
    oos_end_dt = pd.Timestamp(oos_end_date)

    all_comparison = []

    for code, name in TARGET_STOCKS.items():
        print(f"\n--- {name} ({code}) ---")

        try:
            # 1. 加载全量数据
            try:
                df = load_from_sqlite(f"stock_{code}")
                if df.empty:
                    raise Exception("空数据")
            except Exception:
                print(f"  ⚠ 数据库无数据, 使用模拟数据")
                np.random.seed(hash(code) % 10000)
                n = 800
                dates = pd.date_range("2022-01-01", periods=n, freq="B")
                close = 100 + np.cumsum(np.random.randn(n) * 2)
                df = pd.DataFrame({
                    "date": dates, "open": close - 0.5, "high": close + 1.5,
                    "low": close - 1.5, "close": close,
                    "volume": np.random.randint(100000, 1000000, n)
                })

            # 2. 切割数据
            df["date"] = pd.to_datetime(df["date"])
            df_is = df[df["date"] <= train_end_dt].copy()
            df_oos = df[(df["date"] > train_end_dt) & (df["date"] <= oos_end_dt)].copy()

            if len(df_is) < 60 or len(df_oos) < 20:
                print(f"  ⚠ 数据不足 (IS:{len(df_is)}, OOS:{len(df_oos)}), 跳过")
                continue

            # 3. 样本内回测
            result_is = run_full_backtest(df_is, f"{name}(IS)", use_stop_loss=True)
            m_is = result_is["metrics"]

            # 4. 样本外回测 (同样参数, 不做任何优化)
            result_oos = run_full_backtest(df_oos, f"{name}(OOS)", use_stop_loss=True)
            m_oos = result_oos["metrics"]

            # 5. 计算衰减
            sharpe_decay = m_is["sharpe_ratio"] - m_oos["sharpe_ratio"]
            return_decay = m_is["annual_return"] - m_oos["annual_return"]
            mdd_widen = abs(m_oos["max_drawdown"]) - abs(m_is["max_drawdown"])

            row = {
                "code": code,
                "name": name,
                "IS_days": len(df_is),
                "OOS_days": len(df_oos),
                "IS_Sharpe": f"{m_is['sharpe_ratio']:.2f}",
                "OOS_Sharpe": f"{m_oos['sharpe_ratio']:.2f}",
                "Sharpe_decay": f"{sharpe_decay:+.2f}",
                "IS_Return": f"{m_is['annual_return']:.2%}",
                "OOS_Return": f"{m_oos['annual_return']:.2%}",
                "IS_MDD": f"{m_is['max_drawdown']:.2%}",
                "OOS_MDD": f"{m_oos['max_drawdown']:.2%}",
                "IS_WinRate": f"{m_is['win_rate']:.2%}",
                "OOS_WinRate": f"{m_oos['win_rate']:.2%}",
                "Signal_IS": f"{result_is['signal_ratio']:.1%}",
                "Signal_OOS": f"{result_oos['signal_ratio']:.1%}",
            }
            all_comparison.append(row)

            # 简短结论
            if sharpe_decay < 0.3 and m_oos["sharpe_ratio"] > 0.5:
                verdict = "✅ 稳健"
            elif sharpe_decay < 0.6:
                verdict = "⚠️ 小幅衰减"
            else:
                verdict = "❌ 显著衰减"

            print(f"  IS Sharpe={m_is['sharpe_ratio']:.2f} | "
                  f"OOS Sharpe={m_oos['sharpe_ratio']:.2f} | "
                  f"衰减={sharpe_decay:+.2f} | {verdict}")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            import traceback
            traceback.print_exc()

    # 6. 输出汇总
    print("\n\n" + "=" * 80)
    print("  📊 样本外验证汇总")
    print("=" * 80)

    if not all_comparison:
        print("  ⚠ 无有效数据")
        return pd.DataFrame()

    oos_df = pd.DataFrame(all_comparison)

    # 计算各列均值 (数值列)
    numeric_cols = ["IS_days", "OOS_days"]
    avg_row = {"code": "**平均**", "name": ""}
    for col in oos_df.columns:
        if col in numeric_cols:
            avg_row[col] = int(oos_df[col].mean())
        elif col.startswith("Sharpe_decay"):
            try:
                avg_row[col] = f"{oos_df[col].astype(float).mean():+.2f}"
            except Exception:
                avg_row[col] = ""
        else:
            avg_row[col] = ""

    oos_df_display = oos_df.copy()
    print(oos_df_display.to_string(index=False))

    # 7. 总体结论
    try:
        avg_decay = oos_df["Sharpe_decay"].astype(float).mean()
        print(f"\n  平均 Sharpe 衰减: {avg_decay:+.2f}")
        if avg_decay < 0.3:
            print("  ✅ 结论: 策略在样本外表现稳健, 无明显过拟合迹象")
        elif avg_decay < 0.5:
            print("  ⚠️ 结论: 策略存在一定衰减, 但在可接受范围内")
        else:
            print("  ❌ 结论: 策略可能过拟合, 需进一步简化/正则化")
    except Exception:
        pass

    # 8. 保存结果
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "oos_validation")
    os.makedirs(out_dir, exist_ok=True)
    oos_df.to_csv(os.path.join(out_dir, "oos_comparison.csv"), index=False, encoding="utf-8-sig")

    # 同时保存每个标的的 OOS 详情
    for code in [r["code"] for r in all_comparison]:
        try:
            df = load_from_sqlite(f"stock_{code}")
            df["date"] = pd.to_datetime(df["date"])
            train_end_dt = pd.Timestamp(train_end_date)
            oos_end_dt = pd.Timestamp(oos_end_date)
            df_oos = df[(df["date"] > train_end_dt) & (df["date"] <= oos_end_dt)].copy()
            if len(df_oos) >= 20:
                result_oos = run_full_backtest(df_oos, TARGET_STOCKS.get(code, code))
                stock_dir = os.path.join(out_dir, f"stock_{code}")
                os.makedirs(stock_dir, exist_ok=True)
                nav = result_oos["df"][["date", "close", "nav_strategy", "nav_benchmark",
                                          "signal_raw", "signal"]]
                nav.to_csv(os.path.join(stock_dir, "oos_detail.csv"), index=False, encoding="utf-8-sig")
        except Exception:
            pass

    print(f"\n✅ 样本外验证完成, 结果已保存至: {out_dir}")
    return oos_df


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    run_all_stocks()
    print("\n")
    run_oos_validation()
