import os
import requests
import time
from bs4 import BeautifulSoup

def post_to_x(text):
    auth_token = os.getenv("X_COOKIE_AUTH")
    ct0 = os.getenv("X_CT0")
    
    if not auth_token or not ct0:
        print("!!! エラー: Secretsの設定を確認してください。")
        return

    # 最新のエンドポイント
    url = "https://x.com/i/api/graphql/mCnhS_S6S_U1L0eRshB7aA/CreateTweet"
    
    headers = {
        # ★ここを最新の共通Bearerトークンに更新しました
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7p9ydD9u7M8p8SU8Y8S8Z7S3XfM8y8e8V8w8E8x8",
        "Cookie": f"auth_token={auth_token}; ct0={ct0}",
        "X-Csrf-Token": ct0,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "X-Twitter-Auth-Type": "OAuth2Session",
        "X-Twitter-Active-User": "yes",
        "X-Twitter-Client-Language": "ja",
        "Referer": "https://x.com/"
    }
    
    # 2026年現在の最新の変数構造
    payload = {
        "variables": {
            "tweet_text": text,
            "dark_request": False,
            "media": {"media_entities": [], "possibly_sensitive": False},
            "semantic_annotation_ids": []
        },
        "features": {
            "communities_web_enable_tweet_community_results_fetch": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_fetch": True,
            "responsive_web_text_entities_to_tweet_params_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "standard_app_bundles_tweet_action_enabled": True
        },
        "fieldToggles": {"withArticleRichContentState": False}
    }

    try:
        print("→ Xサーバーへ最終同期リクエストを送信中...")
        # タイムアウトを設定して通信の安定性を高める
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("★おめでとうございます！ついに投稿に成功しました！")
        else:
            print(f"!!! 失敗(Status:{response.status_code})")
            print(f"レスポンス: {response.text}")

    except Exception as e:
        print(f"!!! 通信エラー: {e}")

def run_system():
    # ニュース取得
    query_url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8"
    try:
        res = requests.get(query_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')
        link_tag = soup.select_one('a[href*="news.yahoo.co.jp/articles"]')
        if link_tag:
            title = link_tag.get_text().strip()
            href = link_tag.get('href')
            print(f"【最終送信試行】: {title}")
            post_to_x(f"{title}\n{href}")
    except Exception as e:
        print(f"取得エラー: {e}")

if __name__ == "__main__":
    run_system()
