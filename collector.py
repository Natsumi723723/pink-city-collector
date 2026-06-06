"""
PINK CITY - 自動商品収集スクリプト
対象: Etsy, AliExpress, Amazon, 楽天
"""

import os
import re
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
    "粉色全息", "极光粉", "粉色闪光", "桃红色",
]

# AliExpress専用：商品カテゴリ×ピンクの組み合わせ
PINK_KEYWORDS_ALI = [
    # ファッション
    "pink y2k top", "hot pink crop top", "neon pink dress",
    "pink sequin dress", "pink glitter outfit", "pink rhinestone top",
    "pink holographic jacket", "fuchsia bodycon", "magenta mini dress",
    "pink rave outfit", "neon pink bikini", "pink metallic skirt",
    # アクセサリー
    "pink rhinestone necklace", "hot pink earrings", "neon pink ring",
    "pink crystal bracelet", "pink bling accessories", "pink glitter bag",
    "pink holographic bag", "pink sequin purse", "fuchsia handbag",
    # ネイル
    "pink nail charms", "neon pink nail art", "pink glitter nails",
    "hot pink press on nails", "pink rhinestone nails", "pink chrome nails",
    # インテリア・雑貨
    "pink neon sign", "hot pink led light", "pink glitter phone case",
    "neon pink wall decor", "pink holographic sticker", "pink bling phone case",
    "pink mirror decoration", "fuchsia room decor",
    # コスメ
    "hot pink lipstick", "neon pink lip gloss", "pink glitter eyeshadow",
    "pink shimmer highlighter", "fuchsia blush", "pink holographic makeup",
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


# ギラギラ系ワード（これが商品名に1つでも入ってないとスキップ）
GLITTER_WORDS = [
    # 日本語
    "グリッター", "スパンコール", "スパングル", "ラメ", "ラインストーン",
    "ストーン", "クリスタル", "ビジュー", "ホログラム", "ホログラフィック",
    "オーロラ", "メタリック", "シャイン", "シマー", "キラキラ", "ビーズ",
    "パール", "スタッズ", "エナメル", "ミラー", "ネオン",
    # 英語
    "glitter", "sequin", "rhinestone", "crystal", "hologram", "holographic",
    "aurora", "iridescent", "metallic", "shimmer", "shine", "bling",
    "sparkle", "studs", "patent", "mirror", "neon", "chrome",
    "lame", "bijou", "beads", "pearl",
]

EXCLUDE_KEYWORDS = [
    # 魚・釣り・水産・ペット・生き物系
    "金魚", "熱帯魚", "錦鯉", "鯉", "めだか", "メダカ", "グッピー",
    "アロワナ", "ベタ", "プラティ", "ネオンテトラ", "コリドラス",
    "魚", "水槽", "アクアリウム", "aquarium", "fish",
    "えさ", "餌", "飼料", "フィッシュ",
    "サーモン", "マグロ", " タコ", "イカ釣", "エビ釣", "カニ釣",
    "めだか", "メダカ", "稚魚",
    # 釣り用品
    "ジグ", "ルアー", "lure", "釣り", "フィッシング", "fishing",
    "タックル", "tackle", "ロッド", "リール", "仕掛け",
    "メジャークラフト", "シマノ", "ダイワ", "バス釣",
    # 洋服・アパレル系（全ソース共通除外）
    "Tシャツ", "ティーシャツ", "t-shirt", "tshirt", "t shirt",
    "ワンピース", "ドレス", "dress", "スカート", "skirt",
    "ブラウス", "blouse", "シャツ", "shirt",
    "ジャケット", "jacket", "コート", "coat", "アウター",
    "パーカー", "hoodie", "スウェット", "sweatshirt",
    "ニット", "セーター", "sweater", "カーディガン", "cardigan",
    "パンツ", "ズボン", "trousers", "jeans", "デニム",
    "レギンス", "leggings", "タイツ", "tights", "ストッキング",
    "水着", "bikini", "swimsuit", "swimwear",
    "ランジェリー", "ブラジャー", "bra", "lingerie", "下着", "パンティ",
    "ルームウェア", "パジャマ", "pajama",
    "トップス", "カットソー", "チュニック", "tunic",
    "オールインワン", "jumpsuit", "romper",
    "マフラー", "scarf", "ストール", "stole",
    "手袋", "gloves", "帽子", "hat", "cap", "ハット", "キャップ", "ベレー帽",
    # お花・植物系
    "フクシア", "植物", "苗", "花", "園芸", "gardening",
    "garden", "planting", "flower", "floral", "bouquet", "botanical",
    # CD・音楽系のみ（ノート・手帳はOK）
    "remastered", "Remastered", "bonus track", "music album", "soundtrack",
    # コスメ全般（クリップ・グリップ・リップストップは除外しない）
    "リップグロス", "リップティント", "リップクリーム", "リップカラー", "リップモンスター",
    "リップライナー", "リップシャイン", "リップエッセンス", "リップペンシル", "リップセラム",
    "口紅", "ルージュ", "チーク", "アイシャドウ", "ファンデーション", "コンシーラー",
    "マスカラ", "アイライナー", "ハイライター", "ブラッシュ", "ブロンザー",
    # ネイル：塗るタイプ・施術系を除外（アート・チップ・デコ・パーツはOK）
    "ネイルポリッシュ", "マニキュア", "nail polish",
    "ジェルネイル", "ジェルカラー", "カラージェル", "gel nail", "nail gel", "color gel",
    "ネイルカラー", "nail color", "nail lacquer",
    "ベースコート", "トップコート", "base coat", "top coat",
    "ネイルオイル", "ネイルケア", "甘皮", "キューティクル",
    "リップグロス", "ティント", "ルージュ", "リップクリーム",
    "下地", "化粧水", "美容液", "乳液", "クリーム", "洗顔", "日焼け止め",
    "lipstick", "lip gloss", "lip tint", "eyeshadow", "mascara", "blush",
    "foundation", "concealer", "highlighter", "bronzer", "eyeliner",
    "color gel", "skincare", "serum", "moisturizer", "sunscreen", "toner",
    "hair color", "hair dye", "ヘアカラー", "白髪染め", "カラーシャンプー",
    "染料", "色素",
]

# CDジャケット・レコード系パターン
EXCLUDE_PATTERNS = [
    r'\[analog\]', r'\(analog\)', r'limited edition.*lp', r'vinyl lp',
    r'vinyl record', r'bonus track', r'remastered edition',
    r'\bep\b', r'\blp\b',
]

_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in EXCLUDE_PATTERNS]

