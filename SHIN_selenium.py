import os
import requests
import time
from bs4 import BeautifulSoup

def post_to_x(text):
    # 値の取得（前後の不要な空白を自動で削除するように改良）
    auth_token = os.getenv("X_COOKIE_AUTH", "").strip()
    ct0 = os.getenv("X_CT0", "").strip()
    
    if not auth_token or not ct0:
        print("!!! エラー: Secrets(X_COOKIE_AUTH または X_CT0)が空っぽです")
        return

    # 最も安定しているAPIエンドポイント
    url = "https://x.com/i/api/graphql/mCnhS_S6S_U1L0eRshB7aA/CreateTweet"
    
    headers = {
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7p9ydD9u7M8p8SU8Y8S8Z7S3XfM8y8e8V8w8E8x8",
        "Cookie": f"auth_token={auth_token}; ct0={ct0}",
        "X-Csrf-Token": ct0,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "X-Twitter-Auth-Type": "OAuth2Session",
        "X-Twitter-Active-User": "yes",
        "Referer": "https://x.com/"
    }
    
    # データを最新の構造に固定
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
        }
    }

    try:
        print("→ 最終認証プロセスを実行中...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("★完了: 正常に送信されました！")
        else:
            print(f"!!! 認証失敗 (Status:{response.status_code})")
            print(f"エラー詳細: {response.text}")
            print(f"ヒント: ct0の値が [{ct0[:5]}...] であることを確認してください")

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
            print(f"【最終トライ】: {title}")
            post_to_x(f"{title}\n{href}")
    except Exception as e:
        print(f"ニュース取得失敗: {e}")

if __name__ == "__main__":
    run_system()
