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
    chrome_options.add_argument('--window-size=1280,1024') # 画面サイズを固定
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
        time.sleep(12) # 読み込みを長めに待機

        print("→ 投稿内容を入力中...")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        t_box.send_keys(text)
        time.sleep(5)
        
        print("→ 投稿ボタンを『物理的』にクリックします...")
        # ボタンの要素を特定
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="tweetButton"] | //div[@data-testid="tweetButtonInline"]')))
        
        # マウスをボタンに移動させてクリックする動作を再現
        actions = ActionChains(driver)
        actions.move_to_element(btn).click().perform()
        
        print("→ 完了待機中（20秒）...")
        time.sleep(20)
        
        # 最終確認
        if "compose/post" not in driver.current_url:
            print("★おめでとうございます！投稿が完了し、画面が切り替わりました。")
        else:
            print("!!! まだ投稿画面です。最後の手段：JavaScriptで無理やり送信します。")
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(10)

    except Exception as e:
        print(f"!!! 失敗理由: {e}")
    finally:
        driver.quit()

# run_system は検証用のままでOK
