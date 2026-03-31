#!/usr/bin/env python3
"""Cron job: fetch new articles, cleanup old ones, log stats."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import fetch_feeds, get_db
from datetime import datetime, timezone

def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    # Fetch new articles (includes cleanup)
    count = fetch_feeds()
    
    # Stats
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    fresh = db.execute("SELECT COUNT(*) FROM articles WHERE published > datetime('now', '-6 hours')").fetchone()[0]
    good = db.execute("SELECT COUNT(*) FROM articles WHERE score >= 60").fetchone()[0]
    hot = db.execute("SELECT COUNT(*) FROM articles WHERE score >= 80").fetchone()[0]
    db.close()
    
    print(f"[{ts}] +{count} new | {total} total | {fresh} <6h | {good} good+ | {hot} hot")

if __name__ == "__main__":
    main()
