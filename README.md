# Scrapy Crawler

English | [日本語](README.ja.md) | [中文](README.zh.md)

This tool crawls a website's link structure and generates a recursive JSON tree for agent search.

## 1. Usage

Install the dependency:

```bash
uv add scrapy
```

Example:

```bash
uv run scrapy runspider crawler.py \
  -a start_url=https://example.com/ \
  -a max_depth=2 \
  -a max_pages=200 \
  -a output=site_tree.json
```

Main arguments:

- `start_url`: URL to start crawling from
- `max_depth`: Maximum link depth to follow
- `max_pages`: Maximum number of pages to fetch
- `output`: Output JSON file

Example output:

```json
{
  "title": "Root",
  "url": "https://example.com/",
  "children": [
    {
      "title": "Page A",
      "url": "https://example.com/a",
      "children": [
        {
          "title": "Page C",
          "url": "https://example.com/c",
          "children": []
        }
      ]
    },
    {
      "title": "Page B",
      "url": "https://example.com/b",
      "children": [
        {
          "title": "Page C",
          "url": "https://example.com/c",
          "children": []
        }
      ]
    }
  ]
}
```
If the same page can be reached through multiple paths, the same URL is kept in each branch.


## 2. Concept

This project uses [Scrapy](https://scrapy.org/) to collect a website's existing link structure as-is.

It does not use LLM-based classification or embedding search. Instead, it builds an agent-friendly index with the following flow:

```text
Web Docs
   ↓
Scrapy extracts the link structure
   ↓
title / url / children
   ↓
Recursive JSON tree
   ↓
The agent walks the tree to find the target URL
```

## 3. Limitations

- Links generated dynamically by JavaScript may not be collected.
- Unwanted links such as footers, headers, and release notes may also be collected.
- Increasing `max_depth` can make the number of pages grow quickly.
- If the website's link structure itself is poor, the generated tree will also be hard to search.
- No semantic classification, summarization, or relevance ranking is performed.
- Some pages may be blocked by `robots.txt`.