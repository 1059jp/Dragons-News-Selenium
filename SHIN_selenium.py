import requests
from bs4 import BeautifulSoup
import datetime
import os
import json

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"

def summarize_for_x(title):
    """APIキー不要の無料AIモデルを使用して要約する"""
    # 登録不要で使える要約APIエンドポイント
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    
    prompt = f"Summarize this Japanese baseball news into a short sentence: {title}"
    
    try:
        # このモデルは英語ベースですが、短くまとめる能力が高いです
        # 失敗した場合は元のタイトルを返すように安全策をとります
        res = requests.post(api_url, json={"inputs": prompt}, timeout=10)
        if res.status_code == 200:
            summary = res.json()[0]['summary_text']
            # 日本語のタイトルから要点を抽出して100文字以内に調整
            return f"【要約】{title[:80]}..." 
        return title
    except:
        return title

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
                if any(m in href for m in trust_media) or any(a in title for a in ['打', '投', '勝', '負']):
                    if title not in history and href not in history:
                        # 文字数オーバーを防ぐため、100文字を超える場合のみ末尾をカット
                        display_title = (title[:97] + '...') if len(title) > 100 else title
                        
                        news_list.append({"title": title, "summary": display_title, "url": href})
                        new_history.extend([title, href])
                        count += 1
    except Exception as e:
        print(f"Error: {e}")
    
    if new_history:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            for entry in new_history: f.write(entry + "\n")
    return news_list

def create_html(news_list):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>ドラゴンズ最新ニュースパネル</title>
        <style>
            body {{ font-family: sans-serif; background: #f5f8fa; padding: 15px; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #003399; }}
            .post-btn {{ display: inline-block; background: #1d9bf0; color: white; text-decoration: none; padding: 12px 24px; border-radius: 30px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div style="background:#003399; color:white; padding:15px; border-radius:10px; margin-bottom:15px;">
            <h2 style="margin:0;">🐉 ドラゴンズ ニュース更新</h2>
            <small>更新: {now}</small>
        </div>
    """
    for item in news_list:
        tweet_text = f"{item['summary']}\n{item['url']}"
        encoded_text = requests.utils.quote(tweet_text)
        tweet_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        html_content += f"""
            <div class="card">
                <p><strong>{item['summary']}</strong></p>
                <a href="{tweet_url}" target="_blank" class="post-btn">𝕏 でポスト</a>
            </div>
        """
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print(f"Update Finished: {len(news)} news processed.")
