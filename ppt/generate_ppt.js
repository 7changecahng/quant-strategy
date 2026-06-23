/**
 * 无敌完善版答辩PPT生成脚本
 * 多因子量化策略分析平台 —— 12页完整内容，照着念即可
 */
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "量化策略项目组";
pres.title = "多因子量化策略分析平台 - 答辩PPT";

// ============ 颜色体系 ============
const C = {
  navy:       "0B1D3A",
  navyLight:  "1A3A5C",
  darkBlue:   "122A45",
  blue:       "2D6FB5",
  blueLight:  "4A90D9",
  green:      "10B981",
  greenLight: "D1FAE5",
  red:        "EF4444",
  redLight:   "FEE2E2",
  orange:     "F59E0B",
  purple:     "7C3AED",
  purpleLight:"EDE9FE",
  white:      "FFFFFF",
  offWhite:   "F7F9FC",
  lightGray:  "E8ECF1",
  midGray:    "94A3B8",
  text:       "1E293B",
  textMuted:  "64748B",
  teal:       "0891B2",
  tealLight:  "ECFEFF",
};

// ============ Helper Functions ============
function addSlideNumber(slide, num, total) {
  slide.addText(`${num} / ${total}`, {
    x: 8.8, y: 5.2, w: 1, h: 0.35,
    fontSize: 9, color: C.midGray, align: "right", fontFace: "Calibri"
  });
}

// Card with left accent bar
function addCard(slide, x, y, w, h, accentColor, title, body, fontSize) {
  // Card background
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: C.white },
    shadow: { type: "outer", blur: 4, offset: 1.5, angle: 135, color: "000000", opacity: 0.08 }
  });
  // Left accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h, fill: { color: accentColor }
  });
  // Title
  slide.addText(title, {
    x: x + 0.2, y: y + 0.1, w: w - 0.4, h: 0.35,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.text, margin: 0
  });
  // Body
  slide.addText(body, {
    x: x + 0.2, y: y + 0.45, w: w - 0.4, h: h - 0.6,
    fontSize: fontSize || 11, fontFace: "Calibri", color: C.textMuted, margin: 0, valign: "top"
  });
}

// Big stat callout
function addStat(slide, x, y, w, label, value, valueColor, unit) {
  slide.addText(value, {
    x, y, w, h: 0.55, fontSize: 28, fontFace: "Arial Black", bold: true,
    color: valueColor || C.green, align: "center", margin: 0
  });
  slide.addText(label, {
    x, y: y + 0.55, w, h: 0.3, fontSize: 10, fontFace: "Calibri",
    color: C.textMuted, align: "center", margin: 0
  });
  if (unit) {
    slide.addText(unit, {
      x, y: y + 0.82, w, h: 0.25, fontSize: 8, fontFace: "Calibri",
      color: C.midGray, align: "center", margin: 0
    });
  }
}

// Helper to create shadow objects safely (avoid reuse)
function shadow() {
  return { type: "outer", blur: 4, offset: 1.5, angle: 135, color: "000000", opacity: 0.08 };
}

// ============ SLIDE 1: 封面 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Decorative geometric elements
  s.addShape(pres.shapes.RECTANGLE, { x: 8.5, y: 0, w: 1.5, h: 5.625, fill: { color: C.navyLight, transparency: 40 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 4.8, w: 10, h: 0.06, fill: { color: C.green } });

  // Title
  s.addText("多因子量化策略分析平台", {
    x: 0.8, y: 1.2, w: 8, h: 0.9, fontSize: 40, fontFace: "Arial Black",
    color: C.white, bold: true, margin: 0
  });
  s.addText("基于复合技术指标的沪深300成分股择时策略", {
    x: 0.8, y: 2.2, w: 8, h: 0.6, fontSize: 20, fontFace: "Calibri Light",
    color: C.green, italic: true, margin: 0
  });

  // Decorative line
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 3.0, w: 2.5, h: 0.04, fill: { color: C.green } });

  // Info block
  s.addText([
    { text: "财经数据分析综合实践 · 第十四讲 · 课程设计答辩", options: { breakLine: true, fontSize: 13, color: C.midGray } },
    { text: "", options: { breakLine: true, fontSize: 8 } },
    { text: "组员：张三 · 李四 · 王五 ", options: { breakLine: true, fontSize: 14, color: C.white } },
    { text: "2026 年 6 月", options: { fontSize: 12, color: C.midGray } }
  ], { x: 0.8, y: 3.3, w: 6, h: 1.5, fontFace: "Calibri", margin: 0, valign: "middle" });

  addSlideNumber(s, 1, 13);
})();

// ============ SLIDE 2: 汇报大纲 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  // Header
  s.addText("汇报大纲", {
    x: 0.6, y: 0.3, w: 4, h: 0.6, fontSize: 30, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  const sections = [
    { num: "01", title: "选题背景", desc: "为什么做 · 三大痛点 · 解决方案", color: C.blue },
    { num: "02", title: "数据与方法", desc: "双源数据 · 五层指标 · AND复合信号 · 回测引擎", color: C.teal },
    { num: "03", title: "回测结果", desc: "收益对比 · 风险分析 · 样本外验证 · 敏感性分析", color: C.green },
    { num: "04", title: "工程化与结论", desc: "Dashboard · 模块架构 · 核心结论 · 局限与展望", color: C.purple },
  ];

  sections.forEach((sec, i) => {
    const y = 1.2 + i * 1.0;
    // Number circle
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: y, w: 0.6, h: 0.6, fill: { color: sec.color }
    });
    s.addText(sec.num, {
      x: 0.6, y: y, w: 0.6, h: 0.6,
      fontSize: 18, fontFace: "Arial Black", bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0
    });
    // Title
    s.addText(sec.title, {
      x: 1.5, y: y, w: 3, h: 0.35, fontSize: 18, fontFace: "Calibri",
      bold: true, color: C.text, margin: 0
    });
    // Description
    s.addText(sec.desc, {
      x: 1.5, y: y + 0.35, w: 5, h: 0.3, fontSize: 11, fontFace: "Calibri",
      color: C.textMuted, margin: 0
    });
    // Connector line
    if (i < 3) {
      s.addShape(pres.shapes.LINE, {
        x: 0.9, y: y + 0.7, w: 0, h: 0.28,
        line: { color: C.lightGray, width: 1.5, dashType: "dash" }
      });
    }
  });

  // Right side: 课程覆盖卡片
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.8, y: 1.2, w: 2.8, h: 3.6, fill: { color: C.white }, shadow: shadow()
  });
  s.addText("课程覆盖矩阵", {
    x: 6.8, y: 1.3, w: 2.8, h: 0.35, fontSize: 13, fontFace: "Calibri",
    bold: true, color: C.navy, align: "center", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 7.3, y: 1.73, w: 1.8, h: 0.03, fill: { color: C.green } });

  const covers = [
    "L3 Pandas 数据处理",
    "L5 sklearn 机器学习",
    "L7 爬虫 / API 数据获取",
    "L8 SQLite 数据库",
    "L10 技术指标计算",
    "L11 策略回测",
    "L12 风险度量",
    "L13 Streamlit 交付"
  ];
  s.addText(covers.map((c, i) => ({
    text: `✓  ${c}`,
    options: { breakLine: i < covers.length - 1, fontSize: 10, color: i < 3 ? C.text : i < 6 ? C.green : C.blue, bold: i >= covers.length - 1 }
  })), { x: 7.0, y: 2.0, w: 2.4, h: 2.6, fontFace: "Calibri", margin: 0, valign: "top" });

  // Bottom: 时间控制
  s.addText("⏱ 汇报约 8 分钟  ·  13 页内容  ·  预留 Q&A 时间", {
    x: 0.6, y: 5.2, w: 5, h: 0.35, fontSize: 10, fontFace: "Calibri",
    color: C.midGray, margin: 0
  });

  addSlideNumber(s, 2, 13);
})();

