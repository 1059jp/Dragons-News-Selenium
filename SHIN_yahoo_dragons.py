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
    # 余計な記号をカット
    text = re.sub(r'\(.*?\)|（.*?）|【.*?】|\d+時\d+分.*$', '', title).strip()
    text = text.replace("を発表", "を発表！").replace("が判明", "が判明...")
    if "ホームラン" in text: text = text.replace("ホームラン", "🚀ホームラン")
    if "勝利" in text: text = text.replace("勝利", "✨勝利")
    if len(text) > 110: text = text[:107] + "..."
    return f"{text}\n\n#dragons #中日ドラゴンズ"

def get_dragons_news():
    # 💡 1059jpさんが見つけてくれた「中日専用」のURLに変更
    url = "https://sports.yahoo.co.jp/list/news/npb?genre=npb&team=4"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    news_list = []
    new_entries_to_save = []

    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ニュースの枠をすべて取得
        articles = soup.find_all(['li', 'div'], class_=re.compile(r'ListItem|Card'))

        for item in articles:
            link_tag = item.find('a')
            if not link_tag: continue
            
            href = link_tag.get('href', '').split('?')[0]
            if href.startswith('/'): href = "https://sports.yahoo.co.jp" + href
            
            # タイトルを取得
            display_title = link_tag.get_text(strip=True)
            
            # 💡 修正ポイント：
            # このページにあるニュースは「中日」という文字が入っていなくても、
            # 全部ドラゴンズ関連なので、無条件で拾います！
            if len(display_title) >= 8:
                if href not in history and display_title not in history:
                    summary_text = build_summary(display_title)
                    news_list.append({"summary": summary_text, "url": href})
                    new_entries_to_save.extend([display_title, href])
                    history.extend([display_title, href])
                        
    except Exception as e:
        print(f"Error: {e}")
    
    return news_list


def create_html(news_list):
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.datetime.now(JST).strftime('%m/%d %H:%M')
    
    # 💡 消してはいけないブラウザ更新用JavaScript
    js_code = """
    function hideCard(el) { el.closest('.card').style.display = 'none'; }
    function reloadPage() { location.reload(); }

    async function triggerSystemUpdate() {
        let token = localStorage.getItem('GH_TOKEN_YAHOO');
        if(!token || token === "null") {
            token = prompt("鍵（ghp_...）を入力してください。");
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
