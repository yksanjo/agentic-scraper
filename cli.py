"""
CLI Interface for Agentic Scraper

Command-line interface to interact with the agent.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

from agent import AgenticScraperAgent
from tools import ToolExecutor
from memory import MemoryStore, LearningEngine, SessionMemory


class AgenticScraperCLI:
    """Command-line interface for the agentic scraper"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.agent = None
        self.memory = LearningEngine()
        self.session = SessionMemory()
        self.tool_executor = ToolExecutor()
    
    async def initialize(self):
        """Initialize the agent"""
        print("🤖 Initializing Agentic Scraper...")
        
        # Try to set up browser (optional)
        try:
            from playwright.async_api import async_playwright
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            self.agent = AgenticScraperAgent(browser_manager=page)
            print("✅ Browser initialized")
        except ImportError:
            print("⚠️  Playwright not installed - running in demo mode")
            self.agent = AgenticScraperAgent()
        except Exception as e:
            print(f"⚠️  Could not initialize browser: {e}")
            print("   Running in demo mode")
            self.agent = AgenticScraperAgent()
        
        await self.agent.initialize()
        print("✅ Agent ready!")
    
    async def scrape(self, url: str, goal: str, output: str = None):
        """Scrape a URL with a goal"""
        print(f"\n🎯 Goal: {goal}")
        print(f"🌐 URL: {url}")
        
        # Get recommendations from memory
        recommendations = self.memory.get_recommendations(url)
        if recommendations.get("confidence", 0) > 0.5:
            print(f"💡 Using {len(recommendations['recommended_selectors'])} remembered selectors")
        
        # Run the agent
        result = await self.agent.scrape(url, goal)
        
        # Learn from result
        self.memory.learn_from_extraction(url, result)
        
        # Display results
        print("\n" + "="*50)
        print("📊 RESULTS")
        print("="*50)
        
        if result.get("success"):
            print(f"✅ Scraped {result.get('pages_scraped', 1)} page(s)")
            print(f"📝 Actions taken: {result.get('actions_taken', 0)}")
            
            if result.get("data"):
                print("\n📄 Extracted Data:")
                for i, item in enumerate(result["data"], 1):
                    print(f"\n  --- Item {i} ---")
                    print(json.dumps(item, indent=2))
            
            # Save to file if requested
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                print(f"\n💾 Results saved to: {output}")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        return result
    
    async def interactive(self):
        """Run in interactive mode"""
        print("\n" + "="*60)
        print("🤖 AGENTIC SCRAPER - Interactive Mode")
        print("="*60)
        print("Commands:")
        print("  scrape <url> <goal> - Scrape a URL")
        print("  memory                 - Show memory statistics")
        print("  tools                  - List available tools")
        print("  help                   - Show this help")
        print("  quit                   - Exit")
        print("="*60 + "\n")
        
        while True:
            try:
                command = input("> ").strip()
                
                if not command:
                    continue
                
                parts = command.split(maxsplit=2)
                cmd = parts[0].lower()
                
                if cmd == "quit" or cmd == "exit":
                    print("👋 Goodbye!")
                    break
                
                elif cmd == "help":
                    print("Commands:")
                    print("  scrape <url> <goal> - Scrape a URL")
                    print("  memory               - Show memory statistics")
                    print("  tools                - List available tools")
                    print("  help                 - Show this help")
                    print("  quit                 - Exit")
                
                elif cmd == "scrape":
                    if len(parts) < 3:
                        print("Usage: scrape <url> <goal>")
                        continue
                    
                    url = parts[1]
                    goal = parts[2]
                    await self.scrape(url, goal)
                
                elif cmd == "memory":
                    stats = self.memory.get_statistics()
                    print("\n📚 Memory Statistics:")
                    print(json.dumps(stats, indent=2))
                    
                    print("\n🧠 Session Memory:")
                    print(json.dumps(self.session.summarize(), indent=2))
                
                elif cmd == "tools":
                    tools = self.tool_executor.registry.list_tools()
                    print(f"\n🔧 Available Tools ({len(tools)}):")
                    for tool in tools:
                        print(f"  - {tool}")
                
                else:
                    print(f"Unknown command: {cmd}")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_status(self):
        """Show agent status"""
        if self.agent:
            status = self.agent.get_status()
            print("\n📊 Agent Status:")
            print(json.dumps(status, indent=2))


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Agentic Web Scraper - An intelligent scraper that learns"
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="URL to scrape"
    )
    
    parser.add_argument(
        "goal",
        nargs="?",
        help="Goal/description of what to extract"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file for results"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--memory-stats",
        action="store_true",
        help="Show memory statistics"
    )
    
    args = parser.parse_args()
    
    cli = AgenticScraperCLI(headless=args.headless)
    await cli.initialize()
    
    if args.memory_stats:
        stats = cli.memory.get_statistics()
        print(json.dumps(stats, indent=2))
        return
    
    if args.interactive:
        await cli.interactive()
    elif args.url and args.goal:
        await cli.scrape(args.url, args.goal, args.output)
    else:
        parser.print_help()
        print("\n💡 Example:")
        print("  python cli.py https://example.com \"Extract all article titles\"")


if __name__ == "__main__":
    asyncio.run(main())
