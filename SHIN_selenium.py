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
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    # 検索とトピックス、両方の最新ページ
    urls = [
        "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n",
        "https://news.yahoo.co.jp/topics/dragons"
    ]
    headers = {"User-Agent": "Mozilla/5.0"}

    # 履歴を読み込む
    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}

    stock = [] # 今回新しく見つけたものだけを入れる

    for target_url in urls:
        try:
            res = requests.get(target_url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'articles/'))

            for link in links:
                title = link.get_text().strip()
                href = link.get('href', '').split('?')[0]
                aid = re.search(r'articles/([a-z0-9]+)', href).group(1) if "articles/" in href else None
                
                if not aid or not any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                    continue

                # --- 【重要】一度でも履歴(history)にあったら、絶対にリストに出さない ---
                if title in history or aid in history:
                    continue

                # まだ見たことがないニュースだけをストックに入れる
                summary_text = build_summary(title)
                stock.append({"summary": summary_text, "url": f"https://news.yahoo.co.jp/articles/{aid}"})
                
                # 見つけた瞬間に履歴へ追加（次回の実行では出さないようにする）
                history.add(title)
                history.add(aid)
        except Exception as e:
            print(f"Error: {e}")

    # 履歴を保存（ここに入ったものは、二度と画面に出ない）
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for item in sorted(history):
            f.write(f"{item}\n")
            
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
        <title>ドラゴンズ最新速報</title>
        <style>
            body {{ font-family: sans-serif; background: #f0f2f5; padding: 10px; margin: 0; }}
            .header {{ background:#003399; color:white; padding:15px; text-align:center; border-radius: 8px; margin-bottom:15px; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #003399; }}
            .summary-text {{ font-weight: bold; margin-bottom: 15px; white-space: pre-wrap; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1fr 50px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.9em; border: none; }}
            .read-btn {{ background: #e7efff; color: #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #ddd; color: #666; }}
            .done {{ display: none; }}
        </style>
        <script>
            function hide(el) {{ el.closest('.card').classList.add('done'); }}
        </script>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0;">🐉 新着ドラゴンズ ({now})</h2>
            <p style="font-size:0.8em; margin:5px 0 0;">一度表示された記事は、5分後の更新で自動で消えます</p>
        </div>
    """
    for item in news_list:
        tweet_url = f"https://twitter.com/intent/tweet?text={requests.utils.quote(item['summary'] + chr(10) + item['url'])}"
        html_content += f"""
            <div class="card">
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn" onclick="hide(this)">𝕏 ポスト</a>
                    <button class="btn delete-btn" onclick="hide(this)">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:50px; color:#666;'>新着はありません。<br>5分後の自動更新をお待ちください。</p>"
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
