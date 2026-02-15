"""
Agentic Web Scraper - Core Agent Module

An intelligent agent that can:
- Plan extraction strategies
- Use tools (browse, extract, scroll, click)
- Learn from page structures
- Handle dynamic content
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    LEARNING = "learning"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractionPlan:
    """Plan for extracting data from a page"""
    steps: list[dict] = field(default_factory=list)
    selectors: dict[str, str] = field(default_factory=dict)
    pagination: Optional[dict] = None


class AgenticScraperAgent:
    """
    An intelligent agent that autonomously scrapes web data
    using planning, tool-use, and learning capabilities.
    """
    
    def __init__(self, browser_manager=None, llm_provider=None):
        self.browser = browser_manager
        self.llm = llm_provider
        self.state = AgentState.IDLE
        self.memory = []
        self.current_plan: Optional[ExtractionPlan] = None
        self.extracted_data = []
        self.action_history = []
        
    async def initialize(self):
        """Initialize the agent and its tools"""
        self.state = AgentState.PLANNING
        self.log_action("agent_initialized", {"timestamp": datetime.now().isoformat()})
        
    async def scrape(self, url: str, goal: str) -> dict:
        """
        Main entry point - scrape a URL to achieve the goal.
        
        Args:
            url: Target URL to scrape
            goal: Description of what data to extract
            
        Returns:
            Dict containing extracted data and metadata
        """
        try:
            # Step 1: Navigate to page
            self.state = AgentState.EXECUTING
            result = await self.use_tool("navigate", {"url": url})
            if not result.success:
                return {"error": f"Navigation failed: {result.error}"}
            
            # Step 2: Analyze page and create extraction plan
            self.state = AgentState.PLANNING
            plan = await self.create_extraction_plan(goal)
            self.current_plan = plan
            
            # Step 3: Execute extraction plan
            self.state = AgentState.EXECUTING
            data = await self.execute_plan(plan)
            
            # Step 4: Learn from extraction
            self.state = AgentState.LEARNING
            await self.learn_from_extraction(url, plan, data)
            
            self.state = AgentState.COMPLETE
            return {
                "success": True,
                "data": data,
                "goal": goal,
                "url": url,
                "pages_scraped": len(self.extracted_data),
                "actions_taken": len(self.action_history)
            }
            
        except Exception as e:
            self.state = AgentState.ERROR
            return {"error": str(e)}
    
    async def create_extraction_plan(self, goal: str) -> ExtractionPlan:
        """Analyze the current page and create an extraction plan"""
        
        # Get page content for analysis
        content_result = await self.use_tool("get_page_content", {})
        
        if not content_result.success:
            return ExtractionPlan()
        
        # Use LLM to create plan if available
        if self.llm:
            prompt = f"""Analyze this page and create an extraction plan for: {goal}
            
Page content preview:
{content_result.data[:2000]}
            
