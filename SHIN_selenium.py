import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def post_to_x(text):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    # 自動操縦の隠蔽設定
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    # webdriverフラグの削除
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    wait = WebDriverWait(driver, 30)

    try:
        print("--- 接続開始（極限構成） ---")
        driver.get("https://x.com")
        time.sleep(5)

        auth_token = os.getenv("X_COOKIE_AUTH")
        driver.add_cookie({"name": "auth_token", "value": auth_token, "domain": ".x.com"})
        
        # 直接「投稿作成URL」に飛ぶ
        driver.get("https://x.com/compose/post")
        time.sleep(15) 

        print("→ 入力欄を強制特定...")
        # どの言語設定でも共通の「role="textbox"」だけを狙う
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        
        # 1. 一度クリックしてフォーカスを当てる
        t_box.click()
        time.sleep(2)
        
        # 2. 確実に文字を打ち込む
        print("→ テキスト送信中...")
        t_box.send_keys(text)
        time.sleep(5)
        
        # 3. 【最重要】ボタンを探さず、Ctrl + Enter を直接キーボードとして叩き込む
        print("→ 送信キー(Ctrl+Enter)を直接入力...")
        t_box.send_keys(Keys.CONTROL, Keys.ENTER)
        
        # 4. 送信完了を待つ（ここが短いと処理が途切れる）
        print("→ 最終待機（30秒）...")
        time.sleep(30)
        
        print(f"終了時のURL: {driver.current_url}")
        if "compose/post" not in driver.current_url:
             print("★URLが遷移しました。投稿成功の可能性が高いです。")
        else:
             print("!!! まだ投稿画面のままです。")

    except Exception as e:
        print(f"!!! エラー: {e}")
    finally:
        driver.quit()

def run_system():
    # ニュース取得部分はこれまでのままでOK
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    link_tag = soup.select_one('a[href*="news.yahoo.co.jp/articles"]')
    if link_tag:
        title = link_tag.get_text().strip()
        href = link_tag.get('href')
        print(f"【検証投稿】: {title}")
        post_to_x(f"{title}\n{href}")

if __name__ == "__main__":
    run_system()
