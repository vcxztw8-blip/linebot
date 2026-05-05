import feedparser
import requests
from datetime import datetime, timezone, timedelta
import os

LINE_TOKEN = os.environ["LINE_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

FEEDS = [
    {"name": "NHK World", "url": "https://www3.nhk.or.jp/rss/news/cat0.xml"},
    {"name": "公視新聞", "url": "https://news.pts.org.tw/xml/newsfeed.xml"},
    {"name": "BBC Asia", "url": "http://feeds.bbci.co.uk/news/asia/rss.xml"},
    {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews"},
]

MAX_PER_SOURCE = 3

def fetch_news():
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y/%m/%d")
    all_news = []
    for feed_info in FEEDS:
        feed = feedparser.parse(feed_info["url"])
        entries = feed.entries[:MAX_PER_SOURCE]
        for entry in entries:
            title = entry.get("title", "（無標題）")
            summary = entry.get("summary", "")
            summary = summary[:100].replace("\n", " ").strip()
            if summary and not summary.endswith("…"):
                summary += "…"
            link = entry.get("link", "")
            all_news.append({
                "source": feed_info["name"],
                "title": title,
                "summary": summary,
                "link": link,
            })
    return today, all_news

def build_message(today, news_list):
    lines = [f"📰 每日新聞速報 {today}\n"]
    current_source = ""
    for item in news_list:
        if item["source"] != current_source:
            current_source = item["source"]
            lines.append(f"\n【{current_source}】")
        lines.append(f"▍{item['title']}")
        if item["summary"]:
            lines.append(f"  {item['summary']}")
        lines.append(f"  🔗 {item['link']}\n")
    return "\n".join(lines)

def send_line_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}",
    }
    if len(text) > 4900:
        text = text[:4900] + "\n\n（訊息過長，已截斷）"
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}],
    }
    resp = requests.post(url, headers=headers, json=payload)
    print(f"LINE API 回應: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    today, news = fetch_news()
    message = build_message(today, news)
    print(message)
    send_line_message(message)
