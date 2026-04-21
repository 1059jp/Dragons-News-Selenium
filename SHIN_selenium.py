import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
from datetime import timedelta, timezone
import json

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"
STOCK_FILE = "SHIN_stock.json"

def build_summary(title):
    # タイトルから余計な情報を削除
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    # 検索とトピックス、両方の口から入れる
    urls = [
        "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n",
        "https://news.yahoo.co.jp/topics/dragons"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    # 履歴の読み込み（セット形式で高速化）
    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}

    # 現在のストック（未処理分）
    stock = []
    if os.path.exists(STOCK_FILE):
        with open(STOCK_FILE, "r", encoding="utf-8") as f:
            try: stock = json.load(f)
            except: stock = []

    new_found_count = 0
    for target_url in urls:
        try:
            res = requests.get(target_url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # リンク要素を広範囲に探す
            links = soup.find_all('a', href=re.compile(r'articles/'))

            for link in links:
                href = link.get('href', '')
                title = link.get_text().strip()
                
                # 記事IDを抽出
                match = re.search(r'articles/([a-z0-9]+)', href)
                if not match: continue
                aid = match.group(1)

                # 「中日」か「ドラ」が含まれているか
                if not any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                    continue
                
                # 履歴チェック（タイトルかID、どちらかがあればスキップ）
                if title in history or aid in history:
                    continue

                # 新着として登録
                summary_text = build_summary(title)
                clean_url = f"https://news.yahoo.co.jp/articles/{aid}"
                
                # ストックの先頭に追加
                stock.insert(0, {"summary": summary_text, "url": clean_url, "id": aid})
                history.add(title)
                history.add(aid)
                new_found_count += 1
        except Exception as e:
            print(f"Error checking {target_url}: {e}")

    # 履歴ファイルを更新（全上書きして確実に保存）
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for item in sorted(history):
            f.write(f"{item}\n")
    
    # ストックは最大50件に
    stock = stock[:50]
    with open(STOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(stock, f, ensure_ascii=False, indent=4)
        
    return stock

def create_html(news_list):
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST).strftime('%m/%d %H:%M:%S')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Cache-Control" content="no-cache">
        <title>中日ドラゴンズ ニュースパネル</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f0f2f5; padding: 10px; margin: 0; }}
            .header {{ background:#003399; color:white; padding:15px; margin-bottom:15px; text-align:center; border-radius: 8px; position: sticky; top: 0; z-index: 100; }}
            .refresh-btn {{ margin-top:10px; padding:12px; border-radius:5px; border:none; background:white; color:#003399; font-weight:bold; cursor:pointer; width: 100%; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 6px solid #003399; }}
            .summary-text {{ font-size: 1.05em; font-weight: bold; margin-bottom: 15px; line-height: 1.5; color: #1c1e21; white-space: pre-wrap; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1fr 60px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.85em; display: flex; align-items: center; justify-content: center; }}
            .read-btn {{ background: #e7efff; color: #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #f0f2f5; color: #666; border: none; }}
            .card.done {{ display: none; }}
        </style>
        <script>
            function handleAction(el) {{
                const card = el.closest('.card');
                card.style.opacity = '0.3';
                card.classList.add('done');
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0; font-size:1.1em;">🐉 ドラゴンズ情報 ({now})</h2>
            <button class="refresh-btn" onclick="location.reload()">🔄 最新に更新する</button>
        </div>
    """
    for item in news_list:
        tweet_text = f"{item['summary']}\n{item['url']}"
        tweet_url = f"https://twitter.com/intent/tweet?text={requests.utils.quote(tweet_text)}"
        
        html_content += f"""
            <div class="card">
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn" onclick="handleAction(this)">𝕏 ポスト</a>
                    <button class="btn delete-btn" onclick="handleAction(this)">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:50px; color:#666;'>新着ニュースはありません。<br>時間をおいて更新してください。</p>"
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    get_dragons_news()
    print("Update finished successfully.")
