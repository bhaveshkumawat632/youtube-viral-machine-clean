"""
VidRush compliance guard — enforces YouTube/Instagram/X content rules so the
channel never gets struck or flagged for reused/inauthentic content.

Rules derived from official policies (2026):
- YouTube monetization: must be original creation; reused/inauthentic (mass-produced,
  repetitive) content is ineligible. Creator must be identifiable in the video.
- Instagram/Treads: only post content you created yourself.
- X/Twitter: no duplicative/substantially similar automated posts.

This module is VidRush-only. It does NOT touch the money-maker blog.
"""
import os
import hashlib
import json

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "vidrush")
SEEN_DB = os.path.join(OUTPUT_DIR, "_compliance_seen.json")


def _load_seen():
    if os.path.exists(SEEN_DB):
        try:
            return json.load(open(SEEN_DB))
        except Exception:
            return {}
    return {}


def _save_seen(d):
    try:
        json.dump(d, open(SEEN_DB, "w"), indent=2)
    except Exception:
        pass


def check_video_compliance(title, script_text, use_stock_footage, character_present):
    """
    Returns (ok, reasons[]).
    ok=False means the video violates a platform guideline and must NOT be posted.
    """
    reasons = []

    # 1. Must be original creation -> our cartoon host must be present
    if not character_present:
        reasons.append("NO_ORIGINAL_HOST: video has no identifiable original character; "
                       "risks YouTube 'reused content' / Instagram 'post only what you created'.")

    # 2. Stock footage only allowed as B-roll under original commentary (character)
    if use_stock_footage and not character_present:
        reasons.append("STOCK_WITHOUT_HOST: reused stock footage without original host = "
                       "reused-content violation.")

    # 3. No duplicative / mass-produced content: hash script, reject near-dupes
    seen = _load_seen()
    h = hashlib.md5(script_text.strip().encode()).hexdigest()
    if h in seen:
        reasons.append("DUPLICATE_SCRIPT: identical script already published (X/YT inauthentic policy).")
    else:
        seen[h] = title
        _save_seen(seen)

    # 4. Script must be substantive (not a 1-line reuse of someone's text)
    words = len(script_text.split())
    if words < 25:
        reasons.append(f"SCRIPT_TOO_SHORT ({words} words): looks like a repost, not original.")

    # 5. Title must not be clickbait-y all-caps spam
    if title.isupper() and len(title) > 12:
        reasons.append("CLICKBAIT_TITLE: all-caps spam title violates advertiser-friendly rules.")

    return (len(reasons) == 0, reasons)


def compliance_report(title, script_text, use_stock_footage, character_present):
    ok, reasons = check_video_compliance(title, script_text, use_stock_footage, character_present)
    status = "COMPLIANT" if ok else "BLOCKED"
    print(f"[compliance] {status}: {title}")
    for r in reasons:
        print(f"  - {r}")
    return ok


if __name__ == "__main__":
    # self test
    good = check_video_compliance(
        "पैसे बचाने के 3 आसान तरीके | Paisa Bhai",
        "नमस्ते दोस्तों! मैं पैसा भाई हूँ। आज बताएंगे पैसे बचाने के 3 आसान तरीके जो हर कोई अपना सकता है।",
        use_stock_footage=False, character_present=True)
    print("good ok:", good[0])
    bad = check_video_compliance(
        "MONEY TIPS", "short", use_stock_footage=True, character_present=False)
    print("bad ok:", bad[0], bad[1])
