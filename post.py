"""@ai.jugaaad auto-poster.

Posts the next unposted Reel from queue.json to Instagram via the official
Instagram API (Instagram Login), then adds the prompt as a comment.

Env vars:
  IG_ACCESS_TOKEN  long-lived Instagram user token (GitHub secret)
  VIDEO_BASE_URL   public base URL of docs/reels, e.g. https://USER.github.io/REPO/reels
  DRY_RUN=1        check token + show what would be posted, post nothing
  REFRESH_ONLY=1   refresh the token and print it to $GITHUB_OUTPUT (never to the log)
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

API = "https://graph.instagram.com/v26.0"
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
QUEUE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue.json")


def call(method, url, params=None):
    params = dict(params or {})
    data = None
    if method == "GET":
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        sys.exit(f"Instagram API error {e.code} on {url.split('?')[0]}: {body}")


def mask(s):
    return s[:6] + "..." if s else "(missing)"


def refresh():
    r = call("GET", "https://graph.instagram.com/refresh_access_token",
             {"grant_type": "ig_refresh_token", "access_token": TOKEN})
    new = r["access_token"]
    print(f"Token refreshed, valid ~{int(r.get('expires_in', 0)) // 86400} more days")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        print(f"::add-mask::{new}")
        with open(out, "a") as fh:
            fh.write(f"token={new}\n")


def main():
    if not TOKEN:
        sys.exit("IG_ACCESS_TOKEN is not set. Add it under repo Settings > Secrets > Actions.")
    if os.environ.get("REFRESH_ONLY") == "1":
        return refresh()

    me = call("GET", f"{API}/me", {"fields": "user_id,username"})
    ig_id = me.get("user_id") or me.get("id")
    print(f"Logged in as @{me.get('username')} (id {ig_id})")

    q = json.load(open(QUEUE, encoding="utf-8"))
    nxt = next((i for i in q["items"] if not i["posted"]), None)
    if not nxt:
        print("Queue empty: every Reel has been posted. Add new Reels to queue.json.")
        return

    base = os.environ.get("VIDEO_BASE_URL", "").rstrip("/")
    if not base:
        sys.exit("VIDEO_BASE_URL is not set.")
    video_url = f"{base}/{urllib.parse.quote(nxt['video'])}"
    print(f"Next: Reel {nxt['reel']:02d} -> {video_url}")

    lim = call("GET", f"{API}/{ig_id}/content_publishing_limit", {"fields": "quota_usage,config"})
    print(f"Publishing quota: {json.dumps(lim.get('data', lim))}")

    if os.environ.get("DRY_RUN") == "1":
        # also confirm the video URL is reachable, which is the most common setup mistake
        try:
            with urllib.request.urlopen(urllib.request.Request(video_url, method="HEAD"), timeout=30) as r:
                print(f"Video URL OK: {r.status} {r.headers.get('Content-Type')} {r.headers.get('Content-Length')} bytes")
        except Exception as e:
            sys.exit(f"Video URL not reachable ({e}). Is GitHub Pages enabled on /docs?")
        print("DRY RUN: nothing posted.")
        return

    c = call("POST", f"{API}/{ig_id}/media", {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": nxt["caption"],
        "share_to_feed": "true",
    })
    cid = c["id"]
    print(f"Container {cid} created, waiting for Instagram to process the video...")

    status = None
    for _ in range(40):  # up to ~10 minutes
        time.sleep(15)
        status = call("GET", f"{API}/{cid}", {"fields": "status_code,status"})
        code = status.get("status_code")
        print(f"  status: {code}")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"Processing failed: {status}")
    else:
        sys.exit("Timed out waiting for processing; will retry next run.")

    pub = call("POST", f"{API}/{ig_id}/media_publish", {"creation_id": cid})
    media_id = pub["id"]
    print(f"Published Reel {nxt['reel']:02d} as media {media_id}")

    nxt.update(posted=True, media_id=media_id,
               posted_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    json.dump(q, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if nxt.get("comment"):
        time.sleep(5)
        try:
            call("POST", f"{API}/{media_id}/comments", {"message": nxt["comment"][:2200]})
            print("Prompt comment added (pin it from the app if you want it on top).")
        except SystemExit as e:
            # the post is live; don't fail the run over the comment
            print(f"Comment not added: {e}")

    left = sum(not i["posted"] for i in q["items"])
    print(f"Done. {left} Reels left in the queue.")


if __name__ == "__main__":
    main()
