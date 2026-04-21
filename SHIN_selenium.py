import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def post_to_x(text):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        print("--- 接続開始 ---")
        driver.get("https://x.com")
        time.sleep(5)

        auth_token = os.getenv("X_COOKIE_AUTH")
        if not auth_token:
            print("!!! エラー: X_COOKIE_AUTH が空です。GitHubのSettingsを確認してください。")
            return
            
        driver.add_cookie({"name": "auth_token", "value": auth_token, "domain": ".x.com"})
        print("→ Cookieをセットしました。再読み込みします。")
        driver.get("https://x.com/compose/tweet")
        time.sleep(7)

        # ログインできているかチェック（現在のURLを確認）
        print(f"→ 現在のページ: {driver.current_url}")
        if "login" in driver.current_url:
            print("!!! 失敗: Cookieが拒否され、ログイン画面に戻されました。Cookieが古い可能性があります。")
            return

        print("→ 投稿内容を入力中...")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0"]')))
        t_box.send_keys(text)
        
        print("→ 投稿ボタンをクリックします。")
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="tweetButton"]')))
        btn.click()
        time.sleep(5)
        print("★投稿処理が完了しました！")

    except Exception as e:
        print(f"!!! 投稿プロセス中にエラー: {e}")
    finally:
        driver.quit()

# run_system関数（ニュース取得側）
def run_system():
    # 以前のコードと同じですが、念のため1件だけ強制的に送る設定にします
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # ニュースを1件取得
    link_tag = soup.select_one('a[href*="news.yahoo.co.jp/articles"]')
    if link_tag:
        title = link_tag.get_text().strip()
        href = link_tag.get('href')
        print(f"【検証投稿】: {title}")
        post_to_x(f"【自動投稿テスト】\n{title}\n{href}")
    else:
        print("!!! ニュースが1件も取得できませんでした。")

if __name__ == "__main__":
    run_system()