def is_excluded(product_name):
    name_lower = product_name.lower()
    # キーワード除外
    if any(kw.lower() in name_lower for kw in EXCLUDE_KEYWORDS):
        return True
    # パターン除外
    if any(p.search(product_name) for p in _compiled_patterns):
        return True
    return False


PINK_WORDS = [
    "ピンク", "pink", "ホットピンク", "hot pink", "ネオンピンク", "neon pink",
    "ローズ", "rose", "マゼンタ", "magenta", "フューシャ", "fuchsia",
    "桃", "蛍光ピンク", "ショッキングピンク", "バービーピンク", "barbie pink",
    "オーロラピンク", "aurora pink",
]

NEON_WORDS = [
    "ネオンサイン", "ネオンライト", "neon sign", "neon light",
    "ledサイン", "led sign", "ledネオン", "led neon",
]

LEOPARD_WORDS = [
    "レオパード", "ヒョウ柄", "豹柄", "ひょう柄", "leopard", "アニマル柄",
    "チーター", "cheetah", "animal print",
]

CLEAR_WORDS = [
    "クリアバッグ", "クリアポーチ", "クリアケース", "クリアトート",
    "透明バッグ", "透明ポーチ", "透明ケース",
    "clear bag", "clear pouch", "clear case", "clear tote",
    "アクリルバッグ", "アクリルケース", "アクリルポーチ",
    "pvcバッグ", "pvc bag", "ビニールバッグ",
]