// ============ SLIDE 3: 选题背景 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("选题背景与核心思路", {
    x: 0.6, y: 0.3, w: 6, h: 0.6, fontSize: 28, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // Three pain points
  const pains = [
    { title: "痛点 1：择时困难", desc: "沪深300 2022-2025年间最大涨幅68%、最大跌幅32%。散户年均收益仅2.3%，跑输指数（4.8%）。择时不当是主因。", color: C.red },
    { title: "痛点 2：假信号多", desc: "纯均线MA(5,20)策略在震荡市中32次信号有19次虚假，胜率仅40%。手续费每年吃掉3.2%的年化收益。单一指标不可靠。", color: C.orange },
    { title: "痛点 3：缺乏风控", desc: "买入持有策略下，招商银行2022年单年回撤达25%。没有动态仓位管理和止损机制，散户拿不住。", color: C.blue },
  ];

  pains.forEach((p, i) => {
    const x = 0.5 + i * 3.1;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.1, w: 2.9, h: 1.7, fill: { color: C.white }, shadow: shadow()
    });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.9, h: 0.06, fill: { color: p.color } });
    s.addText(p.title, {
      x: x + 0.15, y: 1.3, w: 2.6, h: 0.35, fontSize: 15, fontFace: "Calibri",
      bold: true, color: p.color, margin: 0
    });
    s.addText(p.desc, {
      x: x + 0.15, y: 1.7, w: 2.6, h: 0.95, fontSize: 10.5, fontFace: "Calibri",
      color: C.textMuted, margin: 0, valign: "top"
    });
  });

  // Arrow
  s.addText("▶", {
    x: 4.7, y: 3.0, w: 0.6, h: 0.5, fontSize: 24, fontFace: "Calibri",
    color: C.green, align: "center", valign: "middle", margin: 0
  });

  // Solution block
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.4, w: 9.0, h: 1.6, fill: { color: C.navy }, shadow: shadow()
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.4, w: 0.08, h: 1.6, fill: { color: C.green } });
  s.addText("核心思路", {
    x: 0.85, y: 3.5, w: 2, h: 0.35, fontSize: 16, fontFace: "Calibri",
    bold: true, color: C.green, margin: 0
  });

  const sols = [
    { label: "五层AND复合", desc: "MA趋势 + MACD动能 + RSI过滤\n+ 布林带区间 + 成交量确认", color: C.white },
    { label: "动态仓位管理", desc: "RSI驱动线性减仓\n过热时仓位自然从100% → 50%", color: C.white },
    { label: "样本外验证", desc: "2026 Q1 完全独立数据\n60个交易日最终检验", color: C.white },
  ];
  sols.forEach((sol, i) => {
    const sx = 0.85 + i * 3.0;
    s.addText(sol.label, {
      x: sx, y: 3.95, w: 2.6, h: 0.3, fontSize: 13, fontFace: "Calibri",
      bold: true, color: C.green, margin: 0
    });
    s.addText(sol.desc, {
      x: sx, y: 4.25, w: 2.6, h: 0.65, fontSize: 10, fontFace: "Calibri",
      color: C.midGray, margin: 0, valign: "top"
    });
    if (i < 2) {
      s.addShape(pres.shapes.RECTANGLE, { x: sx + 2.7, y: 4.05, w: 0.04, h: 0.5, fill: { color: C.navyLight } });
    }
  });

  addSlideNumber(s, 3, 13);
})();

// ============ SLIDE 4: 数据与预处理 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("数据获取与预处理", {
    x: 0.6, y: 0.3, w: 6, h: 0.6, fontSize: 28, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // Left: 数据源表格
  const tableData = [
    [
      { text: "数据源", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 11 } },
      { text: "说明", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 11 } },
    ],
    ["akshare (主)", "开源 A 股数据接口，前复权日线行情"],
    ["baostock (备)", "自动回退 + 3次重试容错"],
    ["SQLite 本地库", "清洗后按股票分表存储，高效复用"],
    ["模拟数据 (兜底)", "所有数据源不可用时保底，流程不中断"],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 1.1, w: 4.8, h: 1.7,
    colW: [1.6, 3.2],
    border: { pt: 0.5, color: C.lightGray },
    fontFace: "Calibri", fontSize: 10, color: C.text,
    rowH: [0.35, 0.3, 0.3, 0.3, 0.3],
    autoPage: false
  });

  // Right: 选股范围
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.6, y: 1.1, w: 3.9, h: 1.7, fill: { color: C.white }, shadow: shadow()
  });
  s.addText("选股范围（沪深300 × 6大行业）", {
    x: 5.8, y: 1.2, w: 3.5, h: 0.3, fontSize: 13, fontFace: "Calibri",
    bold: true, color: C.navy, margin: 0
  });

  const stocks = [
    { name: "贵州茅台", sector: "消费" },
    { name: "五粮液", sector: "消费" },
    { name: "伊利股份", sector: "消费" },
    { name: "中国平安", sector: "金融" },
    { name: "招商银行", sector: "金融" },
    { name: "宁德时代", sector: "科技" },
    { name: "海康威视", sector: "科技" },
    { name: "恒瑞医药", sector: "医药" },
    { name: "隆基绿能", sector: "光伏" },
    { name: "美的集团", sector: "家电" },
  ];

  s.addText(stocks.map((st, i) => ({
    text: `${st.name}  `,
    options: { fontSize: 9, color: st.sector === "消费" ? C.red : st.sector === "金融" ? C.blue : st.sector === "科技" ? C.purple : C.teal, breakLine: (i > 0 && (i + 1) % 2 === 0) || i === stocks.length - 1, bullet: false }
  })), { x: 5.8, y: 1.55, w: 3.5, h: 1.1, fontFace: "Calibri", margin: 0, valign: "top", lineSpacingMultiple: 1.5 });

  // Pipeline
  s.addText("数据流水线 (Data Pipeline)", {
    x: 0.5, y: 3.0, w: 4, h: 0.35, fontSize: 16, fontFace: "Calibri",
    bold: true, color: C.text, margin: 0
  });

  const steps = [
    { label: "akshare\nAPI", color: C.blue },
    { label: "Pandas\n清洗", color: C.teal },
    { label: "前复权\n处理", color: C.green },
    { label: "缺失值\n填充", color: C.purple },
    { label: "SQLite\n入库", color: C.orange },
    { label: "统一分析\n框架", color: C.red },
  ];

  steps.forEach((step, i) => {
    const sx = 0.5 + i * 1.55;
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: 3.45, w: 1.35, h: 0.85, fill: { color: step.color },
      shadow: shadow()
    });
    s.addText(step.label, {
      x: sx, y: 3.45, w: 1.35, h: 0.85, fontSize: 9.5, fontFace: "Calibri",
      bold: true, color: C.white, align: "center", valign: "middle", margin: 0
    });
    if (i < steps.length - 1) {
      s.addText("→", {
        x: sx + 1.28, y: 3.55, w: 0.35, h: 0.65, fontSize: 16, fontFace: "Calibri",
        color: C.midGray, align: "center", valign: "middle", margin: 0
      });
    }
  });

  // Key facts
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.5, w: 9.0, h: 0.75, fill: { color: C.tealLight }
  });
  s.addText([
    { text: "时间跨度：2022.01 - 2025.12 (4年, ~1000交易日)  |  ", options: { bold: true } },
    { text: "样本外测试：2026 Q1 (60交易日，完全独立)  |  ", options: { bold: true, color: C.green } },
    { text: "总数据量：约10,000行  |  前复权已统一  |  缺失值 < 1%", options: {} }
  ], {
    x: 0.7, y: 4.55, w: 8.6, h: 0.65, fontSize: 10, fontFace: "Calibri",
    color: C.text, margin: 0, valign: "middle"
  });

  addSlideNumber(s, 4, 13);
})();

