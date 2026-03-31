"""GadgetFinder - Innovative Gadget News Aggregator."""

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from html import escape
from pathlib import Path
from urllib.parse import urlencode

import feedparser
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "gadgets.db"
FEEDS_PATH = BASE / "data" / "feeds.json"

CATEGORY_MAP = {
    "audio":     ("Audio",       "\U0001f3a7", "#6c3fa0", "#3a1f5e"),
    "wearables": ("Wearables",   "\u231a",     "#2e7d32", "#1b4d1e"),
    "mobile":    ("Mobile",      "\U0001f4f1", "#1565c0", "#0d3d75"),
    "smarthome": ("Smart Home",  "\U0001f3e0", "#e65100", "#8a3000"),
    "gaming":    ("Gaming",      "\U0001f3ae", "#c62828", "#771818"),
    "computer":  ("Computer",    "\U0001f4bb", "#37474f", "#1c2529"),
    "vr":        ("VR/AR",       "\U0001f97d", "#7b1fa2", "#4a1262"),
    "gadgets":   ("Gadgets",     "\U0001f4e6", "#455a64", "#263238"),
    "ai":        ("KI/AI",       "\U0001f916", "#00897b", "#004d40"),
    "quantum":   ("Quantum",     "\u269b\ufe0f", "#6a1b9a", "#38006b"),
    "science":   ("Forschung",   "\U0001f52c", "#1565c0", "#003c8f"),
}

PRICE_SEGMENTS = {
    "budget":   ("Budget (<200\u20ac)",     0,    199),
    "premium":  ("Premium (500\u20ac+)",  500,  99999),
    "highend":  ("High-End (1000\u20ac+)", 1000, 99999),
}

SCORE_BADGES = [
    (80, "Hot",  "#e74c3c"),
    (60, "Good", "#c9a84c"),
    (0,  "",     ""),
]

GADGET_CATEGORIES = {k: v for k, v in CATEGORY_MAP.items() if k != "ai"}

AI_SUBCATEGORIES = {
    "models":     ("\U0001f9e0 Modelle & Releases", [
        "gpt", "claude", "gemini", "llama", "mistral", "phi-", "qwen",
        "deepseek", "llm", "language model", "foundation model", "release",
        "parameter", "fine-tun", "training",
        "token", "context window", "multimodal model", "vision model",
    ]),
    "benchmarks": ("\U0001f4ca Benchmarks", [
        "benchmark", "leaderboard", "arena", "elo ", "ranking",
        "mmlu", "humaneval", "hellaswag", "gpqa", "math ", "aime",
        "lmsys", "chatbot arena", "open llm", "eval", "comparison",
        "performance", "score ", "accuracy", "outperform", "beats",
        "state of the art", "sota", "vs ", "head to head", "head-to-head",
        "persuasion benchmark", "coding benchmark", "reasoning benchmark",
    ]),
    "agentic":    ("\U0001f916 Agentic AI", [
        "agent", "agentic", "autonomous", "tool use", "function call",
        "planning", "reasoning", "chain of thought", "rag", "retrieval",
        "workflow", "orchestrat", "copilot", "assistant", "autonom",
        "mcp", "model context protocol",
    ]),
    "opensource":  ("\U0001f310 Open Source", [
        "open source", "open-source", "hugging face", "huggingface",
        "github", "apache", "mit license", "weights", "ollama",
        "local model", "self-host", "gguf", "ggml", "lora",
    ]),
    "europe":     ("\U0001f1ea\U0001f1fa Europa", [
        "europa", "europe", "eu ai act", "gdpr", "dsgvo", "aleph alpha",
        "mistral", "bruessel", "brussels", "regulation", "digital market",
        "european", "deutschland", "germany", "france", "frankreich",
        "handelsblatt", "heise", "golem", "t3n",
        "kuenstliche intelligenz", "ki-", " ki ",
        "datenschutz", "deepl", "sap", "siemens",
    ]),
    "hardware":   ("\u26a1 AI Hardware", [
        "gpu", "tpu", "npu", "nvidia", "h100", "h200", "b200", "blackwell",
        "a100", "chip", "accelerat", "data center", "datacenter", "silicon",
        "groq", "cerebras", "compute", "tensor", "cuda",
    ]),
    "multimedia": ("\U0001f3a8 Multimedia AI", [
        "image generat", "video generat", "text to image", "text to video",
        "diffusion", "stable diffusion", "midjourney", "dall-e", "dalle",
        "sora", "runway", "pika", "audio generat", "music generat",
        "voice clone", "tts", "speech", "suno", "udio", "flux",
    ]),
    "quantum":    ("\u269b\ufe0f Quantum", [
        "quantum", "qubit", "quantum computing", "quantum computer",
        "quantum advantage", "quantum error", "ibm quantum", "google quantum",
        "ionq", "rigetti", "iqm", "d-wave", "trapped ion", "superconducting",
        "topological", "photonic quantum", "quantum network", "quantum key",
    ]),
    "science":    ("\U0001f52c Forschung", [
        "research", "paper", "arxiv", "breakthrough", "scientific",
        "nature", "ieee", "published", "preprint", "benchmark",
        "state of the art", "scaling law", "emergent", "architecture",
        "supercomputer", "exascale", "neuromorphic", "semiconductor",
        "compute", "training run", "inference",
    ]),
}


# Region detection for AI articles
REGION_FILTERS = {
    "usa":   ("\U0001f1fa\U0001f1f8 USA", [
        "openai", "anthropic", "google", "meta ", "microsoft", "nvidia",
        "silicon valley", "san francisco", "washington", "california",
        "us ", "u.s.", "american", "apple", "amazon", "tesla",
        "congress", "senate", "white house", "pentagon", "darpa",
        "stanford", "mit ", "berkeley", "carnegie mellon",
    ]),
    "china": ("\U0001f1e8\U0001f1f3 China", [
        "china", "chinese", "beijing", "shanghai", "shenzhen", "alibaba",
        "baidu", "tencent", "huawei", "bytedance", "xiaomi", "deepseek",
        "qwen", "yi-", "zhipu", "moonshot", "01.ai", "minimax",
        "sensetime", "iflytek", "jinan", "wuhan",
        "pandaily", "south china",
    ]),
    "europe": ("\U0001f1ea\U0001f1fa Europa", [
        "europe", "european", "eu ", "eu-", "brussels", "bruessel",
        "gdpr", "dsgvo", "ai act", "digital market", "digital services",
        "mistral", "aleph alpha", "deepl", "sap", "siemens",
        "germany", "german", "deutschland", "france", "french",
        "uk ", "british", "london", "berlin", "paris", "amsterdam",
        "stockholm", "helsinki", "zurich", "switzerland", "swiss",
        "handelsblatt", "heise", "t3n", "golem", "sifted", "tech.eu",
        "kuenstliche intelligenz", "ki-", " ki ",
    ]),
    "regulation": ("\u2696\ufe0f Regulierung", [
        "regulation", "regulat", "compliance", "law ", "legal",
        "legislation", "policy", "governance", "ethics", "ethical",
        "ai act", "executive order", "copyright", "liability",
        "safety", "alignment", "guardrail", "oversight", "audit",
        "bias", "fairness", "transparency", "accountab",
        "gdpr", "dsgvo", "digital market", "antitrust",
        "ban ", "banned", "restrict", "prohibit",
    ]),
}

