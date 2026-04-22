def get_dragons_news():
    # 監視先：スポーツナビ プロ野球ニュース一覧
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
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 💡 修正：リンクの種類（news, articles, column, official）を問わず、
        # Yahoo関連のリンクを全てチェック対象にします
        all_links = soup.find_all('a', href=re.compile(r'yahoo.co.jp|/news/|/column/|/official/'))

        for link in all_links:
            href = link.get('href', '').split('?')[0]
            if href.startswith('/'):
                href = "https://sports.yahoo.co.jp" + href
            
            # タイトル（テキスト）をより深く取得
            title = link.get_text(separator=" ", strip=True)
            
            # 💡 判定をさらに確実に
            # タイトルに「中日」があり、かつ「8文字以上」のニュースらしいもの
            if '中日' in title or 'ドラゴンズ' in title:
                if len(title) > 8:
                    # 履歴にないかチェック
                    if title not in history and href not in history:
                        summary_text = build_summary(title)
                        news_list.append({"summary": summary_text, "url": href})
                        
                        new_entries_to_save.extend([title, href])
                        history.extend([title, href])

        # 調査結果をログに出す（Actionの画面で確認用）
        print(f"調査完了: 合計 {len(all_links)} 件のリンクから、中日関連を {len(news_list)} 件抽出しました。")
                
    except Exception as e:
        print(f"Error: {e}")
    
    return news_list