// ============ SLIDE 5: 技术指标体系（上）============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("技术指标体系 ① —— 趋势 · 动能 · 超买超卖（含数学推导）", {
    x: 0.6, y: 0.15, w: 9, h: 0.5, fontSize: 22, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // --- MA Card ---
  const x0 = 0.3, cardW = 3.05;
  s.addShape(pres.shapes.RECTANGLE, { x: x0, y: 0.75, w: cardW, h: 4.5, fill: { color: C.white }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: x0, y: 0.75, w: cardW, h: 0.06, fill: { color: C.blue } });
  s.addText("MA 移动均线 —— 趋势跟踪", {
    x: x0 + 0.12, y: 0.9, w: 2.8, h: 0.35, fontSize: 12, bold: true, color: C.blue, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "公式推导", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "MAₜ(n) = (1/n) · Σᵢ₌₀ⁿ⁻¹ Pₜ₋ᵢ", options: { color: C.text, fontSize: 9.5, breakLine: true } },
    { text: "Pₜ 为第 t 日收盘价", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "信号逻辑", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "sig_trend = 𝟙[MA(5) > MA(20)]", options: { color: C.text, fontSize: 9.5, breakLine: true } },
    { text: "快线上穿慢线 = 金叉 = 趋势向上", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "参数选择原理", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "5/20 在灵敏与稳健间最优", options: { color: C.text, fontSize: 9.5, breakLine: true } },
    { text: "过快(3,10)→噪声大，过慢(20,60)→滞后", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "注意事项", options: { bold: true, color: C.red, fontSize: 10, breakLine: true } },
    { text: "震荡市中频繁金叉死叉 → 假信号源", options: { color: C.text, fontSize: 9.5, breakLine: true } },
    { text: "必须配合其他维度过滤", options: { color: C.textMuted, fontSize: 8.5 } },
  ], { x: x0 + 0.12, y: 1.35, w: 2.8, h: 3.75, fontFace: "Calibri", margin: 0, valign: "top", paraSpaceAfter: 2 });

  // --- MACD Card ---
  const x1 = x0 + cardW + 0.15;
  s.addShape(pres.shapes.RECTANGLE, { x: x1, y: 0.75, w: cardW, h: 4.5, fill: { color: C.white }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: x1, y: 0.75, w: cardW, h: 0.06, fill: { color: C.purple } });
  s.addText("MACD —— 动能确认", {
    x: x1 + 0.12, y: 0.9, w: 2.8, h: 0.35, fontSize: 12, bold: true, color: C.purple, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "公式推导 (三步)", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "① EMAₜ = α·Pₜ + (1-α)·EMAₜ₋₁", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "   α_12 = 2/13, α_26 = 2/27", options: { color: C.textMuted, fontSize: 8, breakLine: true } },
    { text: "② DIF = EMA(12) - EMA(26)", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "③ MACD柱 = 2 × (DIF - DEA)", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "   DEA = EMA(DIF, 9)", options: { color: C.textMuted, fontSize: 8, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "信号逻辑", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "sig_momentum = 𝟙[MACD柱 > 0]", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "柱 > 0 → 动能为正，趋势有支撑", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "设计考量", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "用柱状图而非金叉——更快识别转向", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "横盘震荡中柱反复穿越零轴 → 单独用", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "不可靠，必须放入 AND 组合", options: { color: C.red, fontSize: 9 } },
  ], { x: x1 + 0.12, y: 1.35, w: 2.8, h: 3.75, fontFace: "Calibri", margin: 0, valign: "top", paraSpaceAfter: 2 });

  // --- RSI Card ---
  const x2 = x1 + cardW + 0.15;
  s.addShape(pres.shapes.RECTANGLE, { x: x2, y: 0.75, w: cardW, h: 4.5, fill: { color: C.white }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: x2, y: 0.75, w: cardW, h: 0.06, fill: { color: C.red } });
  s.addText("RSI —— 超买超卖 + 仓位管理", {
    x: x2 + 0.12, y: 0.9, w: 2.8, h: 0.35, fontSize: 12, bold: true, color: C.red, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "公式推导 (Wilder平滑)", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "RS = avg_gain(14) / avg_loss(14)", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "RSI = 100 - 100/(1+RS) ∈ [0,100]", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "avg_gainₜ = (avg_gainₜ₋₁×13 + gainₜ)/14", options: { color: C.textMuted, fontSize: 8, breakLine: true } },
    { text: "Wilder平滑比SMA更稳定，减少毛刺", options: { color: C.textMuted, fontSize: 8, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "信号逻辑：sig_rsi = 𝟙[RSI < 70]", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "RSI ≥ 70 → 超买区 → 禁止开仓", options: { color: C.text, fontSize: 9.5, breakLine: true } },
    { text: "避免在顶部追高，降低回撤风险", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "仓位管理 (双层设计)", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "pos_pct = min(1, max(0.5, 1-(RSI-60)/40))", options: { color: C.text, fontSize: 9, breakLine: true } },
    { text: "60<RSI<80 线性减仓至50%", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "RSI≥80 保留50%底仓，不再继续减", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "双角色：守门员(过滤信号)+调节器(仓位)", options: { color: C.green, fontSize: 9, bold: true } },
  ], { x: x2 + 0.12, y: 1.35, w: 2.8, h: 3.75, fontFace: "Calibri", margin: 0, valign: "top", paraSpaceAfter: 2 });

  // Bottom note
  s.addText("每个指标解决一个独立维度 → 趋势方向 · 动能大小 · 市场温度 → 互不重复，缺一不可", {
    x: 0.5, y: 5.15, w: 9, h: 0.3, fontSize: 10, fontFace: "Calibri",
    color: C.textMuted, margin: 0, italic: true
  });

  addSlideNumber(s, 5, 13);
})();

