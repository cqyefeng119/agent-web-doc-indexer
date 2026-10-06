import json
from pathlib import Path
from urllib.parse import urlparse

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.linkextractors import LinkExtractor
from w3lib.url import canonicalize_url


class SiteTreeSpider(scrapy.Spider):
    name = "site_tree"

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 0.1,

        # できるだけ浅いページから取得する
        "DEPTH_PRIORITY": 1,
        "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",

        "LOG_LEVEL": "INFO",
    }

    def __init__(
        self,
        start_url=None,
        max_depth=3,
        max_pages=500,
        output="site_tree.json",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError(
                "start_url is required. "
                "Example: -a start_url=https://docs.example.com/"
            )

        self.root_url = self.normalize_url(start_url)
        self.max_depth = int(max_depth)
        self.max_pages = int(max_pages)
        self.output = output

        parsed = urlparse(self.root_url)
        self.host = parsed.hostname

        if not self.host:
            raise ValueError(f"Invalid URL: {start_url}")

        self.start_urls = [self.root_url]
        self.allowed_domains = [self.host]

        self.link_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            deny=(
                r"/release-notes/",
            ),
            unique=True,
        )

        # URL -> title
        self.pages = {}

        # parent URL -> child URLs
        self.edges = {}

        # URL -> 最初に見つけたリンクテキスト
        self.link_texts = {}

        self.page_count = 0

    @staticmethod
    def normalize_url(url):
        """
        #fragment を削除し、同一URLを安定して比較できる形にする。
        """
        return canonicalize_url(
            url,
            keep_fragments=False,
        )

    def parse(self, response):
        depth = response.meta.get("tree_depth", 0)
        current_url = self.normalize_url(response.url)

        self.page_count += 1

        if self.page_count > self.max_pages:
            raise CloseSpider("max_pages_reached")

        # title取得
        title = response.css("title::text").get()

        if title:
            title = " ".join(title.split())
        else:
            title = response.css("h1::text").get()

            if title:
                title = " ".join(title.split())

        if not title:
            title = self.link_texts.get(current_url, current_url)

        self.pages[current_url] = {
            "title": title,
            "url": current_url,
        }

        self.edges.setdefault(current_url, [])

        # max depthなら、ここから先は辿らない
        if depth >= self.max_depth:
            return

        for link in self.link_extractor.extract_links(response):
            child_url = self.normalize_url(link.url)

            # self linkは不要
            if child_url == current_url:
                continue

            # parent -> child 関係は重複させない
            if child_url not in self.edges[current_url]:
                self.edges[current_url].append(child_url)

            link_text = " ".join((link.text or "").split())

            if link_text and child_url not in self.link_texts:
                self.link_texts[child_url] = link_text

            yield scrapy.Request(
                child_url,
                callback=self.parse,
                meta={
                    "tree_depth": depth + 1,
                },
            )

    def build_tree(self, url, depth=0, path=None):
        """
        取得したWebグラフを再帰JSONとして展開。

        同じURLが別ルートから現れることは許可する。
        ただし同じ経路内で循環した場合だけ停止する。
        """
        if path is None:
            path = set()

        page = self.pages.get(url)

        title = (
            page["title"]
            if page
            else self.link_texts.get(url, url)
        )

        node = {
            "title": title,
            "url": url,
            "depth": depth,
            "children": [],
        }

        # A -> B -> A のような循環だけ止める
        if url in path:
            return node

        if depth >= self.max_depth:
            return node

        new_path = path | {url}

        for child_url in self.edges.get(url, []):
            node["children"].append(
                self.build_tree(
                    child_url,
                    depth=depth + 1,
                    path=new_path,
                )
            )

        return node

    def closed(self, reason):
        tree = self.build_tree(self.root_url)

        output_path = Path(self.output)

        output_path.write_text(
            json.dumps(
                tree,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self.logger.info(
            "Saved %s pages to %s (reason=%s)",
            len(self.pages),
            output_path,
            reason,
        )