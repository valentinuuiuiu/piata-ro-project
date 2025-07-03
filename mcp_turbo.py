
from playwright.async_api import async_playwright
from fastapi import FastAPI
import httpx

app = FastAPI()

class MCPTurbo:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.playwright = None
        self.browser = None

    async def startup(self):
        """Launch one persistent browser instance"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=["--single-process"]  # Save 30% memory
        )

    async def optimize_website(self, url: str):
        """Direct DOM optimizations"""
        page = await self.browser.new_page()
        await page.goto(url)
        
        # 1. Auto-optimize images
        await page.evaluate("""() => {
            document.querySelectorAll('img').forEach(img => {
                img.loading = 'lazy';
                if (!img.alt) img.alt = 'optimized-by-mcp';
            });
        }""")
        
        # 2. Strip unused CSS/JS
        optimized_html = await page.evaluate("""() => {
            [].forEach.call(document.querySelectorAll('link[rel=stylesheet], script'), el => {
                if (!el.hasAttribute('data-critical')) el.remove();
            });
            return document.documentElement.outerHTML;
        }""")
        
        return {
            "optimized_html": optimized_html,
            "metrics": {
                "image_count": await page.eval_on_selector_all("img", "imgs => imgs.length"),
                "removed_assets": await page.eval_on_selector_all(
                    "link[rel=stylesheet], script", 
                    "els => els.filter(el => !el.hasAttribute('data-critical')).length"
            }
        }

# FastAPI endpoints
mcp = MCPTurbo()

@app.on_event("startup")
async def startup():
    await mcp.startup()

@app.post("/optimize")
async def optimize(url: str):
    return await mcp.optimize_website(url)
