"""
数据获取模块 (L7 爬虫 + L3 Pandas + L8 SQL)
获取沪深300成分股行情数据、财务数据
双数据源: akshare(主) + baostock(备) + 重试机制
"""
import pandas as pd
import numpy as np
import sqlite3
import os
import time
from datetime import datetime, timedelta

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(os.path.join(DATA_DIR, "raw"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "processed"), exist_ok=True)

# 精选沪深300代表性标的（覆盖多个行业）
TARGET_STOCKS = {
    "600519": "贵州茅台",   # 白酒
    "000858": "五粮液",     # 白酒
    "601318": "中国平安",   # 金融
    "600036": "招商银行",   # 银行
    "000333": "美的集团",   # 家电
    "002415": "海康威视",   # 科技
    "600276": "恒瑞医药",   # 医药
    "601012": "隆基绿能",   # 光伏
    "300750": "宁德时代",   # 新能源
    "600887": "伊利股份",   # 食品
}

# 基准指数
BENCHMARK = "000300"  # 沪深300

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 秒


def _retry_wrapper(func, *args, max_retries=MAX_RETRIES, delay=RETRY_DELAY, **kwargs):
    """通用重试装饰器逻辑"""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, pd.DataFrame) and not result.empty:
                return result
            if isinstance(result, pd.DataFrame) and attempt < max_retries - 1:
                print(f"    返回空数据, 重试 {attempt+2}/{max_retries}...")
                time.sleep(delay)
                continue
            return result
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                print(f"    失败, 重试 {attempt+2}/{max_retries}... ({e})")
                time.sleep(delay)
    raise last_error if last_error else Exception("所有重试均失败")


def _fetch_stock_akshare(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """akshare 数据源"""
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol=code, period="daily",
                            start_date=start_date, end_date=end_date,
                            adjust="qfq")
    df = df.rename(columns={
        "日期": "date", "开盘": "open", "收盘": "close",
        "最高": "high", "最低": "low", "成交量": "volume",
        "成交额": "amount", "换手率": "turnover"
    })
    df["date"] = pd.to_datetime(df["date"])
    df["code"] = code
    return df.sort_values("date").reset_index(drop=True)


def _fetch_stock_baostock(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """baostock 备用数据源"""
    import baostock as bs
    bs.login()
    try:
        # baostock 格式: sh.600519 或 sz.000858
        prefix = "sh" if code.startswith(("6", "9")) else "sz"
        bs_code = f"{prefix}.{code}"
        start_fmt = start_date[:4] + "-" + start_date[4:6] + "-" + start_date[6:]
        end_fmt = end_date[:4] + "-" + end_date[4:6] + "-" + end_date[6:]

        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount,turn",
            start_date=start_fmt, end_date=end_fmt,
            frequency="d", adjustflag="2"  # 前复权
        )
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())

        df = pd.DataFrame(data_list, columns=["date", "open", "high", "low",
                                               "close", "volume", "amount", "turnover"])
        if df.empty:
            return df

        for col in ["open", "high", "low", "close", "volume", "amount", "turnover"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        df["code"] = code
        return df.sort_values("date").reset_index(drop=True)
    finally:
        bs.logout()


def fetch_stock_daily(code: str, start_date: str = "20220101", end_date: str = "20251231") -> pd.DataFrame:
    """
    使用双数据源获取个股日线数据 (前复权)
    主数据源: akshare, 备用: baostock
    对应课程 L7 爬虫 + L3 Pandas
    """
    print(f"  正在获取 {code} ...")

    # 尝试 akshare (主)
    try:
        df = _retry_wrapper(_fetch_stock_akshare, code, start_date, end_date)
        if not df.empty:
            print(f"    ✓ akshare 成功 ({len(df)} 行)")
            time.sleep(0.3)
            return df
    except Exception as e:
        print(f"    ⚠ akshare 失败: {e}")

    # 回退到 baostock (备)
    print(f"    尝试 baostock 备用数据源...")
    try:
        df = _retry_wrapper(_fetch_stock_baostock, code, start_date, end_date, max_retries=2)
        if not df.empty:
            print(f"    ✓ baostock 成功 ({len(df)} 行)")
            return df
    except Exception as e:
        print(f"    ⚠ baostock 也失败: {e}")

    print(f"    ✗ {code} 所有数据源均获取失败")
    return pd.DataFrame()


def fetch_index_daily(code: str = "000300", start_date: str = "20220101", end_date: str = "20251231") -> pd.DataFrame:
    """获取指数日线作为基准 (双数据源 + 重试)"""
    print(f"  正在获取指数 {code} ...")

    # 尝试 akshare
    try:
        import akshare as ak
        prefix = "sh" if code.startswith("000") else "sz"
        df = _retry_wrapper(lambda: ak.stock_zh_index_daily(symbol=f"{prefix}{code}"))
        df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        df = df.sort_values("date").reset_index(drop=True)
        df["code"] = code
        print(f"    ✓ akshare 成功 ({len(df)} 行)")
        return df
    except Exception as e:
        print(f"    ⚠ akshare 指数失败: {e}")

    # 回退到 baostock
    print(f"    尝试 baostock...")
    try:
        import baostock as bs
        bs.login()
        try:
            start_fmt = start_date[:4] + "-" + start_date[4:6] + "-" + start_date[6:]
            end_fmt = end_date[:4] + "-" + end_date[4:6] + "-" + end_date[6:]
            rs = bs.query_history_k_data_plus(
                f"sh.{code}",
                "date,open,high,low,close,volume,amount",
                start_date=start_fmt, end_date=end_fmt,
                frequency="d", adjustflag="2"
            )
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            df = pd.DataFrame(data_list, columns=["date", "open", "high", "low", "close", "volume", "amount"])
            if df.empty:
                return df
            for col in ["open", "high", "low", "close", "volume", "amount"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])
            df["code"] = code
            print(f"    ✓ baostock 成功 ({len(df)} 行)")
            return df.sort_values("date").reset_index(drop=True)
        finally:
            bs.logout()
    except Exception as e:
        print(f"    ✗ 指数获取失败: {e}")
        return pd.DataFrame()


