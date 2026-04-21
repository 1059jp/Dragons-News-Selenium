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
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    text = text.replace("を発表", "を発表！").replace("が判明", "が判明...").replace("が予告先発", "が予告先発投手に！")
    if "ホームラン" in text: text = text.replace("ホームラン", "🚀ホームラン")
    if "勝利" in text: text = text.replace("勝利", "✨勝利")
    if "予告先発" in text: text = "🎯" + text
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    # 1. 検索結果ページ
    search_url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    # 2. トピックスページ（反映が早い場合がある）
    topic_url = "https://news.yahoo.co.jp/topics/dragons"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    trust_media = ['chunichi', 'fullcount', 'bbm', 'daily', 'nikkansports', 'spnannex', 'baseballeks', 'baseball', 'hochi']

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    stock = []
    if os.path.exists(STOCK_FILE):
        with open(STOCK_FILE, "r", encoding="utf-8") as f:
            try: stock = json.load(f)
            except: stock = []

    new_entries = []
    # 両方のURLを順番にチェック
    for target_url in [search_url, topic_url]:
        try:
            res = requests.get(target_url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 検索とトピックス両方のタグに対応
            items = soup.find_all(['li', 'a', 'div'], class_=lambda x: x and any(c in x for c in ['sw-Card', 'NewsFeed_list_item', 'sc-'] ))

            for item in items:
                title = item.get_text().strip()
                link_tag = item if item.name == 'a' else item.find('a')
                if not link_tag: continue
                
                full_href = link_tag.get('href', '')
                # ID抽出
                article_id_match = re.search(r'articles/([a-z0-9]+)', full_href)
                if not article_id_match: continue
                article_id = article_id_match.group(1)

                # 重複チェック（IDとタイトル両方）
                if title in history or article_id in history:
                    continue

                # フィルタリング
                is_target = any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ'])
                is_sports = any(m in full_href for m in trust_media)
                is_action = any(a in title for a in ['打', '投', '勝', '負', '戦', '安打', '本塁打', '先発', '公示', '登板'])
                
                if is_target and (is_sports or is_action):
                    summary_text = build_summary(title)
                    clean_url = f"https://news.yahoo.co.jp/articles/{article_id}"
                    
                    stock.insert(0, {"summary": summary_text, "url": clean_url, "original": title})
                    new_entries.extend([title, article_id])
                    history.extend([title, article_id])
        except Exception as e:
            print(f"Error on {target_url}: {e}")

    if new_entries:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            for entry in new_entries: f.write(entry + "\n")
    
    stock = stock[:25]
    with open(STOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(stock, f, ensure_ascii=False, indent=4)
    return stock

def create_html(news_list):
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST).strftime('%m/%d %H:%M')
    
    # --- HTMLの中身は同じなので省略（前回のコードのままでOK） ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズ最新ニュースパネル</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f5f8fa; padding: 10px; margin: 0; }}
            .header {{ background:#003399; color:white; padding:15px; margin-bottom:15px; text-align:center; border-radius: 0 0 10px 10px; }}
            .refresh-btn {{ margin-top:10px; padding:12px; border-radius:5px; border:none; background:white; color:#003399; font-weight:bold; cursor:pointer; width: 100%; font-size: 1em; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 5px solid #003399; transition: 0.3s; }}
            .summary-text {{ font-size: 1.05em; font-weight: bold; margin-bottom: 15px; line-height: 1.5; color: #1c1e21; white-space: pre-wrap; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1.2fr 50px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.85em; display: flex; align-items: center; justify-content: center; border: none; }}
            .read-btn {{ background: #f0f2f5; color: #003399; border: 1px solid #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #eeeeee; color: #666; }}
            .card.fade-out {{ opacity: 0; transform: scale(0.95); pointer-events: none; height: 0; margin: 0; padding: 0; overflow: hidden; }}
        </style>
        <script>function hideCard(el) {{ el.closest('.card').classList.add('fade-out'); }}</script>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0; font-size:1.1em;">🐉 未処理リスト ({now})</h2>
            <button class="refresh-btn" onclick="location.reload()">🔄 画面を更新</button>
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
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn" onclick="hideCard(this)">𝕏 ポスト</a>
                    <button class="btn delete-btn" onclick="hideCard(this)">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:20px; color:#666;'>未処理のニュースはありません。</p>"
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    get_dragons_news()
    print("Check finished.")
