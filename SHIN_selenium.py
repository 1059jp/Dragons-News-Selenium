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
    chrome_options.add_argument('--lang=en-US')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 60)

    try:
        print("--- ログイン開始 ---")
        driver.get("https://x.com/login")
        
        print("1. ユーザー名入力待ち...")
        u_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']")))
        u_field.send_keys(os.getenv("X_USER_ID"))
        u_field.send_keys(Keys.ENTER)
        time.sleep(10)

        # 追加認証・画面の文字チェック
        page_text = driver.page_source.lower()
        if "email" in page_text or "phone" in page_text or "text" in page_text:
            print("→ 追加認証画面を検知。メールを入力します。")
            try:
                sub_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-testid='ocfEnterTextNextButton'] | //input[@autocomplete='email'] | //input[@name='text']")))
                sub_field.send_keys(os.getenv("X_EMAIL"))
                sub_field.send_keys(Keys.ENTER)
                time.sleep(10)
            except: pass

        print("2. パスワード入力待ち...")
        # 【改良】パスワード欄が出るまで最大60秒、粘り強く画面を確認し続ける
        try:
            # パスワード欄を探す前に、今の画面の主要なテキストを表示（デバッグ用）
            body_text = driver.find_element(By.TAG_NAME, "body").text.replace('\n', ' ')
            print(f"→ 現在の画面状況: {body_text[:100]}...")
            
            p_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password' and @name='password']")))
            p_field.send_keys(os.getenv("X_PASSWORD"))
            p_field.send_keys(Keys.ENTER)
            print("→ パスワード入力完了")
            time.sleep(15)
        except Exception as e:
            print("→ パスワード欄が見つかりません。画面を強制的にパスワード入力画面へ遷移させます。")
            # パスワード欄が見つからない場合、Enterキーをもう一度押してみる（遷移を促す）
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(5)
            p_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password' or @name='password']")))
            p_field.send_keys(os.getenv("X_PASSWORD"))
            p_field.send_keys(Keys.ENTER)

        print("3. 投稿準備...")
        driver.get("https://x.com/compose/tweet")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0"]')))
        t_box.send_keys(text)
        
        print("4. 投稿実行...")
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="tweetButton"]')))
        btn.click()
        time.sleep(10)
        print("★投稿成功！")

    except Exception as e:
        print(f"!!! エラー発生地点: {driver.current_url}")
        print(f"!!! 詳細: {e}")
    finally:
        driver.quit()

# run_system関数はテスト用のまま（履歴チェックなし）でOK