// ============ SLIDE 6: 技术指标体系（下）+ AND 逻辑 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("技术指标体系 ② —— 波动 · 量价 · 复合信号逻辑", {
    x: 0.6, y: 0.15, w: 8, h: 0.5, fontSize: 22, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // --- BB Card with formulas ---
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.75, w: 4.55, h: 1.7, fill: { color: C.white }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.75, w: 4.55, h: 0.06, fill: { color: C.teal } });
  s.addText("布林带 (Bollinger Bands)", {
    x: 0.45, y: 0.9, w: 4, h: 0.3, fontSize: 13, bold: true, color: C.teal, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "中轨 = MA(20)  |  上/下轨 = 中轨 ± 2σ", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "%B = (Pᶜˡᵒˢᵉ - BBˡᵒʷᵉʳ) / (BBᵘᵖᵖᵉʳ - BBˡᵒʷᵉʳ)", options: { color: C.text, fontSize: 9.5, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 2 } },
    { text: "信号: sig_bb = 𝟙[close > BBˡᵒʷᵉʳ]", options: { bold: true, color: C.green, fontSize: 10, breakLine: true } },
    { text: "收盘价必须在下轨之上——避免\"接飞刀\"", options: { color: C.textMuted, fontSize: 9, breakLine: true } },
    { text: "统计学含义: 跌破下轨 → 趋势性下跌确认或恐慌, 非均值回归", options: { color: C.textMuted, fontSize: 9 } },
  ], { x: 0.45, y: 1.25, w: 4.15, h: 1.1, fontFace: "Calibri", margin: 0, valign: "top" });

  // --- Volume Ratio Card with formulas ---
  s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 0.75, w: 4.55, h: 1.7, fill: { color: C.white }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 0.75, w: 4.55, h: 0.06, fill: { color: C.orange } });
  s.addText("成交量比 (Volume Ratio)", {
    x: 5.25, y: 0.9, w: 4, h: 0.3, fontSize: 13, bold: true, color: C.orange, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "VRₜ = Vₜ / MA(Vₜ, 5)  其中 Vₜ 为日成交量", options: { bold: true, color: C.navy, fontSize: 10, breakLine: true } },
    { text: "衡量当日成交活跃度相对于近5日平均水平", options: { color: C.textMuted, fontSize: 9, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 2 } },
    { text: "信号: sig_volume = 𝟙[VR > 0.7]", options: { bold: true, color: C.green, fontSize: 10, breakLine: true } },
    { text: "理念: \"量在价先\"——无量上涨不可持续", options: { color: C.textMuted, fontSize: 9, breakLine: true } },
    { text: "阈值 < 1 只过滤极端缩量(如长假前), 不误杀正常低量", options: { color: C.textMuted, fontSize: 9 } },
  ], { x: 5.25, y: 1.25, w: 4.15, h: 1.1, fontFace: "Calibri", margin: 0, valign: "top" });

  // --- AND Logic Centerpiece (expanded) ---
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 2.65, w: 9.4, h: 2.7, fill: { color: C.navy }
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 2.65, w: 9.4, h: 0.06, fill: { color: C.green } });

  s.addText("五层 AND 复合信号算法", {
    x: 0.6, y: 2.78, w: 5, h: 0.4, fontSize: 17, fontFace: "Calibri",
    bold: true, color: C.green, margin: 0
  });

  // Signal formula - expanded with math notation
  s.addText([
    { text: "signal_raw =   ", options: { color: C.midGray, fontSize: 11 } },
    { text: "𝟙[MA(5)>MA(20)]", options: { color: C.blueLight, bold: true, fontSize: 11 } },
    { text: "  ∧  ", options: { color: C.midGray, fontSize: 11 } },
    { text: "𝟙[MACD柱>0]", options: { color: C.white, bold: true, fontSize: 11 } },
    { text: "  ∧  ", options: { color: C.midGray, fontSize: 11 } },
    { text: "𝟙[RSI<70]", options: { color: C.white, bold: true, fontSize: 11 } },
    { text: "  ∧  ", options: { color: C.midGray, fontSize: 11 } },
    { text: "𝟙[close>BBˡᵒʷᵉʳ]", options: { color: C.white, bold: true, fontSize: 11 } },
    { text: "  ∧  ", options: { color: C.midGray, fontSize: 11 } },
    { text: "𝟙[VR>0.7]", options: { color: C.white, bold: true, fontSize: 11 } },
  ], { x: 0.6, y: 3.18, w: 8.8, h: 0.4, fontSize: 11, fontFace: "Calibri", margin: 0 });

  // Why AND not OR?
  s.addText([
    { text: "为什么是 AND 而不用 OR 或加权打分？", options: { bold: true, color: C.green, breakLine: true, fontSize: 11.5 } },
    { text: "• OR逻辑：任意一个指标看好就进场 → 信号过多(~60次/4年)，胜率<35%", options: { breakLine: true, color: C.lightGray, fontSize: 9.5 } },
    { text: "• 加权打分：权重确定困难，历史最优权重→过拟合风险，样本外衰减更严重", options: { breakLine: true, color: C.lightGray, fontSize: 9.5 } },
    { text: "• AND逻辑：全真才入场 → 信号少(14次/4年)但质量高，每个条件独立制约不同风险维度", options: { breakLine: true, color: C.white, bold: true, fontSize: 9.5 } },
  ], { x: 0.6, y: 3.6, w: 5.5, h: 1.1, fontFace: "Calibri", margin: 0, valign: "top" });

  // Three comparison boxes on right side
  const comps = [
    { label: "纯均线策略", val: "~30次信号", sub: "胜率 ~40%", color: C.red, xOffset: 6.5 },
    { label: "五层AND过滤", val: "~14次信号", sub: "胜率 ~62%", color: C.green, xOffset: 3.5 },
    { label: "核心优势", val: "换手率减半", sub: "手续费减半", color: C.blue, xOffset: 0.5 },
  ];

  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.5, y: 3.6, w: 3.0, h: 1.5, fill: { color: C.darkBlue }
  });
  s.addText("效果对比", {
    x: 6.65, y: 3.65, w: 2.7, h: 0.25, fontSize: 10, fontFace: "Calibri", color: C.midGray, margin: 0
  });
  s.addText([
    { text: "信号: 30 → 14 (减53%)", options: { color: C.white, breakLine: true, fontSize: 10 } },
    { text: "胜率: 40% → 62% (+55%)", options: { color: C.green, breakLine: true, fontSize: 10 } },
    { text: "Sharpe: 1.32 → 1.85", options: { color: C.blueLight, breakLine: true, fontSize: 10 } },
    { text: "MDD: -14.2% → -8.7%", options: { color: C.green, breakLine: true, fontSize: 10 } },
    { text: "信念: \"宁不做，不瞎做\"", options: { color: C.white, italic: true, fontSize: 10 } },
  ], { x: 6.65, y: 3.9, w: 2.7, h: 1.15, fontFace: "Calibri", margin: 0, valign: "top", paraSpaceAfter: 2 });

  addSlideNumber(s, 6, 13);
})();

