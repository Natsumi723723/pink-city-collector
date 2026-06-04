"""
PINK CITY - 自動商品収集スクリプト
対象: Etsy, AliExpress, Amazon, 楽天
"""

import os
import time
import json
import random
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from urllib.parse import quote, urljoin

# ── 設定 ──────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
ETSY_API_KEY = os.environ.get("ETSY_API_KEY", "")

# ギラギラ・ネオン・濃いピンク系キーワード
PINK_KEYWORDS_EN = [
    "neon pink", "hot pink", "fuchsia", "magenta",
    "pink glitter", "pink rhinestone", "pink holographic",
    "hot pink y2k", "barbie pink", "pink chrome", "pink metallic",
    "electric pink", "deep pink",
    # キラキラ・ラメ・グリッター系
    "pink sequin", "pink sparkle", "pink glam", "pink bling",
    "pink crystal", "pink diamante", "pink shimmer", "pink iridescent",
    "glitter pink", "sparkle pink", "sequin pink",
    # ローズ系
    "rose pink", "rose gold pink", "dusty rose", "hot rose",
    "neon rose", "deep rose", "bright rose",
    # ホログラム・オーロラ系
    "pink hologram", "holographic pink", "aurora pink",
    "pink aurora", "pink rainbow", "iridescent pink",
    "pink prism", "pink opal",
]

PINK_KEYWORDS_JP = [
    "ネオンピンク", "ホットピンク", "蛍光ピンク", "ショッキングピンク", "ビビッドピンク",
    # キラキラ・ラメ・グリッター系
    "ピンク グリッター", "ピンク ラメ", "ピンク キラキラ", "ピンク スパンコール",
    "ピンク ラインストーン", "ピンク ホログラム", "ピンク シマー",
    "グリッターピンク", "ラメピンク", "スパンコールピンク",
    # ローズ系
    "ローズピンク", "ローズゴールド ピンク", "ディープローズ",
    # ホログラム・オーロラ系
    "ピンク ホログラム", "ホログラムピンク", "オーロラピンク",
    "ピンク オーロラ", "ピンク 虹色", "オーロラ ピンク",
]

PINK_KEYWORDS_CN = [
    "荧光粉", "亮粉色", "玫红色", "粉色亮片", "粉色水钻",
    "粉色闪片", "玫瑰粉", "亮片粉色", "粉色镭射", "粉色珠光",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
}


# ── Supabase ──────────────────────────────────────────────────────────
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL と SUPABASE_ANON_KEY を .env に設定してください")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


EXCLUDE_KEYWORDS = [
    "フクシア", "fuchsia", "Fuchsia", "植物", "苗", "花", "園芸", "gardening",
    "garden", "planting", "flower", "floral", "bouquet", "botanical",
]

def is_excluded(product_name):
    name_lower = product_name.lower()
    return any(kw.lower() in name_lower for kw in EXCLUDE_KEYWORDS)


def save_product(sb, product_name, image_url, product_url, source, keyword):
    if is_excluded(product_name):
        print(f"  — スキップ(お花系): {product_name[:40]}")
        return False
    try:
        sb.table("pink_products").upsert({
            "product_name": product_name,
            "image_url": image_url,
            "product_url": product_url,
            "source": source,
            "status": "pending",
            "pink_keywords": keyword,
        }, on_conflict="product_url").execute()
        print(f"  ✓ {source}: {product_name[:40]}")
        return True
    except Exception as e:
        print(f"  ✗ 保存失敗: {e}")
        return False


# ── Etsy（公式API） ────────────────────────────────────────────────────
def collect_etsy(sb):
    if not ETSY_API_KEY:
        print("⚠️  ETSY_API_KEY がないためスキップ（https://www.etsy.com/developers/ で取得）")
        return 0

    count = 0
    for keyword in PINK_KEYWORDS_EN[:6]:
        url = "https://openapi.etsy.com/v3/application/listings/active"
        params = {
            "keywords": keyword,
            "limit": 100,
            "fields": "listing_id,title,url,images",
            "includes": "images",
        }
        headers = {**HEADERS, "x-api-key": ETSY_API_KEY}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"  Etsy API エラー: {resp.status_code}")
                continue

            data = resp.json()
            for item in data.get("results", []):
                images = item.get("images", [])
                image_url = images[0]["url_fullxfull"] if images else ""
                product_url = f"https://www.etsy.com/listing/{item['listing_id']}"
                if save_product(sb, item["title"], image_url, product_url, "etsy", keyword):
                    count += 1

            time.sleep(0.5)
        except Exception as e:
            print(f"  Etsy エラー ({keyword}): {e}")

    return count


