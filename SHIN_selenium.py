import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
from datetime import timedelta, timezone
import json
import urllib.parse

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"
STOCK_FILE = "SHIN_stock.json"

def build_summary(title):
    # 余計な装飾をカット
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    text = text.replace("を発表", "を発表！").replace("が判明", "が判明...")
    if "ホームラン" in text: text = text.replace("ホームラン", "🚀ホームラン")
    if "勝利" in text: text = text.replace("勝利", "✨勝利")
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 日本時間の今日の日付 (例: 4/21)
    JST = timezone(timedelta(hours=+9), 'JST')
    now_jst = datetime.datetime.now(JST)
    today_str = now_jst.strftime('%-m/%-d')

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    stock = []
    # 実行のたびにストックをクリア（当日分のみを新鮮に保つため）
    # 過去分を残したい場合はここを読み込み処理に変えてください

    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all(class_=lambda x: x and 'sw-Card' in x)

        new_entries = []
        for item in items:
            # 時間ラベルの取得
            time_tag = item.find(class_=re.compile(r'time'))
            time_text = time_tag.get_text() if time_tag else ""

            # --- 【当日絞り込み判定：強化版】 ---
            # 「今日の日付」が含まれるか、「分前」「時間前」という相対表記なら「今日」とみなす
            is_today = (today_str in time_text) or ("分" in time_text) or ("時間" in time_text)
            
            if not is_today:
                continue

            link_tag = item.find('a')
            if not link_tag: continue
            
            href = link_tag.get('href', '').split('?')[0]
            title = item.get_text().strip()
            
            if len(title) < 10: continue

            if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                if title not in history and href not in history:
                    summary_text = build_summary(title)
                    stock.insert(0, {"summary": summary_text, "url": href})
                    new_entries.extend([title, href])
                    history.extend([title, href])

        if new_entries:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                for entry in new_entries: f.write(entry + "\n")
                
    except Exception as e:
        print(f"Error: {e}")
    
    stock = stock[:20]
    with open(STOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(stock, f, ensure_ascii=False, indent=4)
        
    return stock

def create_html(news_list):
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST).strftime('%m/%d %H:%M')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズ最新ニュース</title>
        <style>
            body {{ font-family: sans-serif; background: #f5f8fa; padding: 10px; margin: 0; }}
            .header {{ background:#003399; color:white; padding:15px; text-align:center; border-radius: 0 0 10px 10px; position: sticky; top: 0; z-index: 1000; }}
            .refresh-btn {{ margin-top:10px; padding:12px; border-radius:5px; border:none; background:white; color:#003399; font-weight:bold; cursor:pointer; width: 100%; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 5px solid #003399; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .summary-text {{ font-weight: bold; margin-bottom: 15px; line-height: 1.5; color: #1c1e21; white-space: pre-wrap; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1.2fr 50px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.85em; display: flex; align-items: center; justify-content: center; }}
            .read-btn {{ background: #f0f2f5; color: #003399; border: 1px solid #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #eeeeee; color: #666; border: none; }}
        </style>
        <script>
            function hideCard(el) {{
                el.closest('.card').style.display = 'none';
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0; font-size:1.1em;">🐉 ドラゴンズ新着 ({now})</h2>
            <button class="refresh-btn" onclick="location.reload()">🔄 表示を最新に更新</button>
        </div>
    """
    for item in news_list:
        tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(item['summary'] + chr(10) + item['url'])}"
        html_content += f"""
            <div class="card">
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn" onclick="hideCard(this)">𝕏 ポスト</a>
                    <button class="btn delete-btn" onclick="hideCard(this)">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:50px; color:#666;'>本日の新着ニュースはまだありません。</p>"
    html_content += "</body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print("Check finished.")
