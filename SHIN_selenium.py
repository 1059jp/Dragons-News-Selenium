import requests
from bs4 import BeautifulSoup
import datetime

def get_dragons_news():
    query_url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    news_list = []
    try:
        res = requests.get(query_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 最新5件を取得
        articles = soup.select('a[href*="news.yahoo.co.jp/articles"]')[:5]
        
        for art in articles:
            title = art.get_text().strip()
            url = art.get('href').split('?')[0] # 余計なパラメータをカット
            if title and url not in [n['url'] for n in news_list]:
                news_list.append({"title": title, "url": url})
    except Exception as e:
        print(f"取得エラー: {e}")
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
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f8fa; padding: 15px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ background: #003399; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .title {{ font-weight: bold; font-size: 1.1em; color: #1c1e21; margin-bottom: 10px; display: block; }}
            .post-btn {{ 
                display: inline-block; background: #1d9bf0; color: white; text-decoration: none; 
                padding: 10px 20px; border-radius: 30px; font-weight: bold; transition: 0.2s; 
            }}
            .post-btn:hover {{ background: #1a8cd8; }}
            .footer {{ font-size: 0.8em; color: #657786; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin:0;">🐉 ドラゴンズ投稿パネル</h2>
                <small>最終更新: {now}</small>
            </div>
    """

    for item in news_list:
        # Xの投稿用URL (intent) を作成
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
                <p>ボタンを押すと、投稿画面が立ち上がります。<br>内容を確認して送信してください。</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("★ index.html を更新しました")

if __name__ == "__main__":
    news = get_dragons_news()
    if news:
        create_html(news)