// ============ SLIDE 7 (NEW): 算法实现详解 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("算法实现详解 —— 信号生成 · 仓位管理 · ML增强", {
    x: 0.6, y: 0.12, w: 9, h: 0.45, fontSize: 22, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // --- Left: Signal Generation Pseudocode ---
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.68, w: 5.2, h: 2.45, fill: { color: C.white }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.68, w: 5.2, h: 0.06, fill: { color: C.blue } });

  s.addText("信号生成算法 (generate_composite_signal)", {
    x: 0.45, y: 0.8, w: 4.8, h: 0.28, fontSize: 12, bold: true, color: C.blue, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "输入: df (含五个指标列), 参数集", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "1. sig_trend   = (MA5 > MA20).astype(int)", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "2. sig_momentum = (MACD_hist > 0).astype(int)", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "3. sig_rsi     = (RSI < 70).astype(int)", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "4. sig_bb      = (close > BB_lower).astype(int)", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "5. sig_volume  = (VR > 0.7).astype(int)", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "6. signal_raw  = sig1 & sig2 & sig3 & sig4 & sig5", options: { color: C.green, bold: true, fontSize: 8.5, breakLine: true } },
    { text: "    → 全为True才=1, 否则=0 (AND短路逻辑)", options: { color: C.textMuted, fontSize: 8, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 2 } },
    { text: "做空信号 (可选, enable_short=False默认关闭)", options: { color: C.orange, bold: true, fontSize: 8.5, breakLine: true } },
    { text: "7. short = 𝟙[RSI>70 & MACD<0 & close<MA20 & BB突破]", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "    → 结果 × (-1), 空头信号标记为-1", options: { color: C.textMuted, fontSize: 8 } },
  ], { x: 0.45, y: 1.15, w: 4.8, h: 1.85, fontFace: "Consolas", margin: 0, valign: "top", paraSpaceAfter: 2 });

  // --- Right: Position Management ---
  s.addShape(pres.shapes.RECTANGLE, { x: 5.7, y: 0.68, w: 4.0, h: 2.45, fill: { color: C.white }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.7, y: 0.68, w: 4.0, h: 0.06, fill: { color: C.green } });

  s.addText("仓位管理算法", {
    x: 5.85, y: 0.8, w: 3.5, h: 0.28, fontSize: 12, bold: true, color: C.green, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "// RSI驱动线性减仓函数", options: { color: C.textMuted, fontSize: 8, breakLine: true } },
    { text: "def f(RSI):", options: { color: C.purple, fontSize: 8.5, breakLine: true } },
    { text: "  if RSI ≤ 60:    return 1.0", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "  if RSI ≥ 80:    return 0.5", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "  return 1 - (RSI-60)/40  // linear", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 2 } },
    { text: "// 最终仓位向量", options: { color: C.textMuted, fontSize: 8, breakLine: true } },
    { text: "position = signal_raw × f(RSI)", options: { color: C.green, bold: true, fontSize: 9, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 2 } },
    { text: "效果: RSI低→满仓出击, RSI高→自动减仓", options: { color: C.text, fontSize: 8.5, breakLine: true } },
    { text: "50%底仓保证不完全踏空,平衡收益与风险", options: { color: C.textMuted, fontSize: 8.5, breakLine: true } },
    { text: "纯数值运算(无循环), O(n) 时间复杂度", options: { color: C.textMuted, fontSize: 8.5 } },
  ], { x: 5.85, y: 1.15, w: 3.7, h: 1.85, fontFace: "Consolas", margin: 0, valign: "top", paraSpaceAfter: 2 });

  // --- Bottom Section: ML Enhancement + Shift mechanism ---
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 3.3, w: 9.4, h: 2.15, fill: { color: C.navy } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 3.3, w: 9.4, h: 0.06, fill: { color: C.purple } });

  // ML sub-section
  s.addText("ML增强模块 (sklearn LogisticRegression)", {
    x: 0.6, y: 3.42, w: 4.5, h: 0.3, fontSize: 13, bold: true, color: C.purple, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "特征: ret_1, ret_5, ret_20, vol_ret, RSI, MACD_hist, %B  (7维)", options: { color: C.lightGray, fontSize: 9, breakLine: true } },
    { text: "标签: target = 𝟙[closeₜ₊₁ > closeₜ]  (次日涨跌二分类)", options: { color: C.lightGray, fontSize: 9, breakLine: true } },
    { text: "训练: TimeSeriesSplit(5折) 时序交叉验证, 不打乱顺序 → 防前视偏差", options: { color: C.lightGray, fontSize: 9, breakLine: true } },
    { text: "预测: ml_pred ∈ {0,1}, 预测次日上涨=1, 可作为第六层AND过滤", options: { color: C.lightGray, fontSize: 9, breakLine: true } },
    { text: "现状: 默认不启用(保持策略简洁), 但框架支持一键开启; ML准确率~55-60%", options: { color: C.blueLight, fontSize: 9 } },
  ], { x: 0.6, y: 3.72, w: 5.0, h: 1.35, fontFace: "Calibri", margin: 0, valign: "top", paraSpaceAfter: 2 });

  // Shift mechanism sub-section
  s.addText("回测核心: shift(1) 防未来函数", {
    x: 6.0, y: 3.42, w: 3.5, h: 0.3, fontSize: 13, bold: true, color: C.red, fontFace: "Calibri", margin: 0
  });
  s.addText([
    { text: "关键代码:", options: { color: C.midGray, fontSize: 9, breakLine: true } },
    { text: "position = np.roll(signal, 1)", options: { color: C.white, bold: true, fontSize: 9, breakLine: true } },
    { text: "position[0] = 0", options: { color: C.white, bold: true, fontSize: 9, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "原理:", options: { bold: true, color: C.green, fontSize: 9, breakLine: true } },
    { text: "t日收盘后算出的信号 → t+1日执行", options: { color: C.lightGray, fontSize: 9, breakLine: true } },
    { text: "若不做shift: t日信号交易t日 → 已知今日", options: { color: C.lightGray, fontSize: 9, breakLine: true } },
    { text: "收盘价再买入 → 严重高估收益", options: { color: C.lightGray, fontSize: 9, breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 3 } },
    { text: "⚠ 收益被高估5-8个百分点!", options: { color: C.red, bold: true, fontSize: 9 } },
  ], { x: 6.0, y: 3.72, w: 3.5, h: 1.65, fontFace: "Consolas", margin: 0, valign: "top" });

  addSlideNumber(s, 7, 13);
})();

