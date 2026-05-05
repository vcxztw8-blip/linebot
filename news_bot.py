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
    {"name": "中央社", "url": "https://www.cna.com.tw/rss/aall.aspx"},
    {"name": "NHK Asia", "url": "https://www3.nhk.or.jp/rss/news/cat6.xml"},
]

TAIWAN_KEYWORDS = [
    "taiwan", "taipei", "台灣", "臺灣", "台北", "兩岸",
    "tsmc", "台積電", "民進黨", "國民黨", "總統", "立法院",
    "taiwanese", "cross-strait",
]

MAX_PER_SOURCE = 5  # 多抓一點，過濾後才夠

def is_taiwan_related(title, summary):
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in TAIWAN_KEYWORDS)

def fetch_news():
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y/%m/%d")
    taiwan_news = []
    other_news = []

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
            item = {
                "source": feed_info["name"],
                "title": title,
                "summary": summary,
                "link": link,
            }
            if is_taiwan_related(title, summary):
                taiwan_news.append(item)
            else:
                other_news.append(item)

    return today, taiwan_news, other_news

def build_message(today, taiwan_news, other_news):
    lines = [f"📰 每日新聞速報 {today}\n"]

    if taiwan_news:
        lines.append("🇹🇼 【台灣相關新聞】")
        for item in taiwan_news:
            lines.append(f"▍{item['title']}")
            if item["summary"]:
                lines.append(f"  {item['summary']}")
            lines.append(f"  🔗 {item['link']}\n")

    if other_news:
        lines.append("\n🌏 【國際新聞】")
        current_source = ""
        for item in other_news[:9]:  # 國際新聞最多9則
            if item["source"] != current_source:
                current_source = item["source"]
                lines.append(f"\n  [{current_source}]")
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
    today, taiwan_news, other_news = fetch_news()
    message = build_message(today, taiwan_news, other_news)
    print(message)
    send_line_message(message)
