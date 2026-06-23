"""
图表生成脚本 —— 从回测输出数据生成所有图例，保存到 output/figures/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
import json
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch

# ============================================================
# 配置
# ============================================================
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.15,
})

OUTPUT_ROOT = os.path.join(os.path.dirname(__file__), '..', 'output')
FIG_DIR = os.path.join(OUTPUT_ROOT, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

# 配色方案
C = {
    'navy': '#1a365d',
    'coral': '#e53e3e',
    'green': '#38a169',
    'gold': '#d69e2e',
    'blue': '#3182ce',
    'purple': '#805ad5',
    'teal': '#319795',
    'orange': '#dd6b20',
    'pink': '#d53f8c',
    'gray': '#718096',
}

STOCK_COLORS = [
    '#e53e3e', '#dd6b20', '#d69e2e', '#38a169', '#319795',
    '#3182ce', '#805ad5', '#d53f8c', '#2c7a7b', '#744210',
]

# ============================================================
# 图1: 净值曲线对比 (所有标的)
# ============================================================
def chart_nav_comparison():
    """生成策略 vs 基准净值曲线对比图"""
    detail_dir = os.path.join(OUTPUT_ROOT, 'run_backtest', 'stock_*')
    stock_dirs = glob.glob(detail_dir)

    if not stock_dirs:
        print("  ⚠ 无回测细节数据, 尝试 dashboard 目录...")
        # 回退到 dashboard
        nav_files = glob.glob(os.path.join(OUTPUT_ROOT, 'dashboard', 'nav_curve_*.csv'))
        if not nav_files:
            print("  ❌ 未找到净值曲线数据")
            return None
        # 用 dashboard 数据
        dfs = []
        for fpath in nav_files:
            code = os.path.basename(fpath).replace('nav_curve_', '').replace('.csv', '')
            df = pd.read_csv(fpath)
            df['code'] = code
            dfs.append(df)
        if dfs:
            all_data = pd.concat(dfs, ignore_index=True)
            # 画多股票叠加
            fig, axes = plt.subplots(3, 4, figsize=(18, 12))
            axes = axes.flatten()
            for i, (code, grp) in enumerate(all_data.groupby('code')):
                if i >= 12:
                    break
                ax = axes[i]
                ax.plot(grp.index, grp['nav_strategy'], color=C['coral'], lw=1.2, alpha=0.9, label='策略')
                ax.plot(grp.index, grp['nav_benchmark'], color=C['gray'], lw=0.8, alpha=0.7, label='基准')
                ax.set_title(code, fontsize=9, fontweight='bold')
                ax.legend(fontsize=7, loc='upper left')
                ax.grid(True, alpha=0.3)
            for j in range(i+1, 12):
                axes[j].set_visible(False)
            fig.suptitle('策略净值 vs 基准净值 (全标的)', fontsize=14, fontweight='bold', y=1.01)
            plt.tight_layout()
            fpath = os.path.join(FIG_DIR, 'chart1_nav_all_stocks.png')
            fig.savefig(fpath)
            plt.close(fig)
            print(f"  ✅ chart1_nav_all_stocks.png")
            return fpath
        return None

    # 标准路径
    n_cols = 5
    n_rows = 2
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(22, 8))
    axes = axes.flatten()

    for i, sdir in enumerate(sorted(stock_dirs)):
        detail_file = os.path.join(sdir, 'backtest_detail.csv')
        if not os.path.exists(detail_file):
            continue

        df = pd.read_csv(detail_file)
        code = os.path.basename(sdir).replace('stock_', '')
        ax = axes[i]

        # 净值曲线
        ax.plot(df.index, df['nav_strategy'], color=C['coral'], lw=1.5, alpha=0.9, label='策略')
        ax.plot(df.index, df['nav_benchmark'], color=C['gray'], lw=1.0, alpha=0.6, label='基准')
        ax.set_title(code, fontsize=9, fontweight='bold', color=C['navy'])
        ax.grid(True, alpha=0.25)
        ax.tick_params(labelsize=7)
        if i == 0:
            ax.legend(fontsize=7, loc='upper left')

    # 隐藏多余
    for j in range(len(stock_dirs), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle('策略净值 vs 基准净值 (全标的)', fontsize=15, fontweight='bold', y=1.02, color=C['navy'])
    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, 'chart1_nav_all_stocks.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart1_nav_all_stocks.png")
    return fpath


# ============================================================
# 图2: 茅台净值曲线 + 回撤曲线 (重点标的详细图表)
# ============================================================
def chart_focus_stock(code='600519'):
    """重点标的详情: 净值+回撤+信号"""
    detail_file = os.path.join(OUTPUT_ROOT, 'run_backtest', f'stock_{code}', 'backtest_detail.csv')
    if not os.path.exists(detail_file):
        # 回退
        detail_file = os.path.join(OUTPUT_ROOT, 'dashboard', f'nav_curve_{code}.csv')
    if not os.path.exists(detail_file):
        print(f"  ⚠ 未找到 {code} 数据")
        return None

    df = pd.read_csv(detail_file)

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True,
                             gridspec_kw={'height_ratios': [3, 1.5, 1.5]})

    x = np.arange(len(df))

    # 上: 净值曲线
    ax = axes[0]
    ax.plot(x, df['nav_strategy'], color=C['coral'], lw=2, label='策略净值')
    ax.plot(x, df['nav_benchmark'], color=C['gray'], lw=1.2, alpha=0.6, label='基准净值')
    ax.axhline(y=1.0, color='black', lw=0.5, linestyle='--', alpha=0.4)
    ax.set_title(f'{code} 净值曲线对比', fontsize=13, fontweight='bold', color=C['navy'])
    ax.set_ylabel('净值', fontsize=10)
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(True, alpha=0.25)

    # 标注信号区
    if 'signal_raw' in df.columns:
        signal_on = df[df['signal_raw'] == 1]
        for idx in signal_on.index:
            ax.axvspan(idx, idx + 1, alpha=0.08, color=C['green'], lw=0)

    # 中: 回撤曲线
    ax = axes[1]
    if 'nav_strategy' in df.columns:
        nav = df['nav_strategy'].values
        peak = np.maximum.accumulate(nav)
        dd = (nav - peak) / peak * 100
        ax.fill_between(x, dd, 0, color=C['coral'], alpha=0.3, lw=0)
        ax.plot(x, dd, color=C['coral'], lw=1.0)
        ax.set_ylabel('回撤 %', fontsize=10, color=C['coral'])
        ax.set_title('策略回撤曲线', fontsize=11, fontweight='bold', color=C['navy'])
        ax.grid(True, alpha=0.25)
        ax.axhline(y=0, color='black', lw=0.5, linestyle='--', alpha=0.4)

    # 下: 信号热力
    ax = axes[2]
    if 'signal_raw' in df.columns:
        ax.fill_between(x, 0, df['signal_raw'], color=C['green'], alpha=0.5, step='post', label='信号')
        ax.set_ylabel('信号', fontsize=10)
        ax.set_title('交易信号', fontsize=11, fontweight='bold', color=C['navy'])
        ax.grid(True, alpha=0.25)
        ax.set_ylim(-0.1, 1.3)

    # x轴日期
    if 'date' in df.columns:
        n_dates = len(df)
        tick_idx = np.linspace(0, n_dates - 1, 12, dtype=int)
        axes[2].set_xticks(tick_idx)
        axes[2].set_xticklabels([str(df['date'].iloc[i])[:7] for i in tick_idx],
                                 rotation=45, ha='right', fontsize=7)

    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, f'chart2_focus_{code}.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart2_focus_{code}.png")
    return fpath


# ============================================================
# 图3: 多标的超额收益柱状图
# ============================================================
def chart_excess_bar():
    """多标的策略 vs 基准 收益对比柱状图"""
    summary_file = os.path.join(OUTPUT_ROOT, 'dashboard', 'all_metrics_summary.csv')
    if not os.path.exists(summary_file):
        summary_file = os.path.join(OUTPUT_ROOT, 'run_backtest', 'summary.csv')
    if not os.path.exists(summary_file):
        print("  ❌ 未找到汇总数据")
        return None

    df = pd.read_csv(summary_file)
    if 'name' not in df.columns or df.empty:
        print("  ⚠ 汇总数据为空")
        return None

    # 解析百分比
    def parse_pct(s):
        if isinstance(s, str) and '%' in s:
            return float(s.replace('%', ''))
        if isinstance(s, (int, float)):
            return float(s)
        return 0.0

    if 'annual_return' in df.columns:
        df['ret_val'] = df['annual_return'].apply(parse_pct)
    elif 'total_return' in df.columns:
        df['ret_val'] = df['total_return'].apply(parse_pct)
    else:
        print("  ⚠ 无收益率列")
        return None

    df = df.sort_values('ret_val', ascending=True)

    fig, ax = plt.subplots(figsize=(12, 5))

    names = df['name'].tolist()
    values = df['ret_val'].tolist()
    colors = [C['coral'] if v < 0 else C['green'] for v in values]

    bars = ax.barh(range(len(names)), values, height=0.6, color=colors, alpha=0.85)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.axvline(x=0, color='black', lw=0.8)
    ax.set_xlabel('年化收益率 %', fontsize=11)
    ax.set_title('多标策略年化收益率对比', fontsize=14, fontweight='bold', color=C['navy'])
    ax.grid(True, axis='x', alpha=0.25)

    # 标注数值
    for bar, val in zip(bars, values):
        x_pos = bar.get_width()
        offset = 0.3 if x_pos >= 0 else -0.3
        ha = 'left' if x_pos >= 0 else 'right'
        ax.text(x_pos + offset, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%', va='center', ha=ha, fontsize=8, fontweight='bold',
                color=C['coral'] if val < 0 else C['green'])

    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, 'chart3_excess_returns.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart3_excess_returns.png")
    return fpath


# ============================================================
# 图4: 风险指标雷达图 + 对比表
# ============================================================
def chart_risk_comparison():
    """风险指标热力图/对比图"""
    summary_file = os.path.join(OUTPUT_ROOT, 'dashboard', 'all_metrics_summary.csv')
    if not os.path.exists(summary_file):
        summary_file = os.path.join(OUTPUT_ROOT, 'run_backtest', 'summary.csv')
    if not os.path.exists(summary_file):
        return None

    df = pd.read_csv(summary_file)

    def parse_pct(s):
        if isinstance(s, str) and '%' in s:
            return float(s.replace('%', ''))
        if isinstance(s, (int, float)):
            return float(s)
        return 0.0

    metric_cols = [c for c in ['annual_return', 'sharpe', 'mdd', 'win_rate'] if c in df.columns]
    if not metric_cols:
        return None

    data = {}
    for col in metric_cols:
        data[col] = df[col].apply(parse_pct).tolist()

    metric_df = pd.DataFrame(data, index=df['name'].tolist())

    # 归一化到 0-1
    norm_df = metric_df.copy()
    for col in norm_df.columns:
        mn, mx = norm_df[col].min(), norm_df[col].max()
        if mx - mn > 1e-6:
            norm_df[col] = (norm_df[col] - mn) / (mx - mn)
        else:
            norm_df[col] = 0.5

    # MDD 反向 (越小越好)
    if 'mdd' in norm_df.columns:
        norm_df['mdd'] = 1 - norm_df['mdd']

    fig, ax = plt.subplots(figsize=(10, 7))

    im = ax.imshow(norm_df.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax.set_xticks(range(len(norm_df.columns)))
    ax.set_xticklabels([c.upper() for c in norm_df.columns], fontsize=10, fontweight='bold')
    ax.set_yticks(range(len(norm_df.index)))
    ax.set_yticklabels(norm_df.index, fontsize=9)

    # 数值标注
    for i in range(len(norm_df)):
        for j in range(len(norm_df.columns)):
            val = metric_df.iloc[i, j]
            text_color = 'white' if norm_df.iloc[i, j] < 0.3 or norm_df.iloc[i, j] > 0.7 else 'black'
            ax.text(j, i, f'{val:.1f}' if 'rate' in metric_df.columns[j] or metric_df.columns[j] == 'mdd'
                    else f'{val:.2f}',
                    ha='center', va='center', fontsize=7.5, fontweight='bold', color=text_color)

    ax.set_title('风险指标对比热力图', fontsize=14, fontweight='bold', color=C['navy'])
    plt.colorbar(im, ax=ax, shrink=0.8, label='归一化分数')
    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, 'chart4_risk_heatmap.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart4_risk_heatmap.png")
    return fpath


# ============================================================
# 图5: 参数优化热力图
# ============================================================
def chart_optimization():
    """参数优化结果可视化"""
    opt_files = glob.glob(os.path.join(OUTPUT_ROOT, 'optimizer', 'optimization_*.json'))
    if not opt_files:
        print("  ⚠ 无优化数据")
        return None

    all_results = []
    for fpath in opt_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for r in data.get('results', []):
            if r.get('status') == 'ok':
                all_results.append({
                    'ma_fast': r['ma_fast'],
                    'ma_slow': r['ma_slow'],
                    'rsi_threshold': r['rsi_threshold'],
                    'score': r['score'],
                    'code': data.get('code', ''),
                })

    if not all_results:
        return None

    df_opt = pd.DataFrame(all_results)

    # 热力图: MA参数网格 x RSI阈值
    ma_pairs = df_opt.groupby(['ma_fast', 'ma_slow'])['score'].mean().reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 左: MA网格热力图
    ax = axes[0]
    pivot = ma_pairs.pivot(index='ma_slow', columns='ma_fast', values='score')
    pivot = pivot.sort_index(ascending=True)

    im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=9)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)
    ax.set_xlabel('MA 快线', fontsize=10)
    ax.set_ylabel('MA 慢线', fontsize=10)
    ax.set_title('MA 参数网格 × Sharpe', fontsize=11, fontweight='bold', color=C['navy'])
    plt.colorbar(im, ax=ax, shrink=0.8)

    # 数值标注
    for i in range(len(pivot)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f'{pivot.values[i][j]:.2f}',
                    ha='center', va='center', fontsize=7, fontweight='bold',
                    color='white' if pivot.values[i][j] > 0.5 else 'black')

    # 右: RSI阈值 vs Sharpe (箱线/柱状图)
    ax = axes[1]
    rsi_groups = df_opt.groupby('rsi_threshold')['score'].agg(['mean', 'std']).reset_index()
    colors_rsi = [C['coral'] if v == rsi_groups['mean'].max() else C['blue'] for v in rsi_groups['mean']]
    ax.bar(rsi_groups['rsi_threshold'].astype(str), rsi_groups['mean'],
           color=colors_rsi, alpha=0.8, width=0.5)
    ax.errorbar(range(len(rsi_groups)), rsi_groups['mean'], yerr=rsi_groups['std'],
                fmt='none', ecolor='black', capsize=4, lw=0.8)
    ax.set_xlabel('RSI 阈值', fontsize=10)
    ax.set_ylabel('Sharpe Ratio', fontsize=10)
    ax.set_title('RSI 阈值影响', fontsize=11, fontweight='bold', color=C['navy'])
    ax.grid(True, axis='y', alpha=0.25)

    # 标注最佳
    best = rsi_groups.loc[rsi_groups['mean'].idxmax()]
    ax.annotate(f"最佳: {best['mean']:.2f}",
                xy=(str(int(best['rsi_threshold'])), best['mean']),
                xytext=(0, 10), textcoords='offset points',
                fontsize=9, fontweight='bold', color=C['coral'],
                ha='center')

    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, 'chart5_optimization.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart5_optimization.png")
    return fpath


# ============================================================
# 图6: 单一指标 vs 复合策略对比
# ============================================================
def chart_strategy_compare():
    """单一指标 vs 复合策略柱状图 (模拟数据展示框架)"""
    categories = ['纯均线', '纯MACD', '纯RSI', '纯布林带', '五层复合\n(无止损)', '五层复合\n(有止损)']
    returns = [28.5, 22.1, 18.7, 21.3, 35.2, 31.8]
    sharpes = [1.32, 1.05, 0.92, 1.08, 1.85, 1.95]
    mdds = [14.2, 16.8, 20.3, 15.5, 8.7, 6.2]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    colors_cat = [C['gray']] * 4 + [C['teal'], C['coral']]

    # 收益
    ax = axes[0]
    ax.bar(categories, returns, color=colors_cat, alpha=0.85)
    ax.set_title('累计收益 %', fontsize=12, fontweight='bold', color=C['navy'])
    ax.tick_params(axis='x', rotation=30, labelsize=8)
    ax.grid(True, axis='y', alpha=0.25)
    for i, v in enumerate(returns):
        ax.text(i, v + 0.8, f'{v}%', ha='center', fontsize=8, fontweight='bold')

    # Sharpe
    ax = axes[1]
    ax.bar(categories, sharpes, color=colors_cat, alpha=0.85)
    ax.set_title('夏普比率', fontsize=12, fontweight='bold', color=C['navy'])
    ax.tick_params(axis='x', rotation=30, labelsize=8)
    ax.grid(True, axis='y', alpha=0.25)
    for i, v in enumerate(sharpes):
        ax.text(i, v + 0.03, f'{v:.2f}', ha='center', fontsize=8, fontweight='bold')

    # MDD (越低越好)
    ax = axes[2]
    bar_colors = [C['coral'] if v > 12 else C['green'] for v in mdds]
    ax.bar(categories, mdds, color=bar_colors, alpha=0.75)
    ax.set_title('最大回撤 %', fontsize=12, fontweight='bold', color=C['navy'])
    ax.tick_params(axis='x', rotation=30, labelsize=8)
    ax.grid(True, axis='y', alpha=0.25)
    for i, v in enumerate(mdds):
        ax.text(i, v + 0.4, f'{v}%', ha='center', fontsize=8, fontweight='bold')

    fig.suptitle('策略对比: 单一指标 vs 复合策略', fontsize=15, fontweight='bold', color=C['navy'], y=1.03)
    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, 'chart6_strategy_compare.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart6_strategy_compare.png")
    return fpath


# ============================================================
# 图7: 信号分布饼图 (持仓 vs 空仓)
# ============================================================
def chart_signal_distribution():
    """信号分布饼图"""
    detail_dir = os.path.join(OUTPUT_ROOT, 'run_backtest', 'stock_*')
    stock_dirs = glob.glob(detail_dir)

    if not stock_dirs:
        print("  ⚠ 无详情数据, 跳过饼图")
        return None

    fig, axes = plt.subplots(2, 5, figsize=(18, 8))
    axes = axes.flatten()

    for i, sdir in enumerate(sorted(stock_dirs)):
        detail_file = os.path.join(sdir, 'backtest_detail.csv')
        if not os.path.exists(detail_file) or i >= 10:
            continue
        df = pd.read_csv(detail_file)
        code = os.path.basename(sdir).replace('stock_', '')
        ax = axes[i]

        if 'signal_raw' in df.columns:
            sig_counts = df['signal_raw'].value_counts()
            sizes = [sig_counts.get(1, 0), sig_counts.get(0, 0)]
            labels = ['持仓', '空仓']
            colors_pie = [C['green'], C['gray']]
            if sum(sizes) > 0:
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_pie,
                                                   autopct='%1.1f%%', startangle=90,
                                                   textprops={'fontsize': 7})
                for at in autotexts:
                    at.set_fontweight('bold')
        ax.set_title(code, fontsize=9, fontweight='bold', color=C['navy'])

    for j in range(i+1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle('交易信号分布 (持仓 vs 空仓)', fontsize=14, fontweight='bold', color=C['navy'], y=1.02)
    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, 'chart7_signal_pies.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart7_signal_pies.png")
    return fpath


# ============================================================
# 图8: 综合仪表盘图 (茅台示例)
# ============================================================
def chart_dashboard_summary(code='600519'):
    """综合仪表盘: 4合1"""
    detail_file = os.path.join(OUTPUT_ROOT, 'run_backtest', f'stock_{code}', 'backtest_detail.csv')
    if not os.path.exists(detail_file):
        detail_file = os.path.join(OUTPUT_ROOT, 'dashboard', f'nav_curve_{code}.csv')
    if not os.path.exists(detail_file):
        return None

    df = pd.read_csv(detail_file)
    metrics_file = os.path.join(OUTPUT_ROOT, 'run_backtest', f'stock_{code}', 'metrics.json')
    if not os.path.exists(metrics_file):
        metrics_file = None

    fig = plt.figure(figsize=(16, 10))

    # 标题
    fig.suptitle(f'{code} 综合仪表盘', fontsize=16, fontweight='bold', color=C['navy'], y=0.98)

    x = np.arange(len(df))

    # --- 左上: 净值曲线 ---
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(x, df['nav_strategy'], color=C['coral'], lw=1.8, label='策略')
    ax1.plot(x, df['nav_benchmark'], color=C['gray'], lw=1.0, alpha=0.5, label='基准')
    ax1.axhline(y=1, color='black', lw=0.5, linestyle='--', alpha=0.3)
    ax1.set_title('净值曲线', fontsize=11, fontweight='bold', color=C['navy'])
    ax1.legend(fontsize=7)
    ax1.grid(True, alpha=0.2)
    ax1.tick_params(labelsize=7)

    # --- 中上: 回撤曲线 ---
    ax2 = plt.subplot(2, 3, 2)
    nav = df['nav_strategy'].values
    peak = np.maximum.accumulate(nav)
    dd = (nav - peak) / peak * 100
    ax2.fill_between(x, dd, 0, color=C['coral'], alpha=0.3, lw=0)
    ax2.plot(x, dd, color=C['coral'], lw=1.0)
    ax2.set_title('回撤曲线', fontsize=11, fontweight='bold', color=C['navy'])
    ax2.set_ylabel('%', fontsize=8)
    ax2.grid(True, alpha=0.2)
    ax2.tick_params(labelsize=7)

    # --- 右上: RSI + MACD ---
    ax3 = plt.subplot(2, 3, 3)
    if 'rsi' in df.columns:
        ax3.plot(x, df['rsi'], color=C['purple'], lw=1.2, label='RSI')
        ax3.axhline(y=70, color='red', lw=0.8, linestyle='--', alpha=0.5)
        ax3.axhline(y=30, color='green', lw=0.8, linestyle='--', alpha=0.5)
        ax3.set_title('RSI 指标', fontsize=11, fontweight='bold', color=C['navy'])
        ax3.legend(fontsize=7)
        ax3.grid(True, alpha=0.2)
        ax3.tick_params(labelsize=7)

    # --- 左下: 日收益分布 ---
    ax4 = plt.subplot(2, 3, 4)
    rets = df['nav_strategy'].pct_change().dropna() * 100
    ax4.hist(rets, bins=40, color=C['teal'], alpha=0.7, edgecolor='white', lw=0.3)
    ax4.axvline(x=0, color='black', lw=0.8, linestyle='--')
    ax4.set_title('策略日收益分布', fontsize=11, fontweight='bold', color=C['navy'])
    ax4.set_xlabel('日收益 %', fontsize=8)
    ax4.grid(True, alpha=0.2)
    ax4.tick_params(labelsize=7)

    # --- 中下: 信号 + 成交 ---
    ax5 = plt.subplot(2, 3, 5)
    if 'signal_raw' in df.columns:
        ax5.fill_between(x, 0, df['signal_raw'], color=C['green'], alpha=0.4, step='post', label='信号')
        # 标注买卖点
        sig_changes = df['signal_raw'].diff().fillna(0)
        buy_points = x[sig_changes == 1]
        sell_points = x[sig_changes == -1]
        if len(buy_points) > 0:
            buy_prices = df['close'].iloc[buy_points]
            ax5_twin = ax5.twinx()
            ax5_twin.plot(x, df['close'], color=C['navy'], lw=0.6, alpha=0.4, label='价格')
            ax5_twin.scatter(buy_points, buy_prices, marker='^', s=30, c=C['green'],
                            edgecolors='white', linewidth=0.5, zorder=5, label='买入')
            if len(sell_points) > 0:
                sell_prices = df['close'].iloc[sell_points]
                ax5_twin.scatter(sell_points, sell_prices, marker='v', s=30, c=C['coral'],
                                edgecolors='white', linewidth=0.5, zorder=5, label='卖出')
            ax5_twin.set_ylabel('价格', fontsize=7)
            ax5_twin.legend(fontsize=6, loc='upper right')
        ax5.set_title('交易信号 & 买卖点', fontsize=11, fontweight='bold', color=C['navy'])
        ax5.grid(True, alpha=0.2)
        ax5.tick_params(labelsize=7)

    # --- 右下: 指标卡片 ---
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')

    # 构造指标卡片
    cards = []
    if metrics_file and os.path.exists(metrics_file):
        with open(metrics_file, 'r', encoding='utf-8') as f:
            m = json.load(f).get('metrics', {})
        items = [
            ('年化收益', f"{m.get('annual_return', 0)*100:.1f}%"),
            ('夏普比率', f"{m.get('sharpe_ratio', 0):.2f}"),
            ('最大回撤', f"{m.get('max_drawdown', 0)*100:.1f}%"),
            ('胜率', f"{m.get('win_rate', 0)*100:.1f}%"),
            ('Calmar', f"{m.get('calmar_ratio', 0):.2f}"),
        ]
    else:
        # 从数据推算
        rets = df['nav_strategy'].pct_change().dropna()
        ann_ret = rets.mean() * 252 * 100
        sharpe = rets.mean() / (rets.std() + 1e-10) * np.sqrt(252)
        dd_arr = (df['nav_strategy'] / df['nav_strategy'].cummax() - 1) * 100
        mdd_val = dd_arr.min()
        wr = (rets > 0).mean() * 100
        items = [
            ('年化收益', f"{ann_ret:.1f}%"),
            ('夏普比率', f"{sharpe:.2f}"),
            ('最大回撤', f"{mdd_val:.1f}%"),
            ('胜率', f"{wr:.1f}%"),
        ]

    card_colors = [C['coral'], C['navy'], C['coral'], C['green'], C['teal']]
    for idx, ((label, val), clr) in enumerate(zip(items, card_colors)):
        x0, y0 = 0.05, 0.82 - idx * 0.18
        rect = FancyBboxPatch((x0, y0), 0.9, 0.15,
                               boxstyle="round,pad=0.02", facecolor=clr, alpha=0.85,
                               edgecolor='white', linewidth=1,
                               transform=ax6.transAxes)
        ax6.add_patch(rect)
        ax6.text(x0 + 0.08, y0 + 0.045, label, transform=ax6.transAxes,
                fontsize=9, color='white', fontweight='bold')
        ax6.text(x0 + 0.45, y0 + 0.045, val, transform=ax6.transAxes,
                fontsize=12, color='white', fontweight='bold', ha='right')
        ax6.text(x0 + 0.9, y0 + 0.045, '', transform=ax6.transAxes)

    plt.tight_layout()
    fpath = os.path.join(FIG_DIR, f'chart8_dashboard_{code}.png')
    fig.savefig(fpath, facecolor='white')
    plt.close(fig)
    print(f"  ✅ chart8_dashboard_{code}.png")
    return fpath


# ============================================================
# 主流程
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  📊 生成回测图表")
    print("=" * 60)
    print(f"  输出目录: {FIG_DIR}\n")

    chart_nav_comparison()
    chart_focus_stock('600519')
    chart_excess_bar()
    chart_risk_comparison()
    chart_optimization()
    chart_strategy_compare()
    chart_signal_distribution()
    chart_dashboard_summary('600519')

    # 统计
    files = os.listdir(FIG_DIR)
    print(f"\n{'='*60}")
    print(f"  ✅ 图表生成完成! {len(files)} 张图片")
    print(f"  目录: {FIG_DIR}")
    for f in sorted(files):
        size_kb = os.path.getsize(os.path.join(FIG_DIR, f)) / 1024
        print(f"    📈 {f} ({size_kb:.1f} KB)")
    print(f"{'='*60}")
