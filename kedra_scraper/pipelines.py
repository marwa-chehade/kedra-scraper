import os
import re
import time
import urllib.request
from itemadapter import ItemAdapter


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


class PdfDownloadPipeline:
    MAX_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 3

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        pdf_urls = adapter.get('files', [])
        if not pdf_urls:
            return item

        os.makedirs('downloads', exist_ok=True)
        title_slug = slugify(adapter.get('title', 'untitled'))

        for index, url in enumerate(pdf_urls, start=1):
            if len(pdf_urls) > 1:
                filename = f"{title_slug}-{index}.pdf"
            else:
                filename = f"{title_slug}.pdf"
            filepath = os.path.join('downloads', filename)
            self.download_with_retry(url, filepath, spider)

        return item

    def download_with_retry(self, url, filepath, spider):
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                urllib.request.urlretrieve(url, filepath)
                spider.logger.info(f"Downloaded {url} -> {filepath}")
                return
            except Exception as e:
                if attempt < self.MAX_ATTEMPTS:
                    spider.logger.warning(
                        f"Attempt {attempt} failed for {url}: {e}. Retrying..."
                    )
                    time.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    spider.logger.warning(
                        f"Giving up on {url} after {self.MAX_ATTEMPTS} attempts: {e}"
                    )