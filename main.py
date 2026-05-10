from collections import Counter
from typing import Dict, List

import re
from urllib.parse import urlencode
from urllib.request import urlopen
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="AI题材系统")

MOBILE_NAV_ITEMS = [
    {
        "title": "今日复盘",
        "subtitle": "查看最新交易日市场总结、核心题材与风险提示",
        "href": "/mobile/recap",
        "accent": "cyan",
    },
    {
        "title": "AI选股",
        "subtitle": "浏览电脑端已生成的弱转强与主题候选池",
        "href": "/mobile/screener",
        "accent": "violet",
    },
    {
        "title": "新闻荐股",
        "subtitle": "粘贴新闻文本，轻量触发电脑端 AI 研究分析",
        "href": "/mobile/news-recommend",
        "accent": "amber",
    },
    {
        "title": "实时情报",
        "subtitle": "后续接入 JYHF-CDP 与 Redis 情报流的移动看板",
        "href": "/mobile/intel",
        "accent": "green",
    },
]

MOBILE_PAGE_META = {
    "/mobile/recap": {
        "title": "今日复盘",
        "description": "Phase 2 将在这里展示最新交易日复盘、核心题材、重点股票、弱转强观察与风险提示。",
    },
    "/mobile/screener": {
        "title": "AI选股",
        "description": "Phase 3 将在这里展示电脑端已生成的 AI 选股 TopN、候选理由、题材映射与风险条件。",
    },
    "/mobile/news-recommend": {
        "title": "新闻荐股",
        "description": "Phase 4 将在这里支持粘贴新闻文本，并调用电脑端 AI 事件理解与题材匹配能力。",
    },
    "/mobile/intel": {
        "title": "实时情报",
        "description": "Phase 6 将在这里展示实时事件流，第一版建议先使用轮询，后续再接入 SSE。",
    },
}


def _mobile_shell(title: str, body: str) -> str:
    """Render a small, dependency-free HTML5 mobile shell for iPhone Safari."""
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\" />
  <meta name=\"theme-color\" content=\"#07111f\" />
  <title>{title} · AI投资驾驶舱</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07111f;
      --panel: rgba(15, 27, 48, 0.88);
      --panel-strong: rgba(24, 42, 74, 0.96);
      --text: #eef6ff;
      --muted: #8fa7c5;
      --line: rgba(137, 173, 216, 0.18);
      --cyan: #27d8ff;
      --violet: #9b7cff;
      --amber: #ffca68;
      --green: #55e39f;
    }}
    * {{ box-sizing: border-box; }}
    html {{ min-height: 100%; background: var(--bg); }}
    body {{
      min-height: 100vh;
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, \"SF Pro Display\", \"Segoe UI\", sans-serif;
      background:
        radial-gradient(circle at 20% 0%, rgba(39, 216, 255, 0.22), transparent 28rem),
        radial-gradient(circle at 90% 16%, rgba(155, 124, 255, 0.20), transparent 24rem),
        linear-gradient(180deg, #07111f 0%, #09182c 52%, #07111f 100%);
      color: var(--text);
      padding: max(20px, env(safe-area-inset-top)) 16px max(28px, env(safe-area-inset-bottom));
    }}
    a {{ color: inherit; text-decoration: none; }}
    .mobile-shell {{ max-width: 520px; margin: 0 auto; }}
    .hero {{ padding: 18px 2px 22px; }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 14px;
      color: var(--cyan);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }}
    .eyebrow::before {{
      content: \"\";
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--green);
      box-shadow: 0 0 18px var(--green);
    }}
    h1 {{ margin: 0; font-size: clamp(30px, 9vw, 44px); line-height: 1.05; letter-spacing: -0.04em; }}
    .lead {{ margin: 14px 0 0; color: var(--muted); font-size: 15px; line-height: 1.7; }}
    .grid {{ display: grid; gap: 14px; margin-top: 12px; }}
    .card {{
      position: relative;
      overflow: hidden;
      display: block;
      min-height: 132px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: linear-gradient(145deg, var(--panel-strong), var(--panel));
      box-shadow: 0 20px 54px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255,255,255,0.06);
      -webkit-tap-highlight-color: transparent;
    }}
    .card::after {{
      content: \"\";
      position: absolute;
      inset: auto -48px -58px auto;
      width: 148px;
      height: 148px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--accent), transparent 78%);
      filter: blur(2px);
    }}
    .card:active {{ transform: translateY(1px) scale(0.99); }}
    .card-row {{ position: relative; z-index: 1; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }}
    .card h2 {{ margin: 0; font-size: 21px; letter-spacing: -0.02em; }}
    .card p {{ margin: 10px 0 0; color: var(--muted); font-size: 14px; line-height: 1.55; }}
    .arrow {{
      flex: 0 0 auto;
      display: grid;
      place-items: center;
      width: 34px;
      height: 34px;
      border-radius: 999px;
      color: var(--accent);
      background: color-mix(in srgb, var(--accent), transparent 88%);
      border: 1px solid color-mix(in srgb, var(--accent), transparent 72%);
    }}
    .cyan {{ --accent: var(--cyan); }}
    .violet {{ --accent: var(--violet); }}
    .amber {{ --accent: var(--amber); }}
    .green {{ --accent: var(--green); }}
    .notice {{
      margin-top: 18px;
      padding: 14px 16px;
      border: 1px solid rgba(255, 202, 104, 0.24);
      border-radius: 18px;
      background: rgba(255, 202, 104, 0.08);
      color: #ffe1a3;
      font-size: 13px;
      line-height: 1.6;
    }}
    .placeholder {{ margin-top: 18px; padding: 20px; border-radius: 24px; border: 1px solid var(--line); background: var(--panel); }}
    .placeholder h2 {{ margin: 0 0 10px; font-size: 22px; }}
    .placeholder p {{ margin: 0; color: var(--muted); line-height: 1.7; }}
    .back {{ display: inline-flex; margin-top: 18px; color: var(--cyan); font-size: 14px; font-weight: 700; }}
    @supports not (background: color-mix(in srgb, white, black)) {{
      .card::after {{ background: rgba(39, 216, 255, 0.14); }}
      .arrow {{ background: rgba(39, 216, 255, 0.10); border-color: rgba(39, 216, 255, 0.24); }}
    }}
  </style>
