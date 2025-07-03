
from typing import Dict, List
from fastapi import FastAPI
from playwright.async_api import async_playwright
import httpx
import datetime

app = FastAPI()

class NewDevin:
    def __init__(self):
        self.tools = {
            "scraper": self._scrape_data,
            "optimizer": self._optimize_listings
        }
        self.client = httpx.AsyncClient()
        self.browser = None

    async def startup(self):
        """Initialize all subsystems"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    def _select_tool(self, task: str):
        """Route to the appropriate tool"""
        if task not in self.tools:
            raise ValueError(f"Unknown task: {task}")
        return self.tools[task]

    def _format_result(self, result):
        """Standardize output format"""
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.datetime.now().isoformat()
        }

    async def execute_pipeline(self, task: str, params: Dict) -> Dict:
        """Unified execution flow"""
        tool = self._select_tool(task)
        async with await self.browser.new_context() as ctx:
            result = await tool(ctx, params)
        return self._format_result(result)

    async def _scrape_data(self, ctx, params):
        if params["url"].startswith("mock://"):
            return {
                "prices": ["10.99", "20.50", "15.00"],
                "listings": 3
            }
            
        page = await ctx.new_page()
        await page.goto(params["url"])
        return await page.evaluate("""() => ({
            prices: [...document.querySelectorAll('.price')].map(el => el.innerText),
            listings: [...document.querySelectorAll('.listing')].length
        })""")

    async def _optimize_listings(self, ctx, params):
        if str(params["id"]).startswith("mock-"):
            return {"status": "optimized"}
            
        page = await ctx.new_page()
        await page.goto(f"http://localhost:8000/listings/{params['id']}")
        await page.evaluate("""() => {
            document.querySelector('textarea').value = 
                'Optimized by Devin: ' + document.querySelector('textarea').value;
        }""")
        return {"status": "optimized"}

devin = NewDevin()

@app.on_event("startup")
async def startup():
    await devin.startup()

@app.post("/command")
async def command(task: str, params: Dict):
    return await devin.execute_pipeline(task, params)
