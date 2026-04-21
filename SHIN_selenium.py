import requests
from bs4 import BeautifulSoup
import os
import re
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"

def get_dragons_news():
    # 検索窓を通さず、中日ドラゴンズの公式ニュース一覧ページを直接スクレイピング
    url = "https://news.yahoo.co.jp/sports/baseball/teams/11/news"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15",
        "Referer": "https://news.yahoo.co.jp/"
    }
    
    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}

    current_stock = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ページ内のすべてのリンクを確認
        links = soup.find_all('a', href=re.compile(r'news.yahoo.co.jp/articles/'))

        for link in links:
            href = link.get('href', '').split('?')[0]
            title = link.get_text().strip()
            
            # 画像だけのリンクや、文字が極端に短いものは飛ばす
            if len(title) < 10:
                continue

            # 記事固有のID(aid)を抽出して、重複チェックに使用
            aid_match = re.search(r'articles/([a-z0-9]+)', href)
            aid = aid_match.group(1) if aid_match else href

            # 履歴にIDもタイトルも存在しない場合のみ採用
            if aid not in history and title not in history:
                # ドラゴンズ関連か田中選手、死球などのキーワードで最終確認
                if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ', '田中', '死球']):
                    current_stock.append({
                        "summary": title,
                        "url": href
                    })
                    # 今回拾ったものを履歴に予約（保存は最後）
                    history.add(aid)
                    history.add(title)
        
    except Exception as e:
        print(f"Error during scraping: {e}")

    # 履歴をアルファベット順に整理して保存
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for item in sorted(history):
            f.write(f"{item}\n")
            
    return current_stock

def create_html(news_list):
    # 日本時間を取得
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(JST).strftime('%m/%d %H:%M:%S')
    
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
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #003399; animation: slideIn 0.3s ease-out; }}
            @keyframes slideIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            .summary-text {{ font-weight: bold; margin-bottom: 15px; white-space: pre-wrap; color: #1c1e21; font-size: 1.05em; line-height: 1.4; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1fr 60px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.9em; display: flex; align-items: center; justify-content: center; }}
            .read-btn {{ background: #e7efff; color: #003399; border: 1px solid #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #eeeeee; color: #666; border: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0; font-size:1.2em;">🐉 ドラゴンズ新着 ({now})</h2>
            <button type="button" class="refresh-btn" onclick="window.location.reload(true);">🔄 ページを更新</button>
        </div>
    """
    
    # ニュースを表示（新しい順）
    for item in news_list:
        # 𝕏ポスト用のテキスト（タイトル + ハッシュタグ + URL）
        tweet_text = f"{item['summary']}\n\n#dragons #中日ドラゴンズ\n{item['url']}"
        tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(tweet_text)}"
        
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
        html_content += f"""
            <div style='text-align:center; padding:50px; color:#666; background:white; border-radius:12px;'>
                <p>現在、新しいニュースはありません。</p>
                <p style="font-size: 0.8em;">(※既に読み込んだニュースは非表示になります)</p>
            </div>
        """
        
    html_content += "</body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    # 1. ニュースを取得
    latest_news = get_dragons_news()
    # 2. HTMLファイルを生成
    create_html(latest_news)
