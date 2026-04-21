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
    # 余計な装飾をカット
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    # 検索URL（新着順 st=n）
    word = urllib.parse.quote("中日ドラゴンズ")
    url = f"https://news.yahoo.co.jp/search?p={word}&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 履歴読み込み
    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}

    current_stock = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 記事カード（sw-Card）をすべて探す
        items = soup.select('.sw-Card')
        print(f"DEBUG: 発見した記事カード数: {len(items)}")

        for item in items:
            link_tag = item.find('a')
            if not link_tag: continue
            
            title = link_tag.get_text().strip()
            href = link_tag.get('href', '').split('?')[0]
            
            # 記事ID抽出
            aid_match = re.search(r'articles/([a-z0-9]+)', href)
            if not aid_match: continue
            aid = aid_match.group(1)

            # --- 日付チェックを廃止：中日関連 ＆ 未読なら全部出す ---
            if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                if title not in history and aid not in history:
                    print(f"DEBUG: 採用記事: {title}")
                    summary_text = build_summary(title)
                    current_stock.append({
                        "summary": summary_text,
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
            <h2 style="margin:0; font-size:1.2em;">🐉 ドラゴンズ新着 ({now})</h2>
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
        html_content += "<p style='text-align:center; padding:50px; color:#666; background:white; border-radius:12px;'>新着はありません。<br>「更新」を押して最新を確認してください。</p>"
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    current_news = get_dragons_news()
    create_html(current_news)
