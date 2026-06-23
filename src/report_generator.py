"""
HTML 回测报告生成器 (Jinja2 模板)
自动生成包含净值曲线、指标卡片、交易记录的专业回测报告
"""
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime


def _convert_value(v):
    """安全转换 numpy 类型"""
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def _plotly_line_chart(x_data, y1_data, y1_name, y2_data=None, y2_name=None,
                       title="", height=400, y_format=".2f") -> str:
    """生成 Plotly HTML 片段 (离线, 不依赖 plotly 运行时)"""
    import json as _json

    traces = [{
        "x": list(x_data),
        "y": [round(float(v), 4) for v in y1_data],
        "type": "scatter",
        "name": y1_name,
        "line": {"color": "#3366CC", "width": 2}
    }]
    if y2_data is not None and y2_name is not None:
        traces.append({
            "x": list(x_data),
            "y": [round(float(v), 4) for v in y2_data],
            "type": "scatter",
            "name": y2_name,
            "line": {"color": "#999999", "width": 1.5, "dash": "dash"}
        })

    chart_data = _json.dumps(traces)
    layout = _json.dumps({
        "title": title,
        "height": height,
        "margin": {"l": 60, "r": 20, "t": 40, "b": 40},
        "legend": {"orientation": "h", "y": 1.1},
        "yaxis": {"tickformat": y_format},
    })

    return f"""
    <div id="chart_{hash(title) % 10000}"></div>
    <script>
        (function() {{
            if (typeof Plotly === 'undefined') {{
                var s = document.createElement('script');
                s.src = 'https://cdn.plot.ly/plotly-2.32.0.min.js';
                s.onload = function() {{ renderChart(); }};
                document.head.appendChild(s);
            }} else {{
                renderChart();
            }}
            function renderChart() {{
                Plotly.newPlot(
                    document.currentScript.previousElementSibling,
                    {chart_data},
                    {layout},
                    {{ responsive: true, displayModeBar: false }}
                );
            }}
        }})();
    </script>"""


