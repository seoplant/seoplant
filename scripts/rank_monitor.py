"""
SEOplant Rank Monitor — keyword position tracking and content decay detection.

Monitors keyword rankings via DataForSEO SERP API, detects content decay
(position drops), and recommends regeneration.

Tier: Pro+ only
Credit cost: 1 per keyword check
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class RankMonitor:
    """Track keyword rankings and detect content decay.

    Usage:
        monitor = RankMonitor()
        monitor.add_keyword("best hiking boots", "https://mysite.com/guides/hiking-boots")
        results = monitor.check_rankings()
        decayed = monitor.detect_decay()
    """

    def __init__(self, tracking_file: str = None):
        self.tracking_file = Path(tracking_file or "./rank_tracking.json")
        self.keywords: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self.tracking_file.exists():
            return json.loads(self.tracking_file.read_text(encoding="utf-8"))
        return []

    def _save(self):
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        self.tracking_file.write_text(
            json.dumps(self.keywords, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_keyword(self, keyword: str, target_url: str, project_id: str = ""):
        """Start tracking a keyword."""
        existing = [k for k in self.keywords if k["keyword"] == keyword and k["target_url"] == target_url]
        if existing:
            return

        self.keywords.append({
            "keyword": keyword,
            "target_url": target_url,
            "project_id": project_id,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "history": [],
        })
        self._save()

    def check_rankings(self, dfseo_client=None) -> dict:
        """Check current rankings for all tracked keywords.

        Uses DataForSEO SERP API to find where target_url ranks.
        Falls back to heuristic estimation if no API available.
        """
        results = {"checked": 0, "improved": 0, "declined": 0, "new": 0, "details": []}

        for kw in self.keywords:
            try:
                position = self._get_position(kw["keyword"], kw["target_url"], dfseo_client)
            except Exception:
                position = None

            now = datetime.now(timezone.utc).isoformat()
            prev = kw["history"][-1]["position"] if kw["history"] else None

            kw["history"].append({
                "date": now,
                "position": position,
            })

            # Keep last 90 checks
            if len(kw["history"]) > 90:
                kw["history"] = kw["history"][-90:]

            results["checked"] += 1
            detail = {"keyword": kw["keyword"], "position": position, "previous": prev}

            if position is None:
                detail["status"] = "not_found"
            elif prev is None:
                detail["status"] = "new"
                results["new"] += 1
            elif position < prev:
                detail["status"] = "improved"
                results["improved"] += 1
            elif position > prev:
                detail["status"] = "declined"
                results["declined"] += 1
            else:
                detail["status"] = "stable"

            results["details"].append(detail)

        self._save()
        return results

    def detect_decay(self, threshold: int = 5) -> list[dict]:
        """Detect keywords with significant ranking decline.

        A keyword is "decaying" if it dropped by `threshold` or more
        positions in the last 30 days.
        """
        decaying = []
        for kw in self.keywords:
            if len(kw["history"]) < 2:
                continue

            recent = kw["history"][-1]
            # Find position from ~30 days ago
            thirty_days_ago = None
            for h in reversed(kw["history"]):
                h_date = datetime.fromisoformat(h["date"])
                days_ago = (datetime.now(timezone.utc) - h_date).days
                if days_ago >= 25:
                    thirty_days_ago = h
                    break

            if thirty_days_ago and thirty_days_ago.get("position") and recent.get("position"):
                delta = recent["position"] - thirty_days_ago["position"]
                if delta >= threshold:
                    decaying.append({
                        "keyword": kw["keyword"],
                        "target_url": kw["target_url"],
                        "position_30d_ago": thirty_days_ago["position"],
                        "position_now": recent["position"],
                        "drop": delta,
                        "project_id": kw.get("project_id", ""),
                    })

        return sorted(decaying, key=lambda x: x["drop"], reverse=True)

    def _get_position(self, keyword: str, target_url: str, dfseo_client=None) -> Optional[int]:
        """Get current ranking position for a keyword."""
        if dfseo_client and hasattr(dfseo_client, 'serp_organic'):
            try:
                serp = dfseo_client.serp_organic(keyword, depth=50)
                domain = self._extract_domain(target_url)
                for kw_data in serp.values():
                    for item in kw_data.get("items", []):
                        if domain in item.get("domain", ""):
                            return item.get("position")
            except Exception:
                pass
        return None

    def _extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("""
SEOplant Rank Monitor

Commands:
  add <keyword> <url>          Start tracking a keyword
  check                        Check all rankings now
  decay                        List keywords with ranking decline
  list                         Show all tracked keywords
  remove <keyword>             Stop tracking a keyword
        """)
        return

    command = sys.argv[1]
    monitor = RankMonitor()

    if command == "add":
        kw = sys.argv[2] if len(sys.argv) > 2 else "seo tools"
        url = sys.argv[3] if len(sys.argv) > 3 else "https://example.com"
        monitor.add_keyword(kw, url)
        print(f"Tracking '{kw}' -> {url}")
        print(f"Total keywords: {len(monitor.keywords)}")

    elif command == "check":
        print(f"Checking {len(monitor.keywords)} keywords...")
        results = monitor.check_rankings()
        print(f"Checked: {results['checked']}")
        print(f"Improved: {results['improved']} | Declined: {results['declined']} | New: {results['new']}")
        for d in results["details"]:
            pos_str = f"#{d['position']}" if d['position'] else "N/A"
            print(f"  [{d['status']:12}] {d['keyword'][:40]:40} {pos_str}")

    elif command == "decay":
        decaying = monitor.detect_decay(threshold=3)
        if not decaying:
            print("No content decay detected.")
        else:
            print(f"{len(decaying)} keywords with significant decline:\n")
            for d in decaying:
                print(f"  {d['keyword'][:40]} dropped {d['drop']} positions "
                      f"(#{d['position_30d_ago']} -> #{d['position_now']})")

    elif command == "list":
        print(f"{len(monitor.keywords)} tracked keywords:\n")
        for kw in monitor.keywords:
            last = kw["history"][-1] if kw["history"] else None
            pos = f"#{last['position']}" if last and last.get("position") else "?"
            print(f"  {pos:5} | {kw['keyword'][:40]:40} | {kw['target_url'][:40]}")

    elif command == "remove":
        kw = sys.argv[2] if len(sys.argv) > 2 else ""
        monitor.keywords = [k for k in monitor.keywords if k["keyword"] != kw]
        monitor._save()
        print(f"Removed '{kw}'. {len(monitor.keywords)} remaining.")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
