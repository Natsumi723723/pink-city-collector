"""
既存DBのglitter/neon商品の中でCLEARに再分類すべきものを更新するスクリプト
"""
import os
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_ANON_KEY'])

CLEAR_WORDS = [
    "クリアバッグ", "クリアポーチ", "クリアトート", "クリアショルダー",
    "透明バッグ", "透明ポーチ", "透明トート", "透明ショルダー",
    "clear bag", "clear pouch", "clear tote", "clear shoulder",
    "pvcバッグ", "pvc bag", "ビニールバッグ", "ビニールポーチ",
    "クリアケース", "透明ケース", "クリアカバー", "透明カバー",
    "clear case", "clear cover", "transparent case",
    "アクリルバッグ", "アクリルケース", "アクリルポーチ",
    "アクリルキーホルダー", "アクリルチャーム", "アクリルスタンド",
    "acrylic bag", "acrylic case", "acrylic charm", "acrylic keychain",
    "pvcポーチ", "pvcケース", "pvc pouch", "pvcトート",
    "ビニールケース", "ビニールトート",
    "クリア素材", "透明素材", "クリアpvc", "透明pvc",
    "ジェリーバッグ", "ジェリーポーチ", "ゼリーバッグ",
    "jelly bag", "jelly purse",
]

def is_clear(name):
    n = name.lower()
    return any(w.lower() in n for w in CLEAR_WORDS)

# glitter/neonのうちclearキーワードを含むものを取得
print("DBから全商品を取得中...")
all_products = []
offset = 0
PAGE = 1000
while True:
    res = sb.table('pink_products').select('id,product_name,style,status').neq('style', 'clear').range(offset, offset+PAGE-1).execute()
    batch = res.data
    all_products.extend(batch)
    if len(batch) < PAGE:
        break
    offset += PAGE

print(f"取得: {len(all_products)}件")

targets = [p for p in all_products if is_clear(p['product_name'] or '')]
print(f"CLEARに再分類すべき商品: {len(targets)}件")

for p in targets[:5]:
    print(f"  [{p['style']}] {p['product_name'][:60]}")

if not targets:
    print("対象なし")
    exit()

ans = input(f"\n{len(targets)}件をstyle=clearに更新しますか？ (y/n): ")
if ans.lower() != 'y':
    print("キャンセル")
    exit()

updated = 0
for p in targets:
    sb.table('pink_products').update({'style': 'clear'}).eq('id', p['id']).execute()
    updated += 1
    if updated % 10 == 0:
        print(f"  {updated}/{len(targets)}件更新中...")

print(f"\n完了: {updated}件をCLEARに更新しました")
