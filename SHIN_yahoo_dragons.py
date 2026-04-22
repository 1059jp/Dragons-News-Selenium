import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
from datetime import timedelta, timezone
import urllib.parse

# --- 設定 ---
OWNER = "1059jp"
REPO = "Dragons-News-Selenium"
WORKFLOW_FILE = "auto_post.yml" 
HISTORY_FILE = "SHIN_history.txt"

def build_summary(title):
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    text = text.replace("を発表", "を発表！").replace("が判明", "が判明...")
    if "ホームラン" in text: text = text.replace("ホームラン", "🚀ホームラン")
    if "勝利" in text: text = text.replace("勝利", "✨勝利")
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 履歴を読み込む（一度出したやつを覚えるため）
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    news_list = []
    new_entries_to_save = []

    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'news.yahoo.co.jp/articles/'))

        for link in links:
            href = link.get('href', '').split('?')[0]
            title = link.get_text().strip()
            
            if len(title) < 10: continue

            # ドラゴンズ関連かつ、過去に「一度も」出したことがないものだけ
            if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                if title not in history and href not in history:
                    summary_text = build_summary(title)
                    # 今回の表示リストに追加
                    news_list.append({"summary": summary_text, "url": href})
                    # 履歴に保存するリストに追加
                    new_entries_to_save.extend([title, href])
                    history.extend([title, href])

        # 新しいニュースがあったら履歴に追記（これで次回から出なくなる）
        if new_entries_to_save:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                for entry in new_entries_to_save: f.write(entry + "\n")
                
    except Exception as e:
        print(f"Error: {e}")
    
    # 💡 ここで「STOCK_FILE」への保存をやめました。
    # 常に「今見つかった未読分」だけを返します。
    return news_list

def create_html(news_list):
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST).strftime('%m/%d %H:%M')
    
    js_code = """
    function hideCard(el) { el.closest('.card').style.display = 'none'; }
    function reloadPage() { location.reload(); }

    async function triggerSystemUpdate() {
        let token = localStorage.getItem('GH_TOKEN_YAHOO');
        if(!token || token === "null") {
            token = prompt("鍵を入力してください。");
            if(token) { localStorage.setItem('GH_TOKEN_YAHOO', token); }
            else { return; }
        }
        const btn = document.querySelector('.system-btn');
        btn.innerText = "⏳ 実行中...";
        btn.disabled = true;

        try {
            const response = await fetch('https://api.github.com/repos/""" + OWNER + "/" + REPO + """/actions/workflows/""" + WORKFLOW_FILE + """/dispatches', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Accept': 'application/vnd.github.v3+json'
                },
                body: JSON.stringify({ ref: 'main' })
            });
            if (response.status === 204) { alert("🚀 更新完了！\\n1分後にリロードしてください。"); }
            else { alert("エラー: " + response.status); }
        } catch (e) { alert("失敗: " + e); }
        finally { btn.innerText = "🚀 システム更新"; btn.disabled = false; }
    }
    """
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ドラゴンズ最新ニュース</title>
        <style>
            body {{ font-family: sans-serif; background: #f5f8fa; padding: 10px; margin: 0; }}
            .header {{ background:#003399; color:white; padding:15px; text-align:center; border-radius: 0 0 10px 10px; position: sticky; top: 0; z-index: 1000; }}
            .btn-header-group {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }}
            .refresh-btn {{ padding:10px; border-radius:20px; border:none; background:white; color:#003399; font-weight:bold; cursor:pointer; }}
            .system-btn {{ padding:10px; border-radius:20px; border:none; background:#ff4444; color:white; font-weight:bold; cursor:pointer; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 5px solid #003399; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .summary-text {{ font-weight: bold; margin-bottom: 15px; line-height: 1.5; color: #1c1e21; white-space: pre-wrap; }}
            .btn-group {{ display: grid; grid-template-columns: 1fr 1.2fr 50px; gap: 8px; }}
            .btn {{ text-align: center; text-decoration: none; padding: 12px 5px; border-radius: 8px; font-weight: bold; font-size: 0.85em; display: flex; align-items: center; justify-content: center; }}
            .read-btn {{ background: #f0f2f5; color: #003399; border: 1px solid #003399; }}
            .post-btn {{ background: #1d9bf0; color: white; }}
            .delete-btn {{ background: #eeeeee; color: #666; border: none; }}
        </style>
        <script>{js_code}</script>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0; font-size:1.1em;">🐉 ドラゴンズ新着 ({now})</h2>
            <div class="btn-header-group">
                <button class="system-btn" onclick="triggerSystemUpdate()">🚀 システム更新</button>
                <button class="refresh-btn" onclick="reloadPage()">🔄 更新</button>
            </div>
        </div>
        <div style="margin-top:15px;">
    """
    for item in news_list:
        tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(item['summary'] + chr(10) + item['url'])}"
        html_content += f"""
            <div class="card">
                <div class="summary-text">{item['summary']}</div>
                <div class="btn-group">
                    <a href="{item['url']}" target="_blank" class="btn read-btn">📰 読む</a>
                    <a href="{tweet_url}" target="_blank" class="btn post-btn" onclick="hideCard(this)">𝕏 ポスト</a>
                    <button class="btn delete-btn" onclick="hideCard(this)">✕</button>
                </div>
            </div>
        """
    if not news_list:
        html_content += "<p style='text-align:center; padding:50px; color:#666;'>【未読なし】<br>新しいニュースはありません。</p>"
    html_content += "</div></body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    news_data = get_dragons_news()
    create_html(news_data)
