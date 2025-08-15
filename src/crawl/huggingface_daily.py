from typing import List, Dict, Any, Optional
import re
import httpx
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from src.logger import logger


class HuggingFaceDailyPapers:
    """Class for crawling and parsing Hugging Face daily papers"""
    
    def __init__(self):
        self.base_url = "https://huggingface.co/papers/date"
        self.timeout = 20
    
    def extract_arxiv_id(self, url: str) -> Optional[str]:
        """Extract arXiv ID from a URL"""
        if not url:
            return None
        # matches https://huggingface.co/papers/2508.10711
        m = re.search(r"huggingface\.co/papers/(\d{4,5}\.\d+)(v\d+)?", url)
        if m:
            return m.group(1)
        return None

    def extract_json_data(self, html: str) -> Dict[str, Any]:
        """Extract JSON data from the HTML page to get GitHub stars and other metadata."""
        try:
            soup = BeautifulSoup(html, "lxml")

            # Look for GitHub stars in the HTML structure
            # Based on the user's description, GitHub stars are displayed with SVG icons
            # Look for SVG elements that might represent GitHub stars
            svg_elements = soup.find_all("svg")

            github_stars_map = {}

            for svg in svg_elements:
                # Look for GitHub-related SVG (usually has specific viewBox or path)
                svg_html = str(svg)
                if "github" in svg_html.lower() or "256 250" in svg_html:  # GitHub icon viewBox
                    # Look for the star count near this SVG
                    parent = svg.parent
                    if parent:
                        # Look for numbers that might be star counts
                        text_content = parent.get_text()
                        numbers = re.findall(r'\b(\d+)\b', text_content)
                        if numbers:
                            # The number near a GitHub SVG is likely the star count
                            star_count = int(numbers[0])
                            # Try to find the paper title or ID to associate with
                            # Look for the closest article or card container
                            article = svg.find_parent("article")
                            if article:
                                title_elem = article.find("h3")
                                if title_elem:
                                    paper_title = title_elem.get_text(strip=True)
                                    github_stars_map[paper_title] = star_count

            # Also look for any elements with GitHub-related text
            github_text_elements = soup.find_all(string=lambda text: text and "github" in text.lower())
            for text_elem in github_text_elements:
                parent = text_elem.parent
                if parent:
                    text_content = parent.get_text()
                    numbers = re.findall(r'\b(\d+)\b', text_content)
                    if numbers:
                        star_count = int(numbers[0])
                        # Try to find the paper title
                        article = parent.find_parent("article")
                        if article:
                            title_elem = article.find("h3")
                            if title_elem:
                                paper_title = title_elem.get_text(strip=True)
                                if paper_title not in github_stars_map:
                                    github_stars_map[paper_title] = star_count

            return {"github_stars_map": github_stars_map}

        except Exception as e:
            logger.error(f"Error extracting JSON data: {e}")

        return {"github_stars_map": {}}

    async def fetch_daily_html(self, target_date: str) -> tuple[str, str]:
        """Fetch daily papers HTML, with fallback to find the latest available date"""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            # First try the requested date
            url = f"{self.base_url}/{target_date}"
            try:
                r = await client.get(url)

                # Check if we got redirected
                if r.status_code in [301, 302, 303, 307, 308]:
                    # We got redirected, extract the actual date from the redirect location
                    location = r.headers.get('location', '')
                    logger.info(f"Got redirect to: {location}")

                    # Extract date from redirect URL (e.g., /papers/date/2025-08-08)
                    date_match = re.search(r'/papers/date/(\d{4}-\d{2}-\d{2})', location)
                    if date_match:
                        actual_date = date_match.group(1)
                        logger.info(f"Redirected from {target_date} to {actual_date}")

                        # Fetch the actual page
                        actual_url = f"https://huggingface.co{location}"
                        r = await client.get(actual_url)
                        if r.status_code == 200:
                            return actual_date, r.text
                        else:
                            raise Exception(f"Failed to fetch redirected page: {r.status_code}")
                    else:
                        # Couldn't extract date from redirect, use fallback
                        raise Exception("Could not extract date from redirect")

                elif r.status_code == 200:
                    # Direct success, check if the page actually contains the requested date
                    if target_date in r.text or "Daily Papers" in r.text:
                        return target_date, r.text
                    else:
                        # Page exists but doesn't contain expected content
                        raise Exception("Page exists but doesn't contain expected content")
                else:
                    # Other error status
                    raise Exception(f"Status code {r.status_code}")

            except Exception as e:
                logger.error(f"Failed to fetch {target_date}: {e}")
                # If the requested date fails, try to find the latest available date
                actual_date, html = await self.find_latest_available_date(client)
                return actual_date, html

    async def find_latest_available_date(self, client: httpx.AsyncClient) -> tuple[str, str]:
        """Find the latest available date by checking recent dates"""

        # Start from today and go backwards up to 30 days
        today = datetime.now()
        for i in range(30):
            check_date = today - timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")
            url = f"{self.base_url}/{date_str}"

            try:
                r = await client.get(url)
                if r.status_code == 200:
                    # Check if the page actually has content (not just a 404 or empty page)
                    if "Daily Papers" in r.text and len(r.text) > 1000:
                        logger.info(f"Found latest available date: {date_str}")
                        return date_str, r.text
            except Exception:
                continue

        # If no date found, return a default page or raise an error
        raise Exception("No available daily papers found in the last 30 days")

    def parse_daily_cards(self, html: str) -> List[Dict[str, Any]]:
        """Parse daily papers HTML and extract paper cards"""
        soup = BeautifulSoup(html, "lxml")

        # First, extract JSON data from the page to get GitHub stars
        json_data = self.extract_json_data(html)

        # Find all article elements that contain paper cards
        cards: List[Dict[str, Any]] = []

        # Look for article elements with the specific class structure from Hugging Face
        for article in soup.select("article.relative.flex.flex-col.overflow-hidden.rounded-xl.border"):
            try:
                card_data = {}

                # Extract title and link
                title_link = article.select_one("h3 a")
                if title_link:
                    card_data["title"] = title_link.get_text(strip=True)
                    href = title_link.get("href")
                    if href:
                        if href.startswith("http"):
                            card_data["huggingface_url"] = href
                        else:
                            card_data["huggingface_url"] = f"https://huggingface.co{href}"

                # Extract upvote count
                upvote_div = article.select_one("div.shadow-alternate div.leading-none")
                if upvote_div:
                    upvote_text = upvote_div.get_text(strip=True)
                    try:
                        card_data["upvotes"] = int(upvote_text)
                    except ValueError:
                        card_data["upvotes"] = 0

                # Extract author count - look for the author count text
                author_count_div = article.select_one("div.flex.truncate.text-sm")
                if author_count_div:
                    author_text = author_count_div.get_text(strip=True)
                    # Extract number from "· 10 authors"
                    author_match = re.search(r'(\d+)\s*authors?', author_text)
                    if author_match:
                        card_data["author_count"] = int(author_match.group(1))
                    else:
                        card_data["author_count"] = 0

                # Extract GitHub stars from JSON data in the page
                # This will be handled later when we parse the JSON data
                card_data["github_stars"] = 0  # Default value

                # Extract comments count - look for comment icon and number
                comment_links = article.select("a[href*='#community']")
                for comment_link in comment_links:
                    comment_text = comment_link.get_text(strip=True)
                    try:
                        card_data["comments"] = int(comment_text)
                        break
                    except ValueError:
                        continue

                # Extract submitter information
                submitted_div = article.select_one("div.shadow-xs")
                if submitted_div:
                    submitter_text = submitted_div.get_text(strip=True)
                    # Extract submitter name from "Submitted byLiang0223" (no space)
                    submitter_match = re.search(r'Submitted by(\S+)', submitter_text)
                    if submitter_match:
                        card_data["submitter"] = submitter_match.group(1)

                # Extract arXiv ID from the URL
                if card_data.get("huggingface_url"):
                    arxiv_id = self.extract_arxiv_id(card_data["huggingface_url"])
                    if arxiv_id:
                        card_data["arxiv_id"] = arxiv_id

                # Try to get GitHub stars from the extracted data
                # Look for GitHub stars by matching paper title
                paper_title = card_data.get("title", "")
                if paper_title in json_data.get("github_stars_map", {}):
                    card_data["github_stars"] = json_data["github_stars_map"][paper_title]

                # Only add cards that have at least a title
                if card_data.get("title"):
                    cards.append(card_data)

            except Exception as e:
                logger.error(f"Error parsing card: {e}")
                continue

        # If the above method didn't work, fall back to the old method
        if not cards:
            logger.info("Falling back to old parsing method")
            for h3 in soup.select("h3"):
                # Title and Hugging Face paper link (if present)
                a = h3.find("a")
                title = h3.get_text(strip=True)
                hf_link = None
                if a and a.get("href"):
                    href = a.get("href")
                    # Absolute URL to huggingface
                    if href.startswith("http"):
                        hf_link = href
                    else:
                        hf_link = f"https://huggingface.co{href}"

                # Try to capture sibling info (authors, votes, etc.) as a small snippet
                meta_text = None
                parent = h3.parent
                if parent:
                    # Join immediate text content following h3
                    collected: List[str] = []
                    for sib in parent.find_all(text=True, recursive=False):
                        t = (sib or "").strip()
                        if t:
                            collected.append(t)
                    if collected:
                        meta_text = " ".join(collected)

                # Try to discover any arXiv link inside nearby anchors
                arxiv_id: Optional[str] = None
                container = parent if parent else h3
                for link in container.find_all("a", href=True):
                    possible = self.extract_arxiv_id(link["href"])
                    if possible:
                        arxiv_id = possible
                        break

                cards.append(
                    {
                        "title": title,
                        "huggingface_url": hf_link,
                        "meta": meta_text,
                        "arxiv_id": arxiv_id,
                    }
                )

        # Deduplicate by title
        seen = set()
        unique_cards: List[Dict[str, Any]] = []
        for c in cards:
            key = c.get("title") or ""
            if key and key not in seen:
                seen.add(key)
                unique_cards.append(c)

        logger.info(f"Parsed {len(unique_cards)} cards")
        return unique_cards

    async def get_daily_papers(self, target_date: str) -> tuple[str, List[Dict[str, Any]]]:
        """Get daily papers for a specific date"""
        date_str, html = await self.fetch_daily_html(target_date)
        cards = self.parse_daily_cards(html)
        return date_str, cards
