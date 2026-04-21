import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def post_to_x(text):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 1. 画面サイズを一般的なノートPCサイズに設定
    chrome_options.add_argument('--window-size=1920,1080')
    # 2. 自動操縦であることを隠す設定を追加
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    # 3. 画面上の「webdriver」フラグを消す（ロボット検知対策）
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    wait = WebDriverWait(driver, 30)

    try:
        print("--- 接続開始 ---")
        driver.get("https://x.com")
        time.sleep(5)

        auth_token = os.getenv("X_COOKIE_AUTH")
        driver.add_cookie({"name": "auth_token", "value": auth_token, "domain": ".x.com"})
        
        print("→ 投稿画面へ移動")
        driver.get("https://x.com/compose/post")
        time.sleep(15) # 完全に読み込むまで長く待つ

        print("→ 投稿内容を入力中...")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        t_box.send_keys(text)
        time.sleep(5)
        
        print("→ 投稿ボタンを狙い撃ちします...")
        # ボタンを特定（より確実な要素を指定）
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButton"], [data-testid="tweetButtonInline"]')))
        
        # ボタンまでスクロールして、マウスでクリック
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(2)
        ActionChains(driver).move_to_element(btn).click().perform()
        
        print("→ 投稿完了をじっくり待機中（30秒）...")
        time.sleep(30) 
        
        # 画面が変わったかログに出す
        print(f"最終URL: {driver.current_url}")
        if "compose/post" not in driver.current_url:
            print("★URLが変化しました！投稿成功です！")
        else:
            print("!!! 画面が変わりませんでした。投稿が拒否された可能性があります。")

    except Exception as e:
        print(f"!!! エラー発生: {e}")
    finally:
        driver.quit()