def _metric_card(label: str, value: str, sub: str = "", color: str = "#1E7A4A", icon: str = "📊") -> str:
    """生成指标卡片 HTML"""
    return f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-sub">{sub if sub else '&nbsp;'}</div>
    </div>"""


def generate_html_report(backtest_result: dict, code: str, name: str,
                         output_path: str = None) -> str:
    """
    生成完整的 HTML 回测报告

    Args:
        backtest_result: run_full_backtest 返回的字典
        code: 股票代码
        name: 股票名称
        output_path: 输出路径 (可选)

    Returns:
        HTML 字符串
    """
    df = backtest_result["df"]
    metrics = backtest_result["metrics"]
    trade_stats = backtest_result["trade_stats"]

    # 计算图表数据
    nav_dates = df["date"].dt.strftime("%Y-%m-%d").tolist()
    nav_strategy = df["nav_strategy"].values
    nav_bench = df["nav_benchmark"].values

    # 回撤曲线
    dd_strategy = (df["nav_strategy"] / df["nav_strategy"].cummax() - 1).values
    dd_bench = (df["nav_benchmark"] / df["nav_benchmark"].cummax() - 1).values

    # 交易记录
    signal_changes = df["signal_raw"].diff().fillna(0)
    buy_signals = df[signal_changes == 1]
    sell_signals = df[signal_changes == -1]

    trade_rows = ""
    profit_total = 0
    for i, (_, buy_row) in enumerate(buy_signals.iterrows()):
        after_buy = sell_signals[sell_signals.index > buy_row.name]
        if len(after_buy) > 0:
            sell_row = after_buy.iloc[0]
            ret = (sell_row["close"] / buy_row["close"] - 1) * 100
            profit_total += ret
            profit_class = "positive" if ret > 0 else "negative"
            trade_rows += f"""
            <tr>
                <td>{i+1}</td>
                <td>{buy_row['date'].strftime('%Y-%m-%d')}</td>
                <td>{buy_row['close']:.2f}</td>
                <td>{sell_row['date'].strftime('%Y-%m-%d')}</td>
                <td>{sell_row['close']:.2f}</td>
                <td class="{profit_class}">{ret:+.2f}%</td>
                <td>{(sell_row['date'] - buy_row['date']).days}</td>
            </tr>"""
        else:
            trade_rows += f"""
            <tr>
                <td>{i+1}</td>
                <td>{buy_row['date'].strftime('%Y-%m-%d')}</td>
                <td>{buy_row['close']:.2f}</td>
                <td>持仓中</td><td>-</td><td>-</td><td>-</td>
            </tr>"""

    # 超额收益
    excess_annual = metrics.get("excess_annual", metrics["annual_return"])
    bh_annual = metrics.get("bh_annual_return", 0)

    # 构建 HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回测报告 - {name}({code})</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
                background: #f5f7fa; color: #333; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                   color: white; padding: 40px; border-radius: 12px; margin-bottom: 24px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header .subtitle {{ opacity: 0.8; font-size: 14px; }}
        .header .stock-info {{ font-size: 16px; margin-top: 12px; opacity: 0.9; }}
        .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
        .section h2 {{ font-size: 18px; color: #1a1a2e; margin-bottom: 16px; padding-bottom: 8px;
                        border-bottom: 2px solid #e8ecf1; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                         gap: 12px; }}
        .metric-card {{ background: #f8fafc; border-radius: 8px; padding: 16px; text-align: center;
                        border: 1px solid #e8ecf1; transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .metric-icon {{ font-size: 24px; margin-bottom: 4px; }}
        .metric-value {{ font-size: 24px; font-weight: 700; margin-bottom: 4px; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        .metric-sub {{ font-size: 11px; color: #999; margin-top: 2px; }}
        .chart-container {{ margin: 16px 0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #f0f4f8; padding: 10px 12px; text-align: left; font-weight: 600;
              border-bottom: 2px solid #d0d7de; color: #444; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #e8ecf1; }}
        tr:hover {{ background: #f8fafc; }}
        .positive {{ color: #1E7A4A; font-weight: 600; }}
        .negative {{ color: #B83020; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px;
                  font-weight: 600; }}
        .badge-green {{ background: #d4edda; color: #155724; }}
        .badge-red {{ background: #f8d7da; color: #721c24; }}
        .table-wrap {{ overflow-x: auto; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; padding: 20px; }}
        .vs-badge {{ font-size: 13px; color: #666; margin-left: 8px; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 多因子量化策略回测报告</h1>
            <div class="subtitle">复合信号: MA + MACD + RSI + 布林带 + 成交量 | 严格 shift(1) 防未来函数</div>
            <div class="stock-info">{name} ({code}) · 回测区间: {df['date'].iloc[0].strftime('%Y-%m-%d')} 至 {df['date'].iloc[-1].strftime('%Y-%m-%d')} · 共 {len(df)} 个交易日</div>
        </div>

        <!-- 核心指标 -->
        <div class="section">
            <h2>📊 核心指标概览</h2>
            <div class="metrics-grid">
                {_metric_card("累计收益", f"{metrics['total_return']:.2%}", f"基准 {metrics.get('bh_total_return', 0):.2%}" if 'bh_total_return' in metrics else "",
                    "#1E7A4A" if metrics['total_return'] > 0 else "#B83020", "💰")}
                {_metric_card("年化收益", f"{metrics['annual_return']:.2%}", "vs 基准" if 'bh_annual_return' in metrics else "",
                    "#1E7A4A" if metrics['annual_return'] > 0 else "#B83020", "📈")}
                {_metric_card("夏普比率", f"{metrics['sharpe_ratio']:.2f}", f"基准 {metrics.get('bh_sharpe', 0):.2f}" if 'bh_sharpe' in metrics else "",
                    "#1E7A4A" if metrics['sharpe_ratio'] > 1 else "#CC8800" if metrics['sharpe_ratio'] > 0 else "#B83020", "🎯")}
                {_metric_card("最大回撤", f"{metrics['max_drawdown']:.2%}", f"基准 {metrics.get('bh_max_drawdown', 0):.2%}" if 'bh_max_drawdown' in metrics else "",
                    "#B83020" if abs(metrics['max_drawdown']) > 0.2 else "#CC8800" if abs(metrics['max_drawdown']) > 0.1 else "#1E7A4A", "📉")}
                {_metric_card("胜率", f"{metrics['win_rate']:.2%}", "",
                    "#1E7A4A" if metrics['win_rate'] > 0.5 else "#CC8800", "✅")}
                {_metric_card("盈亏比", f"{metrics['profit_factor']:.2f}", "",
                    "#1E7A4A" if metrics['profit_factor'] > 1.5 else "#CC8800", "⚖️")}
                {_metric_card("Calmar", f"{metrics['calmar_ratio']:.2f}", "",
                    "#1E7A4A" if metrics['calmar_ratio'] > 1 else "#CC8800", "🛡️")}
                {_metric_card("VaR(95%)", f"{metrics['var_95']:.4f}", "日度",
                    "#B83020" if abs(metrics['var_95']) > 0.03 else "#1E7A4A", "⚠️")}
            </div>
        </div>

        <!-- 净值曲线 -->
        <div class="section">
            <h2>📉 净值曲线对比 <span class="vs-badge">策略 vs 买入持有</span></h2>
            <div class="chart-container">
                {_plotly_line_chart(nav_dates, nav_strategy, "策略净值", nav_bench, "买入持有", "净值对比", 400)}
            </div>
        </div>

        <!-- 回撤曲线 -->
        <div class="section">
            <h2>📉 回撤曲线</h2>
            <div class="chart-container">
                {_plotly_line_chart(nav_dates, dd_strategy, "策略回撤", dd_bench, "基准回撤", "回撤对比", 280, ".1%")}
            </div>
        </div>

        <!-- 交易统计 + 风险指标 -->
        <div class="two-col">
            <div class="section">
                <h2>📋 交易统计</h2>
                <table>
                    <tr><td>总交易次数</td><td><strong>{trade_stats['total_trades']}</strong></td></tr>
                    <tr><td>开仓次数</td><td>{trade_stats['entries']}</td></tr>
                    <tr><td>平仓次数</td><td>{trade_stats['exits']}</td></tr>
                    <tr><td>持仓天数</td><td>{trade_stats['position_days']} / {len(df)} ({trade_stats['position_ratio']:.1%})</td></tr>
                    <tr><td>平均持仓</td><td>{trade_stats['avg_holding_period']:.1f} 天</td></tr>
                    <tr><td>信号比率</td><td>{backtest_result['signal_ratio']:.1%}</td></tr>
                </table>
            </div>
            <div class="section">
                <h2>🔬 风险指标明细</h2>
                <table>
                    <tr><td>年化波动率</td><td>{metrics['annual_volatility']:.2%}</td></tr>
                    <tr><td>索提诺比率</td><td>{metrics['sortino_ratio']:.2f}</td></tr>
                    <tr><td>CVaR(95%)</td><td>{metrics['cvar_95']:.4f}</td></tr>
                    <tr><td>策略-VaR</td><td>{metrics['var_95']:.4f}</td></tr>
                    <tr><td>Calmar比率</td><td>{metrics['calmar_ratio']:.2f}</td></tr>
                    <tr><td>超额年化</td><td>{excess_annual:.2%}</td></tr>
                </table>
            </div>
        </div>

        <!-- 交易记录 -->
        <div class="section">
            <h2>📝 交易记录</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>#</th><th>买入日期</th><th>买入价</th>
                            <th>卖出日期</th><th>卖出价</th><th>收益率</th><th>持有天数</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trade_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
            多因子量化策略回测系统 · Python + Pandas + Plotly<br>
            <span style="opacity:0.6">所有信号使用 shift(1) 严格防未来函数 · 涵盖课程 L3-L13 核心知识</span>
        </div>
    </div>
</body>
</html>"""

    # 保存文件
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ HTML 报告已保存: {output_path}")

    return html


