import requests
from bs4 import BeautifulSoup
import datetime
import os
from google import genai

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# AIクライアント設定
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def summarize_for_x(title):
    """選ばれたタイトルを元に、100文字以内の要約を作る"""
    if not client:
        return title
        
    # 日付や曜日を削り、短く言い換えるための指示
    prompt = f"以下の野球ニュースのタイトルを、Xで投稿できるように100文字以内で要約してください。日付や時間は削除してください。語尾は『〜だ』『〜か』など短くしてください。\n\nタイトル: {title}"
    
    try:
        # モデル名を確実に認識させるための呼び出し
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"AI要約エラー: {e}")
        return title

def get_dragons_news():
    # --- 元の抽出ロジック（維持） ---
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}
    trust_media = ['chunichi', 'fullcount', 'bbm', 'daily', 'nikkansports', 'spnannex', 'baseballeks', 'baseball']
    # ----------------------------

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
                        summary = summarize_for_x(title) # AI要約実行
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
        <title>ドラゴンズAIパネル</title>
        <style>
            body {{ font-family: sans-serif; background: #f5f8fa; padding: 15px; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #003399; }}
            .summary-box {{ background: #e1f5fe; padding: 10px; border-radius: 8px; font-size: 0.95em; margin: 10px 0; color: #1a1a1a; }}
            .post-btn {{ display: inline-block; background: #1d9bf0; color: white; text-decoration: none; padding: 12px 24px; border-radius: 30px; font-weight: bold; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div style="background:#003399; color:white; padding:15px; border-radius:10px; margin-bottom:15px;">
            <h2 style="margin:0;">🐉 AI要約済み中日ニュース</h2>
            <small>最終更新: {now}</small>
        </div>
    """
    if not news_list:
        html_content += "<div class='card'>新しいニュースはありません。</div>"
    else:
        for item in news_list:
            tweet_text = f"{item['summary']}\n{item['url']}"
            encoded_text = requests.utils.quote(tweet_text)
            tweet_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
            
            html_content += f"""
                <div class="card">
                    <div style="font-size:0.8em; color:gray;">元のニュース: {item['title']}</div>
                    <div class="summary-box">{item['summary']}</div>
                    <a href="{tweet_url}" target="_blank" class="post-btn">𝕏 でポストする</a>
                </div>
            """
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print(f"Update Finished: {len(news)} news processed.")