</head>
<body>
  <main class=\"mobile-shell\">
    {body}
  </main>
</body>
</html>"""


@app.get("/")
def read_root():
    return {"message": "AI题材系统已启动"}

class NewsItem(BaseModel):
    title: str
    content: str


class AnalyzeRequest(BaseModel):
    news: List[NewsItem]


class AnalyzeResponse(BaseModel):
    hotspots: Dict[str, int]


def simple_keyword_extraction(text: str) -> List[str]:
    """Extract simple Chinese keywords for the legacy news analysis endpoint."""
    return [word for word in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{2,}", text)]


@app.post("/analyze_news", response_model=AnalyzeResponse)
def analyze_news(req: AnalyzeRequest):
    all_keywords = []
    for item in req.news:
        all_keywords.extend(simple_keyword_extraction(f"{item.title} {item.content}"))
    counter = Counter(all_keywords)
    return AnalyzeResponse(hotspots=dict(counter.most_common(10)))


NEWS_API_KEY = "你的API_KEY"
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"


@app.get("/fetch_news")
def fetch_news(country: str = "us", category: str = "business"):
    params = {
        "apiKey": NEWS_API_KEY,
        "country": country,
        "category": category,
        "pageSize": 10,
    }
    query = urlencode(params)
    with urlopen(f"{NEWS_API_URL}?{query}", timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("status") != "ok":
        return {"error": "无法获取新闻"}
    articles = data.get("articles", [])
    return {"news": [{"title": article["title"], "content": article.get("description") or ""} for article in articles]}


@app.get("/mobile", response_class=HTMLResponse)
def mobile_home():
    cards = "".join(
        f"""
        <a class=\"card {item['accent']}\" href=\"{item['href']}\" aria-label=\"打开{item['title']}\">
          <div class=\"card-row\">
            <div>
              <h2>{item['title']}</h2>
              <p>{item['subtitle']}</p>
            </div>
            <span class=\"arrow\" aria-hidden=\"true\">›</span>
          </div>
        </a>
        """
        for item in MOBILE_NAV_ITEMS
    )
    body = f"""
      <section class=\"hero\">
        <div class=\"eyebrow\">Mobile Gateway · Phase 1</div>
        <h1>AI投资驾驶舱</h1>
        <p class=\"lead\">面向 iPhone Safari 的 HTML5 移动入口。手机端负责展示与轻量触发，电脑端继续负责 AI 计算、复盘生成与本地数据服务。</p>
      </section>
      <section class=\"grid\" aria-label=\"移动端功能入口\">{cards}</section>
      <div class=\"notice\">仅作研究分析与系统演示，不构成任何交易建议。Phase 1 仅提供页面骨架与路由入口。</div>
    """
    return HTMLResponse(_mobile_shell("移动端首页", body))


@app.get("/mobile/recap", response_class=HTMLResponse)
def mobile_recap():
    return _render_mobile_placeholder("/mobile/recap")


@app.get("/mobile/screener", response_class=HTMLResponse)
def mobile_screener():
    return _render_mobile_placeholder("/mobile/screener")


@app.get("/mobile/news-recommend", response_class=HTMLResponse)
def mobile_news_recommend():
    return _render_mobile_placeholder("/mobile/news-recommend")


@app.get("/mobile/intel", response_class=HTMLResponse)
def mobile_intel():
    return _render_mobile_placeholder("/mobile/intel")


@app.get("/mobile/page/{page_name}", response_class=HTMLResponse, include_in_schema=False)
def mobile_legacy_placeholder(page_name: str):
    return _render_mobile_placeholder(f"/mobile/{page_name}")


def _render_mobile_placeholder(path: str) -> HTMLResponse:
    meta = MOBILE_PAGE_META.get(path, {"title": "移动端功能", "description": "该移动端功能将在后续阶段实现。"})
    body = f"""
      <section class=\"hero\">
        <div class=\"eyebrow\">Mobile Gateway · Coming Soon</div>
        <h1>{meta['title']}</h1>
        <p class=\"lead\">{meta['description']}</p>
      </section>
      <section class=\"placeholder\">
        <h2>Phase 1 已接入路由</h2>
        <p>当前阶段只交付移动端 HTML5 页面骨架和入口导航，业务数据读取、AI 调用与实时情报将在后续阶段逐步接入。</p>
      </section>
      <a class=\"back\" href=\"/mobile\">← 返回移动端首页</a>
    """
    return HTMLResponse(_mobile_shell(meta["title"], body))
