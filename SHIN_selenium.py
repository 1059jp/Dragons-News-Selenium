import requests
from bs4 import BeautifulSoup
import datetime
import os

# 履歴ファイルの保存先
HISTORY_FILE = "SHIN_history.txt"

def get_dragons_news():
    # 元のこだわり検索URL
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 元のこだわり判定条件
    trust_media = ['chunichi', 'fullcount', 'bbm', 'daily', 'nikkansports', 'spnannex', 'baseballeks', 'baseball']
    action_keywords = ['打', '投', '勝', '負', '戦', '安打', 'ホームラン']

    # 履歴の読み込み
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    news_list = []
    new_history_entries = []

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all('li', class_=lambda x: x and 'sw-Card' in x)
        if not items: items = soup.find_all('a')

        count = 0
        for item in items:
            if count >= 5: break
            
            title = item.get_text().strip()
            link_tag = item if item.name == 'a' else item.find('a')
            if not link_tag: continue
            href = link_tag.get('href', '').split('?')[0] # 履歴判定を確実にするためURLを清掃

            # --- 元のロジックによる厳選 ---
            if 'news.yahoo.co.jp/articles' in href and any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                is_sports = any(m in href for m in trust_media)
                is_action = any(a in title for a in action_keywords)
                
                if is_sports or is_action:
                    # --- 重複チェック ---
                    if title not in history and href not in history:
                        count += 1
                        news_list.append({"title": title, "url": href})
                        new_history_entries.append(title)
                        new_history_entries.append(href)
                        
    except Exception as e:
        print(f"取得エラー: {e}")
    
    # 履歴の更新
    if new_history_entries:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            for entry in new_history_entries:
                f.write(entry + "\n")
                
    return news_list

def create_html(news_list):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズ投稿パネル</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f5f8fa; padding: 15px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ background: #003399; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .title {{ font-weight: bold; font-size: 1.05em; color: #1c1e21; margin-bottom: 12px; display: block; line-height: 1.4; }}
            .post-btn {{ 
                display: inline-block; background: #1d9bf0; color: white; text-decoration: none; 
                padding: 12px 24px; border-radius: 30px; font-weight: bold; font-size: 14px;
            }}
            .post-btn:hover {{ background: #1a8cd8; }}
            .footer {{ font-size: 0.8em; color: #657786; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin:0;">🐉 中日ドラゴンズ厳選ニュース</h2>
                <small>最終更新: {now}</small>
            </div>
    """

    if not news_list:
        html_content += "<div class='card'><p>新しい厳選ニュースはありません。次回の更新をお待ちください。</p></div>"
    else:
        for item in news_list:
            encoded_text = requests.utils.quote(f"{item['title']}\n{item['url']}")
            tweet_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
            
            html_content += f"""
                <div class="card">
                    <span class="title">{item['title']}</span>
                    <a href="{tweet_url}" target="_blank" class="post-btn">𝕏 でポストする</a>
                </div>
            """

    html_content += """
            <div class="footer">
                <p>ボタンを押すと、下書き状態のポスト画面が開きます。</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    news = get_dragons_news()
    create_html(news)
    print(f"★ 元の厳選条件を維持しつつ、{len(news)} 件をパネルに反映しました")
