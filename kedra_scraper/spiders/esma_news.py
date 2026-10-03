import scrapy
from datetime import datetime
from kedra_scraper.items import NewsItem


class EsmaNewsSpider(scrapy.Spider):
    name = "esma_news"
    allowed_domains = ["esma.europa.eu"]
    start_urls = ["https://www.esma.europa.eu/press-news/esma-news"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_scraped = 0
        self.max_pages = 5

    def parse(self, response):
        self.pages_scraped += 1
        self.logger.info(f"Parsing listing page {self.pages_scraped}: {response.url}")

        item_links = response.css('div.news-contentcard a[rel="bookmark"]::attr(href)').getall()
        for link in item_links:
            yield response.follow(link, callback=self.parse_item)

        if self.pages_scraped < self.max_pages:
            next_page = response.css('a[rel="next"]::attr(href)').get()
            if next_page:
                yield response.follow(next_page, callback=self.parse)
            else:
                self.logger.warning("Expected a next page link but found none.")

    def parse_item(self, response):
        item = NewsItem()
        item["title"] = response.css('h1 .field--name-title::text').get(default="").strip()
        raw_date = response.css('.publication-date::text').get(default="").strip()
        item["date"] = self.normalize_date(raw_date)
        item["source_url"] = response.url

        description_parts = response.css('.field--name-field-news-body ::text').getall()
        item["description"] = " ".join(part.strip() for part in description_parts if part.strip())

        pdf_links = response.css('a[href$=".pdf"]::attr(href)').getall()
        item["files"] = sorted(set(response.urljoin(link) for link in pdf_links))

        yield item

    @staticmethod
    def normalize_date(raw_date):
        try:
            return datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None