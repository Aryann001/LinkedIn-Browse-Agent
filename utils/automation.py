import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext
from config.settings import settings
import json
from typing import List, Dict, Any
import random
from models.selectors import SelectorConfig

class LinkedInAutomator:
    def __init__(self, cookie_json: str, auto_like: bool = False, auto_comment: bool = False):
        self.browser = None
        self.context = None
        self.page = None
        self.auto_like = auto_like
        self.auto_comment = auto_comment
        self.cookie_json = cookie_json # Store the cookie string
        self.selectors: SelectorConfig | None = None

    async def fetch_selectors(self):
        """Fetches selectors from DB or uses defaults."""
        if self.selectors is None:
            self.selectors = await SelectorConfig.find_one()
            if self.selectors is None:
                print("No selectors found in DB, using defaults.")
                self.selectors = SelectorConfig()
            else:
                print("Fetched selectors from DB.")
        return self.selectors

    async def __aenter__(self):
        playwright = await async_playwright().start()
        # When deploying, you will change this to headless=True
        self.browser = await playwright.chromium.launch(headless=True, slow_mo=500)
        self.context = await self.browser.new_context()
        
        # Load saved session cookies FROM THE PASSED STRING
        try:
            # --- START: AUTOMATIC COOKIE FIX ---
            
            # 1. Load the potentially broken JSON
            cookies_list = json.loads(self.cookie_json)
            
            # 2. Fix the 'sameSite' issue in-memory
            cleaned_cookies_count = 0
            for cookie in cookies_list:
                if "sameSite" not in cookie or cookie.get("sameSite") not in ["Strict", "Lax", "None"]:
                    cookie["sameSite"] = "Lax" # Set a safe default
                    cleaned_cookies_count += 1
            
            if cleaned_cookies_count > 0:
                print(f"Automatically fixed {cleaned_cookies_count} cookie 'sameSite' entries.")
            
            # 3. Add the cleaned cookies to the context
            await self.context.add_cookies(cookies_list)
            
            # --- END: AUTOMATIC COOKIE FIX ---

        except json.JSONDecodeError:
            print("Error: Invalid cookie JSON provided.")
            raise ValueError("Invalid cookie JSON")
        except Exception as e:
            print(f"Error loading cookies: {e}")
            raise
            
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        print("Playwright session closed.")

    async def go_to_feed(self):
        print("Navigating to LinkedIn feed...")
        try:
            # Increased timeout and using 'networkidle'
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=90000)
        except Exception as e:
            print(f"Page.goto failed: {e}")
            raise Exception("Failed to load LinkedIn feed, server may be slow or page timed out. Try again.")

        await asyncio.sleep(3) 

        # --- LOGIN CHECK ---
        current_url = self.page.url
        print(f"Current page URL: {current_url}")

        if "linkedin.com/feed" not in current_url:
            if "login" in current_url:
                raise Exception("Login failed. Cookies are invalid or expired. Please re-export new cookies.")
            if "checkpoint" in current_url or "challenge" in current_url:
                raise Exception("Login failed. LinkedIn is asking for a security check. Please re-export new cookies.")
            else:
                raise Exception(f"Login failed. Redirected to unknown page: {current_url}. Please re-export cookies.")
        
        print("Login successful, on feed page.")


    async def scroll_and_scrape_posts(self, max_posts: int) -> List[Dict[str, Any]]:
        selectors = await self.fetch_selectors()
        print(f"Scrolling and scraping up to {max_posts} posts...")
        posts_data = []
        post_selector = selectors.post_container

        while len(posts_data) < max_posts:
            await self.page.evaluate("window.scrollBy(0, window.innerHeight * 0.8);")
            await asyncio.sleep(2.5)
            
            new_elements = await self.page.locator(post_selector).all()
            
            for post_element in new_elements:
                post_urn = await post_element.get_attribute("data-urn")
                if not post_urn or any(p['urn'] == post_urn for p in posts_data):
                    continue

                try:
                    # AUTHOR
                    author_name_locator = post_element.locator(selectors.author_selector).first
                    author_name = await author_name_locator.text_content(timeout=5000)
                    
                    # CONTENT
                    content_locator = post_element.locator(selectors.content_selector).first
                    post_content = await content_locator.text_content(timeout=5000)

                    if not post_content:
                        continue

                    posts_data.append({
                        "urn": post_urn,
                        "element": post_element,
                        "author": author_name.strip(),
                        "content": post_content.strip()
                    })
                    print(f"Scraped post from {author_name.strip()}")

                    if len(posts_data) >= max_posts:
                        break
                except Exception as e:
                    print(f"Error scraping post {post_urn}: {e}")
            
            if len(new_elements) == 0:
                print("No posts found, ending.")
                break
            
            if len(posts_data) >= max_posts:
                break

        return posts_data[:max_posts]

    async def perform_actions(self, post: Dict[str, Any], comment_text: str):
        selectors = await self.fetch_selectors()
        post_element = post['element']
        urn = post['urn']
        posted_comment = False
        liked_post = False
        
        if self.auto_like:
            try:
                like_button_selector = selectors.like_button
                await post_element.locator(like_button_selector).first.click()
                print(f"Liked post {urn}")
                liked_post = True
                await asyncio.sleep(random.uniform(1.5, 3.0))
            except Exception as e:
                print(f"Could not like post {urn}: {e}")

        if self.auto_comment and comment_text:
            try:
                comment_button_selector = selectors.comment_button
                await post_element.locator(comment_button_selector).first.click()
                await asyncio.sleep(random.uniform(2.0, 4.0))

                comment_box_selector = selectors.comment_textbox
                await post_element.locator(comment_box_selector).first.fill(comment_text)
                await asyncio.sleep(random.uniform(2.5, 5.0))

                post_button_selector = selectors.comment_post_button
                await post_element.locator(post_button_selector).first.click()
                print(f"Posted comment on {urn}")
                posted_comment = True
                await asyncio.sleep(random.uniform(3.0, 5.0))
            except Exception as e:
                print(f"Could not comment on post {urn}: {e}")
        
        return {"posted": posted_comment, "liked": liked_post}