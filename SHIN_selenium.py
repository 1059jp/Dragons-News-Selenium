import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
from datetime import timedelta, timezone
import json

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"

def build_summary(title):
    # 余計な装飾を消す
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    # 検索結果（新着順 st=n）を優先
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}

    # 履歴を読み込む
    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}

    current_stock = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ニュースのカードをすべて取得
        items = soup.find_all('li', class_=lambda x: x and 'sw-Card' in x)
        
        for item in items:
            title_tag = item.find('h3')
            link_tag = item.find('a')
            time_tag = item.find('span', class_=re.compile(r'time')) # 時間を取得
            
            if not title_tag or not link_tag: continue
            
            title = title_tag.get_text().strip()
            href = link_tag.get('href', '').split('?')[0]
            time_text = time_tag.get_text() if time_tag else ""

            # 記事IDを抽出
            aid_match = re.search(r'articles/([a-z0-9]+)', href)
            if not aid_match: continue
            aid = aid_match.group(1)

            # --- 判定1：日付チェック（古いニュースを捨てる） ---
            # 「日前」や「週前」が含まれていたら古いので無視
            if "日前" in time_text or "週前" in time_text or "ヶ月前" in time_text:
                continue

            # --- 判定2：キーワードと履歴チェック ---
            if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                if title not in history and aid not in history:
                    summary_text = build_summary(title)
                    # 新しい順にリストに追加
                    current_stock.append({
                        "summary": summary_text, 
                        "url": f"https://news.yahoo.co.jp/articles/{aid}",
                        "id": aid,
                        "time": time_text
                    })
                    # 履歴に即追加（次回出さないため）
                    history.add(title)
                    history.add(aid)
                    
    except Exception as e:
        print(f"Error: {e}")

    # 履歴を保存
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for item in sorted(history):
            f.write(f"{item}\n")
            
    return current_stock

def create_html(news_list):
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST).strftime('%m/%d %H:%M:%S')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズ速報</title>
        <style>
            body {{ font-family: sans-serif; background: #f0f2f5; padding: 10px; margin: 0; }}
            .header {{ background:#003399; color:white; padding:15px; text-align:center; border-radius: 8px; margin-bottom:15px; position: sticky; top: 0; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #003399; }}
            .time-label {{ font-size: 0.8em; color: #cc0000; font-weight: bold; margin-bottom: 5px; }}
            .summary-text {{ font-weight: bold; margin-bottom: 15px; white-space: pre-wrap; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1fr 50px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.9em; }}
            .read-btn {{ background: #e7efff; color: #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #ddd; color: #666; border: none; }}
            .card.done {{ display: none; }}
        </style>
        <script>
            function hide(el) {{ el.closest('.card').classList.add('done'); }}
        </script>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0;">🐉 今日のドラゴンズ ({now})</h2>
            <p style="font-size:0.8em; margin:5px 0 0;">一度出たニュースは、更新で消えます</p>
        </div>
    """
    for item in news_list:
        tweet_url = f"https://twitter.com/intent/tweet?text={requests.utils.quote(item['summary'] + chr(10) + item['url'])}"
        html_content += f"""
            <div class="card">
                <div class="time-label">🕒 {item['time']}</div>
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn" onclick="hide(this)">𝕏 ポスト</a>
                    <button class="btn delete-btn" onclick="hide(this)">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:50px; color:#666;'>新しいニュースはありません。<br>しばらく待ってから更新してください。</p>"
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
