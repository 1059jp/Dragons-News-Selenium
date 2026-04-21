def get_dragons_news():
    # 検索ワードを「中日」と「ドラゴンズ」の両方を含むように設定
    # これで、特定のキーワードから漏れている記事も拾えるようになります
    word = urllib.parse.quote("中日 ドラゴンズ")
    url = f"https://news.yahoo.co.jp/search?p={word}&ei=utf-8&st=n"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15",
    }

    history = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = {line.strip() for line in f if line.strip()}

    current_stock = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 記事リンクを全スキャン
        links = soup.find_all('a', href=re.compile(r'news.yahoo.co.jp/articles/'))

        for link in links:
            title = link.get_text().strip()
            if not title or len(title) < 10: continue
            
            href = link.get('href', '').split('?')[0]
            aid_match = re.search(r'articles/([a-z0-9]+)', href)
            if not aid_match: continue
            aid = aid_match.group(1)

            # --- ここで「田中」もキーワードに含めて判定を確実にします ---
            if any(k in title for k in ['中日', 'ドラゴンズ', '田中']):
                if title not in history and aid not in history:
                    summary_text = build_summary(title)
                    current_stock.append({
                        "summary": summary_text,
                        "url": f"https://news.yahoo.co.jp/articles/{aid}"
                    })
                    history.add(title)
                    history.add(aid)
                    
    except Exception as e:
        print(f"DEBUG: エラー発生: {e}")

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for item in sorted(history):
            f.write(f"{item}\n")
            
    return current_stock
