import requests
from bs4 import BeautifulSoup
import datetime
import os

# --- 設定 ---
HISTORY_FILE = "SHIN_history.txt"

def summarize_with_ai(title):
    """
    AI（Hugging Face提供の日本語モデル）を使用して、
    ニュースを130文字以内の自然な日本語に要約する。
    """
    # 登録不要・キー不要で使える日本語要約API
    api_url = "https://api-inference.huggingface.co/models/staka/gettt-yahoorealtimenews-summary"
    
    try:
        # AIにタイトルを投げて要約を依頼
        response = requests.post(api_url, json={"inputs": title}, timeout=15)
        if response.status_code == 200:
            result = response.json()
            summary = result[0]['summary_text']
            # ポスト用に130文字以内に微調整（AIが長めに答えた場合の保険）
            return summary[:127] + "..." if len(summary) > 130 else summary
        
        # AIが混雑等で反応しない場合の予備処理（整った文章にする）
        return f"【ドラゴンズ最新】{title[:110]}..."
    except:
        return title[:127] + "..."

def get_dragons_news():
    # 元々のコードのURLと抽出条件
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}
    trust_media = ['chunichi', 'fullcount', 'bbm', 'daily', 'nikkansports', 'spnannex', 'baseballeks', 'baseball']

    # 履歴読み込み
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
            href = link_tag.get('href', '').split('?')[0] # 不要なパラメータ削除

            # 元々のフィルタ条件（信頼できるメディアか、野球の動作キーワードを含むか）
            if 'news.yahoo.co.jp/articles' in href and any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                is_sports = any(m in href for m in trust_media)
                is_action = any(a in title for a in ['打', '投', '勝', '負', '戦', '安打', 'ホームラン'])
                
                if is_sports or is_action:
                    if title not in history and href not in history:
                        # ★ここが重要：カットではなくAI要約を実行
                        summary = summarize_with_ai(title)
                        
                        news_list.append({"summary": summary, "url": href, "original_title": title})
                        new_history.extend([title, href])
                        count += 1
    except Exception as e:
        print(f"Error: {e}")
    
    # 履歴を更新
    if new_history:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            for entry in new_history: f.write(entry + "\n")
    return news_list

def create_html(news_list):
    now = datetime.datetime.now().strftime('%m/%d %H:%M')
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズAI要約パネル</title>
        <style>
            body {{ font-family: sans-serif; background: #f0f2f5; padding: 10px; }}
            .card {{ background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-top: 4px solid #003399; }}
            .summary {{ font-size: 1.05em; color: #1c1e21; margin-bottom: 12px; line-height: 1.5; font-weight: bold; }}
            .original {{ font-size: 0.85em; color: gray; margin-bottom: 8px; }}
            .post-btn {{ display: block; text-align: center; background: #1d9bf0; color: white; text-decoration: none; padding: 12px; border-radius: 25px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h3 style="color:#003399;">🐉 ドラゴンズAI要約 ({now})</h3>
    """
    if not news_list:
        html_content += "<p>新しいニュースはありません。</p>"
    else:
        for item in news_list:
            # 要約文 + リンクで140字以内に収まるように設計
            tweet_text = f"{item['summary']}\n{item['url']}"
            encoded_text = requests.utils.quote(tweet_text)
            tweet_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
            
            html_content += f"""
                <div class="card">
                    <div class="original">元記事: {item['original_title']}</div>
                    <div class="summary">{item['summary']}</div>
                    <a href="{tweet_url}" target="_blank" class="post-btn">𝕏 でポストする</a>
                </div>
            """
    html_content += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print(f"Update Finished: {len(news)} news processed.")