# Chinese sources auto-tag
_CHINA_SOURCES = {"pandaily (china tech)", "south china morning post ai", "tech in asia"}
_EUROPE_SOURCES = {"handelsblatt tech", "heise ki", "t3n", "golem.de", "sifted (eu tech)",
                   "tech.eu", "ai news eu", "google news ki de", "google news ai eu"}
_USA_SOURCES = {"openai blog", "google ai blog", "google research blog", "microsoft ai blog",
                "deepmind blog", "meta research"}

def detect_region(title, summary, source=""):
    """Detect regions for an article. Returns set of region keys."""
    text = f"{title} {summary or ''}".lower()
    src_lower = source.lower()
    regions = set()
    # Source-based auto-tag
    if src_lower in _CHINA_SOURCES:
        regions.add("china")
    if src_lower in _EUROPE_SOURCES:
        regions.add("europe")
    if src_lower in _USA_SOURCES:
        regions.add("usa")
    # Keyword-based detection
    for key, (_, keywords) in REGION_FILTERS.items():
        for kw in keywords:
            if kw in text or kw in src_lower:
                regions.add(key)
                break
    return regions


def detect_ai_subcategory(title, summary, source=""):
    """Detect AI subcategory from title+summary+source text. Returns key or None."""
    text = f"{title} {summary or ''} {source}".lower()
    # German sources = Europe
    german_sources = ["handelsblatt", "heise", "t3n", "golem", "smarthome assistent"]
    if any(gs in source.lower() for gs in german_sources):
        return "europe"
    best_key = None
    best_hits = 0
    for key, (_, keywords) in AI_SUBCATEGORIES.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_key = key
    return best_key


