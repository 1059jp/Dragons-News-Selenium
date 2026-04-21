import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
from datetime import timedelta, timezone

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"

def build_summary(title):
    """
    ニュースの核となる部分を抽出し、130文字以内の自然な文章に再構成する。
    """
    # 1. 不要な記号や日付を削除
    clean_title = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    
    # 2. ポスト用の文章を組み立て
    summary = clean_title
    
    if len(summary) > 115:
        summary = summary[:112] + "..."
        
    return f"{summary} #dragons #中日ドラゴンズ"

def get_dragons_news():
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}
    trust_media = ['chunichi', 'fullcount', 'bbm', 'daily', 'nikkansports', 'spnannex', 'baseballeks', 'baseball']

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    news_list = []
    new_history = []

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all('li', class_=lambda x: x and 'sw-Card' in x) or soup.find_all('a')

        count = 0
        for item in items:
            if count >= 5: break
            title = item.get_text().strip()
            link_tag = item if item.name == 'a' else item.find('a')
            if not link_tag: continue
            href = link_tag.get('href', '').split('?')[0]

            if 'news.yahoo.co.jp/articles' in href and any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                is_sports = any(m in href for m in trust_media)
                is_action = any(a in title for a in ['打', '投', '勝', '負', '戦', '安打', 'ホームラン'])
                
                if is_sports or is_action:
                    if title not in history and href not in history:
                        summary_text = build_summary(title)
                        news_list.append({"summary": summary_text, "url": href, "original": title})
                        new_history.extend([title, href])
                        count += 1
    except Exception as e:
        print(f"Error: {e}")
    
    if new_history:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            for entry in new_history: f.write(entry + "\n")
    return news_list

def create_html(news_list):
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST).strftime('%m/%d %H:%M')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズ最新ニュースパネル</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f5f8fa; padding: 15px; }}
            .header {{ background:#003399; color:white; padding:15px; border-radius:10px; margin-bottom:15px; }}
            .refresh-btn {{ margin-top:10px; padding:10px 20px; border-radius:5px; border:none; background:white; color:#003399; font-weight:bold; cursor:pointer; }}
            
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #003399; transition: 0.3s; position: relative; }}
            .summary-text {{ font-size: 1.1em; font-weight: bold; margin-bottom: 12px; line-height: 1.4; padding-right: 30px; }}
            
            .btn-group {{ display: flex; gap: 10px; align-items: center; }}
            .post-btn {{ flex-grow: 1; text-align: center; background: #1d9bf0; color: white; text-decoration: none; padding: 12px; border-radius: 30px; font-weight: bold; }}
            .delete-btn {{ background: #e0e0e0; color: #666; text-decoration: none; padding: 12px 18px; border-radius: 30px; font-weight: bold; cursor: pointer; border: none; }}
            
            /* 消える時のアニメーション */
            .card.fade-out {{ opacity: 0; transform: scale(0.9); pointer-events: none; height: 0; margin: 0; padding: 0; overflow: hidden; }}
        </style>
        
        <script>
            function hideCard(el) {{
                const card = el.closest('.card');
                card.classList.add('fade-out');
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0;">🐉 ドラゴンズ更新 ({now})</h2>
            <button class="refresh-btn" onclick="location.reload()">🔄 画面を更新する</button>
        </div>
    """
    for item in news_list:
        tweet_text = f"{item['summary']}\n{item['url']}"
        encoded_text = requests.utils.quote(tweet_text)
        tweet_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        
        html_content += f"""
            <div class="card">
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{tweet_url}" target="_blank" class="post-btn" onclick="hideCard(this)">𝕏 ポスト</a>
                    <button class="delete-btn" onclick="hideCard(this)">✕ 消す</button>
                </div>
            </div>
        """
    
    if not news_list:
        html_content += "<p style='text-align:center;'>新しいニュースはありません。</p>"
        
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print(f"Update Finished: {len(news)} news processed.")
