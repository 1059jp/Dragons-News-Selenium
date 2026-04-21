import requests
from bs4 import BeautifulSoup
import datetime
import os
import google.generativeai as genai

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"
# ★ここに取得した Gemini APIキーを貼り付けてください
GEMINI_API_KEY = "AIzaSyBtcdro0KKc8sKS4amghwnd0W6yw1NZylE" 

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def summarize_for_x(title):
    """選ばれたタイトルを元に、X（140文字）に収まる要約を作る"""
    prompt = f"以下の野球ニュースのタイトルを、Xで投稿できるように130文字以内で魅力的に言い換えてください。日付や曜日は不要です。語尾は短くしてください。\n\nタイトル: {title}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return title # エラー時は元のタイトルを使う

def get_dragons_news():
    # --- 【重要】ここから元のロジック ---
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}
    trust_media = ['chunichi', 'fullcount', 'bbm', 'daily', 'nikkansports', 'spnannex', 'baseballeks', 'baseball']
    # ----------------------------------

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]
    else: history = []

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

            # --- 【重要】ここも元の判定条件のまま ---
            if 'news.yahoo.co.jp/articles' in href and any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                is_sports = any(m in href for m in trust_media)
                is_action = any(a in title for a in ['打', '投', '勝', '負', '戦', '安打', 'ホームラン'])
                
                if is_sports or is_action:
                    if title not in history and href not in history:
                        # --- 採用されたニュースだけAI要約をかける ---
                        summary = summarize_for_x(title)
                        
                        news_list.append({"title": title, "summary": summary, "url": href})
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズAI要約パネル</title>
        <style>
            body {{ font-family: sans-serif; background: #f5f8fa; padding: 15px; line-height: 1.4; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .summary-box {{ background: #e1f5fe; padding: 10px; border-radius: 8px; font-size: 0.9em; margin: 10px 0; border-left: 4px solid #1d9bf0; }}
            .post-btn {{ display: inline-block; background: #1d9bf0; color: white; text-decoration: none; padding: 10px 20px; border-radius: 30px; font-weight: bold; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div style="background:#003399; color:white; padding:10px; border-radius:10px; margin-bottom:15px;">
            <h2 style="margin:0;">🐉 AI要約済みニュース</h2>
            <small>更新: {now}</small>
        </div>
    """
    if not news_list:
        html_content += "<div class='card'>新しいニュースはありません。</div>"
    else:
        for item in news_list:
            # AIが作った要約 + URL で投稿文を作成
            tweet_text = f"{item['summary']}\n{item['url']}"
            encoded_text = requests.utils.quote(tweet_text)
            tweet_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
            
            html_content += f"""
                <div class="card">
                    <div style="font-size:0.8em; color:gray;">元の題名: {item['title']}</div>
                    <div class="summary-box"><strong>AI要約:</strong><br>{item['summary']}</div>
                    <a href="{tweet_url}" target="_blank" class="post-btn">𝕏 でポストする</a>
                </div>
            """
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print(f"Update Finished: {len(news)} news summarized.")
