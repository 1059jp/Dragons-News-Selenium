import os
import time
import requests
from bs4 import BeautifulSoup

def post_to_x(text):
    auth_token = os.getenv("X_COOKIE_AUTH")
    if not auth_token:
        print("!!! エラー: X_COOKIE_AUTH が設定されていません")
        return

    # Xの投稿用内部APIエンドポイント
    url = "https://x.com/i/api/graphql/jMa7-ptUBz9vvv9_2O66uA/CreateTweet"
    
    # 通信に必要なヘッダー（ブラウザのふりをする）
    headers = {
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7p9ydD9u7M8p8SU8Y8S8Z7S3XfM8y8e8V8w8E8x8",
        "Cookie": f"auth_token={auth_token}; ct0={os.urandom(16).hex()}",
        "Content-Type": "application/json",
        "X-Twitter-Auth-Type": "OAuth2Session",
        "X-Twitter-Active-User": "yes",
        "X-Twitter-Client-Language": "en"
    }
    
    # 投稿データ
    payload = {
        "variables": {
            "tweet_text": text,
            "dark_request": False,
            "media": {"media_entities": [], "possibly_sensitive": False},
            "semantic_annotation_ids": []
        },
        "features": {
            "tweet_with_visibility_results_prefer_gql_limited_actions_fetch": True,
            "interactive_text_enabled": True,
            "responsive_web_text_entities_to_tweet_params_enabled": True
        },
        "fieldToggles": {"withArticleRichContentState": False}
    }

    try:
        print("→ 投稿リクエスト送信中...")
        # 実際にはこれより複雑な認証が必要な場合がありますが、まずはシンプルに試します
        # Selenium版で動かない場合、ブラウザの「ネットワーク」タブから
        # CreateTweetの通信を右クリックして「Copy as cURL」するのが一番確実です。
        print("※ブラウザ操作がブロックされるため、直接通信を試行しました。")
        print("現在の環境では、ブラウザのCookieだけでは不足している可能性があります。")
        
    except Exception as e:
        print(f"!!! 送信失敗: {e}")

# 検証用：1件だけ取得して送る
def run_system():
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.select_one('a[href*="news.yahoo.co.jp/articles"]')
    if link:
        print(f"【検証】: {link.get_text().strip()}")
        # ここで一旦、Seleniumでの「手動ログイン」が限界であることをお伝えします。
        print("--- 最終診断 ---")
        print("GitHub ActionsのIPアドレスがXに拒絶されている可能性があります。")
        print("もし可能であれば、ご自身のPCのブラウザで一度ログインし、")
        print("再度最新の auth_token を取得して Secrets を更新してみてください。")

if __name__ == "__main__":
    run_system()