def deduplicate_articles(articles):
    """Multi-strategy dedup: first-6-words key + 4-word overlap check."""
    result = []
    seen_keys = {}     # first 6 words -> article
    seen_4w = set()    # 4-word sequences for cross-source dedup
    for a in articles:
        words = re.sub(r'[^\w\s]', '', a["title"].lower()).split()
        # Strategy 1: first 6 words as primary key
        key6 = " ".join(words[:6])
        if key6 in seen_keys:
            if a.get("score", 0) > seen_keys[key6].get("score", 0):
                result = [a if r is seen_keys[key6] else r for r in result]
                seen_keys[key6] = a
            continue
        # Strategy 2: check for 4-word overlapping sequences (catches Google News dupes)
        found_dup = False
        if len(words) >= 4:
            for i in range(min(len(words) - 3, 6)):  # check first 6 positions
                seq = " ".join(words[i:i+4])
                if seq in seen_4w and len(seq) > 12:  # skip short generic sequences
                    found_dup = True
                    break
        if found_dup:
            continue
        # Record sequences
        if len(words) >= 4:
            for i in range(min(len(words) - 3, 8)):
                seq = " ".join(words[i:i+4])
                if len(seq) > 12:
                    seen_4w.add(seq)
        seen_keys[key6] = a
        result.append(a)
    return result

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS articles (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
        source TEXT NOT NULL, category TEXT DEFAULT 'gadgets', brand TEXT,
        summary TEXT, image_url TEXT, published TEXT, fetched TEXT,
        score INTEGER DEFAULT 0
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_published ON articles(published DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON articles(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_brand ON articles(brand)")
    return conn

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config():
    with open(FEEDS_PATH) as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

_HIGH_VALUE = [
    ('breakthrough', 25), ('launches', 20), ('announced', 20), ('released', 20),
    ('review', 15), ('first look', 15), ('hands-on', 15), ('tested', 15),
    ('benchmark', 15), ('vs ', 12), ('comparison', 12),
    ('new model', 20), ('new feature', 15), ('update', 10),
    ('open source', 15), ('state of the art', 20), ('record', 15),
    ('exclusive', 15),
]
_LOW_VALUE = [
    ('how to', -15), ('guide', -10), ('tips', -10),
    ('deal', -20), ('sale', -20), ('discount', -20), ('save ', -20),
]
_POPULAR_SUBS = {
    'r/MachineLearning': 15, 'r/LocalLLaMA': 15, 'r/technology': 10,
    'r/gadgets': 10, 'r/singularity': 10, 'r/headphones': 8,
    'r/QuantumComputing': 10, 'r/ClaudeAI': 8, 'r/OpenAI': 8,
}

def compute_score(title, summary, source, brand, image_url, cfg):
    s = 0
    text = f"{title} {summary or ''}".lower()
    # Source tier
    tier_map = {f["name"]: f.get("tier", 3) for f in cfg["feeds"]}
    s += {1: 30, 2: 20, 3: 10}.get(tier_map.get(source, 3), 10)
    # Brand
    if brand:
        s += 15
    # Image
    if image_url:
        s += 10
    # Content signals
    for sig, pts in _HIGH_VALUE:
        if sig in text:
            s += pts
    for sig, pts in _LOW_VALUE:
        if sig in text:
            s += pts
    # Reddit community bonus
    if source.startswith('r/'):
        s += _POPULAR_SUBS.get(source, 5)
    # Reddit: treat as community signal, not primary news source
    # Cap Reddit base score — they shouldn't outrank actual journalism
    if source.startswith('r/'):
        s = min(s, 65)  # Hard cap before position bonus
        # Long titles = not a headline, it's a discussion post
        if len(title) > 150:
            s -= 15
        # Noise penalty for personal/discussion/question posts
        _REDDIT_NOISE = ['i just', 'i tried', 'i tested', 'i built', 'i made',
                         'i want', 'i need', 'my ', 'anyone', 'how do',
                         'how are you', 'what do you', 'which ', 'is it worth',
                         'should i ', 'help me ', 'does anyone', 'can someone',
                         'am i the only', 'tips on ', 'has anyone', 'looking for',
                         'thoughts on', 'unpopular opinion', 'rant', 'eli5',
                         '[d]', '[p]', 'rate my', 'system question',
                         'vs ', 'versus ']
        for rn in _REDDIT_NOISE:
            if rn in text:
                s -= 20
                break
    return max(0, min(200, s))

# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------

VR_SOURCES = {"Road to VR", "UploadVR"}

_GADGET_ONLY_SOURCES = {
    '9to5Google', '9to5Mac', 'China-Gadgets', 'Gadget Flow', 'Gear Patrol Tech',
    'Android Authority', 'Liliputing', 'Smarthome Assistent', 'Tom\'s Guide',
    'What Hi-Fi', 'SoundGuys', 'GSMArena', 'Wareable', 'Notebookcheck Reviews',
    'TechRadar Reviews', 'Wirecutter', 'MajorHiFi', 'Scarbir (TWS earbuds)',
    'r/gadgets', 'r/headphones', 'r/audiophile', 'r/Android', 'r/apple',
    'r/smarthome', 'r/homeassistant', 'r/hardware', 'r/nvidia',
}
_AI_STRONG_KW = ['artificial intelligence', 'machine learning', 'llm ', 'large language model',
                 'gpt-', 'claude ', 'gemini ', 'neural network', 'deep learning',
                 'transformer', 'quantum comput', 'openai', 'anthropic', 'deepmind']

def detect_category(title, summary, source, cfg):
    if source in VR_SOURCES:
        return "vr"
    text = f"{title} {summary or ''}".lower()
    for kw in ["vr headset", "mixed reality", "quest ", "vision pro",
                "ar glasses", "xr ", "spatial computing", "vr game"]:
        if kw in text:
            return "vr"
    # Gadget-only sources: only categorize as AI if strong AI signal
    if source in _GADGET_ONLY_SOURCES:
        has_strong_ai = any(kw in text for kw in _AI_STRONG_KW)
        if not has_strong_ai:
            # Skip AI keywords, only check gadget categories
            cat_remap = {"desk": "computer", "power": "computer"}
            for cat, kws in cfg["keywords"].items():
                if cat in ("ai", "quantum", "science"):
                    continue
                for kw in kws:
                    if kw.lower() in text:
                        mapped = cat_remap.get(cat, cat)
                        if mapped in CATEGORY_MAP:
                            return mapped
            return "gadgets"
    cat_remap = {"desk": "computer", "power": "computer"}
    for cat, kws in cfg["keywords"].items():
        for kw in kws:
            if kw.lower() in text:
                mapped = cat_remap.get(cat, cat)
                if mapped in CATEGORY_MAP:
                    return mapped
    return "gadgets"

# ---------------------------------------------------------------------------
# Brand detection
# ---------------------------------------------------------------------------

def detect_brand(title, summary, cfg):
    text = f"{title} {summary or ''}"
    for b in cfg["brands_watchlist"]:
        if b.lower() in text.lower():
            return b
    return None

# ---------------------------------------------------------------------------
# Price extraction
# ---------------------------------------------------------------------------

PRICE_RE = re.compile(
    r'(?:[\$\u20ac\u00a3])\s*(\d[\d,]*(?:\.\d{2})?)'
    r'|(\d[\d,]*(?:\.\d{2})?)\s*(?:\u20ac|dollars?|USD|EUR)',
    re.IGNORECASE,
)

def extract_price(title, summary):
    text = f"{title} {summary or ''}"
    for m in PRICE_RE.finditer(text):
        raw = m.group(1) or m.group(2)
        try:
            return int(float(raw.replace(",", "")))
        except (ValueError, TypeError):
            continue
    return None

# ---------------------------------------------------------------------------
# Noise filter
# ---------------------------------------------------------------------------

# Source blocklist: these generate too much low-value content via Google News
_SOURCE_BLOCKLIST = {
    "the motley fool", "motley fool", "yahoo finance", "aol.com",
    "cureus", "seeking alpha", "benzinga", "investopedia",
    "the globe and mail",  # syndicated Motley Fool
}

def _is_blocked_source(source_name):
    """Check if article comes from a blocked source (via Google/Bing News)."""
    return source_name.lower().strip() in _SOURCE_BLOCKLIST

def is_noise(title, cfg):
    t = title.lower()
    noise_hit = any(p in t for p in cfg["noise_patterns"])
    if not noise_hit:
        return False
    signals = sum(1 for s in cfg["product_signals"] if s in t)
    return signals < 2

# ---------------------------------------------------------------------------
# Feed fetcher
# ---------------------------------------------------------------------------

def fetch_feeds():
    cfg = load_config()
    db = get_db()
    # Auto-cleanup: delete articles older than 5 days, or low-score after 2 days
    cutoff_5d = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    cutoff_2d = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    db.execute("DELETE FROM articles WHERE published < ?", (cutoff_5d,))
    db.execute("DELETE FROM articles WHERE published < ? AND score < 40 AND vote = 0", (cutoff_2d,))
    db.commit()
    added = 0
    for feed_cfg in cfg["feeds"]:
        try:
            d = feedparser.parse(feed_cfg["url"])
        except Exception:
            continue
        for entry_idx, entry in enumerate(d.entries[:30]):
            url = getattr(entry, "link", "")
            if not url:
                continue
            aid = hashlib.md5(url.encode()).hexdigest()
            if db.execute("SELECT 1 FROM articles WHERE id=?", (aid,)).fetchone():
                continue
            title = getattr(entry, "title", "").strip()
            if not title or is_noise(title, cfg):
                continue
            summary_raw = getattr(entry, "summary", "") or ""
            summary = re.sub(r"<[^>]+>", "", summary_raw)[:300].strip()
            # For aggregator feeds (Google/Bing News), use original source name
            original_source = getattr(entry, "source", {})
            if hasattr(original_source, "get"):
                orig_name = original_source.get("title", "")
            elif hasattr(original_source, "title"):
                orig_name = original_source.title
            else:
                orig_name = str(original_source) if original_source else ""
            if orig_name and _is_blocked_source(orig_name):
                continue
            source = feed_cfg["name"]
            brand = detect_brand(title, summary, cfg)
            category = detect_category(title, summary, source, cfg)
            text = f"{title} {summary}".lower()
            has_keyword = any(
                kw.lower() in text
                for kws in cfg["keywords"].values()
                for kw in kws
            )
            if not brand and not has_keyword:
                continue
            image_url = None
            for link in getattr(entry, "links", []):
                if link.get("type", "").startswith("image"):
                    image_url = link["href"]
                    break
            if not image_url:
                for enc in getattr(entry, "enclosures", []):
                    if enc.get("type", "").startswith("image"):
                        image_url = enc.get("href") or enc.get("url")
                        break
            if not image_url:
                media = getattr(entry, "media_content", [])
                if media:
                    image_url = media[0].get("url")
            if not image_url:
                media_thumb = getattr(entry, "media_thumbnail", [])
                if media_thumb:
                    image_url = media_thumb[0].get("url")
            pub = getattr(entry, "published_parsed", None)
            if pub:
                published = datetime(*pub[:6], tzinfo=timezone.utc).isoformat()
            else:
                published = datetime.now(timezone.utc).isoformat()
            score = compute_score(title, summary, source, brand, image_url, cfg)
            # Reddit position bonus (reduced — Reddit is signal, not primary source)
            if source.startswith("r/"):
                position_bonus = max(0, 10 - entry_idx)  # #1 = +10, #5 = +5, #10 = 0
                score += position_bonus
            # Skip very low-quality articles
            if score < 15:
                continue
            try:
                db.execute(
                    "INSERT INTO articles (id,title,url,source,category,brand,summary,image_url,published,fetched,score) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (aid, title, url, source, category, brand, summary,
                     image_url, published, datetime.now(timezone.utc).isoformat(), score),
                )
                added += 1
            except sqlite3.IntegrityError:
                pass
    db.commit()
    db.close()
    return added

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(s):
    return escape(str(s)) if s else ""

def strip_dashes(s):
    return s.replace("\u2014", " ").replace("\u2013", " ") if s else s

def clean_reddit_title(title, source):
    """Clean Reddit titles: remove tags, truncate to headline length (max ~80 chars)."""
    if not source.startswith("r/"):
        return title
    t = title.strip()
    # Remove Reddit tags like [R], [D], [P], [N]
    t = re.sub(r'^\[([RDPN])\]\s*', '', t)
    # Already short enough
    if len(t) <= 80:
        return t
    # Cut at first sentence boundary (prefer short)
    for sep in ['. ', '! ', '? ', ' — ', ' - ']:
        idx = t.find(sep)
        if 15 < idx <= 80:
            return t[:idx + 1].rstrip()
    # Cut at colon if it's a headline pattern ("Topic: details")
    colon = t.find(': ')
    if 10 < colon <= 60:
        return t[:colon]
    # Cut at pipe/dash separator
    for sep in [' | ', ' — ', ' - ']:
        idx = t.find(sep)
        if 15 < idx <= 80:
            return t[:idx]
    # Fallback: word boundary at 80 chars
    cut = t[:80].rsplit(' ', 1)[0]
    return cut + "…"

def format_date(iso):
    try:
        dt = datetime.fromisoformat(iso)
    except (ValueError, TypeError):
        return ""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now.date() - dt.date()
    if diff.days == 0:
        hours = int((now - dt).total_seconds() / 3600)
        if hours < 1:
            return "Gerade eben"
        return f"Heute (vor {hours}h)"
    if diff.days == 1:
        return "Gestern"
    if diff.days < 7:
        days_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        return f"{days_de[dt.weekday()]} (vor {diff.days} Tagen)"
    return dt.strftime("%d.%m.%Y")

def score_badge(score):
    for threshold, label, color in SCORE_BADGES:
        if score >= threshold:
            return label, color
    return "Low", "#555"

BASE_PATH = os.environ.get("BASE_PATH", "")  # Set to "/gadgetfinder" when behind Caddy

def build_filter_url(current_params, key, value):
    params = dict(current_params)
    if value is None or params.get(key) == value:
        params.pop(key, None)
    else:
        params[key] = value
    base = BASE_PATH + "/"
    if not params:
        return base
    return base + "?" + urlencode(params)

def price_badge(price):
    if price is None:
        return ""
    if price >= 1000:
        return (f'<span style="background:#8b5e0a;color:#ffd;font-size:11px;'
                f'padding:2px 6px;border-radius:4px;margin-left:4px">{price}\u20ac</span>')
    if price >= 500:
        return (f'<span style="background:#5a3e0a;color:#ffd;font-size:11px;'
                f'padding:2px 6px;border-radius:4px;margin-left:4px">{price}\u20ac</span>')
    return (f'<span style="background:#333;color:#aaa;font-size:11px;'
            f'padding:2px 6px;border-radius:4px;margin-left:4px">{price}\u20ac</span>')

# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

CSS = """
:root{
  --bg:#000000;--card:#1c1c1e;--text:#f5f5f7;--secondary:#8e8e93;
  --accent:#0a84ff;--border:rgba(255,255,255,0.08);--hover:rgba(255,255,255,0.04);
  --glass:rgba(0,0,0,0.72);--glass-border:rgba(255,255,255,0.1);
  --chip-bg:rgba(255,255,255,0.06);--chip-border:rgba(255,255,255,0.1);
  --score-hot:#ff453a;--score-good:#ffd60a;--score-mid:#8e8e93;--score-low:#48484a;
  --brand-bg:rgba(10,132,255,0.12);--brand-text:#64b5f6;
}
[data-theme='light']{
  --bg:#f2f2f7;--card:#ffffff;--text:#1d1d1f;--secondary:#8e8e93;
  --accent:#007aff;--border:rgba(0,0,0,0.06);--hover:rgba(0,0,0,0.03);
  --glass:rgba(242,242,247,0.72);--glass-border:rgba(0,0,0,0.06);
  --chip-bg:rgba(0,0,0,0.04);--chip-border:rgba(0,0,0,0.08);
  --score-hot:#ff3b30;--score-good:#ff9f0a;--score-mid:#8e8e93;--score-low:#c7c7cc;
  --brand-bg:rgba(0,122,255,0.1);--brand-text:#007aff;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text',system-ui,sans-serif;
  font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
  overflow-x:hidden}
a{color:var(--text);text-decoration:none}
.wrap{max-width:1280px;margin:0 auto;padding:0 16px 48px;overflow:hidden}
/* Header */
.topbar{position:sticky;top:0;z-index:200;
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  background:var(--glass);border-bottom:1px solid var(--glass-border);
  padding:12px 16px;display:flex;align-items:center;justify-content:space-between}
.topbar-logo{font-size:17px;font-weight:700;letter-spacing:-0.3px;color:var(--text)}
.topbar-actions{display:flex;align-items:center;gap:8px}
.topbar-btn{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;background:var(--chip-bg);border:1px solid var(--chip-border);
  cursor:pointer;color:var(--secondary);font-size:16px;transition:all .2s ease}
.topbar-btn:hover{background:var(--hover);color:var(--text)}
/* Search */
.search-wrap{position:sticky;top:57px;z-index:190;
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  background:var(--glass);overflow:hidden;
  max-height:0;opacity:0;transition:max-height .3s ease,opacity .2s ease,padding .3s ease;padding:0 16px}
.search-wrap.open{max-height:60px;opacity:1;padding:8px 16px 10px}
.search-input{width:100%;padding:8px 14px;border-radius:10px;border:1px solid var(--border);
  background:var(--card);color:var(--text);font-size:15px;outline:none;
  font-family:inherit;transition:border-color .2s ease}
.search-input::placeholder{color:var(--secondary)}
.search-input:focus{border-color:var(--accent)}
/* Tabs */
.tabs{display:flex;gap:4px;padding:16px 16px 0;justify-content:center}
.segment{display:flex;background:var(--chip-bg);border-radius:10px;padding:2px;width:100%;max-width:320px}
.tab-btn{flex:1;padding:8px 0;border-radius:8px;font-size:15px;font-weight:600;
  text-align:center;color:var(--secondary);transition:all .2s ease;border:none;background:none}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{background:var(--accent);color:#fff}
/* Chips */
.chip-row{display:flex;gap:8px;overflow-x:auto;padding:12px 16px 4px;scrollbar-width:none;
  -ms-overflow-style:none;justify-content:center;flex-wrap:wrap}
.chip-row::-webkit-scrollbar{display:none}
@media(max-width:767px){.chip-row{flex-wrap:nowrap;justify-content:flex-start}}
.chip{display:inline-flex;align-items:center;padding:6px 16px;border-radius:20px;
  font-size:13px;font-weight:500;white-space:nowrap;background:var(--chip-bg);color:var(--secondary);
  border:1px solid var(--chip-border);transition:all .2s ease}
.chip:hover{color:var(--text);border-color:var(--accent)}
.chip.on{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
/* Hero card */
.hero-row{display:grid;grid-template-columns:1fr;gap:12px;margin:16px 0;align-items:start}
@media(min-width:768px){.hero-row{grid-template-columns:1fr 1fr}}
@media(min-width:1200px){.hero-row{grid-template-columns:2fr 1fr 1fr}}
.hero{border-radius:16px;overflow:hidden;position:relative;background:var(--card);min-width:0}
.hero-img-wrap{position:relative;width:100%;overflow:hidden}
.hero img{width:100%;height:100%;object-fit:cover;display:block}
.hero-placeholder{width:100%;padding:20px 0;display:flex;align-items:center;
  justify-content:center;font-size:40px}
.hero-overlay{padding:12px 16px 14px}
.hero-overlay h2{font-size:16px;font-weight:700;line-height:1.3;color:#f0f0f0;margin-bottom:4px}
.hero-overlay h2 a{color:#f0f0f0}
.hero-overlay-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:rgba(255,255,255,0.7)}
.hero-score{display:inline-block;padding:3px 8px;border-radius:6px;
  font-size:11px;font-weight:600;color:#fff}
.hero-source{font-size:12px;color:rgba(255,255,255,0.6)}
/* Card grid */
.card-grid{display:grid;grid-template-columns:1fr;gap:8px}
@media(min-width:768px){.card-grid{grid-template-columns:repeat(2,1fr);gap:12px}}
@media(min-width:1200px){.card-grid{grid-template-columns:repeat(3,1fr);gap:14px}}
/* Cards */
.card{padding:14px 16px;background:var(--card);border-radius:16px;
  display:flex;align-items:flex-start;gap:12px;min-width:0;
  transition:transform .2s ease,box-shadow .2s ease;border:1px solid var(--border)}
.card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.2)}
.card-emoji{width:52px;height:52px;border-radius:12px;display:flex;align-items:center;
  justify-content:center;font-size:24px;flex-shrink:0}
.card-content{flex:1;min-width:0}
.card-title{font-size:15px;font-weight:600;line-height:1.4;margin-bottom:4px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word}
.card-title a{color:var(--text);transition:color .2s ease}
.card-title a:hover{color:var(--accent)}
.card-summary{font-size:13px;color:var(--secondary);line-height:1.45;margin-bottom:8px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word}
.card-bottom{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:12px;color:var(--secondary)}
.card-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.card-vote{display:flex;gap:4px;margin-left:auto;flex-shrink:0}
.vote-btn{text-decoration:none;font-size:16px;opacity:.25;transition:all .2s ease;
  padding:2px 4px;border-radius:6px}
.vote-btn:hover{opacity:.7;background:var(--hover)}
.vote-btn.voted{opacity:1}
.vote-btn.voted-down{opacity:1}
/* Badges */
.badge{padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;letter-spacing:0.2px}
.badge-score{color:#fff}
.badge-brand{background:var(--brand-bg);color:var(--brand-text)}
.badge-new{background:rgba(255,214,10,0.12);color:#ffd60a}
/* Date separator */
.date-sep{font-size:12px;font-weight:500;color:var(--secondary);
  margin:20px 0 10px;padding-left:4px;display:flex;align-items:center;gap:10px;
  grid-column:1/-1}
.date-sep::after{content:'';flex:1;height:1px;background:var(--border)}
/* Footer */
.footer{text-align:center;padding:32px 0 16px;font-size:13px;color:var(--secondary)}
.footer a{color:var(--accent);transition:opacity .2s}
.footer a:hover{opacity:.7}
/* Empty state */
.empty{text-align:center;padding:48px 16px;color:var(--secondary);font-size:15px}
"""

# Topic-aware emoji mapping for richer visual variety
TOPIC_EMOJIS = {
    # AI subcategories
    "models": ("\U0001f9e0", "#00897b", "#004d40"),
    "benchmarks": ("\U0001f4ca", "#ff6f00", "#e65100"),
    "agentic": ("\U0001f916", "#1565c0", "#0d3d75"),
    "opensource": ("\U0001f310", "#2e7d32", "#1b4d1e"),
    "europe": ("\U0001f1ea\U0001f1fa", "#003399", "#001a4d"),
    "hardware": ("\u26a1", "#e65100", "#8a3000"),
    "multimedia": ("\U0001f3a8", "#7b1fa2", "#4a1262"),
    "quantum": ("\u269b\ufe0f", "#6a1b9a", "#38006b"),
    "science": ("\U0001f52c", "#1565c0", "#003c8f"),
    # Brand-specific emojis
    "Apple": ("\U0001f34e", "#555555", "#333333"),
    "Google": ("\U0001f50d", "#1a73e8", "#0d47a1"),
    "Samsung": ("\U0001f4f1", "#1428a0", "#0b1a6e"),
    "Sony": ("\U0001f3ae", "#00439c", "#002266"),
    "Microsoft": ("\U0001f4bb", "#00a4ef", "#005a8c"),
    "NVIDIA": ("\u26a1", "#76b900", "#4a7500"),
    "Meta": ("\U0001f97d", "#0668e1", "#034699"),
    "OpenAI": ("\u2728", "#10a37f", "#076650"),
    "Anthropic": ("\U0001f9e0", "#d4a574", "#8a6a4a"),
}

def get_article_emoji(article):
    """Get emoji + colors for an article based on category, subcategory, and brand."""
    cat = article.get("category", "gadgets")
    # For AI articles, use subcategory colors
    if cat in ("ai", "quantum", "science"):
        subcat = detect_ai_subcategory(article.get("title", ""), article.get("summary", ""), article.get("source", ""))
        if subcat and subcat in TOPIC_EMOJIS:
            return TOPIC_EMOJIS[subcat]
    # Brand-specific emoji
    brand = article.get("brand")
    if brand and brand in TOPIC_EMOJIS:
        return TOPIC_EMOJIS[brand]
    # Fallback to category
    info = CATEGORY_MAP.get(cat, CATEGORY_MAP["gadgets"])
    return info[1], info[2], info[3]

def render_placeholder(category, variant="card"):
    info = CATEGORY_MAP.get(category, CATEGORY_MAP["gadgets"])
    icon, c1, c2 = info[1], info[2], info[3]
    return (f'<div class="{variant}-placeholder" '
            f'style="background:linear-gradient(135deg,{c1},{c2})">{icon}</div>')

def render_hero(article, params):
    title = esc(strip_dashes(clean_reddit_title(article["title"], article.get("source", ""))))
    badge_label, badge_color = score_badge(article["score"])
    cat_info = CATEGORY_MAP.get(article["category"], CATEGORY_MAP["gadgets"])
    emoji, c1, c2 = get_article_emoji(article)
    img_html = f'<div class="hero-placeholder" style="background:linear-gradient(135deg,{c1},{c2})">{emoji}</div>'
    brand_html = (f'<span class="badge badge-brand">{esc(article["brand"])}</span>'
                  if article["brand"] else "")
    return f'''<div class="hero">
  <a href="{esc(article["url"])}" target="_blank" rel="noopener">{img_html}</a>
  <div class="hero-overlay">
    <h2><a href="{esc(article["url"])}" target="_blank" rel="noopener">{title}</a></h2>
    <div class="hero-overlay-meta">
      <span>{esc(article["source"])}</span>
      {brand_html}
      <span>{cat_info[1]} {cat_info[0]}</span>
      {"<span class='hero-score' style='background:" + badge_color + "'>" + badge_label + "</span>" if badge_label else ""}
    </div>
  </div>
</div>'''

def render_card(article):
    title = esc(strip_dashes(clean_reddit_title(article["title"], article.get("source", ""))))
    summary = esc(strip_dashes(article["summary"] or ""))
    price = extract_price(article["title"], article["summary"])
    badge_label, badge_color = score_badge(article["score"])
    cat_info = CATEGORY_MAP.get(article["category"], CATEGORY_MAP["gadgets"])
    source_color = cat_info[2]
    emoji, c1, c2 = get_article_emoji(article)
    brand_html = (f' <span class="badge badge-brand">{esc(article["brand"])}</span>'
                  if article["brand"] else "")
    is_new = False
    try:
        pub = datetime.fromisoformat(article["published"])
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        is_new = (datetime.now(timezone.utc) - pub).total_seconds() < 86400
    except (ValueError, TypeError):
        pass
    new_html = ' <span class="badge badge-new">Neu</span>' if is_new else ""
    price_html = ""
    if price is not None:
        price_html = f" &middot; {price}\u20ac"
    date_str = format_date(article.get("published", ""))
    return f'''<div class="card" data-searchable>
  <div class="card-emoji" style="background:linear-gradient(135deg,{c1},{c2})">{emoji}</div>
  <div class="card-content">
    <div class="card-title"><a href="{esc(article["url"])}" target="_blank" rel="noopener">{title}</a></div>
    <div class="card-summary">{summary}</div>
    <div class="card-bottom">
      <span class="card-dot" style="background:{source_color}"></span>
      <span>{esc(article["source"])}</span>
      {brand_html}
      {"<span class='badge badge-score' style='background:" + badge_color + "'>" + badge_label + " " + str(article["score"]) + "</span>" if badge_label else ""}
      {new_html}
      <span>{date_str}{price_html}</span>
      <span class="card-vote">
        <a href="{BASE_PATH}/vote/{article["id"]}/up" class="vote-btn{" voted" if article.get("vote") == 1 else ""}" title="Relevant">\U0001f44d</a>
        <a href="{BASE_PATH}/vote/{article["id"]}/down" class="vote-btn{" voted-down" if article.get("vote") == -1 else ""}" title="Irrelevant">\U0001f44e</a>
      </span>
    </div>
  </div>
</div>'''

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="GadgetFinder", docs_url=None, redoc_url=None)


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def index(request: Request):
    params = dict(request.query_params)
    active_tab = params.get("tab", "ai")
    active_cat = params.get("cat")
    active_brand = params.get("brand")
    active_sub = params.get("sub")
    active_region = params.get("region")

    cfg = load_config()
    db = get_db()

    rows = db.execute("SELECT * FROM articles ORDER BY score DESC, published DESC LIMIT 500").fetchall()
    all_articles = []
    now_ts = datetime.now(timezone.utc)
    for r in rows:
        a = dict(r)
        # Vote boost: Oliver's ratings override algorithm
        vote = a.get("vote", 0)
        if vote == 1:
            a["score"] = a.get("score", 0) + 50
        elif vote == -1:
            a["score"] = max(0, a.get("score", 0) - 30)
        # Recency boost: fresh articles get boost, old ones decay
        # Reddit gets half the recency boost (community signal, not breaking news)
        try:
            pub = datetime.fromisoformat(a.get("published", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            age_hours = (now_ts - pub).total_seconds() / 3600
            is_reddit = a.get("source", "").startswith("r/")
            if age_hours < 6:
                a["score"] += 15 if is_reddit else 30
            elif age_hours < 12:
                a["score"] += 10 if is_reddit else 20
            elif age_hours < 24:
                a["score"] += 5 if is_reddit else 12
            elif age_hours < 48:
                a["score"] += 2 if is_reddit else 5
            elif age_hours > 96:
                a["score"] -= 15
        except (ValueError, TypeError):
            pass
        # Cap display score at 100
        a["score"] = min(100, a["score"])
        # Only show Good (60+) and Hot (80+) articles — no mid/low noise
        if a["score"] < 60 and vote != 1:
            continue
        all_articles.append(a)
    db.close()

    # Split into AI vs Gadgets
    if active_tab == "ai":
        ai_cats = {"ai", "quantum", "science"}
        articles = [a for a in all_articles if a["category"] in ai_cats]
        # Apply AI subcategory filter
        if active_sub and active_sub in AI_SUBCATEGORIES:
            articles = [a for a in articles
                        if detect_ai_subcategory(a["title"], a["summary"], a.get("source","")) == active_sub]
        # Apply region filter
        if active_region and active_region in REGION_FILTERS:
            articles = [a for a in articles
                        if active_region in detect_region(a["title"], a["summary"], a.get("source",""))]
    else:
        articles = [a for a in all_articles if a["category"] not in {"ai", "quantum", "science"}]
        # Apply category filter
        if active_cat and active_cat in GADGET_CATEGORIES:
            articles = [a for a in articles if a["category"] == active_cat]
        # Apply brand filter
        if active_brand:
            articles = [a for a in articles
                        if a["brand"] and a["brand"].lower() == active_brand.lower()]

    # Deduplicate
    articles = sorted(articles, key=lambda a: (-a["score"], a.get("published", "")))
    articles = deduplicate_articles(articles)

    # Sort: score DESC, then published DESC (ISO strings sort lexicographically)
    articles.sort(key=lambda a: (-a["score"], a.get("published", "") or ""), reverse=False)
    # Reverse published within same score: negate won't work on strings, use two stable sorts
    articles.sort(key=lambda a: a.get("published", "") or "", reverse=True)
    articles.sort(key=lambda a: a["score"], reverse=True)

    feed = articles[:80]

    # Brand chips (gadgets tab only)
    top_brands = []
    if active_tab == "gadgets":
        brand_counts = {}
        for a in articles:
            if a["brand"]:
                brand_counts[a["brand"]] = brand_counts.get(a["brand"], 0) + 1
        top_brands = sorted(brand_counts.keys(),
                            key=lambda b: brand_counts[b], reverse=True)[:12]

    # Count for header
    ai_cats = {"ai", "quantum", "science"}
    ai_count = sum(1 for a in all_articles if a["category"] in ai_cats)
    gadget_count = sum(1 for a in all_articles if a["category"] not in ai_cats)

    # Count feeds for footer
    try:
        feed_count = len(cfg.get("feeds", []))
    except Exception:
        feed_count = 0

    # Build HTML
    tab_ai_url = build_filter_url({}, "tab", "ai")
    tab_gadgets_url = build_filter_url({}, "tab", "gadgets")

    parts = [f'''<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#000000">
<title>Gadgetfinder</title>
<style>{CSS}</style>
</head>
<body>

<div class="topbar">
  <span class="topbar-logo">Gadgetfinder</span>
  <div class="topbar-actions">
    <button class="topbar-btn" id="searchToggle" aria-label="Suche" onclick="toggleSearch()">
      <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    </button>
    <button class="topbar-btn" id="themeToggle" aria-label="Design wechseln" onclick="toggleTheme()">
      <span id="themeIcon">\U0001f319</span>
    </button>
  </div>
</div>

<div class="search-wrap" id="searchWrap">
  <input class="search-input" id="searchInput" type="text"
    placeholder="Suche in {len(articles)} Artikeln..."
    oninput="filterCards(this.value)"
    onkeydown="if(event.key==='Escape')closeSearch()">
</div>

<div class="tabs">
  <div class="segment">
    <a class="tab-btn{" active" if active_tab == "ai" else ""}" href="{tab_ai_url}">KI & AI ({ai_count})</a>
    <a class="tab-btn{" active" if active_tab == "gadgets" else ""}" href="{tab_gadgets_url}">Gadgets ({gadget_count})</a>
  </div>
</div>
''']

    # Filter chips
    if active_tab == "ai":
        # Subcategory chips
        parts.append('<div class="chip-row">')
        base_params = dict(params)
        base_params["tab"] = "ai"
        base_params.pop("cat", None)
        base_params.pop("brand", None)
        sub_base = {k: v for k, v in base_params.items() if k != "sub"}
        parts.append(f'<a class="chip{"" if active_sub else " on"}" '
                     f'href="{build_filter_url(sub_base, "sub", None)}">Alle</a>')
        for skey, (slabel, _) in AI_SUBCATEGORIES.items():
            on = " on" if active_sub == skey else ""
            href = build_filter_url(sub_base, "sub", skey)
            parts.append(f'<a class="chip{on}" href="{href}">{slabel}</a>')
        parts.append('</div>')
        # Region chips (second row)
        parts.append('<div class="chip-row" style="padding-top:4px">')
        reg_base = {k: v for k, v in base_params.items() if k != "region"}
        parts.append(f'<a class="chip{"" if active_region else " on"}" '
                     f'href="{build_filter_url(reg_base, "region", None)}">\U0001f30d Alle Regionen</a>')
        for rkey, (rlabel, _) in REGION_FILTERS.items():
            on = " on" if active_region == rkey else ""
            href = build_filter_url(reg_base, "region", rkey)
            parts.append(f'<a class="chip{on}" href="{href}">{rlabel}</a>')
        parts.append('</div>')
    else:
        parts.append('<div class="chip-row">')
        base_params = {"tab": "gadgets"}
        parts.append(f'<a class="chip{"" if active_cat else " on"}" '
                     f'href="{build_filter_url(base_params, "cat", None)}">Alle</a>')
        for ckey, cinfo in GADGET_CATEGORIES.items():
            on = " on" if active_cat == ckey else ""
            href = build_filter_url(base_params, "cat", ckey)
            parts.append(f'<a class="chip{on}" href="{href}">{cinfo[1]} {cinfo[0]}</a>')
        parts.append('</div>')

        if top_brands:
            parts.append('<div class="chip-row">')
            parts.append(f'<a class="chip{"" if active_brand else " on"}" '
                         f'href="{build_filter_url(base_params, "brand", None)}">Alle Marken</a>')
            for b in top_brands:
                on = " on" if active_brand and active_brand.lower() == b.lower() else ""
                href = build_filter_url(base_params, "brand", b)
                parts.append(f'<a class="chip{on}" href="{href}">{esc(b)}</a>')
            parts.append('</div>')

    parts.append('<div class="wrap">')

    if not feed:
        parts.append('<div class="empty">Keine Artikel gefunden. Versuche andere Filter.</div>')
    else:
        # Hero row: top 3 articles
        hero_count = min(3, len(feed))
        heroes = feed[:hero_count]
        rest = feed[hero_count:]

        parts.append('<div class="hero-row">')
        for h in heroes:
            parts.append(render_hero(h, params))
        parts.append('</div>')

        parts.append('<div class="card-grid">')
        for a in rest:
            parts.append(render_card(a))
        parts.append('</div>')

    parts.append(f'''
<div class="footer">
  {feed_count} Quellen &middot;
  <a href="{BASE_PATH}/refresh">Aktualisieren</a> &middot;
  <a href="{BASE_PATH}/stats">Quellen-Report</a>
</div>
</div>

<script>
(function(){{
  var html=document.documentElement;
  var saved=localStorage.getItem('gf-theme');
  if(saved)html.setAttribute('data-theme',saved);
  else if(window.matchMedia&&window.matchMedia('(prefers-color-scheme:light)').matches)html.setAttribute('data-theme','light');
  updateIcon();
  function updateIcon(){{
    var icon=document.getElementById('themeIcon');
    if(icon)icon.textContent=html.getAttribute('data-theme')==='light'?'\u2600\ufe0f':'\U0001f319';
  }}
  window.toggleTheme=function(){{
    var cur=html.getAttribute('data-theme');
    var next=cur==='light'?'dark':'light';
    html.setAttribute('data-theme',next);
    localStorage.setItem('gf-theme',next);
    updateIcon();
  }};
  window.toggleSearch=function(){{
    var w=document.getElementById('searchWrap');
    var inp=document.getElementById('searchInput');
    if(w.classList.contains('open')){{closeSearch();return;}}
    w.classList.add('open');
    inp.focus();
  }};
  window.closeSearch=function(){{
    var w=document.getElementById('searchWrap');
    var inp=document.getElementById('searchInput');
    w.classList.remove('open');
    inp.value='';
    filterCards('');
  }};
  window.filterCards=function(q){{
    q=q.toLowerCase();
    var cards=document.querySelectorAll('[data-searchable]');
    var hero=document.querySelector('.hero');
    for(var i=0;i<cards.length;i++){{
      var t=cards[i].textContent.toLowerCase();
      cards[i].style.display=(!q||t.indexOf(q)!==-1)?'':'none';
    }}
    if(hero){{
      var ht=hero.textContent.toLowerCase();
      hero.style.display=(!q||ht.indexOf(q)!==-1)?'':'none';
    }}
    var seps=document.querySelectorAll('.date-sep');
    for(var j=0;j<seps.length;j++){{
      if(!q){{seps[j].style.display='';continue;}}
      var next=seps[j].nextElementSibling;
      var hasVisible=false;
      while(next&&!next.classList.contains('date-sep')){{
        if(next.style.display!=='none'&&(next.hasAttribute('data-searchable')||next.classList.contains('hero')))hasVisible=true;
        next=next.nextElementSibling;
      }}
      seps[j].style.display=hasVisible?'':'none';
    }}
  }};
}})();
</script>
</body>
</html>''')

    resp = HTMLResponse("".join(parts))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


@app.get("/refresh")
def refresh():
    count = fetch_feeds()
    return RedirectResponse(f"{BASE_PATH}/?refreshed={count}", status_code=303)


@app.get("/vote/{article_id}/{direction}")
def vote(article_id: str, direction: str, request: Request):
    """Daumen hoch (+1) oder runter (-1) fuer einen Artikel."""
    if direction not in ("up", "down"):
        return {"ok": False}
    val = 1 if direction == "up" else -1
    db = get_db()
    db.execute("UPDATE articles SET vote = ? WHERE id = ?", (val, article_id))
    # Update source stats
    row = db.execute("SELECT source FROM articles WHERE id = ?", (article_id,)).fetchone()
    if row:
        source = row[0]
        db.execute("""INSERT INTO source_stats (source, total_shown, upvotes, downvotes)
            VALUES (?, 0, 0, 0) ON CONFLICT(source) DO NOTHING""", (source,))
        if val == 1:
            db.execute("UPDATE source_stats SET upvotes = upvotes + 1 WHERE source = ?", (source,))
        else:
            db.execute("UPDATE source_stats SET downvotes = downvotes + 1 WHERE source = ?", (source,))
        stats = db.execute("SELECT upvotes, downvotes FROM source_stats WHERE source = ?", (source,)).fetchone()
        total_votes = (stats[0] or 0) + (stats[1] or 0)
        rate = (stats[0] or 0) / total_votes if total_votes > 0 else 0
        db.execute("UPDATE source_stats SET approval_rate = ? WHERE source = ?", (round(rate, 3), source))
    db.commit()
    db.close()
    return RedirectResponse(request.headers.get("referer", f"{BASE_PATH}/"), status_code=303)


@app.get("/stats")
def source_stats_page():
    """Wochenbericht: Welche Quellen performen gut/schlecht?"""
    db = get_db()
    # Aggregate votes per source
    stats = db.execute("""
        SELECT source,
            COUNT(*) as total,
            SUM(CASE WHEN vote = 1 THEN 1 ELSE 0 END) as ups,
            SUM(CASE WHEN vote = -1 THEN 1 ELSE 0 END) as downs,
            SUM(CASE WHEN vote = 0 THEN 1 ELSE 0 END) as unrated
        FROM articles
        GROUP BY source
        ORDER BY total DESC
    """).fetchall()
    db.close()

    rows_html = ""
    for s in stats:
        total_votes = (s[2] or 0) + (s[3] or 0)
        rate = round((s[2] or 0) / total_votes * 100) if total_votes > 0 else -1
        if rate >= 70:
            color = "#2e7d32"
            label = "Gut"
        elif rate >= 40:
            color = "#c9a84c"
            label = "OK"
        elif rate >= 0 and total_votes > 0:
            color = "#c62828"
            label = "Schlecht"
        else:
            color = "#555"
            label = "Keine Votes"
        rows_html += f'''<tr>
            <td>{escape(s[0])}</td><td>{s[1]}</td>
            <td style="color:#2e7d32">{s[2] or 0}</td>
            <td style="color:#c62828">{s[3] or 0}</td>
            <td>{s[4] or 0}</td>
            <td style="color:{color};font-weight:600">{rate}% {label if total_votes > 0 else label}</td>
        </tr>'''

    return HTMLResponse(f"""<!DOCTYPE html><html lang="de"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gadgetfinder: Quellen-Report</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#08080c;color:#e0dcd4;padding:1rem}}
.w{{max-width:700px;margin:0 auto}}
h1{{font-size:1.2rem;margin-bottom:.5rem;color:#c9a84c}}
p{{font-size:.8rem;color:#888;margin-bottom:1rem}}
a{{color:#c9a84c;text-decoration:none}}
table{{width:100%;border-collapse:collapse;font-size:.8rem}}
th{{text-align:left;padding:.5rem;border-bottom:1px solid #222;color:#888;font-weight:500}}
td{{padding:.4rem .5rem;border-bottom:1px solid #111}}
tr:hover{{background:#111}}
</style></head><body>
<div class="w">
<h1>📊 Quellen-Report</h1>
<p>Bewertungen deiner Artikel-Votes. Quellen mit niedriger Zustimmungsrate (&lt;40%) sollten evaluiert werden. <a href="{BASE_PATH}/">Zurueck</a></p>
<table>
<tr><th>Quelle</th><th>Artikel</th><th>👍</th><th>👎</th><th>Unbewertet</th><th>Zustimmung</th></tr>
{rows_html}
</table>
</div></body></html>""")


@app.get("/api/health")
def health():
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    voted = db.execute("SELECT COUNT(*) FROM articles WHERE vote != 0").fetchone()[0]
    db.close()
    return {"status": "ok", "articles": count, "voted": voted}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3023)
