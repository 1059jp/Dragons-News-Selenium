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
    chrome_options.add_argument('--lang=en-US')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        print("--- 接続開始 ---")
        driver.get("https://x.com")
        time.sleep(5)

        auth_token = os.getenv("X_COOKIE_AUTH")
        driver.add_cookie({"name": "auth_token", "value": auth_token, "domain": ".x.com"})
        
        print("→ 投稿画面へ移動")
        driver.get("https://x.com/compose/post")
        
        # 画面がしっかり出るまで待つ
        time.sleep(10)

        print("→ 投稿内容を入力中...")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        t_box.send_keys(text)
        time.sleep(3)
        
        print("→ 投稿ボタンを探してクリック...")
        # ボタンを特定するための複数のXPATH
        btn_xpath = '//button[@data-testid="tweetButton"] | //div[@role="button"]//span[text()="Post"] | //div[@data-testid="tweetButton"]'
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
        
        # 1. 普通にクリック
        try:
            btn.click()
        except:
            # 2. 失敗したらJavaScriptで強制クリック
            driver.execute_script("arguments[0].click();", btn)
        
        print("→ 投稿完了を待機中（15秒）...")
        time.sleep(15) 
        
        # 投稿が成功して画面が切り替わったかチェック
        if "compose/post" not in driver.current_url:
            print("★投稿成功の可能性が高いです！画面が切り替わりました。")
        else:
            print("!!! 警告: まだ投稿画面のままです。ボタンが押せていない可能性があります。")

    except Exception as e:
        print(f"!!! 失敗理由: {e}")
    finally:
        driver.quit()

# ニュース取得側の run_system 関数はそのまま（前回の検証用）でOKです
def run_system():
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    link_tag = soup.select_one('a[href*="news.yahoo.co.jp/articles"]')
    if link_tag:
        title = link_tag.get_text().strip()
        href = link_tag.get('href')
        print(f"【検証投稿】: {title}")
        post_to_x(f"【自動投稿テスト】\n{title}\n{href}")

if __name__ == "__main__":
    run_system()
