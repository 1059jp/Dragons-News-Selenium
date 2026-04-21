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
import traceback

HISTORY_FILE = "SHIN_history.txt"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_history(url):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def post_to_x(text):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 人間らしく見せるためのUser-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        print("--- ログイン開始 ---")
        driver.get("https://x.com/login")
        
        print("1. ユーザー名入力待ち...")
        u_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@autocomplete='username']")))
        u_field.send_keys(os.getenv("X_USER_ID"))
        u_field.send_keys(Keys.ENTER)
        time.sleep(5)

        # 追加認証（メール/電話）の有無を確認
        curr_url = driver.current_url
        if "checkpoint" in curr_url or "identify" in curr_url or "email" in driver.page_source.lower():
            print("→ 追加認証が要求されました。メールアドレスを入力します。")
            try:
                sub_input = driver.find_element(By.XPATH, "//input[@data-testid='ocfEnterTextNextButton'] | //input[@autocomplete='email'] | //input[@name='text']")
                sub_input.send_keys(os.getenv("X_EMAIL"))
                sub_input.send_keys(Keys.ENTER)
                time.sleep(5)
            except:
                print("→ 追加認証の入力欄が見つかりませんでした。スキップします。")

        print("2. パスワード入力待ち...")
        p_field = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
        p_field.send_keys(os.getenv("X_PASSWORD"))
        p_field.send_keys(Keys.ENTER)
        time.sleep(10)

        print("3. 投稿画面へ移動...")
        driver.get("https://x.com/compose/tweet")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0"]')))
        t_box.send_keys(text)
        
        print("4. 投稿ボタンをクリック...")
        btn = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetButton"]')
        btn.click()
        time.sleep(5)
        print("★投稿成功！")

    except Exception as e:
        print(f"!!! エラー発生地点: {driver.current_url}")
        print(f"!!! エラー詳細: {e}")
        # traceback.print_exc() # これを有効にするとさらに詳しく出ます
    finally:
        driver.quit()

def run_system():
    history = load_history()
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}
    trust_media = ['chunichi', 'fullcount', 'bbm', 'daily', 'nikkansports', 'spnannex', 'baseballeks', 'baseball']

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    items = soup.find_all('li', class_=lambda x: x and 'sw-Card' in x)
    if not items: items = soup.find_all('a')

    count = 0
    for item in items:
        if count >= 3: break 
        title = item.get_text().strip()
        link_tag = item if item.name == 'a' else item.find('a')
        if not link_tag: continue
        href = link_tag.get('href', '')

        if 'news.yahoo.co.jp/articles' in href and any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
            if href not in history:
                is_sports = any(m in href for m in trust_media)
                is_action = any(a in title for a in ['打', '投', '勝', '負', '戦', '安打', 'ホームラン'])
                
                if is_sports or is_action:
                    count += 1
                    print(f"\n【{count}件目処理中】: {title}")
                    post_to_x(f"{title}\n{href}")
                    save_history(href)

if __name__ == "__main__":
    run_system()