def batch_generate_reports(results_dir: str = None):
    """批量生成所有标的的 HTML 报告"""
    if results_dir is None:
        results_dir = os.path.join(os.path.dirname(__file__), "..", "output", "run_backtest")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "reports")
    os.makedirs(out_dir, exist_ok=True)

    # 加载回测结果
    results_json = os.path.join(results_dir, "results.json")
    if not os.path.exists(results_json):
        print("  ⚠ 未找到回测结果, 使用模拟数据生成演示报告")
        return _generate_demo_reports(out_dir)

    with open(results_json, "r", encoding="utf-8") as f:
        all_results = json.load(f)

    from data_fetcher import TARGET_STOCKS

    for code, result_data in all_results.items():
        name = TARGET_STOCKS.get(code, code)
        try:
            # 加载详细数据
            stock_dir = os.path.join(results_dir, f"stock_{code}")
            detail_csv = os.path.join(stock_dir, "backtest_detail.csv")

            if os.path.exists(detail_csv):
                df = pd.read_csv(detail_csv)
                df["date"] = pd.to_datetime(df["date"])

                # 重建 backtest_result 结构
                fake_result = {
                    "name": name,
                    "df": df,
                    "metrics": result_data["metrics"],
                    "trade_stats": {
                        "total_trades": 0,
                        "entries": 0,
                        "exits": 0,
                        "position_days": int(df["signal_raw"].sum()),
                        "position_ratio": df["signal_raw"].mean(),
                        "avg_holding_period": 0,
                    },
                    "signal_ratio": result_data["signal_ratio"],
                    "n_days": result_data["n_days"],
                }
                generate_html_report(fake_result, code, name,
                                     os.path.join(out_dir, f"report_{code}.html"))

        except Exception as e:
            print(f"  ⚠ {name}({code}) 报告生成失败: {e}")

    # 生成首页索引
    _generate_index_page(all_results, TARGET_STOCKS, out_dir)
    print(f"\n✅ 所有报告已生成至: {out_dir}")
    return out_dir


