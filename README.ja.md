# Scrapy Crawler

English | [日本語](README.ja.md) | [中文](README.zh.md)

Webサイトのリンク構造をクロールし、Agent検索用の再帰JSON Treeを生成するツールです。

## 1. 使い方

依存関係をインストールします。

```bash
uv add scrapy
```

実行例:

```bash
uv run scrapy runspider crawler.py \
  -a start_url=https://example.com/ \
  -a deny_patterns='["/release-notes/", "/archive/"]'\
  -a max_depth=2 \
  -a max_pages=200 \
  -a output=site_tree.json
```

主な引数:

- `start_url`: クロール開始URL
- `max_depth`: リンクを辿る最大階層
- `max_pages`: 最大取得ページ数
- `output`: 出力JSONファイル
- `deny_patterns`: 除外するURLの正規表現を指定するJSON配列（既定値: `[]`、独自の除外なし）



いずれかのパターンに一致するリンクを除外します。開始URL自体は除外対象になりません。
シェルでは配列全体をシングルクォートで囲み、JSON内の文字列にはダブルクォートを使います。
正規表現のバックスラッシュはJSON内でエスケープします（例: `"\\.pdf$"`）。
不正なJSON、文字列以外の要素、不正な正規表現は起動時エラーになります。

出力例:

```json
{
  "title": "Root",
  "url": "https://example.com/",
  "id": "1",
  "children": [
    {
      "title": "Page A",
      "url": "https://example.com/a",
      "id": "1-1",
      "children": [
        {
          "title": "Page C",
          "url": "https://example.com/c",
          "id": "1-1-1",
          "children": []
        }
      ]
    },
    {
      "title": "Page B",
      "url": "https://example.com/b",
      "id": "1-2",
      "children": [
        {
          "title": "Page C",
          "url": "https://example.com/c",
          "id": "1-2-1",
          "children": []
        }
      ]
    }
  ]
}
```
同じページに複数経路から到達できる場合は、それぞれの枝に同じURLを残します。

各ノードには、Tree上の位置を表す階層IDが付きます。例: `1`, `1-1`, `1-1-1`。
同じページに複数経路から到達した場合は、経路ごとに異なるIDになります。


## 2. コンセプト

[Scrapy](https://scrapy.org/) を利用して、Webサイトが持つ既存のリンク構造をそのまま取得します。

LLMによる分類やEmbedding検索は行わず、以下の考え方でAgent向け索引を生成します。

```text
Web Docs
   ↓
Scrapyでリンク構造を取得
   ↓
id / title / url / children
   ↓
再帰JSON Tree
   ↓
AgentがTreeを辿って対象URLを探す
```



## 3. 制限

- JavaScriptで動的生成されるリンクは取得できない場合があります。
- Footer、ヘッダー、Release Notesなど不要なリンクも取得される場合があります。
- `max_depth` を大きくすると対象ページ数が急増する可能性があります。
- Webサイトのリンク構造自体が適切でない場合、生成されるTreeも検索しにくくなります。
- 意味的な分類、要約、関連度判定は行いません。
- `robots.txt` の設定によりクロールできないページがあります。