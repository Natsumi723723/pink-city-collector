# 💖 PINK CITY Collector

> 世界中のPINK商品を自動収集して、Supabaseに登録するツール。

ネオン・ホットピンク・グリッター・ホログラム・オーロラ・ローズ系など、**ギラギラ・濃いピンク**に特化したキュレーションコレクター。

---

## 何ができるの？

- 🔍 Amazon / AliExpress / 楽天 からPINK商品を自動収集
- 🗄️ Supabaseへ自動登録（商品名・画像URL・商品URL）
- 💖 レビューUI で 💗/✕ ワンタップ判定
- 🚫 お花・植物系を自動スキップ

---

## セットアップ

### 1. パッケージインストール
```bash
pip3 install supabase beautifulsoup4 requests
```

### 2. .envファイルを作成
```bash
cp .env.example .env
```
`.env` を開いてSupabaseのURLとキーを入力。

### 3. Supabaseにテーブル作成
Supabase の SQL Editor で `setup_supabase.sql` を実行。

---

## 収集を実行する

```bash
cd pink-city-collector
source .env && python3 collector.py
```

---

## レビューUIを使う

```bash
python3 -m http.server 8888
```

ブラウザで `http://localhost:8888/review.html` を開く。

SupabaseのURLとAnon Keyを入力して「PINKを読み込む」→ 💗/✕ で判定するだけ！

---

## 収集キーワード（一部）

| カテゴリ | キーワード例 |
|---------|------------|
| ネオン系 | neon pink, hot pink, electric pink |
| キラキラ系 | pink glitter, pink sequin, pink sparkle |
| ホログラム系 | holographic pink, aurora pink, iridescent pink |
| ローズ系 | rose pink, deep rose, neon rose |
| 中国語 | 荧光粉, 粉色亮片, 玫红色 |
| 日本語 | ネオンピンク, ピンクラメ, オーロラピンク |

---

## これは何のプロジェクト？

**PINK CITY** — 世界中の買えるPINK商品を全部集めることが目標の、純粋欲求プロジェクト。💖