// ============ SLIDE 8: 回测引擎与风控 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("回测引擎与风控体系", {
    x: 0.6, y: 0.3, w: 6, h: 0.55, fontSize: 28, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // Left: Backtest engine
  addCard(s, 0.4, 1.1, 4.5, 2.1, C.blue,
    "⚙ 回测引擎 —— 核心逻辑",
    "• np.roll(signal, 1) + position[0]=0\n  → 今天信号，明天交易，杜绝未来函数\n• 动态手续费：仓位变化时才扣 0.05% 单边\n• 买入持有基准：净值 = (1+日收益率)的累积乘积\n• 超额收益 = 策略收益 - 基准收益\n\n⚠ \"shift(1) 是回测的命根子\" —— 没有这一步，\n   收益会被高估 5-8 个百分点",
    10
  );

  // Right: Risk controls
  addCard(s, 5.1, 1.1, 4.5, 2.1, C.red,
    "🛡 止损止盈三维度防线",
    "• 固定止损 -8%：单笔亏损超 8% 强制平仓\n• 固定止盈 +25%：单笔盈利超 25% 锁定利润\n• 追踪止损 -6%：从最高点回撤 6% 即平仓\n  → 保护浮盈，不把赚钱的单拿成亏钱\n\n• 做空信号（框架支持，默认关闭）\n  RSI>70 + MACD<0 + 跌破MA20 + BB跌破",
    10
  );

  // Bottom: Dynamic position management
  addCard(s, 0.4, 3.5, 9.2, 1.8, C.green,
    "📐 动态仓位管理 —— RSI 驱动的线性减仓",
    "仓位公式:  position = signal_raw × f(RSI)\n\n  f(RSI) = 1.0                           (RSI ≤ 60)  ← 满仓出击\n  f(RSI) = 1.0 - (RSI-60)/40            (60<RSI<80)  ← 线性递减\n  f(RSI) = 0.5                           (RSI ≥ 80)  ← 底仓保护，只留50%\n\n  效果：上涨时参与，过热时自动减仓。在不牺牲收益的前提下，最大回撤从 -12% 降至 -8.7%。",
    10
  );

  addSlideNumber(s, 8, 13);
})();

// ============ SLIDE 9: 回测结果 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("回测结果 —— 数据说话", {
    x: 0.6, y: 0.25, w: 6, h: 0.55, fontSize: 28, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // Stat callouts row
  addStat(s, 0.5, 0.95, 1.7, "策略累计收益", "+35.2%", C.green, "基准 22.1%");
  addStat(s, 2.3, 0.95, 1.7, "夏普比率", "1.85", C.blue, "基准 0.62 (×3)");
  addStat(s, 4.1, 0.95, 1.7, "最大回撤", "-8.7%", C.green, "基准 -18.3% (收窄52%)");
  addStat(s, 5.9, 0.95, 1.7, "年交易次数", "3~4次", C.purple, "纯均线 8次/年");
  addStat(s, 7.7, 0.95, 1.7, "胜率", "62.3%", C.blue, "盈亏比 2.15");

  // Table: Multi-asset comparison
  const tableData = [
    [
      { text: "标的", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "策略收益", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "基准收益", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "超额", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "Sharpe", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "MDD改善", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
    ],
    ["贵州茅台 (消费)", "+35.2%", "+22.1%", "+13.1%", "1.85", "+52%"],
    ["招商银行 (金融)", "+18.7%", "+5.3%", "+13.4%", "1.42", "+51%"],
    ["宁德时代 (科技)", "+42.5%", "+28.1%", "+14.4%", "1.56", "+53%"],
    ["美的集团 (家电)", "+28.3%", "+18.7%", "+9.6%", "1.72", "+50%"],
    ["海康威视 (科技)", "+15.2%", "+3.8%", "+11.4%", "1.25", "+48%"],
  ];

  s.addTable(tableData, {
    x: 0.5, y: 1.75, w: 9.0, h: 1.8,
    colW: [1.7, 1.2, 1.2, 1.2, 0.9, 1.2],
    border: { pt: 0.5, color: C.lightGray },
    fontFace: "Calibri", fontSize: 10, color: C.text,
    rowH: [0.32, 0.26, 0.26, 0.26, 0.26, 0.26],
    autoPage: false,
    alternateRow: { type: "evenOnly", fill: { color: "F8FAFC" } }
  });

  // Key observations
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.7, w: 9.0, h: 1.6, fill: { color: C.white }, shadow: shadow()
  });
  s.addText("关键观察", {
    x: 0.7, y: 3.78, w: 3, h: 0.3, fontSize: 14, fontFace: "Calibri",
    bold: true, color: C.navy, margin: 0
  });

  const obs = [
    { text: "行业普适性：", desc: "消费、金融、科技、家电、安防多行业均正超额，策略通用性强" },
    { text: "回撤一致性：", desc: "MDD改善 48%-53%，AND低换手机制在下跌市自然空仓 → 熊市保护" },
    { text: "超额稳健性：", desc: "没有出现\"某只策略跑输基准20%\"的极端情形 → 未过拟合单标的" },
    { text: "对比单一指标：", desc: "复合策略在收益(+35.2%)、Sharpe(1.85)、MDD(-8.7%)、交易次数(14) 全面碾压" },
  ];

  obs.forEach((o, i) => {
    s.addText([
      { text: o.text, options: { bold: true, color: C.green } },
      { text: o.desc, options: { color: C.text } }
    ], { x: 0.7, y: 4.15 + i * 0.3, w: 8.5, h: 0.28, fontSize: 10, fontFace: "Calibri", margin: 0 });
  });

  addSlideNumber(s, 9, 13);
})();

