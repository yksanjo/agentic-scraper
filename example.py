"""
Example Usage for Agentic Scraper

This file demonstrates various ways to use the agentic scraper.
"""

import asyncio
import json
from agent import AgenticScraperAgent
from tools import ToolExecutor
from memory import LearningEngine, SessionMemory


# Example 1: Basic scrape with demo mode (no browser)
async def basic_scrape():
    """Simple scrape without browser - demo mode"""
    print("=" * 60)
    print("Example 1: Basic Scrape (Demo Mode)")
    print("=" * 60)
    
    # Create agent - no browser = demo mode
    agent = AgenticScraperAgent()
    await agent.initialize()
    
    # Scrape with goal
    result = await agent.scrape(
        url="https://example.com",
        goal="Extract all article titles and links"
    )
    
    print(json.dumps(result, indent=2))
    print(f"\nAgent status: {agent.get_status()}")
    
    return result


# Example 2: Using the tool executor directly
async def use_tools_directly():
    """Use tools without the agent"""
    print("\n" + "=" * 60)
    print("Example 2: Using Tools Directly")
    print("=" * 60)
    
    executor = ToolExecutor()
    
    # List available tools
    tools = executor.registry.list_tools()
    print(f"Available tools: {len(tools)}")
    for tool in tools[:10]:
        print(f"  - {tool}")
    print("  ...")
    
    # Execute a tool (will return mock data in demo mode)
    result = await executor.execute("extract_links", {"selector": "a[href]"})
    print(f"\nExtracted links: {json.dumps(result, indent=2)}")
    
    return result


# Example 3: Memory and learning system
async def use_memory():
    """Demonstrate the memory system"""
    print("\n" + "=" * 60)
    print("Example 3: Memory & Learning")
    print("=" * 60)
    
    # Initialize learning engine
    learning = LearningEngine()
    
    # Remember some selectors
    learning.remember_selector(
        url="https://example.com/articles",
        selector=".article-title",
        success=True,
        element_type="heading"
    )
    
    learning.remember_selector(
        url="https://example.com/articles",
        selector="div.content",
        success=True,
        element_type="div"
    )
    
    # Get recommendations
    recommendations = learning.get_recommendations("https://example.com/articles")
    print("Recommendations for example.com/articles:")
    print(json.dumps(recommendations, indent=2))
    
    # Get statistics
    stats = learning.get_statistics()
    print(f"\nMemory statistics: {json.dumps(stats, indent=2)}")
    
    return recommendations


# Example 4: Session memory
async def use_session_memory():
    """Use session memory for temporary storage"""
    print("\n" + "=" * 60)
    print("Example 4: Session Memory")
    print("=" * 60)
    
    session = SessionMemory()
    
    # Store page analysis
    session.store_page_analysis(
        url="https://example.com",
        structure={"title": "Example", "headings": 5, "links": 10}
    )
    
    # Add extracted data
    session.add_extracted_data({"title": "Article 1", "url": "/article1"})
    session.add_extracted_data({"title": "Article 2", "url": "/article2"})
    
    # Add action
    session.add_action({"action": "navigate", "url": "https://example.com"})
    session.add_action({"action": "extract", "selector": "h1"})
    
    # Set context
    session.set_context("user_goal", "Extract articles")
    session.set_context("max_items", 10)
    
    # Get summary
    print("Session summary:")
    print(json.dumps(session.summarize(), indent=2))
    
    return session.summarize()


# Example 5: Full agent with browser (requires Playwright)
async def full_agent_with_browser():
    """Full agent with Playwright browser automation"""
    print("\n" + "=" * 60)
    print("Example 5: Full Agent with Browser")
    print("=" * 60)
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Create agent with browser
            agent = AgenticScraperAgent(browser_manager=page)
            await agent.initialize()
            
            # Scrape
            result = await agent.scrape(
                url="https://example.com",
                goal="Extract the page title and all links"
            )
            
            print(json.dumps(result, indent=2))
            
            # Cleanup
            await browser.close()
            
            return result
            
    except ImportError:
        print("⚠️  Playwright not installed")
        print("   Install with: pip install playwright && playwright install chromium")
        return None


# Example 6: Custom extraction strategy
async def custom_strategy():
    """Demonstrate custom extraction strategies"""
    print("\n" + "=" * 60)
    print("Example 6: Custom Extraction Strategy")
    print("=" * 60)
    
    # Create learning engine and remember custom strategy
    learning = LearningEngine()
    
    # Remember a custom strategy for e-commerce
    learning.remember_strategy(
        url="https://example.com/products",
        strategy={
            "type": "pagination",
            "max_pages": 5,
            "selectors": {
                "product": ".product-card",
                "title": ".product-title",
                "price": ".product-price",
                "next_button": ".next-page"
            }
        },
        success=True
    )
    
    # Remember a pattern
    learning.remember_pattern(
        url="https://example.com/products",
        pattern={
            "type": "e-commerce",
            "tags": ["products", "listing", "pagination"],
            "structure": {
                "container": ".product-grid",
                "items": ".product-card"
            }
        }
    )
    
    # Get recommendations
    recommendations = learning.get_recommendations("https://example.com/products")
    print("Recommendations for products page:")
    print(json.dumps(recommendations, indent=2))
    
    return recommendations


async def main():
    """Run all examples"""
    print("🤖 Agentic Scraper - Examples")
    print("=" * 60)
    
    # Run examples
    await basic_scrape()
    await use_tools_directly()
    await use_memory()
    await use_session_memory()
    await custom_strategy()
    
    # Browser example (optional)
    # await full_agent_with_browser()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
