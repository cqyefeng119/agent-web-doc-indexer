# Scrapy Crawler

English | [日本語](README.ja.md) | [中文](README.zh.md)

这是一个用于抓取网站链接结构，并生成给 Agent 检索使用的递归 JSON Tree 的工具。

## 1. 使用方法

安装依赖:

```bash
uv add scrapy
```

运行示例:

```bash
uv run scrapy runspider crawler.py \
  -a start_url=https://example.com/ \
  -a deny_patterns='["/release-notes/", "/archive/"]'\
  -a max_depth=2 \
  -a max_pages=200 \
  -a output=site_tree.json
```

主要参数:

- `start_url`: 抓取起始 URL
- `max_depth`: 允许跟随的最大链接层级
- `max_pages`: 最大抓取页面数
- `output`: 输出 JSON 文件
- `deny_patterns`: 用于排除 URL 的正则表达式 JSON 数组（默认: `[]`，无自定义排除规则）



匹配任意模式的链接都会被排除。起始 URL 本身不受此规则过滤。
在 shell 中使用单引号包裹整个数组，JSON 字符串使用双引号。
正则表达式中的反斜杠必须在 JSON 中转义（例如 `"\\.pdf$"`）。
无效 JSON、非字符串元素和无效正则表达式都会导致启动错误。

输出示例:

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
如果同一个页面可以通过多个路径到达，会在每个分支中保留相同的 URL。

每个节点都有表示其在树中位置的层级 ID，例如 `1`、`1-1` 和 `1-1-1`。
如果同一个页面通过多个路径到达，每条路径都会有独立的 ID。


## 2. 概念

本项目使用 [Scrapy](https://scrapy.org/) 原样获取网站已有的链接结构。

它不做基于 LLM 的分类，也不做向量检索，而是按照下面的思路构建适合 Agent 使用的索引：

```text
Web Docs
   ↓
Scrapy 提取链接结构
   ↓
id / title / url / children
   ↓
递归 JSON Tree
   ↓
Agent 逐层遍历 Tree 找到目标 URL
```

## 3. 限制

- JavaScript 动态生成的链接可能无法抓取。
- 页脚、页眉、Release Notes 等非目标链接也可能被抓取。
- `max_depth` 设得越大，页面数量可能增长得很快。
- 如果网站本身的链接结构不适合搜索，生成的树也会难以检索。
- 不进行语义分类、摘要或相关性判断。
- 某些页面可能会被 `robots.txt` 限制。