# Kedra Data Engineer Coding Test

## Part 1: Scraper

### Setup

1. Clone this repository and navigate into it.
2. Create a virtual environment and activate it:
```
python -m venv venv
venv\Scripts\activate # Windows
source venv/bin/activate # macOS/Linux
```
3. Install dependencies:
```
pip install scrapy
```
### Running the scraper

Clear any previous output, then run:
```
Remove-Item downloads -Recurse -Force -ErrorAction SilentlyContinue
scrapy crawl esma_news -o output.jsonl
```

This crawls the first 5 pages of ESMA news, writes one JSON object per item to `output.jsonl`, and downloads PDFs into `./downloads/`, named after each article.

### Known limitations

- PDF downloads are retried up to 3 times on failure, but the `downloads` folder is not cleared automatically between runs — run the `Remove-Item` command above first for a clean result.
- Downloads use Python's built-in `urllib`, which is synchronous and slower than Scrapy's own async requests; a production version might integrate with Scrapy's `FilesPipeline` instead.

## Part 2: Selectors

### 2a — Results table
| Field | Selector |
|---|---|
| Repeating item | `table.results tr:has(td)` |
| Title | `td a::text` |
| Date | `td:nth-child(3)::text` |
| Link | `td a::attr(href)` |

### 2b — Publications list
| Field | Selector |
|---|---|
| Repeating item | `div.row` |
| Title | `h3 a::text` |
| Date | `.meta::text` |
| Link | `h3 a::attr(href)` |
| Description | `p.summary::text` |
| File | `a.download::attr(href)` |

### 2c — News page
| Field | Selector |
|---|---|
| Repeating item | `#latest .card` |
| Title | `h2 a::text` |
| Date | `time::text` |
| Link | `h2 a::attr(href)` |

**Note:** date formats vary across these snippets and would likely vary further on real sites (e.g. `04/03/2025` vs. `12 May 2025`). These selectors extract the raw date text only — normalizing it to a consistent format (as done in Part 1) is a separate step handled after extraction, not by the selector itself.

## Part 3: JavaScript

To reveal the hidden accordion panels:

```javascript
function revealAccordions() {
  document.querySelectorAll('.accordion-body').forEach(panel => {
    panel.style.display = 'block';
    panel.classList.remove('hidden');
  });
}

revealAccordions();
```

**Surviving re-renders:** Some sites redraw parts of the page automatically after load, which could silently reset the accordion back to hidden. To survive this, I'd wrap the reveal logic in a named function and register it with a `MutationObserver`, which watches the page for DOM changes and reruns the function automatically whenever something changes, rather than fixing the panels only once:

```javascript
const observer = new MutationObserver(revealAccordions);
observer.observe(document.body, { childList: true, subtree: true });
```

## Part 4: Debugging

1. **Scraper returns nothing; browser shows results; saved HTML is just `<div id="root"></div>`.**
   The page is rendered client-side by JavaScript after the server sends a near-empty HTML skeleton. Scrapy only downloads the raw HTML and does not execute JavaScript, so it captures the page before any content is injected. The fix is to use a tool that renders JavaScript before returning the page — such as Scrapy's Splash integration, or a headless browser tool like Playwright or Selenium.

2. **Stored URL has `%25E2%2580%2599` where the live site has `%E2%80%99`; returns 404.**
   The URL has been percent-encoded twice — `%25` is itself the encoded form of the `%` character, so an already-encoded URL (`%E2%80%99`) got run through encoding again, turning every `%` into `%25`. To prevent this, I'd make sure a URL is only ever encoded once, right before it's used in a request, and check the pipeline for any place a URL might pass through an encoding step twice (e.g. once when extracted from HTML, again when building the request).

3. **PDF guard `extension(url) == "pdf"` never fires for `/reports/annual.pdf?v=8f21c3`.**
   `extension(url)` likely extracts everything after the last `.` in the raw URL, including the query string — so it returns `"pdf?v=8f21c3"` instead of `"pdf"`. Since that never equals `"pdf"`, the guard's skip condition is never true, so PDFs slip through and get incorrectly parsed as HTML. The fix is to strip the query string before checking the extension — e.g. using a proper URL-parsing function (like Python's `urllib.parse.urlparse`) to isolate the path first, rather than operating on the raw URL string.