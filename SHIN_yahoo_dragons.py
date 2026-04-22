def get_dragons_news():
    # ターゲット：スポーツナビ プロ野球ニュース
    url = "https://sports.yahoo.co.jp/list/news/npb?genre=npb"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f.readlines()]

    news_list = []
    new_entries_to_save = []

    try:
        print(f"DEBUG: 接続開始 -> {url}")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 💡 修正：リンクの条件を「aタグなら全部」にまで広げます
        all_links = soup.find_all('a')
        print(f"DEBUG: ページ内の全リンク数: {len(all_links)}")

        for link in all_links:
            href = link.get('href', '')
            if not href: continue

            # リンクを絶対パスに変換
            if href.startswith('/'):
                href = "https://sports.yahoo.co.jp" + href
            
            # 💡 修正：タイトルの取得をより柔軟に
            title = link.get_text(strip=True)
            
            # 「中日」が含まれているか。大文字小文字や記号を無視して判定
            if '中日' in title or 'ドラゴンズ' in title or 'ドラ' in title:
                # ニュースらしい長さ（5文字以上）であれば採用
                if len(title) >= 5:
                    if title not in history and href not in history:
                        summary_text = build_summary(title)
                        news_list.append({"summary": summary_text, "url": href})
                        new_entries_to_save.extend([title, href])
                        history.extend([title, href])

        if new_entries_to_save:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                for entry in new_entries_to_save: f.write(entry + "\n")
        
        print(f"DEBUG: 最終取得件数: {len(news_list)}")
                
    except Exception as e:
        # 💡 重要：エラーが起きたら内容を画面用のリストに突っ込む
        error_msg = f"プログラム実行エラー: {str(e)}"
        print(error_msg)
        news_list.append({"summary": error_msg, "url": "#"})
    
    return news_list
