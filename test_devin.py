

import asyncio
from ai_assistant.devin import NewDevin
import pytest

@pytest.mark.asyncio
async def test_scraper():
    devin = NewDevin()
    await devin.startup()
    
    try:
        # Test with mock data
        result = await devin.execute_pipeline(
            "scraper", 
            {"url": "mock://testdata"}
        )
        
        assert "status" in result
        assert result["status"] == "success"
        assert "data" in result
        assert isinstance(result["data"], dict)
        assert "prices" in result["data"]
        assert "listings" in result["data"]
    finally:
        await devin.browser.close()

@pytest.mark.asyncio 
async def test_optimizer():
    devin = NewDevin()
    await devin.startup()
    
    try:
        # Test with mock data
        result = await devin.execute_pipeline(
            "optimizer",
            {"id": "mock-123"}
        )
        
        assert "status" in result
        assert result["status"] == "success"
        assert "data" in result
        assert isinstance(result["data"], dict)
    finally:
        await devin.browser.close()

if __name__ == "__main__":
    asyncio.run(test_scraper())
    asyncio.run(test_optimizer())