def save_to_sqlite(df: pd.DataFrame, table_name: str, db_path: str = None):
    """
    数据存入 SQLite (L8 SQL)
    """
    if db_path is None:
        db_path = os.path.join(DATA_DIR, "processed", "finance.db")
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()  # 别忘了 commit！(L8 教训)
    conn.close()
    print(f"  ✓ 已写入 SQLite: {table_name} ({len(df)} 行)")


def load_from_sqlite(table_name: str, db_path: str = None) -> pd.DataFrame:
    """从 SQLite 读取数据"""
    if db_path is None:
        db_path = os.path.join(DATA_DIR, "processed", "finance.db")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def run_data_pipeline():
    """
    完整数据流水线: 获取 → 清洗 → 入库
    """
    print("=" * 50)
    print("数据流水线启动 (L3+L7+L8)")
    print("=" * 50)

    all_stocks = {}
    all_data_list = []

    # 1. 获取个股数据
    print("\n[1/3] 获取个股日线...")
    for code, name in TARGET_STOCKS.items():
        df = fetch_stock_daily(code)
        if not df.empty:
            df["name"] = name
            all_stocks[code] = df
            all_data_list.append(df)
            save_to_sqlite(df, f"stock_{code}")

    # 2. 获取基准指数
    print("\n[2/3] 获取基准指数...")
    bench_df = fetch_index_daily(BENCHMARK)
    if not bench_df.empty:
        save_to_sqlite(bench_df, "benchmark_hs300")

    # 3. 合并全部数据
    print("\n[3/3] 合并数据...")
    if all_data_list:
        merged = pd.concat(all_data_list, ignore_index=True)
        merged.to_csv(os.path.join(DATA_DIR, "raw", "all_stocks.csv"), index=False)
        print(f"  ✓ 合并数据已保存: {len(merged)} 行, {len(all_stocks)} 只股票")

    print("\n" + "=" * 50)
    print("数据流水线完成!")
    print("=" * 50)
    return all_stocks, bench_df


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    # 尝试运行数据流水线（可能因网络失败）
    try:
        run_data_pipeline()
    except Exception as e:
        print(f"[提示] 数据下载失败 (网络不可用): {e}")
        print("  将使用现有数据库导出摘要...")

    # 将数据摘要保存到 output/data_fetcher/
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "data_fetcher")
    os.makedirs(out_dir, exist_ok=True)

    # 复制数据库（如果存在）
    db_src = os.path.join(DATA_DIR, "processed", "finance.db")
    db_dst = os.path.join(out_dir, "finance.db")
    if os.path.exists(db_src):
        import shutil
        shutil.copy2(db_src, db_dst)
        print(f"  ✓ 数据库已复制至: {db_dst}")

    # 保存标的清单
    import json
    stocks_info = [{"code": k, "name": v} for k, v in TARGET_STOCKS.items()]
    with open(os.path.join(out_dir, "target_stocks.json"), "w", encoding="utf-8") as f:
        json.dump(stocks_info, f, ensure_ascii=False, indent=2)

    # 保存数据摘要（读取现有数据库统计）
    try:
        summary = []
        for code in TARGET_STOCKS:
            try:
                df = load_from_sqlite(f"stock_{code}")
                summary.append({
                    "code": code,
                    "name": TARGET_STOCKS[code],
                    "rows": len(df),
                    "start": str(df["date"].min().date()) if not df.empty else "N/A",
                    "end": str(df["date"].max().date()) if not df.empty else "N/A",
                })
            except Exception:
                summary.append({"code": code, "name": TARGET_STOCKS[code], "rows": 0, "start": "N/A", "end": "N/A"})

        summary_df = pd.DataFrame(summary)
        summary_df.to_csv(os.path.join(out_dir, "data_summary.csv"), index=False, encoding="utf-8-sig")
        print(f"  ✓ 数据摘要已保存")
    except Exception as e:
        print(f"  ⚠ 数据摘要生成失败: {e}")

    print(f"\n结果已保存至: {out_dir}")