def detect_style(product_name):
    """商品名からスタイルを判定"""
    name_lower = product_name.lower()
    if any(w.lower() in name_lower for w in NEON_WORDS):
        return 'neon'
    if any(w.lower() in name_lower for w in LEOPARD_WORDS):
        return 'leopard'
    if any(w.lower() in name_lower for w in CLEAR_WORDS):
        return 'clear'
    return 'glitter'

def save_product(sb, product_name, image_url, product_url, source, keyword, require_image=False, price=None, style=None):
    if is_excluded(product_name):
        return False
    name_lower = product_name.lower()

    # スタイル自動判定
    detected_style = style or detect_style(product_name)

    # ピンクワードチェック（全スタイル共通）
    if not any(w.lower() in name_lower for w in PINK_WORDS):
        return False

    # グリッター・ネオン・クリアはギラギラ語が必要、レオパードは不要
    if detected_style not in ('leopard',):
        if not any(w.lower() in name_lower for w in GLITTER_WORDS):
            # ネオン・クリアはキーワード自体がギラギラ語になるので別途チェック
            if detected_style == 'neon' and any(w.lower() in name_lower for w in NEON_WORDS):
                pass  # OK
            elif detected_style == 'clear' and any(w.lower() in name_lower for w in CLEAR_WORDS):
                pass  # OK
            else:
                return False

    if require_image and (not image_url or len(image_url) < 10):
        return False
    try:
        row = {
            "product_name": product_name,
            "image_url": image_url,
            "product_url": product_url,
            "source": source,
            "status": "pending",
            "pink_keywords": keyword,
            "style": detected_style,
        }
        if price:
            row["price"] = price
        sb.table("pink_products").upsert(row, on_conflict="product_url").execute()
        print(f"  ✓ {source}[{detected_style}]: {product_name[:40]}")
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
    keywords = PINK_KEYWORDS_ALI + PINK_KEYWORDS_CN + PINK_KEYWORDS_EN[:8]
    for keyword in keywords:
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

                if save_product(sb, title, image_url, href, "aliexpress", keyword, require_image=True):
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
AMAZON_KEYWORDS = [
    # ネオン・ホット系
    "ネオンピンク", "ホットピンク", "蛍光ピンク", "ショッキングピンク",
    "neon pink", "hot pink", "electric pink",
    # キラキラ・グリッター系
    "ピンク グリッター", "ピンク スパンコール", "ピンク ラメ", "ピンク ラインストーン",
    "pink glitter", "pink sequin", "pink rhinestone", "pink bling",
    "ピンク キラキラ アクセサリー", "グリッター ピンク バッグ",
    # ホログラム・オーロラ系
    "ピンク ホログラム", "オーロラ ピンク", "ホログラフィック ピンク",
    "holographic pink", "aurora pink", "iridescent pink",
    # カテゴリ別
    "ピンク ネオン サイン", "ピンク ネイル キラキラ", "ピンク スマホケース キラキラ",
    "ピンク ドレス キラキラ", "ピンク バッグ キラキラ", "ピンク ヘアアクセ キラキラ",
    "hot pink dress", "pink glitter shoes", "pink sequin bag",
    "pink chrome nails", "fuchsia accessories", "magenta outfit",
    # ローズ系
    "ローズピンク", "rose pink", "deep rose",
    # ノート・手帳・文具系（ピンク）
    "ピンク ノート キラキラ", "ピンク 手帳 かわいい", "ピンク 日記帳",
    "ピンク ダイアリー", "ピンク スケジュール帳", "ピンク 文具 キラキラ",
    "ピンク 手帳 ラメ", "ネオンピンク ノート", "ホットピンク 手帳",
    "pink journal glitter", "pink notebook sparkle", "pink diary holographic",
    "pink planner rhinestone", "hot pink notebook", "pink glitter journal",
    "pink spiral notebook", "pink stationery bling",
    # シール・ステーショナリー系
    "ピンク シール帳", "ピンク バインダー", "ピンク ステーショナリー",
    "pink sticker book", "pink binder glitter",
]

