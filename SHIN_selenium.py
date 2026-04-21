import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
from datetime import timedelta, timezone
import json

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"

def get_dragons_news():
    # 検索URLを「新着順」に固定
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 履歴読み込み
    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}
    
    print(f"DEBUG: 現在の履歴数: {len(history)}")

    current_stock = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Yahoo!の検索結果リンクを全て取得
        links = soup.select('a[href*="articles/"]')
        print(f"DEBUG: 記事リンク発見数: {len(links)}")

        for link in links:
            title = link.get_text().strip()
            if not title or len(title) < 10: continue # 短すぎるのは無視
            
            href = link.get('href', '').split('?')[0]
            aid_match = re.search(r'articles/([a-z0-9]+)', href)
            if not aid_match: continue
            aid = aid_match.group(1)

            # 「中日」か「ドラ」が含まれているか
            if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                if title not in history and aid not in history:
                    print(f"DEBUG: 新着採用: {title}")
                    current_stock.append({
                        "summary": title, # 要約を一旦タイトルそのままにする
                        "url": f"https://news.yahoo.co.jp/articles/{aid}"
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
            body {{ font-family: sans-serif; background: #f0f2f5; padding: 10px; }}
            .header {{ background:#003399; color:white; padding:15px; text-align:center; border-radius: 8px; margin-bottom:15px; position: sticky; top: 0; z-index: 1000; }}
            .refresh-btn {{ margin-top:10px; padding:12px; border-radius:8px; border:none; background:white; color:#003399; font-weight:bold; width: 100%; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #003399; }}
            .summary-text {{ font-weight: bold; margin-bottom: 15px; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1fr 60px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 0.9em; display: flex; align-items: center; justify-content: center; }}
            .read-btn {{ background: #e7efff; color: #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #eee; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0;">🐉 ドラゴンズ新着 ({now})</h2>
            <button type="button" class="refresh-btn" onclick="window.location.reload(true);">🔄 更新</button>
        </div>
    """
    for item in news_list:
        tweet_url = f"https://twitter.com/intent/tweet?text={requests.utils.quote(item['summary'] + chr(10) + item['url'])}"
        html_content += f"""
            <div class="card">
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn">𝕏 ポスト</a>
                    <button class="btn delete-btn" onclick="this.closest('.card').style.display='none'">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:50px;'>新着なし（または全件既読）</p>"
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print(f"DEBUG: 処理完了。新着数: {len(news)}")
