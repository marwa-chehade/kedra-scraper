import scrapy


class NewsItem(scrapy.Item):
    title = scrapy.Field()
    date = scrapy.Field()
    source_url = scrapy.Field()
    description = scrapy.Field()
    files = scrapy.Field()