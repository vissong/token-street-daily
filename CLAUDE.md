# 词元长街 · Token Street — CLAUDE.md

这是 **词元长街（Token Street）** AI 日报站点的工作仓库。
每天运行一次采集→合并→分类→渲染流水线，产出一个静态 HTML 日报页面并更新首页索引。

---

## 项目结构

```
/
├── index.html                  # 首页（词元长街设计，JS 从 data/issues.json 渲染）
├── feed.xml                    # RSS 2.0 订阅源
├── assets/
│   └── style.css               # 词元长街设计系统 CSS（勿手动修改）
├── issues/
│   └── YYYY-MM-DD.html         # 每日期刊页面
├── data/
│   ├── issues.json             # 所有期刊的索引清单（首页 JS 读取）
│   └── raw/
│       └── YYYY-MM-DD/
│           ├── <source>.md     # 各数据源采集的原始内容
│           ├── merged.json     # 去重+分类后的合并条目
│           └── collect.log     # 采集日志
├── config/
│   ├── sources.yaml            # 数据源配置
│   └── site.yaml               # 站点元信息
└── CLAUDE.md                   # 本文件
```

---

## 技能依赖

本项目使用 **`ai-newsletter-builder`** skill（位于 `~/.claude/skills/ai-newsletter-builder/`）。
所有生成操作都通过该 skill 执行，不要绕过它直接编写脚本。

---

## 每日生成新期刊

### 标准流程（最常用）

在 Claude Code 中运行：

```
/ai-newsletter-builder 生成今天的日报
```

skill 会自动执行以下步骤：
1. **采集**：并发抓取 `config/sources.yaml` 中所有 `enabled: true` 的数据源
2. **合并去重**：写入 `data/raw/<date>/merged.json`
3. **分类**：5 个固定分类（重大发布 / 行业动态 / 研究前沿 / 工具发布 / 政策监管）
4. **渲染期刊页**：写入 `issues/<date>.html`
5. **更新索引**：更新 `data/issues.json`，复制 `standalone.html → index.html`
6. **生成 RSS**：写入 `feed.xml`

### 只补某一天的期刊

```
/ai-newsletter-builder 补一下昨天（或指定日期）的日报
```

### 只更新首页 / RSS（不重新采集）

```
/ai-newsletter-builder 重新生成首页和 RSS
```

---

## 数据源管理

当前启用的数据源见 `config/sources.yaml`。

### 添加新数据源

```
/ai-newsletter-builder 添加一个数据源
```

skill 会引导你完成：类型选择 → 参数填写 → **试采集验证** → 写入 sources.yaml。
**不要跳过试采集步骤**——配置看起来正确但实际抓不到内容是最常见的静默错误。

### 现有数据源说明

| name | 类型 | 备注 |
|------|------|------|
| openai-blog | web (RSS) | `https://openai.com/blog/rss.xml`，近 7 天 |
| ai-hub-today | web | `https://ai.hubtoday.app/YYYY-MM/YYYY-MM-DD`，当日精选 |

---

## 设计系统：词元长街（ciyuan-jie）

本站使用词元长街设计，**CSS 已预编译，禁止从 DESIGN.md 重新生成**。

- CSS 源文件：`~/.claude/skills/ai-newsletter-builder/designs/ciyuan-jie/style.css`
- 首页模板：`~/.claude/skills/ai-newsletter-builder/designs/ciyuan-jie/standalone.html`
- 完整设计规范：`~/.claude/skills/ai-newsletter-builder/designs/ciyuan-jie/DESIGN.md`

### 期刊页关键 class 规范（渲染时必须遵守）

```html
<!-- 页面包装：必须是 <body><main class="paper">，不能是 <body class="paper"> -->
<body><main class="paper">…</main></body>

<!-- Topbar：必须有 .left / .right 子 div -->
<div class="topbar">
  <div class="left"><span><span class="dot"></span>正在刊行</span></div>
  <div class="right"><span id="live-clock">— : —</span></div>
</div>

<!-- Masthead：期刊页用日期作 h1，站名缩为 kicker -->
<header class="masthead">
  <div class="kicker"><a href="../index.html">词元长街 · Token Street</a></div>
  <h1 style="font-size:clamp(36px,4vw,52px)">2026年04月19日</h1>
  <div class="en">第 001 期 · AI 每日简报</div>
  <div class="meta-strip">
    <span class="l">北京 · 上海 · 旧金山</span>
    <span class="c">17 条 · 2 个数据源</span>
    <span class="r">SUNDAY · 2026-04-19</span>
  </div>
</header>

<!-- 今日要闻：用 .highlights-block，不存在 .lead-section -->
<div class="highlights-block">
  <div>
    <div class="hl-title">今日要闻 · TODAY'S HIGHLIGHTS</div>
    <h2>今日概要标题</h2>
    <ol class="hl-list"><li><a href="#item-1">头条标题</a></li></ol>
  </div>
  <aside class="stats-aside">
    <h4>今日数字 · IN NUMBERS</h4>
    <ul>
      <li><span class="n">17</span><span>今日条目</span><span class="v">ITEMS</span></li>
    </ul>
  </aside>
</div>

<!-- .sep 必须是空元素，CSS 渲染为 3px 圆点 -->
<span class="sep"></span>   <!-- ✓ -->
<span class="sep">·</span>  <!-- ✗ 会同时显示点和字符 -->

<!-- Footer：必须是 <footer> 元素 + .colophon + div×3 + .bottom -->
<footer class="site-footer">
  <div class="colophon"><span class="brand">词元长街</span>简介文字</div>
  <div><h5>栏目</h5><ul>…</ul></div>
  <div><h5>数据源</h5><ul>…</ul></div>
  <div><h5>关于</h5><ul>…</ul></div>
  <div class="bottom">
    <span>© MMXXVI Token Street</span>
    <span>Powered by ai-newsletter-builder</span>
  </div>
</footer>
```

---

## issues.json 必填字段

每次生成期刊后，`data/issues.json` 的每个条目**必须包含 `source_count`**，
否则首页 JS 渲染出"来源 undefined 个"：

```json
{
  "date": "2026-04-19",
  "title": "AI 日报 · 词元长街 — 2026-04-19",
  "path": "issues/2026-04-19.html",
  "item_count": 17,
  "source_count": 2,
  "summary": "今日重点：……",
  "generated_at": "2026-04-19T08:30:00Z",
  "categories": {
    "major-release": 4,
    "industry-business": 5,
    "tools-release": 4,
    "research-frontier": 3,
    "policy-regulation": 1
  },
  "top_items": [
    {"title": "…", "category": "major-release", "source_count": 1}
  ]
}
```

---

## 运行本地预览服务器

由于首页用 JS fetch `data/issues.json`，必须通过 HTTP 服务器访问，不能直接打开文件：

```bash
cd /path/to/token-street-daily
python3 -m http.server 8766
# 然后访问 http://localhost:8766
```

---

## 发布

本仓库已配置为 GitHub Pages 源（或可接入 Cloudflare Pages）。
每次推送 `main` 分支后自动发布。

```bash
git add .
git commit -m "issue: YYYY-MM-DD"
git push
```

不要手动编辑 `index.html` 和 `feed.xml`——它们是构建产物，由 skill 流水线负责更新。