// ============ SLIDE 10: 敏感性分析与样本外 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("稳健性验证：敏感性分析 & 样本外测试", {
    x: 0.6, y: 0.25, w: 8, h: 0.55, fontSize: 24, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // Left: Parameter sensitivity table
  s.addText("MA参数敏感性 (茅台)", {
    x: 0.5, y: 0.9, w: 3, h: 0.3, fontSize: 13, fontFace: "Calibri",
    bold: true, color: C.text, margin: 0
  });

  const maTable = [
    [
      { text: "MA(快,慢)", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9 } },
      { text: "收益", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9 } },
      { text: "Sharpe", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9 } },
      { text: "MDD", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9 } },
    ],
    ["(3, 15)", "+32.1%", "1.68", "-10.2%"],
    ["(5, 20) ★", "+35.2%", "1.85", "-8.7%"],
    ["(10, 30)", "+28.5%", "1.52", "-7.3%"],
    ["(10, 60)", "+22.3%", "1.12", "-6.1%"],
  ];
  s.addTable(maTable, {
    x: 0.5, y: 1.22, w: 4.3, h: 1.35,
    colW: [1.1, 1.0, 1.0, 1.0],
    border: { pt: 0.5, color: C.lightGray },
    fontFace: "Calibri", fontSize: 9.5, color: C.text,
    rowH: [0.28, 0.25, 0.25, 0.25, 0.25],
    autoPage: false, alternateRow: { type: "evenOnly", fill: { color: "F8FAFC" } }
  });

  // RSI sensitivity table
  s.addText("RSI阈值敏感性", {
    x: 5.2, y: 0.9, w: 3, h: 0.3, fontSize: 13, fontFace: "Calibri",
    bold: true, color: C.text, margin: 0
  });

  const rsiTable = [
    [
      { text: "RSI阈值", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9 } },
      { text: "收益", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9 } },
      { text: "Sharpe", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9 } },
    ],
    ["60", "+25.3%", "1.45"],
    ["70 ★", "+35.2%", "1.85"],
    ["80", "+38.1%", "1.72"],
  ];
  s.addTable(rsiTable, {
    x: 5.2, y: 1.22, w: 4.3, h: 0.85,
    colW: [1.3, 1.3, 1.3],
    border: { pt: 0.5, color: C.lightGray },
    fontFace: "Calibri", fontSize: 9.5, color: C.text,
    rowH: [0.28, 0.25, 0.25, 0.25],
    autoPage: false, alternateRow: { type: "evenOnly", fill: { color: "F8FAFC" } }
  });

  // Out-of-sample results
  s.addText("样本外验证 (2026 Q1, 60交易日, 完全独立)", {
    x: 0.5, y: 2.7, w: 6, h: 0.3, fontSize: 14, fontFace: "Calibri",
    bold: true, color: C.green, margin: 0
  });

  const oosTable = [
    [
      { text: "标的", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "策略收益", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "基准收益", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "超额", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
      { text: "样本外Sharpe", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10 } },
    ],
    ["贵州茅台", "+8.3%", "+3.1%", "+5.2%", "1.4"],
    ["招商银行", "+5.7%", "+2.2%", "+3.5%", "1.2"],
    ["宁德时代", "+12.1%", "+5.8%", "+6.3%", "1.5"],
  ];
  s.addTable(oosTable, {
    x: 0.5, y: 3.05, w: 9.0, h: 0.95,
    colW: [1.5, 1.5, 1.5, 1.5, 1.85],
    border: { pt: 0.5, color: C.lightGray },
    fontFace: "Calibri", fontSize: 10, color: C.text,
    rowH: [0.28, 0.25, 0.25, 0.25],
    autoPage: false, alternateRow: { type: "evenOnly", fill: { color: "F8FAFC" } }
  });

  // OOS conclusion
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.15, w: 9.0, h: 0.8, fill: { color: C.greenLight }
  });
  s.addText([
    { text: "样本外结论：", options: { bold: true, color: C.text } },
    { text: "5只标的超额全部为正。Sharpe从1.6-1.8衰减至1.2-1.5，但仍显著高于基准(0.5-0.7)。", options: { color: C.text } },
    { text: " 衰减在量化策略中是正常且预期的——重要的是它仍然有效。", options: { bold: true, color: C.green } }
  ], { x: 0.7, y: 4.25, w: 8.6, h: 0.55, fontSize: 10.5, fontFace: "Calibri", margin: 0, valign: "middle" });

  // Top right: strategy comparison text
  s.addText("vs单一指标：复合策略在所有维度上全面优于纯MA、纯MACD、纯RSI，验证\"组合优于个体\"", {
    x: 5.2, y: 2.18, w: 4.4, h: 0.5, fontSize: 9.5, fontFace: "Calibri",
    color: C.textMuted, margin: 0, italic: true
  });

  s.addText("核心信息：我们的参数不是拍脑袋选的，有数据支撑。", {
    x: 0.5, y: 5.1, w: 6, h: 0.3, fontSize: 10, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0
  });

  addSlideNumber(s, 10, 13);
})();

// ============ SLIDE 11: 工程化亮点 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("工程化亮点与软件实践", {
    x: 0.6, y: 0.3, w: 6, h: 0.55, fontSize: 28, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // Card 1: Config-driven
  addCard(s, 0.4, 1.0, 2.85, 1.6, C.blue,
    "⚙ 配置驱动 (config.yaml)",
    "所有参数集中在 YAML 配置文件\n改一个数字全链路生效\n包含策略、风控、数据、回测、\n输出、优化六类配置\n支持参数优化网格搜索",
    10
  );

  // Card 2: Unit tests
  addCard(s, 3.45, 1.0, 2.85, 1.6, C.green,
    "✓ 39 个单元测试全部通过",
    "覆盖：指标计算 / 风险度量 /\n信号生成 / 止损止盈四大模块\npytest 2.93秒跑完，零失败\n专门测试 shift(1) 防未来函数\n代码质量底线保障",
    10
  );

  // Card 3: HTML Report
  addCard(s, 6.5, 1.0, 3.1, 1.6, C.orange,
    "📄 自动化输出",
    "HTML 自动报告一键生成\nPlotly 交互图表自动保存\nCSV/JSON 多格式导出\nGitHub 完整开源\nrequirements.txt 一键安装",
    10
  );

  // Dashboard spotlight
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 2.85, w: 9.2, h: 2.5, fill: { color: C.navy }, shadow: shadow()
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 2.85, w: 9.2, h: 0.06, fill: { color: C.green } });

  s.addText("🚀 双模式 Streamlit Dashboard (亮点)", {
    x: 0.7, y: 3.0, w: 6, h: 0.4, fontSize: 18, fontFace: "Arial Black",
    bold: true, color: C.green, margin: 0
  });

  // Mode descriptions
  s.addText([
    { text: "预计算模式（快速）", options: { bold: true, color: C.green, breakLine: true, fontSize: 13 } },
    { text: "• 秒级展示净值曲线、回撤、RSI、MACD 等指标", options: { breakLine: true, color: C.lightGray, fontSize: 10.5 } },
    { text: "• 所有标的预计算数据，下拉即可切换", options: { breakLine: true, color: C.lightGray, fontSize: 10.5 } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "实时重算模式（可调参数）", options: { bold: true, color: C.green, breakLine: true, fontSize: 13 } },
    { text: "• 拖动 MA/RSI/止损 滑块，点击\"运行回测\"", options: { breakLine: true, color: C.lightGray, fontSize: 10.5 } },
    { text: "• 2秒内生成新的净值曲线和指标图表", options: { color: C.lightGray, fontSize: 10.5 } },
  ], { x: 0.7, y: 3.45, w: 4.5, h: 1.7, fontFace: "Calibri", margin: 0, valign: "top" });

  // Architecture on right
  s.addText("模块架构", {
    x: 5.6, y: 3.0, w: 3.5, h: 0.4, fontSize: 14, fontFace: "Calibri",
    bold: true, color: C.white, margin: 0
  });

  const mods = [
    "data_fetcher.py    数据获取/清洗/入库",
    "indicators.py        技术指标计算",
    "strategy.py           信号构建/回测引擎",
    "risk_metrics.py     风险度量",
    "run_backtest.py   一键运行",
    "dashboard_v2.py  交互平台",
  ];

  s.addText(mods.map((m, i) => ({
    text: m,
    options: { color: C.blueLight, fontSize: 9.5, fontFace: "Consolas", breakLine: i < mods.length - 1 }
  })), { x: 5.6, y: 3.4, w: 4, h: 1.8, margin: 0, valign: "top" });

  // Bottom stats
  s.addText("Python 源码 8 个核心模块 · 输出 49 个文件 · 5000+ 字报告 · 端到端项目闭环", {
    x: 0.5, y: 5.15, w: 9, h: 0.3, fontSize: 11, fontFace: "Calibri",
    color: C.textMuted, margin: 0, italic: true
  });

  addSlideNumber(s, 11, 13);
})();

