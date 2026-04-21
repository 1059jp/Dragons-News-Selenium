import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
from datetime import timedelta, timezone
import urllib.parse

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"

def build_summary(title):
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    # 検索ワードをエンコードして確実にアクセス
    word = urllib.parse.quote("中日ドラゴンズ")
    url = f"https://news.yahoo.co.jp/search?p={word}&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"}

    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST)
    m = str(now.month)
    d = str(now.day)
    
    print(f"DEBUG: 検索ターゲット日付: {m}月{d}日")

    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}

    current_stock = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 特定のクラス名に依存せず、記事へのリンク（articles/を含むaタグ）をすべて探す
        links = soup.find_all('a', href=re.compile(r'news.yahoo.co.jp/articles/'))
        print(f"DEBUG: 発見したリンク総数: {len(links)}")

        for a in links:
            # 親要素を遡って、日付情報が入っている場所を探す
            parent = a.find_parent(['li', 'div', 'section'])
            if not parent: continue
            
            title = a.get_text().strip()
            if not title or len(title) < 5: continue
            
            # 日付らしきテキストを親要素から探す
            time_text = parent.get_text()
            
            # --- 判定1：今日の日付チェック ---
            if not (m in time_text and d in time_text):
                continue
            
            href = a.get('href').split('?')[0]
            aid_match = re.search(r'articles/([a-z0-9]+)', href)
            if not aid_match: continue
            aid = aid_match.group(1)

            # --- 判定2：中日関連か ---
            if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                if title not in history and aid not in history:
                    summary_text = build_summary(title)
                    current_stock.append({
                        "summary": summary_text,
                        "url": f"https://news.yahoo.co.jp/articles/{aid}",
                        "time": f"{m}/{d} 掲載"
                    })
                    history.add(title)
                    history.add(aid)
        
    except Exception as e:
        print(f"DEBUG: エラー発生: {e}")

    # 履歴保存
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
            .header {{ background:#003399; color:white; padding:15px; text-align:center; border-radius: 8px; margin-bottom:15px; position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            .refresh-btn {{ margin-top:10px; padding:12px; border-radius:8px; border:none; background:white; color:#003399; font-weight:bold; cursor:pointer; width: 100%; font-size: 1.1em; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #003399; }}
            .summary-text {{ font-weight: bold; margin-bottom: 15px; white-space: pre-wrap; color: #1c1e21; font-size: 1.05em; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1fr 60px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.9em; display: flex; align-items: center; justify-content: center; }}
            .read-btn {{ background: #e7efff; color: #003399; border: 1px solid #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #eeeeee; color: #666; border: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0; font-size:1.2em;">🐉 今日のドラゴンズ ({now})</h2>
            <button type="button" class="refresh-btn" onclick="window.location.reload(true);">🔄 最新ニュースを読み込む</button>
        </div>
    """
    for item in news_list:
        tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(item['summary'] + chr(10) + item['url'])}"
        html_content += f"""
            <div class="card">
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn" onclick="this.closest('.card').style.display='none'">𝕏 ポスト</a>
                    <button type="button" class="btn delete-btn" onclick="this.closest('.card').style.display='none'">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:50px; color:#666; background:white; border-radius:12px;'>今日の新着はありません。</p>"
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    current_news = get_dragons_news()
    create_html(current_news)