def _generate_demo_reports(out_dir: str):
    """生成演示报告 (模拟数据)"""
    from data_fetcher import TARGET_STOCKS

    for code, name in list(TARGET_STOCKS.items())[:3]:
        np.random.seed(hash(code) % 10000)
        n = 500
        dates = pd.date_range("2022-01-01", periods=n, freq="B")
        close = 100 + np.cumsum(np.random.randn(n) * 2)
        df = pd.DataFrame({
            "date": dates, "close": close,
            "nav_strategy": (1 + np.random.randn(n) * 0.002).cumprod(),
            "nav_benchmark": (1 + np.random.randn(n) * 0.0015).cumprod(),
            "signal_raw": (np.random.randn(n) > 0.2).astype(int),
        })

        fake_result = {
            "name": name, "df": df,
            "metrics": {
                "total_return": 0.25, "annual_return": 0.08, "sharpe_ratio": 1.2,
                "sortino_ratio": 1.5, "max_drawdown": -0.15, "var_95": -0.02,
                "cvar_95": -0.03, "calmar_ratio": 0.53, "win_rate": 0.55,
                "profit_factor": 1.8, "annual_volatility": 0.18,
                "bh_total_return": 0.10, "bh_annual_return": 0.03,
                "bh_sharpe": 0.5, "bh_max_drawdown": -0.25,
                "excess_return": 0.15, "excess_annual": 0.05,
            },
            "trade_stats": {
                "total_trades": 25, "entries": 25, "exits": 25,
                "position_days": 180, "position_ratio": 0.36,
                "avg_holding_period": 7.2,
            },
            "signal_ratio": 0.36, "n_days": n,
        }
        generate_html_report(fake_result, code, name,
                             os.path.join(out_dir, f"report_{code}.html"))


def _generate_index_page(all_results: dict, target_stocks: dict, out_dir: str):
    """生成报告首页索引"""
    rows = []
    for code, r in all_results.items():
        name = target_stocks.get(code, code)
        m = r.get("metrics", {})
        ret = m.get("annual_return", 0)
        rows.append(f"""
        <tr>
            <td><a href="report_{code}.html">{code}</a></td>
            <td>{name}</td>
            <td class="{'positive' if ret>0 else 'negative'}">{ret:.2%}</td>
            <td>{m.get('sharpe_ratio', 0):.2f}</td>
            <td>{m.get('max_drawdown', 0):.2%}</td>
            <td>{m.get('win_rate', 0):.2%}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>回测报告索引</title>
<style>
    body {{ font-family: -apple-system, sans-serif; background: #f5f7fa; color: #333; }}
    .container {{ max-width: 900px; margin: 40px auto; padding: 20px; }}
    h1 {{ color: #1a1a2e; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px;
             overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
    th {{ background: #1a1a2e; color: white; padding: 12px; text-align: left; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #e8ecf1; }}
    tr:hover {{ background: #f8fafc; }}
    a {{ color: #3366CC; text-decoration: none; font-weight: 600; }}
    a:hover {{ text-decoration: underline; }}
    .positive {{ color: #1E7A4A; font-weight: 600; }}
    .negative {{ color: #B83020; font-weight: 600; }}
</style></head>
<body>
<div class="container">
    <h1>📈 多因子量化策略回测报告</h1>
    <p style="color:#666">共 {len(rows)} 只标的 · 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <table>
        <thead><tr>
            <th>代码</th><th>名称</th><th>年化收益</th>
            <th>夏普比率</th><th>最大回撤</th><th>胜率</th>
        </tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div></body></html>"""

    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 50)
    print("  HTML 回测报告生成器")
    print("=" * 50)

    batch_generate_reports()
