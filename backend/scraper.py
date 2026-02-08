"""
PriceWatch AI - Web Scraping Engine
Automated price extraction from e-commerce websites
"""

import asyncio
import re
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Browser, Page
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceScraper:
    """Main scraping engine for extracting product prices"""

    def __init__(self, use_proxy: bool = False, proxy_url: Optional[str] = None):
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        self.browser: Optional[Browser] = None

        # Price extraction patterns for major e-commerce sites
        self.site_patterns = {
            "amazon.com": {
                "price_selectors": [
                    ".a-price-whole",
                    "#priceblock_ourprice",
                    "#priceblock_dealprice",
                    ".a-price .a-offscreen",
                    "[data-a-color='price'] .a-offscreen"
                ],
                "name_selectors": ["#productTitle", "h1.product-title"],
                "stock_selectors": ["#availability span"]
            },
            "walmart.com": {
                "price_selectors": [
                    "[itemprop='price']",
                    ".price-characteristic",
                    "[data-testid='price']",
                    "span[data-automation-id='product-price']"
                ],
                "name_selectors": ["h1[itemprop='name']", "h1.prod-ProductTitle"],
                "stock_selectors": ["[data-testid='fulfillment-badge']"]
            },
            "target.com": {
                "price_selectors": [
                    "[data-test='product-price']",
                    ".h-text-orangeDark",
                    "[data-test='product-price-current']"
                ],
                "name_selectors": ["[data-test='product-title']", "h1"],
                "stock_selectors": ["[data-test='availability']"]
            },
            "ebay.com": {
                "price_selectors": [
                    ".x-price-primary",
                    "[itemprop='price']",
                    ".display-price"
                ],
                "name_selectors": ["h1.x-item-title__mainTitle", ".it-ttl"],
                "stock_selectors": [".x-quantity__availability"]
            },
            "bestbuy.com": {
                "price_selectors": [
                    "[data-testid='customer-price']",
                    ".priceView-customer-price",
                    ".pricing-price__regular-price"
                ],
                "name_selectors": ["h1.sku-title", ".heading-5"],
                "stock_selectors": [".fulfillment-add-to-cart-button"]
            }
        }

    async def initialize(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()

        launch_options = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        }

        if self.use_proxy and self.proxy_url:
            launch_options["proxy"] = {"server": self.proxy_url}

        self.browser = await playwright.chromium.launch(**launch_options)
        logger.info("✅ Browser initialized")

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www.
        domain = domain.replace("www.", "")
        return domain

    def clean_price(self, price_text: str) -> Optional[float]:
        """Clean and convert price text to float"""
        if not price_text:
            return None

        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d.,]', '', price_text)

        # Handle different decimal separators
        # $1,234.56 -> 1234.56
        # €1.234,56 -> 1234.56
        if ',' in cleaned and '.' in cleaned:
            # If both present, last one is decimal
            if cleaned.rindex(',') > cleaned.rindex('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Check if it's decimal or thousands separator
            parts = cleaned.split(',')
            if len(parts[-1]) == 2:  # Likely decimal (e.g., 12,99)
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')

        try:
            price = float(cleaned)
            return round(price, 2)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse price: {price_text}")
            return None

    async def extract_with_selectors(self, page: Page, selectors: list) -> Optional[str]:
        """Try multiple selectors and return first match"""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and text.strip():
                        return text.strip()
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        return None

    async def scrape_product(self, url: str) -> Dict[str, Any]:
        """
        Scrape product information from URL

        Returns:
            {
                "success": bool,
                "url": str,
                "price": float,
                "currency": str,
                "name": str,
                "in_stock": bool,
                "timestamp": datetime,
                "error": str (optional)
            }
        """
        if not self.browser:
            await self.initialize()

        result = {
            "success": False,
            "url": url,
            "price": None,
            "currency": "USD",
            "name": None,
            "in_stock": None,
            "timestamp": datetime.now(),
            "error": None
        }

        try:
            # Create new page
            page = await self.browser.new_page()

            # Set user agent to avoid bot detection
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            })

            # Navigate to page
            logger.info(f"Scraping: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for page to load
            await page.wait_for_timeout(2000)

            # Detect site and use appropriate selectors
            domain = self.extract_domain(url)
            patterns = None

            for site_domain, site_patterns in self.site_patterns.items():
                if site_domain in domain:
                    patterns = site_patterns
                    break

            if patterns:
                # Extract price
                price_text = await self.extract_with_selectors(page, patterns["price_selectors"])
                if price_text:
                    result["price"] = self.clean_price(price_text)

                # Extract name
                name_text = await self.extract_with_selectors(page, patterns["name_selectors"])
                if name_text:
                    result["name"] = name_text[:200]  # Limit length

                # Extract stock status
                stock_text = await self.extract_with_selectors(page, patterns["stock_selectors"])
                if stock_text:
                    stock_lower = stock_text.lower()
                    result["in_stock"] = not any(word in stock_lower for word in ["out of stock", "unavailable", "sold out"])
            else:
                # Generic extraction if site not recognized
                logger.warning(f"Unknown site: {domain}, using generic extraction")

                # Try to find price in page text using regex
                content = await page.content()
                price_matches = re.findall(r'\$\s*(\d+[.,]\d{2})', content)
                if price_matches:
                    result["price"] = self.clean_price(price_matches[0])

                # Try to get title
                title = await page.title()
                result["name"] = title[:200] if title else None

            # Mark success if we got a price
            if result["price"] is not None:
                result["success"] = True
                logger.info(f"✅ Scraped: {result['name']} - ${result['price']}")
            else:
                result["error"] = "Price not found on page"
                logger.warning(f"⚠️ No price found for {url}")

            await page.close()

        except Exception as e:
            logger.error(f"❌ Scraping error for {url}: {str(e)}")
            result["error"] = str(e)

        return result

    async def scrape_multiple(self, urls: list) -> list:
        """Scrape multiple URLs concurrently"""
        if not self.browser:
            await self.initialize()

        tasks = [self.scrape_product(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "url": urls[i],
                    "error": str(result),
                    "timestamp": datetime.now()
                })
            else:
                processed_results.append(result)

        return processed_results


# ========================================
# TESTING & USAGE EXAMPLES
# ========================================

async def test_scraper():
    """Test the scraper with sample products"""
    scraper = PriceScraper()

    test_urls = [
        "https://www.amazon.com/dp/B0BSHF7WHW",  # Example product
        "https://www.walmart.com/ip/Apple-AirPods-Pro-2nd-Generation/1752657021",
        "https://www.target.com/p/apple-airpods-pro/-/A-54191097"
    ]

    print("🔍 Testing PriceWatch AI Scraper...")
    print("=" * 50)

    for url in test_urls:
        result = await scraper.scrape_product(url)
        print(f"\nURL: {result['url']}")
        print(f"Success: {result['success']}")
        print(f"Name: {result['name']}")
        print(f"Price: ${result['price']}" if result['price'] else "Price: Not found")
        print(f"In Stock: {result['in_stock']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        print("-" * 50)

    await scraper.close()


if __name__ == "__main__":
    # Run test
    asyncio.run(test_scraper())