def collect_amazon(sb):
    count = 0
    for keyword in AMAZON_KEYWORDS:
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

                # 価格取得
                price = None
                price_el = card.select_one(".a-price .a-offscreen, .a-price-whole")
                if price_el:
                    price = price_el.get_text(strip=True).replace("¥", "¥").strip()
                    # "¥1,234" 形式に整える
                    if price and not price.startswith("¥"):
                        price = "¥" + price

                # バリアント指定のhrefを優先（ピンク等の特定カラーが選択された状態のURL）
                link_el = card.select_one("a.a-link-normal[href*='/dp/']")
                if link_el and link_el.get("href"):
                    href = link_el["href"]
                    # 相対URLを絶対URLに
                    if href.startswith("/"):
                        href = "https://www.amazon.co.jp" + href
                    # refパラメータは不要、dp/ASIN部分以降だけ残す
                    import re as _re
                    m = _re.search(r'(https://www\.amazon\.co\.jp/dp/[A-Z0-9]+(?:\?[^"]*)?)', href)
                    product_url = m.group(1) if m else f"https://www.amazon.co.jp/dp/{asin}"
                    # ref=... などのトラッキング部分を除去してth/pscだけ残す
                    base = f"https://www.amazon.co.jp/dp/{asin}"
                    params = []
                    if "th=1" in href: params.append("th=1")
                    if "psc=1" in href: params.append("psc=1")
                    product_url = base + ("?" + "&".join(params) if params else "")
                else:
                    product_url = f"https://www.amazon.co.jp/dp/{asin}"

                if save_product(sb, title, image_url, product_url, "amazon", keyword, require_image=True, price=price):
                    count += 1

            time.sleep(random.uniform(3, 5))
        except Exception as e:
            print(f"  Amazon エラー ({keyword}): {e}")

    return count


# ── BUYMA（スクレイピング） ────────────────────────────────────────────
# BUYMAカラーコード: CL10=ピンク系
# 洋服（レディース・メンズ・キッズ）は除外、バッグ・シューズ・アクセサリーのみ対象
BUYMA_PINK_URLS = [
    ("/r/-C4-CL10/",           "バッグ × ピンク"),
    ("/r/-C5-CL10/",           "シューズ × ピンク"),
    ("/r/-C6-CL10/",           "アクセサリー × ピンク"),
    ("/r/-C4-CL10/?page=2",    "バッグ × ピンク p2"),
    ("/r/-C5-CL10/?page=2",    "シューズ × ピンク p2"),
    ("/r/-C6-CL10/?page=2",    "アクセサリー × ピンク p2"),
    ("/r/-C4-CL10/?page=3",    "バッグ × ピンク p3"),
    ("/r/-C5-CL10/?page=3",    "シューズ × ピンク p3"),
    ("/r/-C6-CL10/?page=3",    "アクセサリー × ピンク p3"),
]

# BUYMAで洋服と判定するキーワード（商品名に含まれていたらスキップ）
BUYMA_CLOTHING_WORDS = [
    "Tシャツ", "T-shirt", "tshirt", "カットソー", "ニット", "セーター", "sweater",
    "パーカー", "hoodie", "スウェット", "sweatshirt", "ジャケット", "jacket",
    "コート", "coat", "ブルゾン", "ワンピース", "dress", "スカート", "skirt",
    "パンツ", "trousers", "shorts", "デニム", "jeans", "ショーツ", "ビキニ",
    "swimwear", "水着", "ブラウス", "blouse", "シャツ", " shirt", "トップス",
    "レギンス", "leggings", "タンクトップ", "tank", "ベスト", "vest",
    "カーディガン", "cardigan", "polo", "ポロシャツ", "ロンT",
]

