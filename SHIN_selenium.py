def get_dragons_news():
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0"}

    # 日本時間の今日の日付を取得
    JST = timezone(timedelta(hours=+9), 'JST')
    today_str = datetime.datetime.now(JST).strftime('%m/%d') # 例: "04/21"

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    stock = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all(class_=lambda x: x and 'sw-Card' in x)

        new_entries = []
        for item in items:
            # 時間ラベルを取得 (例: "4/21(火) 20:33")
            time_tag = item.find(class_=re.compile(r'time'))
            time_text = time_tag.get_text() if time_tag else ""

            # 【追加】今日の日付(例: 4/21)が含まれていない記事はスキップ
            # ※Yahooの表記に合わせて調整が必要な場合があります
            if today_str.lstrip('0') not in time_text:
                continue

            link_tag = item.find('a')
            if not link_tag: continue
            
            title = item.get_text().strip()
            href = link_tag.get('href', '').split('?')[0]

            if any(k in title for k in ['中日', 'ドラゴンズ', 'ドラ']):
                if title not in history and href not in history:
                    summary_text = build_summary(title)
                    stock.insert(0, {"summary": summary_text, "url": href})
                    new_entries.extend([title, href])
                    history.extend([title, href])

        if new_entries:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                for entry in new_entries: f.write(entry + "\n")
                
    except Exception as e:
        print(f"Error: {e}")
    
    return stock[:20]