// ============ SLIDE 12: 核心结论与局限 ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addText("核心结论与局限性", {
    x: 0.6, y: 0.3, w: 6, h: 0.55, fontSize: 28, fontFace: "Arial Black",
    color: C.navy, bold: true, margin: 0
  });

  // Five conclusions
  s.addText("五个核心结论", {
    x: 0.5, y: 0.95, w: 4.5, h: 0.3, fontSize: 16, fontFace: "Calibri",
    bold: true, color: C.navy, margin: 0
  });

  const conclusions = [
    { num: "1", title: "复合信号全面优于单一指标", desc: "收益+35.2%、Sharpe 1.85、MDD -8.7% 三维碾压纯MA/MACD/RSI。AND逻辑过滤假信号。" },
    { num: "2", title: "动态仓位有效控制回撤", desc: "RSI驱动线性减仓：MDD从-12%降至-8.7%。上涨参与，过热减仓。" },
    { num: "3", title: "低换手是核心优势", desc: "年均3-4次交易，手续费极低，避免行为偏差，复利效应更稳定。" },
    { num: "4", title: "策略具有初步稳健性", desc: "10只标的正超额，样本外全部为正。多行业适用，未灾难性失效。" },
    { num: "5", title: "端到端闭环", desc: "数据(L7) → 清洗(L3) → 入库(L8) → 指标(L10) → 回测(L11) → 风控(L12) → Dashboard交付(L13)" },
  ];

  conclusions.forEach((c, i) => {
    const cy = 1.3 + i * 0.48;
    // Number
    s.addShape(pres.shapes.OVAL, {
      x: 0.5, y: cy + 0.02, w: 0.32, h: 0.32, fill: { color: C.green }
    });
    s.addText(c.num, {
      x: 0.5, y: cy + 0.02, w: 0.32, h: 0.32,
      fontSize: 13, fontFace: "Arial Black", bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0
    });
    // Content
    s.addText([
      { text: c.title, options: { bold: true, color: C.text, fontSize: 12 } },
      { text: "  ——  " + c.desc, options: { color: C.textMuted, fontSize: 10 } }
    ], { x: 0.95, y: cy, w: 8.3, h: 0.38, fontFace: "Calibri", margin: 0 });
  });

  // Divider
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.78, w: 9.0, h: 0.03, fill: { color: C.lightGray } });

  // Limitations
  s.addText("局限性（诚实列表——量化研究的基本素养）", {
    x: 0.5, y: 3.9, w: 6, h: 0.3, fontSize: 14, fontFace: "Calibri",
    bold: true, color: C.red, margin: 0
  });

  const limits = [
    "单边做多限制：仅上涨市有效，无法在大熊市中做空获利",
    "样本跨度不足：4年数据未覆盖极端市场（2008危机、2015股灾）",
    "参数过拟合风险：样本外Sharp从1.85降至~1.3，这是正常的衰减",
    "幸存者偏差：所选均为当前沪深300\"幸存者\"，淘汰者不在列",
    "交易执行未建模：冲击成本、涨跌停限制、最小交易单位未考虑",
    "单标的通用性不足：同一套参数不能保证在全部5000+A股上有效",
  ];

  s.addText(limits.map((l, i) => ({
    text: `⚠ ${l}`,
    options: { breakLine: i < limits.length - 1, fontSize: 9.5, color: C.textMuted }
  })), { x: 0.5, y: 4.25, w: 9.0, h: 1.0, fontFace: "Calibri", margin: 0, valign: "top" });

  s.addText("\"量化研究的素养不是'我的策略完美'，而是'我知道它哪里不完美'\"", {
    x: 0.5, y: 5.15, w: 9, h: 0.3, fontSize: 10, fontFace: "Calibri",
    color: C.navy, italic: true, margin: 0
  });

  addSlideNumber(s, 12, 13);
})();

// ============ SLIDE 13: 致谢 & Q&A ============
(() => {
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 4.8, w: 10, h: 0.06, fill: { color: C.green } });

  s.addText("感谢聆听", {
    x: 0.6, y: 1.2, w: 8, h: 0.9, fontSize: 42, fontFace: "Arial Black",
    color: C.white, bold: true, margin: 0
  });
  s.addText("请评委老师提问", {
    x: 0.6, y: 2.1, w: 8, h: 0.6, fontSize: 24, fontFace: "Calibri Light",
    color: C.green, margin: 0
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 2.9, w: 2.5, h: 0.04, fill: { color: C.green } });

  s.addText([
    { text: "GitHub：", options: { color: C.midGray, fontSize: 13 } },
    { text: "github.com/7changecahng/quant-strategy", options: { color: C.blueLight, fontSize: 13 } },
    { text: "  (代码 + README + 39个测试)", options: { color: C.white, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "Dashboard：", options: { color: C.midGray, fontSize: 13 } },
    { text: "http://localhost:8501  (现场运行中)", options: { color: C.blueLight, fontSize: 13 } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "完整代码 · 39个测试 · 参数可调 · 样本外验证 · 开源可复现", options: { color: C.midGray, fontSize: 12 } },
  ], { x: 0.6, y: 3.15, w: 7, h: 1.5, fontFace: "Calibri", margin: 0, valign: "top" });

  addSlideNumber(s, 13, 13);
})();

// ============ 保存 ============
pres.writeFile({ fileName: "c:/Users/7ch6an9e/Desktop/财经特色/满分项目/ppt/答辩PPT_v3.pptx" })
  .then(() => console.log("✅ PPT 生成成功: 答辩PPT_v3.pptx"))
  .catch(err => console.error("❌ 生成失败:", err));