Return a JSON object with:
- steps: array of extraction steps
- selectors: dict of element selectors to use
- pagination: how to handle pagination (if needed)
"""
            plan_json = await self.llm.generate(prompt)
            try:
                plan_data = json.loads(plan_json)
                return ExtractionPlan(**plan_data)
            except:
                pass
        
        # Fallback: create basic plan
        return ExtractionPlan(
            steps=[
                {"action": "extract_main_content", "target": "main"},
                {"action": "extract_links", "target": "links"},
            ],
            selectors={"main": "main, article, .content, #content"},
            pagination=None
        )
    
    async def execute_plan(self, plan: ExtractionPlan) -> list[dict]:
        """Execute the extraction plan step by step"""
        
        results = []
        
        for step in plan.steps:
            action = step.get("action")
            target = step.get("target")
            
            if action == "extract_main_content":
                result = await self.use_tool("extract", {
                    "selector": plan.selectors.get("main", "main, article"),
                    "type": "content"
                })
                
            elif action == "extract_links":
                result = await self.use_tool("extract", {
                    "selector": "a[href]",
                    "type": "links"
                })
                
            elif action == "scroll":
                result = await self.use_tool("scroll", {
                    "direction": step.get("direction", "down"),
                    "amount": step.get("amount", 1)
                })
                
            elif action == "click":
                result = await self.use_tool("click", {
                    "selector": step.get("selector")
                })
                
            elif action == "wait":
                result = await self.use_tool("wait", {
                    "seconds": step.get("seconds", 2)
                })
                
            else:
                continue
                
            if result.success:
                results.append({
                    "step": action,
                    "target": target,
                    "data": result.data
                })
                self.extracted_data.append(result.data)
        
        return results
    
    async def use_tool(self, tool_name: str, params: dict) -> ToolResult:
        """Execute a tool and track the action"""
        
        self.log_action(tool_name, params)
        
        try:
            if not self.browser:
                # Demo mode - return mock data
                return ToolResult(
                    success=True,
                    data=self._get_mock_data(tool_name),
                    metadata={"mode": "demo"}
                )
            
            # Real browser operations
            if tool_name == "navigate":
                await self.browser.goto(params["url"])
                await self.browser.wait_for_load_state()
                return ToolResult(success=True, data={"url": params["url"]})
            
            elif tool_name == "get_page_content":
                content = await self.browser.content()
                return ToolResult(success=True, data=content)
            
            elif tool_name == "extract":
                elements = await self.browser.query_selector_all(params["selector"])
                if params.get("type") == "links":
                    data = []
                    for el in elements:
                        href = await el.get_attribute("href")
                        text = await el.text_content()
                        if href:
                            data.append({"href": href, "text": text})
                else:
                    data = [await el.text_content() for el in elements]
                return ToolResult(success=True, data=data)
            
            elif tool_name == "scroll":
                direction = params.get("direction", "down")
                if direction == "down":
                    await self.browser.evaluate("window.scrollBy(0, window.innerHeight)")
                else:
                    await self.browser.evaluate("window.scrollBy(0, -window.innerHeight)")
                return ToolResult(success=True, data={"scrolled": direction})
            
            elif tool_name == "click":
                element = await self.browser.query_selector(params["selector"])
                if element:
                    await element.click()
                    return ToolResult(success=True, data={"clicked": params["selector"]})
                return ToolResult(success=False, error="Element not found")
            
            elif tool_name == "wait":
                await asyncio.sleep(params.get("seconds", 2))
                return ToolResult(success=True, data={"waited": params["seconds"]})
            
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _get_mock_data(self, tool_name: str) -> Any:
        """Return mock data for demo mode"""
        mock_data = {
            "get_page_content": "<html><main><article>Sample content with data to extract...</article></main></html>",
            "extract_main_content": ["Sample extracted content", "More data here"],
            "extract_links": [
                {"href": "https://example.com/page1", "text": "Page 1"},
                {"href": "https://example.com/page2", "text": "Page 2"},
            ],
            "scroll": {"scrolled": "down"},
            "click": {"clicked": "button.selector"},
            "wait": {"waited": 2}
        }
        return mock_data.get(tool_name, {})
    
    async def learn_from_extraction(self, url: str, plan: ExtractionPlan, data: list):
        """Store learned information about the page structure"""
        
        learning = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "selectors_used": plan.selectors,
            "steps_executed": len(plan.steps),
            "data_extracted": len(data),
            "successful": True
        }
        
        self.memory.append(learning)
        
        # Keep only last 100 memories
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]
    
    def log_action(self, action: str, params: dict):
        """Log an action to history"""
        self.action_history.append({
            "action": action,
            "params": params,
            "timestamp": datetime.now().isoformat(),
            "state": self.state.value
        })
    
    def get_memory(self) -> list[dict]:
        """Get agent's memory of past extractions"""
        return self.memory
    
    def get_status(self) -> dict:
        """Get current agent status"""
        return {
            "state": self.state.value,
            "actions_taken": len(self.action_history),
            "data_extracted": len(self.extracted_data),
            "memory_size": len(self.memory)
        }


# Demo function to test the agent
async def demo():
    """Run a demo of the agentic scraper"""
    agent = AgenticScraperAgent()
    await agent.initialize()
    
    print("Agent initialized")
    print(f"Status: {agent.get_status()}")
    
    # Demo scrape
    result = await agent.scrape(
        url="https://example.com",
        goal="Extract all article titles and links"
    )
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    print(f"\nFinal status: {agent.get_status()}")
    
    return agent


if __name__ == "__main__":
    asyncio.run(demo())
