#!/usr/bin/env python3
"""
Fetch content from zarazhangrui/follow-builders and emit normalized item blocks.

This source tracks three feed files (feed-x.json, feed-blogs.json, feed-podcasts.json)
in a GitHub repo. Each file is updated daily with content from AI KOC/KOL builders.

Change detection: SHA-256 hashes of each file are stored in
  <cache-dir>/.hashes.json
Only files whose hash changed since the last run are processed. On a clean run
(no hash file), all files are processed.

Usage:
    python fetch_follow_builders.py --cache-dir site/data/sources/follow-builders \\
                                    --output site/data/raw/2026-04-19/follow-builders.md \\
                                    [--date 2026-04-19] \\
                                    [--recent-hours 24]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import textwrap
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_URL = "https://github.com/zarazhangrui/follow-builders.git"
FEED_FILES = ["feed-x.json", "feed-blogs.json", "feed-podcasts.json"]
HASH_FILE = ".hashes.json"


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_clone(repo_url: str, dest: Path) -> None:
    subprocess.run(["git", "clone", "--depth=1", repo_url, str(dest)], check=True)


def git_pull(repo_dir: Path) -> None:
    subprocess.run(["git", "-C", str(repo_dir), "pull", "--ff-only"], check=True)


def ensure_repo(cache_dir: Path) -> None:
    if (cache_dir / ".git").exists():
        git_pull(cache_dir)
    else:
        cache_dir.mkdir(parents=True, exist_ok=True)
        git_clone(REPO_URL, cache_dir)


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_hashes(cache_dir: Path) -> dict[str, str]:
    p = cache_dir / HASH_FILE
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def save_hashes(cache_dir: Path, hashes: dict[str, str]) -> None:
    (cache_dir / HASH_FILE).write_text(json.dumps(hashes, indent=2))


def changed_files(cache_dir: Path) -> list[str]:
    old = load_hashes(cache_dir)
    changed = []
    for fname in FEED_FILES:
        path = cache_dir / fname
        if not path.exists():
            continue
        h = file_sha256(path)
        if old.get(fname) != h:
            changed.append(fname)
    return changed


def commit_hashes(cache_dir: Path) -> None:
    new = {}
    for fname in FEED_FILES:
        p = cache_dir / fname
        if p.exists():
            new[fname] = file_sha256(p)
    save_hashes(cache_dir, new)


# ---------------------------------------------------------------------------
# Parsers — one per feed type
# ---------------------------------------------------------------------------

def _ts(value: str | None, fallback: str) -> str:
    if value:
        return value
    return fallback


def _is_recent(ts: str, recent_hours: int) -> bool:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - dt <= timedelta(hours=recent_hours)
    except Exception:
        return False


def _block(title: str, url: str, source_tag: str, published_at: str,
           fetched_at: str, recent: bool, summary: str) -> str:
    recent_line = "\n- recent: true" if recent else ""
    safe_summary = summary.strip().replace("\n", " ")
    wrapped = "\n".join(textwrap.wrap(safe_summary, width=100))
    return (
        f"## {title}\n"
        f"- url: {url}\n"
        f"- source: {source_tag}\n"
        f"- published_at: {published_at}\n"
        f"- fetched_at: {fetched_at}"
        f"{recent_line}\n\n"
        f"{wrapped}\n"
    )


def parse_x(data: dict, fetched_at: str, recent_hours: int) -> list[str]:
    blocks = []
    for builder in data.get("builders", data if isinstance(data, list) else []):
        handle = builder.get("handle", "unknown")
        name = builder.get("name", handle)
        for tweet in builder.get("tweets", []):
            text: str = tweet.get("text", "").strip()
            if not text:
                continue
            url = tweet.get("url", f"https://x.com/{handle}")
            created_at = tweet.get("createdAt", fetched_at)
            title = text[:80] + ("…" if len(text) > 80 else "")
            likes = tweet.get("likes", 0)
            rts = tweet.get("retweets", 0)
            engagement = f"[{name} @{handle} · ❤️{likes} 🔁{rts}]"
            summary = f"{engagement} {text}"
            blocks.append(_block(
                title=title,
                url=url,
                source_tag="follow-builders-x",
                published_at=created_at,
                fetched_at=fetched_at,
                recent=_is_recent(created_at, recent_hours),
                summary=summary,
            ))
    return blocks


def parse_blogs(data: dict, fetched_at: str, recent_hours: int) -> list[str]:
    blocks = []
    for item in data.get("blogs", []):
        title = item.get("title", "").strip()
        url = item.get("url", "")
        if not title or not url:
            continue
        published_at = item.get("publishedAt") or fetched_at
        author = item.get("author") or item.get("name", "")
        description = item.get("description", "").strip()
        content = item.get("content", "").strip()
        summary = description or content[:400] or title
        if author:
            summary = f"[{author}] {summary}"
        blocks.append(_block(
            title=title,
            url=url,
            source_tag="follow-builders-blogs",
            published_at=published_at,
            fetched_at=fetched_at,
            recent=_is_recent(published_at, recent_hours),
            summary=summary,
        ))
    return blocks


def parse_podcasts(data: dict, fetched_at: str, recent_hours: int) -> list[str]:
    blocks = []
    for item in data.get("podcasts", []):
        title = item.get("title", "").strip()
        url = item.get("url", "")
        if not title or not url:
            continue
        published_at = item.get("publishedAt") or fetched_at
        name = item.get("name", "")
        transcript = item.get("transcript", "").strip()
        summary = transcript[:400] if transcript else title
        if name:
            summary = f"[{name}] {summary}"
        blocks.append(_block(
            title=title,
            url=url,
            source_tag="follow-builders-podcasts",
            published_at=published_at,
            fetched_at=fetched_at,
            recent=_is_recent(published_at, recent_hours),
            summary=summary,
        ))
    return blocks


PARSERS = {
    "feed-x.json": parse_x,
    "feed-blogs.json": parse_blogs,
    "feed-podcasts.json": parse_podcasts,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", required=True,
                    help="Local directory to clone/pull the repo into")
    ap.add_argument("--output", required=True,
                    help="Output .md file path (site/data/raw/<date>/follow-builders.md)")
    ap.add_argument("--recent-hours", type=int, default=24)
    ap.add_argument("--force", action="store_true",
                    help="Process all files regardless of change detection")
    args = ap.parse_args()

    cache_dir = Path(args.cache_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Ensure repo is up to date
    print(f"Syncing {REPO_URL} → {cache_dir}", file=sys.stderr)
    try:
        ensure_repo(cache_dir)
    except subprocess.CalledProcessError as e:
        print(f"error: git operation failed: {e}", file=sys.stderr)
        return 2

    # 2. Detect changed files
    if args.force:
        to_process = [f for f in FEED_FILES if (cache_dir / f).exists()]
        print("--force: processing all files", file=sys.stderr)
    else:
        to_process = changed_files(cache_dir)
        if not to_process:
            print("No feed files changed since last run — skipping.", file=sys.stderr)
            # Write empty output so collect.log can record 0 items cleanly
            output_path.write_text("")
            return 0
        print(f"Changed files: {to_process}", file=sys.stderr)

    # 3. Parse each changed file
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_blocks: list[str] = []

    for fname in to_process:
        path = cache_dir / fname
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"warning: could not parse {fname}: {e}", file=sys.stderr)
            continue
        parser = PARSERS.get(fname)
        if parser is None:
            print(f"warning: no parser for {fname}", file=sys.stderr)
            continue
        blocks = parser(data, fetched_at, args.recent_hours)
        print(f"  {fname}: {len(blocks)} items", file=sys.stderr)
        all_blocks.extend(blocks)

    # 4. Write output
    output_path.write_text("\n".join(all_blocks), encoding="utf-8")
    print(f"✓ follow-builders: {len(all_blocks)} items → {output_path}", file=sys.stderr)

    # 5. Commit hashes so next run detects changes correctly
    commit_hashes(cache_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
