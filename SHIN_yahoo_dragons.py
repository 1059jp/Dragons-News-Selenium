def get_dragons_news():
    # 検索URL（新着順 st=n）
    url = "https://news.yahoo.co.jp/search?p=%E4%B8%AD%E6%97%A5%E3%83%89%E3%83%A9%E3%82%B4%E3%83%B3%E3%82%BA&ei=utf-8&st=n"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    news_list = []
    new_entries_to_save = []

    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 💡 修正：もっと広い範囲でリンクを探すようにしました
        # hrefに "articles" が含まれる全てのリンクをチェック
        all_links = soup.find_all('a', href=re.compile(r'news.yahoo.co.jp/articles/'))

        for link in all_links:
            href = link.get('href', '').split('?')[0]
            # 💡 修正：タイトルの取得方法をより確実に（子要素も含めてテキストを拾う）
            title = link.get_text(separator=" ", strip=True)
            
            if len(title) < 8: continue

            # 「中日」という文字が入っていて、まだ履歴にない場合
            if '中日' in title or 'ドラゴンズ' in title:
                if title not in history and href not in history:
                    summary_text = build_summary(title)
                    news_list.append({"summary": summary_text, "url": href})
                    new_entries_to_save.extend([title, href])
                    history.extend([title, href])

        if new_entries_to_save:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                for entry in new_entries_to_save: f.write(entry + "\n")
                
    except Exception as e:
        print(f"Error: {e}")
    
    return news_list
