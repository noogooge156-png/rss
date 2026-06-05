import os
import json
import requests
import feedparser

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BLOGS_FILE = "blogs.json"
SEEN_FILE = "seen_posts.json"


def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def load_json(path: str, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_blogs() -> None:
    blogs = load_json(BLOGS_FILE, [])
    seen_posts: list = load_json(SEEN_FILE, [])
    seen_set = set(seen_posts)
    new_seen = []

    for blog in blogs:
        name = blog["name"]
        rss_url = blog["rss"]
        print(f"[INFO] 확인 중: {name} ({rss_url})")

        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"[ERROR] RSS 파싱 실패 ({name}): {e}")
            continue

        for entry in feed.entries:
            link = entry.get("link", "")
            title = entry.get("title", "(제목 없음)").strip()

            if not link:
                continue

            if link not in seen_set:
                print(f"[NEW] {title}")
                message = (
                    f"📢 <b>[{name}]</b> 새 글이 올라왔어요!\n\n"
                    f"📝 <b>{title}</b>\n"
                    f"🔗 {link}"
                )
                try:
                    send_telegram(message)
                    print(f"[SENT] 텔레그램 전송 완료: {title}")
                except Exception as e:
                    print(f"[ERROR] 텔레그램 전송 실패: {e}")

                seen_set.add(link)
                new_seen.append(link)

    # 기존 목록 + 신규 항목 저장 (최대 500개 유지)
    updated = list(seen_set)[-500:]
    save_json(SEEN_FILE, updated)
    print(f"[INFO] 완료. 신규 글 {len(new_seen)}개 발견.")


if __name__ == "__main__":
    check_blogs()
