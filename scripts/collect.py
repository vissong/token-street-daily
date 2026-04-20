#!/usr/bin/env python3
"""
Token Street Daily — Data Collector with Time Filtering.

Reads config/sources.yaml, fetches from all enabled sources, applies strict
time-window filtering, outputs per-source .md + merged.json.

Usage:
    python3 scripts/collect.py --date 2026-04-20 --max-age-hours 48
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote_plus

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TENCENT_CLI = "/Users/vissong/.tencent-news-cli/bin/tencent-news-cli"


# ── Time helpers ──────────────────────────────────────────────────────

def parse_date(raw: str) -> datetime | None:
    """Parse various date formats into timezone-aware datetime."""
    if not raw:
        return None
    raw = raw.strip()
    # ISO format
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # RFC 2822 (RSS pubDate): "Mon, 14 Apr 2026 10:30:00 +0000"
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y %H:%M:%S %z",
    ]:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # Try dateutil as fallback
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    # Extract YYYY-MM-DD from string
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        try:
            return datetime(int(m[1]), int(m[2]), int(m[3]), tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def is_within_window(published_at: str, max_age_hours: int, now: datetime) -> bool:
    """Check if a date string is within the time window."""
    dt = parse_date(published_at)
    if dt is None:
        return False
    return (now - dt) <= timedelta(hours=max_age_hours)


def make_id(title: str, url: str) -> str:
    return hashlib.md5(f"{title}|{url}".encode()).hexdigest()[:12]


# ── RSS/Atom parser ──────────────────────────────────────────────────

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def fetch_url(url: str, timeout: int = 30) -> str | None:
    """Fetch URL content via curl."""
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A",
             "Mozilla/5.0 TokenStreetBot/1.0", url],
            capture_output=True, text=True, timeout=timeout + 10,
        )
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def parse_rss_items(xml_text: str, source_name: str, max_age_hours: int,
                    item_limit: int, now: datetime, lang: str) -> list[dict]:
    """Parse RSS/Atom XML and return time-filtered items."""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    # RSS 2.0
    for item in root.iter("item"):
        if len(items) >= item_limit:
            break
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate")
               or item.findtext("dc:date", namespaces=NS)
               or item.findtext("{http://purl.org/dc/elements/1.1/}date")
               or "")
        desc = (item.findtext("description") or "").strip()
        # Strip HTML tags from description
        desc = re.sub(r"<[^>]+>", "", desc).strip()[:300]

        if not title:
            continue
        if not is_within_window(pub, max_age_hours, now):
            continue

        dt = parse_date(pub)
        items.append({
            "title": title,
            "url": url,
            "source": source_name,
            "sources": [source_name],
            "published_at": dt.strftime("%Y-%m-%d") if dt else "",
            "language": lang,
            "summary": desc,
            "source_count": 1,
            "id": make_id(title, url),
        })

    # Atom
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        if len(items) >= item_limit:
            break
        title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = entry.find("{http://www.w3.org/2005/Atom}link")
        url = link_el.get("href", "") if link_el is not None else ""
        pub = (entry.findtext("{http://www.w3.org/2005/Atom}published")
               or entry.findtext("{http://www.w3.org/2005/Atom}updated")
               or "")
        summary = (entry.findtext("{http://www.w3.org/2005/Atom}summary") or "").strip()
        summary = re.sub(r"<[^>]+>", "", summary).strip()[:300]

        if not title:
            continue
        if not is_within_window(pub, max_age_hours, now):
            continue

        dt = parse_date(pub)
        items.append({
            "title": title,
            "url": url,
            "source": source_name,
            "sources": [source_name],
            "published_at": dt.strftime("%Y-%m-%d") if dt else "",
            "language": lang,
            "summary": summary,
            "source_count": 1,
            "id": make_id(title, url),
        })

    return items


# ── Web page scraper (non-RSS) ───────────────────────────────────────

def scrape_web_page(url: str, source_name: str, max_age_hours: int,
                    item_limit: int, now: datetime, lang: str) -> list[dict]:
    """Scrape a web page for article links and dates via Jina Reader."""
    jina_url = f"https://r.jina.ai/{url}"
    content = fetch_url(jina_url, timeout=30)
    if not content:
        content = fetch_url(url, timeout=30)
    if not content:
        return []

    items = []
    # Extract markdown-style links: [title](url) or ## title patterns
    lines = content.split("\n")
    current_title = ""
    current_url = ""
    for line in lines:
        # Markdown link
        m = re.search(r"\[([^\]]{10,})\]\((https?://[^\)]+)\)", line)
        if m:
            current_title = m.group(1).strip()
            current_url = m.group(2).strip()
        # Try to find date near the title
        dm = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2})", line)
        pub_date = dm.group(1).replace("/", "-") if dm else ""

        if current_title and current_url:
            if pub_date and not is_within_window(pub_date, max_age_hours, now):
                current_title = ""
                current_url = ""
                continue
            if pub_date or not items:  # Accept if has date, or as fallback
                items.append({
                    "title": current_title,
                    "url": current_url,
                    "source": source_name,
                    "sources": [source_name],
                    "published_at": pub_date or now.strftime("%Y-%m-%d"),
                    "language": lang,
                    "summary": "",
                    "source_count": 1,
                    "id": make_id(current_title, current_url),
                })
            current_title = ""
            current_url = ""
            if len(items) >= item_limit:
                break

    return items


# ── Source collectors ─────────────────────────────────────────────────

def collect_web(src: dict, max_age_hours: int, now: datetime) -> list[dict]:
    """Collect from a web/RSS source."""
    url = src["url"]
    # Template substitution
    date_str = now.strftime("%Y-%m-%d")
    url = url.replace("{{year-month}}", now.strftime("%Y-%m"))
    url = url.replace("{{date}}", date_str)
    name = src["name"]
    lang = src.get("language", "en")
    ext = src.get("extract", {})
    limit = ext.get("item_limit", 15)
    window = min(ext.get("time_window_hours", 48), max_age_hours)

    log(f"  Fetching {name}: {url}")
    content = fetch_url(url, timeout=ext.get("timeout_seconds", 30))
    if not content:
        log(f"  ⚠ {name}: fetch failed, trying Jina Reader")
        content = fetch_url(f"https://r.jina.ai/{url}", timeout=30)
    if not content:
        log(f"  ✗ {name}: all fetch methods failed")
        return []

    # Try RSS/Atom first
    if "<?xml" in content[:200] or "<rss" in content[:500] or "<feed" in content[:500]:
        items = parse_rss_items(content, name, window, limit, now, lang)
        log(f"  ✓ {name}: {len(items)} items (RSS)")
        return items

    # Fallback to web scraping
    items = scrape_web_page(url, name, window, limit, now, lang)
    log(f"  ✓ {name}: {len(items)} items (web scrape)")
    return items


def collect_cli(src: dict, max_age_hours: int, now: datetime) -> list[dict]:
    """Collect from a CLI source (tencent-news or follow-builders)."""
    name = src["name"]
    cmd = src["command"]
    lang = src.get("language", "zh")
    ext = src.get("extract", {})
    window = min(ext.get("time_window_hours", 48), max_age_hours)
    limit = ext.get("item_limit", 20)
    exclude_kw = ext.get("exclude_keywords", [])

    # Handle follow-builders separately (it's a Python script)
    if "fetch_follow_builders" in cmd:
        date_str = now.strftime("%Y-%m-%d")
        cmd_expanded = cmd.replace("{{date}}", date_str)
        log(f"  Running {name}: {cmd_expanded}")
        try:
            r = subprocess.run(
                cmd_expanded, shell=True, capture_output=True, text=True,
                timeout=120, cwd=str(PROJECT_ROOT),
            )
            if r.returncode != 0:
                log(f"  ⚠ {name}: exit code {r.returncode}")
        except Exception as e:
            log(f"  ✗ {name}: {e}")
        return []  # follow-builders writes its own output file

    # Tencent News CLI
    log(f"  Running {name}: {cmd}")
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            log(f"  ⚠ {name}: exit code {r.returncode}")
            return []
    except Exception as e:
        log(f"  ✗ {name}: {e}")
        return []

    items = []
    # Parse tencent-news-cli output (JSON or text)
    try:
        data = json.loads(r.stdout)
        news_list = data if isinstance(data, list) else data.get("data", data.get("news", []))
        if isinstance(news_list, dict):
            news_list = news_list.get("items", news_list.get("list", []))
    except json.JSONDecodeError:
        # Try line-by-line parsing
        news_list = []
        for line in r.stdout.strip().split("\n"):
            if line.strip():
                news_list.append({"title": line.strip()})

    for entry in news_list:
        if len(items) >= limit:
            break
        title = entry.get("title", "").strip()
        if not title:
            continue
        # Exclude financial spam
        if any(kw in title for kw in exclude_kw):
            continue

        url = entry.get("url", entry.get("link", ""))
        pub = entry.get("publishTime", entry.get("publish_time",
              entry.get("time", entry.get("date", ""))))
        source_name = entry.get("source", entry.get("media", name))

        if pub and not is_within_window(pub, window, now):
            continue

        dt = parse_date(pub) if pub else None
        items.append({
            "title": title,
            "url": url,
            "source": source_name if source_name != name else name,
            "sources": [name],
            "published_at": dt.strftime("%Y-%m-%d") if dt else now.strftime("%Y-%m-%d"),
            "language": lang,
            "summary": entry.get("summary", entry.get("desc", entry.get("abstract", "")))[:300],
            "source_count": 1,
            "id": make_id(title, url),
        })

    log(f"  ✓ {name}: {len(items)} items (CLI)")
    return items


def collect_search(src: dict, max_age_hours: int, now: datetime) -> list[dict]:
    """Collect from a search query via web_search (curl + Google)."""
    name = src["name"]
    query = src["query"]
    lang = src.get("language", "en")
    ext = src.get("extract", {})
    limit = ext.get("result_limit", 10)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    query = query.replace("{{yesterday}}", yesterday)

    log(f"  Searching {name}: {query}")
    # Use DuckDuckGo HTML as a simple search
    encoded = quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    content = fetch_url(url, timeout=20)
    if not content:
        log(f"  ✗ {name}: search failed")
        return []

    items = []
    # Parse DuckDuckGo HTML results
    results = re.findall(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.+?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(.+?)</a>',
        content, re.DOTALL,
    )
    if not results:
        # Alternative pattern
        results = re.findall(
            r'<a[^>]+href="(https?://[^"]+)"[^>]*class="result__a"[^>]*>(.*?)</a>',
            content,
        )

    for match in results[:limit]:
        if len(match) >= 3:
            url, title, snippet = match[0], match[1], match[2]
        elif len(match) == 2:
            url, title = match
            snippet = ""
        else:
            continue

        title = re.sub(r"<[^>]+>", "", title).strip()
        snippet = re.sub(r"<[^>]+>", "", snippet).strip()
        if not title:
            continue

        items.append({
            "title": title,
            "url": url,
            "source": name,
            "sources": [name],
            "published_at": now.strftime("%Y-%m-%d"),
            "language": lang,
            "summary": snippet[:300],
            "source_count": 1,
            "id": make_id(title, url),
        })

    log(f"  ✓ {name}: {len(items)} items (search)")
    return items


def collect_email(src: dict, max_age_hours: int, now: datetime) -> list[dict]:
    """Collect from Gmail via himalaya CLI."""
    name = src["name"]
    account = src.get("cli_account", "gmail")
    lang = src.get("language", "en")
    ext = src.get("extract", {})
    max_msgs = ext.get("max_messages", 30)
    newsletter_senders = ext.get("newsletter_senders", [])

    log(f"  Fetching {name}: himalaya envelopes")
    # Get envelope list
    for attempt in range(3):
        try:
            r = subprocess.run(
                ["himalaya", "envelope", "list",
                 "--folder", "AI Newsletter", "--page-size", str(max_msgs),
                 "--output", "json"],
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode == 0 and r.stdout.strip():
                break
        except Exception:
            pass
        log(f"  ⚠ {name}: retry {attempt+1}/3")
        time.sleep(3)
    else:
        log(f"  ✗ {name}: himalaya failed after 3 attempts")
        return []

    try:
        envelopes = json.loads(r.stdout)
    except json.JSONDecodeError:
        log(f"  ✗ {name}: invalid JSON from himalaya")
        return []

    items = []
    cutoff = now - timedelta(hours=max_age_hours)

    for env in envelopes:
        env_id = env.get("id", "")
        subject = env.get("subject", "").strip()
        date_str = env.get("date", "")
        sender = env.get("from", {})
        if isinstance(sender, dict):
            sender_name = sender.get("name", sender.get("addr", ""))
        elif isinstance(sender, list) and sender:
            sender_name = sender[0].get("name", sender[0].get("addr", ""))
        else:
            sender_name = str(sender)

        # Check date
        dt = parse_date(date_str)
        if dt and dt < cutoff:
            continue

        if not subject:
            continue

        # Read body
        body = ""
        tmp = f"/tmp/tsd_email_{env_id}.txt"
        for attempt in range(2):
            try:
                subprocess.run(
                    f'himalaya message read --folder "AI Newsletter" {env_id} > {tmp} 2>/dev/null',
                    shell=True, timeout=60,
                )
                body_path = Path(tmp)
                if body_path.exists() and body_path.stat().st_size > 0:
                    body = body_path.read_text(errors="replace")[:4000]
                    break
            except Exception:
                time.sleep(2)

        items.append({
            "title": subject,
            "url": "",
            "source": sender_name,
            "sources": [name],
            "published_at": dt.strftime("%Y-%m-%d") if dt else now.strftime("%Y-%m-%d"),
            "language": lang,
            "summary": body[:300].replace("\n", " "),
            "source_count": 1,
            "id": make_id(subject, str(env_id)),
        })

    log(f"  ✓ {name}: {len(items)} items (email)")
    return items


# ── Dedup ─────────────────────────────────────────────────────────────

def title_similarity(a: str, b: str) -> float:
    """Simple Jaccard similarity on character bigrams."""
    if not a or not b:
        return 0.0
    a_clean = re.sub(r"\W+", "", a.lower())
    b_clean = re.sub(r"\W+", "", b.lower())
    if not a_clean or not b_clean:
        return 0.0
    a_bi = {a_clean[i:i+2] for i in range(len(a_clean)-1)}
    b_bi = {b_clean[i:i+2] for i in range(len(b_clean)-1)}
    if not a_bi or not b_bi:
        return 0.0
    return len(a_bi & b_bi) / len(a_bi | b_bi)


def dedup_items(items: list[dict], threshold: float = 0.6) -> list[dict]:
    """Deduplicate items by title similarity."""
    deduped = []
    for item in items:
        is_dup = False
        for existing in deduped:
            if title_similarity(item["title"], existing["title"]) > threshold:
                # Merge sources
                for s in item["sources"]:
                    if s not in existing["sources"]:
                        existing["sources"].append(s)
                existing["source_count"] = len(existing["sources"])
                if len(item.get("summary", "")) > len(existing.get("summary", "")):
                    existing["summary"] = item["summary"]
                is_dup = True
                break
        if not is_dup:
            deduped.append(item)
    return deduped


# ── Categorize ────────────────────────────────────────────────────────

CAT_KEYWORDS = {
    "major-release": [
        "launch", "release", "announce", "发布", "推出", "上线", "正式",
        "GPT", "Claude", "Gemini", "o3", "o4", "Llama", "模型",
        "open source", "开源", "AGI",
    ],
    "industry-business": [
        "funding", "raise", "Series", "valuation", "acquire", "IPO",
        "融资", "估值", "收购", "合并", "营收", "partnership", "合作",
        "billion", "million", "亿",
    ],
    "research-frontier": [
        "paper", "research", "arxiv", "study", "benchmark", "论文",
        "研究", "突破", "algorithm", "SOTA", "attention", "transformer",
    ],
    "tools-release": [
        "tool", "API", "SDK", "framework", "plugin", "extension",
        "工具", "平台", "插件", "agent", "智能体", "workflow", "MCP",
        "IDE", "开发者", "developer",
    ],
    "policy-regulation": [
        "regulation", "policy", "law", "bill", "ban", "safety",
        "政策", "法规", "监管", "合规", "安全", "伦理", "治理",
    ],
}


def categorize(item: dict) -> str:
    """Assign a category based on title + summary keywords."""
    text = f"{item['title']} {item.get('summary', '')}".lower()
    scores = {}
    for cat, keywords in CAT_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw.lower() in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "tools-release"


# ── Output ────────────────────────────────────────────────────────────

def write_source_md(items: list[dict], source_name: str, output_dir: Path):
    """Write per-source markdown file."""
    path = output_dir / f"{source_name}.md"
    lines = [f"# {source_name}\n"]
    for item in items:
        lines.append(f"## {item['title']}")
        lines.append(f"- url: {item['url']}")
        lines.append(f"- source: {item['source']}")
        lines.append(f"- published_at: {item['published_at']}")
        if item.get("summary"):
            lines.append(f"\n{item['summary']}\n")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def log(msg: str):
    print(msg, file=sys.stderr)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Token Street Daily Collector")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                    help="Issue date (default: today)")
    ap.add_argument("--max-age-hours", type=int, default=48,
                    help="Max age of items in hours (default: 48)")
    ap.add_argument("--sources-config", default="config/sources.yaml",
                    help="Path to sources.yaml")
    ap.add_argument("--output-dir", default=None,
                    help="Output directory (default: data/raw/{date})")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data" / "raw" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load sources config
    config_path = PROJECT_ROOT / args.sources_config
    with open(config_path) as f:
        config = yaml.safe_load(f)
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]

    log(f"=== Token Street Daily Collector ===")
    log(f"Date: {args.date}")
    log(f"Max age: {args.max_age_hours}h")
    log(f"Enabled sources: {len(sources)}")
    log(f"Output: {output_dir}")
    log("")

    all_items: list[dict] = []
    source_stats: dict[str, int] = {}

    collectors = {
        "web": collect_web,
        "cli": collect_cli,
        "search": collect_search,
        "email": collect_email,
    }

    for src in sources:
        stype = src.get("type", "web")
        name = src["name"]
        collector = collectors.get(stype)
        if not collector:
            log(f"  ⚠ Unknown type '{stype}' for {name}, skipping")
            continue

        try:
            items = collector(src, args.max_age_hours, now)
            if items:
                write_source_md(items, name, output_dir)
                all_items.extend(items)
                source_stats[name] = len(items)
        except Exception as e:
            log(f"  ✗ {name}: exception: {e}")
            source_stats[name] = 0

    log(f"\n=== Pre-dedup: {len(all_items)} items ===")

    # Dedup
    all_items = dedup_items(all_items)
    log(f"=== Post-dedup: {len(all_items)} items ===")

    # Categorize
    for item in all_items:
        if "category" not in item:
            item["category"] = categorize(item)

    # Final time filter enforcement
    final = []
    cutoff = now - timedelta(hours=args.max_age_hours)
    for item in all_items:
        dt = parse_date(item.get("published_at", ""))
        if dt and dt < cutoff:
            continue
        final.append(item)

    log(f"=== Final (after strict time filter): {len(final)} items ===")

    # Sort by date descending
    final.sort(key=lambda x: x.get("published_at", ""), reverse=True)

    # Write merged.json
    merged_path = output_dir / "merged.json"
    merged_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"\n✓ Wrote {merged_path} ({len(final)} items)")

    # Summary
    log(f"\n=== Collection Summary ===")
    from collections import Counter
    cat_counts = Counter(i["category"] for i in final)
    date_counts = Counter(i["published_at"] for i in final)
    log(f"By category:")
    for cat, cnt in cat_counts.most_common():
        log(f"  {cat}: {cnt}")
    log(f"By date:")
    for d, cnt in sorted(date_counts.items(), reverse=True):
        log(f"  {d}: {cnt}")
    log(f"\nSources collected:")
    for name, cnt in sorted(source_stats.items(), key=lambda x: -x[1]):
        log(f"  {name}: {cnt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
