-- PINK CITY コレクター テーブル
create table if not exists pink_products (
  id uuid default gen_random_uuid() primary key,
  product_name text not null,
  image_url text,
  product_url text not null,
  source text,  -- 'etsy', 'aliexpress', 'amazon', 'rakuten', etc.
  status text default 'pending',  -- 'pending', 'approved', 'rejected'
  pink_keywords text,  -- どのキーワードで見つかったか
  created_at timestamp with time zone default now()
);

-- 重複URLを防ぐ
create unique index if not exists pink_products_url_idx on pink_products(product_url);

-- ステータス別に取得しやすくするインデックス
create index if not exists pink_products_status_idx on pink_products(status);