# ── AliExpress（スクレイピング） ────────────────────────────────────────
def collect_aliexpress(sb):
    count = 0
    for keyword in PINK_KEYWORDS_EN[:4] + PINK_KEYWORDS_CN[:3]:
        url = f"https://www.aliexpress.com/wholesale?SearchText={quote(keyword)}&SortType=default"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            # AliExpressの商品カード
            items = soup.select("a[href*='/item/']")
            seen = set()
            for item in items[:50]:
                href = item.get("href", "")
                if not href or href in seen:
                    continue
                seen.add(href)

                if not href.startswith("http"):
                    href = "https:" + href if href.startswith("//") else "https://www.aliexpress.com" + href

                # 商品名
                title_el = item.select_one("h3, .item-title, [class*='title']")
                title = title_el.get_text(strip=True) if title_el else item.get("title", "")
                if not title:
                    continue

                # 画像
                img_el = item.select_one("img")
                image_url = ""
                if img_el:
                    image_url = img_el.get("src") or img_el.get("data-src", "")
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url

                if save_product(sb, title, image_url, href, "aliexpress", keyword):
                    count += 1

            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"  AliExpress エラー ({keyword}): {e}")

    return count


# ── 楽天（商品検索API） ────────────────────────────────────────────────
def collect_rakuten(sb):
    # 楽天APIは無料で使えるが要アプリID（https://webservice.rakuten.co.jp/）
    RAKUTEN_APP_ID = os.environ.get("RAKUTEN_APP_ID", "")
    if not RAKUTEN_APP_ID:
        print("⚠️  RAKUTEN_APP_ID がないためスキップ（https://webservice.rakuten.co.jp/ で取得）")
        return 0

    count = 0
    for keyword in PINK_KEYWORDS_JP[:5]:
        url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
        params = {
            "applicationId": RAKUTEN_APP_ID,
            "keyword": keyword,
            "hits": 30,
            "imageFlag": 1,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            items = data.get("Items", [])
            for item in items:
                # 楽天APIはItems: [{Item: {...}}] または Items: [{...}] の両方ありうる
                i = item.get("Item", item)
                image_urls = i.get("mediumImageUrls", [])
                if image_urls and isinstance(image_urls[0], dict):
                    image_url = image_urls[0].get("imageUrl", "")
                elif image_urls:
                    image_url = image_urls[0]
                else:
                    image_url = ""
                if save_product(sb, i["itemName"], image_url, i["itemUrl"], "rakuten", keyword):
                    count += 1
            time.sleep(1)
        except Exception as e:
            print(f"  楽天 エラー ({keyword}): {e}")

    return count


# ── Amazon（スクレイピング） ───────────────────────────────────────────
def collect_amazon(sb):
    count = 0
    for keyword in PINK_KEYWORDS_EN[:3] + PINK_KEYWORDS_JP[:2]:
        url = f"https://www.amazon.co.jp/s?k={quote(keyword)}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select("[data-asin]:not([data-asin=''])"):
                asin = card.get("data-asin")
                if not asin:
                    continue

                title_el = card.select_one("h2 span, .a-text-normal")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue

                img_el = card.select_one("img.s-image")
                image_url = img_el.get("src", "") if img_el else ""

                product_url = f"https://www.amazon.co.jp/dp/{asin}"

                if save_product(sb, title, image_url, product_url, "amazon", keyword):
                    count += 1

            time.sleep(random.uniform(3, 5))
        except Exception as e:
            print(f"  Amazon エラー ({keyword}): {e}")

    return count


# ── メイン ────────────────────────────────────────────────────────────
def main():
    print("🌸 PINK CITY 収集スタート！")
    print("=" * 50)

    sb = get_supabase()
    total = 0

    print("\n📦 Etsy 収集中...")
    total += collect_etsy(sb)

    print("\n📦 AliExpress 収集中...")
    total += collect_aliexpress(sb)

    print("\n📦 楽天 収集中...")
    total += collect_rakuten(sb)

    print("\n📦 Amazon 収集中...")
    total += collect_amazon(sb)

    print("\n" + "=" * 50)
    print(f"🎉 完了！ 合計 {total} 件をSupabaseに登録しました")

    # 登録済み件数確認
    result = sb.table("pink_products").select("id", count="exact").execute()
    print(f"📊 データベース総件数: {result.count} 件")


if __name__ == "__main__":
    main()