def collect_buyma(sb):
    count = 0
    headers = {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.buyma.com/",
    }
    seen_global = set()
    for path, label in BUYMA_PINK_URLS:
        url = f"https://www.buyma.com{path}"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"  BUYMA HTTP {resp.status_code} ({label})")
                time.sleep(2)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href*='/item/']")
            page_new = 0
            for link in links:
                href = link.get("href", "")
                if not href or href in seen_global:
                    continue
                seen_global.add(href)
                if not href.startswith("http"):
                    href = "https://www.buyma.com" + href

                # 商品名: syo_name属性 または img alt
                title = link.get("syo_name", "")
                if not title:
                    img_el = link.select_one("img")
                    title = img_el.get("alt", "") if img_el else ""
                if not title or len(title) < 3:
                    continue

                # 画像
                img_el = link.select_one("img")
                image_url = ""
                if img_el:
                    image_url = img_el.get("src") or img_el.get("data-src", "")
                    if image_url and image_url.startswith("//"):
                        image_url = "https:" + image_url

                title_lower = title.lower()

                # 洋服スキップ
                if any(w.lower() in title_lower for w in BUYMA_CLOTHING_WORDS):
                    continue

                # 価格取得（price属性 or 親要素のテキスト）
                price = link.get("price", "")
                if price:
                    try:
                        price = f"¥{int(price):,}"
                    except:
                        price = None
                else:
                    price = None

                if save_product(sb, title, image_url, href, "buyma", label, price=price):
                    count += 1
                    page_new += 1

            print(f"  [{label}] +{page_new}件")
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"  BUYMA エラー ({label}): {e}")

    return count


# ── Yahoo!ショッピング（公式API） ──────────────────────────────────────
YAHOO_KEYWORDS = [
    # ✨ グリッター×ピンク
    "ピンク グリッター", "ピンク スパンコール", "ピンク ラメ", "ピンク ラインストーン",
    "ピンク ホログラム", "オーロラ ピンク", "ピンク キラキラ",
    "ネオンピンク", "ホットピンク", "ショッキングピンク",
    "pink glitter", "pink rhinestone", "pink sequin", "holographic pink",
    "ピンク バッグ ラメ", "ピンク 財布 キラキラ", "ピンク アクセサリー ストーン",
    "ピンク シューズ スパンコール", "ピンク ジュエリー クリスタル",
    "ピンク 財布 ラインストーン", "ピンク バッグ スパンコール",
    # 🐆 レオパード×ピンク
    "ピンク レオパード バッグ", "ピンク ヒョウ柄 バッグ", "ピンク 豹柄",
    "ピンク レオパード 財布", "ピンク レオパード アクセサリー",
    "pink leopard bag", "pink animal print",
    # 🫧 クリア×ピンク
    "ピンク クリアバッグ", "ピンク 透明バッグ", "ピンク アクリルバッグ",
    "ピンク クリアポーチ", "ピンク PVCバッグ", "ピンク ビニールバッグ",
    "pink clear bag", "pink transparent bag", "pink acrylic bag",
]

# iPhone以外のスマホ機種名パターン（これが含まれていたら除外）
NON_IPHONE_MODELS = re.compile(
    r'AQUOS|XPERIA|Xperia|Galaxy|Redmi|OPPO|HUAWEI|Pixel|arrows|ZenFone|Zenfone|nubia|BASIO|'
    r'らくらく|TORQUE|Libero|Android One|S24|S23|S22|S21|A54|A53|A52|Find X|Reno',
    re.IGNORECASE
)

# iPhone番号抽出（iPhone 17, 16 Pro Max など → 17.0 などの数値）
def extract_iphone_num(title):
    """タイトルからiPhone番号を抽出。無ければNone"""
    m = re.search(r'iPhone\s*(\d+)', title, re.IGNORECASE)
    return int(m.group(1)) if m else None

