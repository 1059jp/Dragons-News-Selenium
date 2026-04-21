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

# --- 履歴管理（あなたのロジックを維持） ---
HISTORY_FILE = "SHIN_history.txt"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_history(url):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

# --- Seleniumによるブラウザ投稿処理 ---
def post_to_x(text):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 画面なしで実行
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1280,1024')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        # --- SHIN_selenium.py のログイン部分を以下に差し替え ---
        driver.get("https://x.com/login")
        
        # ユーザー名入力（より確実な指定に変更）
        user_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        user_input.send_keys(os.getenv("X_USER_ID"))
        user_input.send_keys(Keys.ENTER)
        time.sleep(5)

        # メールアドレス要求のチェックを強化
        try:
            # 画面内に "email" という文字があるか確認
            if "email" in driver.page_source.lower() or "phone" in driver.page_source.lower():
                sub_input = driver.find_element(By.XPATH, "//input[@data-testid='ocfEnterTextNextButton'] or //input[@autocomplete='email']")
                sub_input.send_keys(os.getenv("X_EMAIL"))
                sub_input.send_keys(Keys.ENTER)
                time.sleep(5)
        except:
            pass

        # パスワード入力
        pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        pass_input.send_keys(os.getenv("X_PASSWORD"))
        pass_input.send_keys(Keys.ENTER)
        time.sleep(10) # ログイン完了まで少し長めに待つ
        # 投稿画面へ
        driver.get("https://x.com/compose/tweet")
        tweet_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0"]')))
        tweet_box.send_keys(text)
        
        # 投稿ボタンをクリック
        post_btn = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetButton"]')
        post_btn.click()
        time.sleep(5)
        print("投稿に成功しました！")

    except Exception as e:
        print(f"エラー発生: {e}")
    finally:
        driver.quit()

# --- 実行メイン ---
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
        if count >= 1: break # 最初は1件だけでテスト
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
                    print(f"取得: {title}")
                    post_to_x(f"{title}\n{href}")
                    save_history(href)

if __name__ == "__main__":
    run_system()
