# 💗 PINK CITY Collector

> 世界中の「ギラギラ系ピンク」商品を自動収集して、キュレーションするプロジェクト。

ネオン・ホットピンク・グリッター・ホログラム・オーロラ・ラメ・スパンコール・ラインストーン系など、**キラキラ・濃いピンクに特化**したコレクター。

🌐 **ギャラリー**: https://natsumi723723.github.io/pink-city-collector/

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `collector.py` | 商品収集スクリプト（全ソース） |
| `gallery.html` / `index.html` | ギャラリーサイト（棚UI） |
| `review.html` | レビュー・審査UI |
| `admin.html` | カテゴリ手動編集UI |
| `reclassify_clear.py` | 既存商品のstyle=clearへの再分類スクリプト |
| `backfill_prices.py` | 既存商品の価格を遡って取得 |
| `setup_supabase.sql` | Supabaseテーブル作成SQL |
| `.env` | APIキー（非公開） |

---

## 収集ソース

| ソース | 収集方法 | 対象 |
|--------|---------|------|
| **Amazon** | スクレイピング | バッグ・アクセサリー・雑貨・シューズ |
| **AliExpress** | スクレイピング | バッグ・アクセサリー・インテリア・シューズ |
| **BUYMA** | スクレイピング | バッグ・シューズ・アクセサリー（洋服除外） |
| **Yahoo Shopping** | 公式API（V3） | 全カテゴリ |
| **eBay** | 公式Browse API | 海外ブランド・グリッター・シューズ（新品のみ） |

> ⚠️ Etsy はBANされたため停止中。

---

## スタイルカテゴリ

収集商品は自動的に4スタイルに分類される：

| スタイル | 説明 |
|---------|------|
| ✨ **GLITTER** | ラメ・グリッター・スパンコール・ラインストーン系 |
| 🌈 **NEON** | ネオンピンク・蛍光・発光系 |
| 🐆 **LEOPARD** | ピンクレオパード・チーター柄系 |
| 🫧 **CLEAR** | クリア・透明・PVC・ジェリー・アクリル系ピンク |

---

## ギャラリーカテゴリ

承認済み商品は商品名のキーワードで自動分類（`category`カラムで手動上書き可）：

| カテゴリ | 対象 |
|---------|------|
| 👜 BAGS & POUCHES | バッグ・ポーチ・財布 |
| 💍 JEWELRY | ネックレス・リング・ピアス等 |
| 🎀 HAIR ACCESSORIES | ヘアクリップ・バレッタ等 |
| 💻 GADGETS | スマホケース（iPhoneのみ）・マウス等 |
| 🪩 NEON SIGNS & LIGHTS | ネオンサイン・LEDライト |
| 📓 STATIONERY | ノート・手帳・バインダー |
| 👠 FASHION & SHOES | シューズ・サンダル・ブーツ・帽子等 |
| 🎀 DECO & CRAFT | デコパーツ・ラインストーン・グリッターテープ等 |
| 🚗 CAR ACCESSORIES | ハンドルカバー・カーマット等 |
| ✨ OTHER | その他 |

---

## フィルタリングルール

収集した商品は以下の条件を**すべて満たす**ものだけDBに登録：

1. **ピンク語を含む**（商品名にピンク・pink・ローズ・rose等）
2. **ギラギラ語を含む**（グリッター・スパンコール・ラメ・ラインストーン・ホログラム・メタリック等）
3. **除外ワードを含まない**（洋服・コスメ・植物・音楽CD・ネイルポリッシュ等）
4. **スマホケース**: iPhoneのみ収集（AQUOS・XPERIA・Redmi・Galaxy等は除外）、複数機種は最新モデルのみ

---

## セットアップ

```bash
pip3 install supabase beautifulsoup4 requests python-dotenv
```

`.env` を作成：
```
SUPABASE_URL=https://xxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
YAHOO_APP_ID=xxxx
EBAY_APP_ID=xxxx-PRD-xxxx
EBAY_CERT_ID=PRD-xxxx
```

Supabaseのテーブル作成：
```sql
-- setup_supabase.sql を Supabase SQL Editor で実行
-- category カラムも追加済み:
ALTER TABLE pink_products ADD COLUMN IF NOT EXISTS category text;
```

---

## 収集を実行する

```bash
source .env && python3 collector.py
```

---

## ギャラリーサイト（gallery.html / index.html）

承認済み商品をショップの棚スタイルで一覧表示するサイト。

- **棚がカテゴリ別**に自動分類（DBの`category`カラムで手動上書き可）
- **スタイルフィルター**（ALL / ✨GLITTER / 🌈NEON / 🐆LEOPARD / 🫧CLEAR）
- **スタイル別承認数バー**（各カテゴリの承認済み件数を上部に表示）
- ソースフィルター（ALL / Amazon / AliExpress / BUYMA / Yahoo / eBay）
- キーワード検索・価格表示
- **デザインスキン切り替え**（💎ボタン）
  - 💎 RHINESTONE QUEEN — マゼンダピンク背景 + ネオングロー
  - 🔩 DARK CHROME — メタリックシルバー縁 + 高級感
  - 🌈 Y2K GLITTER — 虹色ホログラフィックボーダー
  - 🖤 NEON NOIR — 純黒 + シャープなネオンピンク
- スマホ対応（タッチスクロール・レスポンシブヘッダー）

---

## レビューUI（review.html）

収集されたpending商品を審査するUI。

- 💗 ボタン → 承認（ギャラリーに表示される）
- ✕ ボタン → 却下
- **スタイルフィルター**（ALL / GLITTER / NEON / LEOPARD / CLEAR）でスタイル別に審査
- **承認済みスタイル別件数**をリアルタイム表示（バランス確認用）
- ソースフィルター（ALL / Amazon / AliExpress / BUYMA / Yahoo / eBay）
- **ゲーミフィケーション**：TODAY / TOTAL / STREAK カウンター、マイルストーントースト、進捗メーター
- ヘッダーから **⚙️ ADMIN** ページへリンク

---

## 管理UI（admin.html）

承認済み商品のカテゴリを手動で変更するUI。

- 全承認済み商品をグリッド表示
- カテゴリドロップダウンで変更 → SAVEでSupabaseに即反映
- 手動設定した商品には「✏️ 手動」バッジ表示（ギャラリーで自動分類より優先）
- カテゴリフィルター・商品名検索付き
- review.htmlのヘッダーからアクセス可

---

## Supabaseテーブル構造（pink_products）

| カラム | 型 | 説明 |
|-------|-----|------|
| id | int8 | 自動採番 |
| product_name | text | 商品名 |
| image_url | text | 画像URL |
| product_url | text | 商品ページURL（UNIQUE） |
| source | text | amazon / aliexpress / buyma / yahoo / ebay |
| status | text | pending / approved / rejected |
| style | text | glitter / neon / leopard / clear |
| category | text | 手動カテゴリ上書き（nullable） |
| pink_keywords | text | ヒットしたキーワード |
| price | text | 価格（¥1,234 形式） |
| created_at | timestamptz | 登録日時 |

---

## これは何のプロジェクト？

**PINK CITY** — 世界中の買えるギラギラ系ピンク商品を全部集めることが目標の、純粋欲求プロジェクト。💗