def make_phone_case_key(title):
    """スマホケース商品のデザインキー（機種名を除去した文字列）"""
    # iPhoneモデル部分を除去
    key = re.sub(
        r'iPhone\s*\d+\s*(?:Pro\s*Max|Pro\s*Plus|Pro|Plus|Max|mini|SE)?\s*(?:シリーズ)?',
        '', title, flags=re.IGNORECASE
    )
    # その他機種表記を除去
    key = re.sub(r'(?:for\s+)?(?:スマホ|スマートフォン)(?:ケース)?', '', key)
    # 括弧・記号・空白を除去して小文字化
    key = re.sub(r'[\s　【】「」\[\]()（）・]+', '', key).lower()
    return key


def collect_yahoo(sb):
    YAHOO_APP_ID = os.environ.get("YAHOO_APP_ID", "")
    if not YAHOO_APP_ID:
        print("⚠️  YAHOO_APP_ID がないためスキップ")
        return 0

    count = 0
    # 商品名 → {price, url, title, image, keyword} の最安値候補を一時保存
    cheapest = {}
    for keyword in YAHOO_KEYWORDS:
        url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
        params = {
            "appid": YAHOO_APP_ID,
            "query": keyword,
            "results": 100,
            "sort": "-score",
            "image_size": 500,
        }
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            data = resp.json()
            hits = data.get("hits", [])

            for item in hits:
                title = item.get("name", "")
                if not title:
                    continue

                image = item.get("image", {})
                image_url = image.get("medium", "") or image.get("small", "")
                product_url = item.get("url", "") or item.get("externalUrl", "")
                if not product_url:
                    continue
                price_val = item.get("price", None)

                # スマホケース判定
                is_phone_case = bool(re.search(r'スマホケース|スマートフォンケース|iPhoneケース|phone case', title, re.IGNORECASE))

                if is_phone_case:
                    # iPhone以外の機種 → スキップ
                    if NON_IPHONE_MODELS.search(title):
                        continue
                    # iPhoneケースはデザインキーで重複チェック（機種名除去）
                    name_key = 'iphone_case:' + make_phone_case_key(title)
                    iphone_num = extract_iphone_num(title)
                    if name_key in cheapest:
                        # より新しいiPhoneモデルを優先
                        existing_num = cheapest[name_key].get("iphone_num")
                        if iphone_num and (existing_num is None or iphone_num > existing_num):
                            cheapest[name_key] = {"title": title, "image_url": image_url,
                                                  "url": product_url, "price_val": price_val,
                                                  "keyword": keyword, "iphone_num": iphone_num}
                        continue
                    else:
                        cheapest[name_key] = {"title": title, "image_url": image_url,
                                              "url": product_url, "price_val": price_val,
                                              "keyword": keyword, "iphone_num": iphone_num}
                else:
                    # 通常商品：商品名全体で最安値チェック
                    name_key = re.sub(r'[\s　【】「」\[\]()（）]+', '', title).lower()
                    if name_key in cheapest:
                        existing_price = cheapest[name_key]["price_val"]
                        if price_val and (existing_price is None or price_val < existing_price):
                            cheapest[name_key] = {"title": title, "image_url": image_url,
                                                  "url": product_url, "price_val": price_val, "keyword": keyword}
                    else:
                        cheapest[name_key] = {"title": title, "image_url": image_url,
                                              "url": product_url, "price_val": price_val, "keyword": keyword}

            time.sleep(0.5)
        except Exception as e:
            print(f"  Yahoo エラー ({keyword}): {e}")

    # 最安値候補をまとめてDB保存
    for name_key, d in cheapest.items():
        price = f"¥{int(d['price_val']):,}" if d["price_val"] else None
        if save_product(sb, d["title"], d["image_url"], d["url"], "yahoo", d["keyword"], price=price):
            count += 1

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

    print("\n📦 BUYMA 収集中...")
    total += collect_buyma(sb)

    print("\n📦 Yahoo!ショッピング 収集中...")
    total += collect_yahoo(sb)

    print("\n" + "=" * 50)
    print(f"🎉 完了！ 合計 {total} 件をSupabaseに登録しました")

    # 登録済み件数確認
    result = sb.table("pink_products").select("id", count="exact").execute()
    print(f"📊 データベース総件数: {result.count} 件")


if __name__ == "__main__":
    main()
