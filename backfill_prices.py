"""
既存商品の価格をバックフィルするスクリプト
Amazon: 商品ページから価格取得
BUYMA: 商品ページから価格取得
"""
import os, time, random, warnings
warnings.filterwarnings('ignore')
import requests
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
}

def fetch_amazon_price(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        # パターン1: .a-price .a-offscreen
        el = soup.select_one(".a-price .a-offscreen")
        if el:
            return el.get_text(strip=True)
        # パターン2: #priceblock_ourprice
        el = soup.select_one("#priceblock_ourprice, #priceblock_dealprice")
        if el:
            return el.get_text(strip=True)
        # パターン3: .priceToPay
        el = soup.select_one(".priceToPay .a-offscreen")
        if el:
            return el.get_text(strip=True)
    except Exception as e:
        pass
    return None

def fetch_buyma_price(url):
    try:
        resp = requests.get(url, headers={**HEADERS, "Referer": "https://www.buyma.com/"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        # BUYMAの価格要素
        el = soup.select_one(".item_selling_price, .showcase_price, [class*='price']")
        if el:
            text = el.get_text(strip=True)
            if "¥" in text or "円" in text:
                return text.split("(")[0].strip()
    except:
        pass
    return None

def main():
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # price が null の商品を全件取得
    print("価格未設定の商品を取得中...")
    all_products = []
    offset = 0
    while True:
        res = sb.table("pink_products")\
            .select("id,product_url,source")\
            .is_("price", "null")\
            .range(offset, offset + 999)\
            .execute()
        rows = res.data
        if not rows:
            break
        all_products.extend(rows)
        if len(rows) < 1000:
            break
        offset += 1000

    print(f"対象: {len(all_products)} 件\n")

    updated = 0
    skipped = 0
    for i, p in enumerate(all_products):
        source = p.get("source", "")
        url = p.get("product_url", "")
        price = None

        if source == "amazon":
            price = fetch_amazon_price(url)
            sleep_time = random.uniform(2, 4)
        elif source == "buyma":
            price = fetch_buyma_price(url)
            sleep_time = random.uniform(2, 3)
        else:
            skipped += 1
            continue

        if price:
            sb.table("pink_products").update({"price": price}).eq("id", p["id"]).execute()
            updated += 1
            print(f"  [{i+1}/{len(all_products)}] ✓ {source}: {price} — {url[-40:]}")
        else:
            skipped += 1
            print(f"  [{i+1}/{len(all_products)}] — 価格なし: {url[-40:]}")

        time.sleep(sleep_time)

        # 50件ごとに進捗表示
        if (i + 1) % 50 == 0:
            print(f"\n--- 進捗: {i+1}/{len(all_products)} 件処理済み / 更新: {updated} 件 ---\n")

    print(f"\n完了！ 更新: {updated} 件 / スキップ: {skipped} 件")

if __name__ == "__main__":
    main()
