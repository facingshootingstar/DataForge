"""
DataForge - Web Scraper
========================
Multi-strategy web scraper with requests + BeautifulSoup
for static pages and Playwright for JS-rendered pages.
Includes retry logic, rate limiting, and structured output.
"""

from __future__ import annotations

import time
from typing import Any
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd
from loguru import logger

from config import SCRAPING


class WebScraper:
    """
    Production web scraper with dual-engine support.

    Usage:
        scraper = WebScraper()

        # Static page
        data = scraper.scrape_table("https://example.com/data")

        # Dynamic (JS-rendered) page
        data = scraper.scrape_dynamic("https://example.com/spa", selector=".data-table")

        # Custom extraction
        soup = scraper.get_soup("https://example.com")
        items = scraper.extract(soup, {
            "title": "h1.title",
            "price": "span.price",
            "desc": "p.description",
        })
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": SCRAPING.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    # ── Static Scraping (requests + BS4) ─────────────────────

    def get_soup(
        self, url: str, retries: int | None = None
    ) -> BeautifulSoup:
        """Fetch a page and return parsed BeautifulSoup object."""
        max_retries = retries or SCRAPING.max_retries

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt}/{max_retries})")
                resp = self._session.get(url, timeout=SCRAPING.timeout_ms / 1000)
                resp.raise_for_status()
                return BeautifulSoup(resp.text, "lxml")
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(SCRAPING.retry_delay * attempt)
                else:
                    raise

    def scrape_table(
        self,
        url: str,
        table_index: int = 0,
        header_row: int = 0,
    ) -> pd.DataFrame:
        """Scrape an HTML table into a DataFrame."""
        logger.info(f"Scraping table from: {url}")
        try:
            tables = pd.read_html(url, header=header_row)
            if not tables:
                logger.warning("No tables found on page")
                return pd.DataFrame()
            logger.info(f"Found {len(tables)} tables, returning index {table_index}")
            return tables[table_index]
        except Exception as e:
            logger.error(f"Table scraping failed: {e}")
            return pd.DataFrame()

    def extract(
        self,
        soup: BeautifulSoup,
        selectors: dict[str, str],
        multiple: bool = False,
    ) -> list[dict[str, str]] | dict[str, str]:
        """
        Extract data using CSS selectors.

        Args:
            soup: BeautifulSoup object
            selectors: dict mapping field names to CSS selectors
            multiple: If True, extract all matches (returns list of dicts)
        """
        if multiple:
            return self._extract_multiple(soup, selectors)
        else:
            return self._extract_single(soup, selectors)

    def scrape_multiple_pages(
        self,
        urls: list[str],
        selectors: dict[str, str],
        delay: float = 1.0,
    ) -> pd.DataFrame:
        """
        Scrape multiple pages and combine results into a DataFrame.

        Args:
            urls: List of URLs to scrape
            selectors: CSS selectors for data extraction
            delay: Delay between requests (seconds)
        """
        all_data: list[dict] = []

        for i, url in enumerate(urls, 1):
            logger.info(f"Scraping page {i}/{len(urls)}: {url}")
            try:
                soup = self.get_soup(url)
                items = self.extract(soup, selectors, multiple=True)
                for item in items:
                    item["_source_url"] = url
                all_data.extend(items)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")

            if i < len(urls):
                time.sleep(delay)

        df = pd.DataFrame(all_data)
        logger.info(f"Scraped {len(df)} items from {len(urls)} pages")
        return df

    # ── Dynamic Scraping (Playwright) ────────────────────────

    def scrape_dynamic(
        self,
        url: str,
        selector: str | None = None,
        wait_for: str | None = None,
        extract_selectors: dict[str, str] | None = None,
        screenshot_path: str | None = None,
    ) -> pd.DataFrame | str:
        """
        Scrape JS-rendered pages using Playwright.

        Args:
            url: Target URL
            selector: CSS selector to wait for before extracting
            wait_for: Additional selector to wait for
            extract_selectors: If provided, extract structured data
            screenshot_path: If provided, save screenshot
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: playwright install chromium")
            raise

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=SCRAPING.headless)
            context = browser.new_context(
                user_agent=SCRAPING.user_agent,
                viewport={"width": 1920, "height": 1080},
            )
            page = context.new_page()

            try:
                logger.info(f"Loading dynamic page: {url}")
                page.goto(url, timeout=SCRAPING.timeout_ms)

                if wait_for:
                    page.wait_for_selector(wait_for, timeout=SCRAPING.timeout_ms)
                elif selector:
                    page.wait_for_selector(selector, timeout=SCRAPING.timeout_ms)
                else:
                    page.wait_for_load_state("networkidle")

                if screenshot_path:
                    page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"Screenshot saved: {screenshot_path}")

                if extract_selectors:
                    html = page.content()
                    soup = BeautifulSoup(html, "lxml")
                    items = self.extract(soup, extract_selectors, multiple=True)
                    return pd.DataFrame(items)

                # Return page content for custom processing
                if selector:
                    element = page.query_selector(selector)
                    return element.inner_html() if element else ""
                return page.content()

            finally:
                browser.close()

    # ── Pagination Support ───────────────────────────────────

    def scrape_paginated(
        self,
        base_url: str,
        selectors: dict[str, str],
        next_page_selector: str = "a.next",
        max_pages: int = 10,
        delay: float = 1.5,
    ) -> pd.DataFrame:
        """Scrape paginated content following next-page links."""
        all_data: list[dict] = []
        current_url = base_url

        for page_num in range(1, max_pages + 1):
            logger.info(f"Scraping page {page_num}: {current_url}")
            try:
                soup = self.get_soup(current_url)
                items = self.extract(soup, selectors, multiple=True)

                if not items:
                    logger.info("No more items found, stopping pagination")
                    break

                for item in items:
                    item["_page"] = page_num
                all_data.extend(items)

                # Find next page link
                next_link = soup.select_one(next_page_selector)
                if not next_link or not next_link.get("href"):
                    logger.info("No next page link found, stopping")
                    break

                href = next_link["href"]
                if href.startswith("http"):
                    current_url = href
                elif href.startswith("/"):
                    from urllib.parse import urljoin
                    current_url = urljoin(base_url, href)
                else:
                    break

                time.sleep(delay)

            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                break

        return pd.DataFrame(all_data)

    # ── Private Helpers ──────────────────────────────────────

    def _extract_single(
        self, soup: BeautifulSoup, selectors: dict[str, str]
    ) -> dict[str, str]:
        result = {}
        for field, css in selectors.items():
            el = soup.select_one(css)
            result[field] = el.get_text(strip=True) if el else None
        return result

    def _extract_multiple(
        self, soup: BeautifulSoup, selectors: dict[str, str]
    ) -> list[dict[str, str]]:
        """Extract all matching items. Aligns on the first selector."""
        first_key = list(selectors.keys())[0]
        first_css = selectors[first_key]
        anchors = soup.select(first_css)

        if not anchors:
            return []

        results = []
        for anchor in anchors:
            item = {first_key: anchor.get_text(strip=True)}
            # Try to find sibling/parent matches for other fields
            parent = anchor.parent
            for field, css in selectors.items():
                if field == first_key:
                    continue
                # Search within parent context
                while parent:
                    el = parent.select_one(css)
                    if el:
                        item[field] = el.get_text(strip=True)
                        break
                    parent = parent.parent
                if field not in item:
                    # Fallback: search entire soup
                    el = soup.select_one(css)
                    item[field] = el.get_text(strip=True) if el else None
            results.append(item)

        return results
