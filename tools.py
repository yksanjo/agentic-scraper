"""
Tool-use System for Agentic Scraper

Defines the tools available to the agent and handles tool execution.
"""

import asyncio
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Tool:
    """Definition of a tool the agent can use"""
    name: str
    description: str
    parameters: dict
    handler: Callable = field(default=None)
    category: str = "general"
    requires_browser: bool = True
    
    def to_schema(self) -> dict:
        """Return OpenAI-style tool schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolRegistry:
    """Registry of all available tools"""
    
    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the default set of tools"""
        
        # Navigation tools
        self.register(Tool(
            name="navigate",
            description="Navigate to a URL",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"}
                },
                "required": ["url"]
            },
            category="navigation"
        ))
        
        self.register(Tool(
            name="go_back",
            description="Go back in browser history",
            parameters={"type": "object", "properties": {}},
            category="navigation"
        ))
        
        self.register(Tool(
            name="go_forward",
            description="Go forward in browser history",
            parameters={"type": "object", "properties": {}},
            category="navigation"
        ))
        
        # Extraction tools
        self.register(Tool(
            name="extract_text",
            description="Extract text content from elements matching a CSS selector",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector"},
                    "many": {"type": "boolean", "description": "Extract multiple elements", "default": False}
                },
                "required": ["selector"]
            },
            category="extraction"
        ))
        
        self.register(Tool(
            name="extract_links",
            description="Extract all links (anchor tags) from the page",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for links", "default": "a[href]"}
                }
            },
            category="extraction"
        ))
        
        self.register(Tool(
            name="extract_attributes",
            description="Extract attribute values from elements matching a selector",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector"},
                    "attribute": {"type": "string", "description": "Attribute name to extract"},
                    "many": {"type": "boolean", "description": "Extract from multiple elements", "default": True}
                },
                "required": ["selector", "attribute"]
            },
            category="extraction"
        ))
        
        self.register(Tool(
            name="extract_structured",
            description="Extract structured data (like tables or lists) from the page",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for container"},
                    "schema": {"type": "object", "description": "Schema defining fields to extract"}
                },
                "required": ["selector", "schema"]
            },
            category="extraction"
        ))
        
        # Interaction tools
        self.register(Tool(
            name="click",
            description="Click on an element",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for element to click"},
                    "wait_for_nav": {"type": "boolean", "description": "Wait for navigation after click", "default": False}
                },
                "required": ["selector"]
            },
            category="interaction"
        ))
        
        self.register(Tool(
            name="type",
            description="Type text into an input field",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for input element"},
                    "text": {"type": "string", "description": "Text to type"},
                    "clear_first": {"type": "boolean", "description": "Clear input first", "default": False}
                },
                "required": ["selector", "text"]
            },
            category="interaction"
        ))
        
        self.register(Tool(
            name="select_option",
            description="Select an option from a dropdown",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for select element"},
                    "value": {"type": "string", "description": "Value to select"},
                    "by_label": {"type": "boolean", "description": "Select by label text", "default": False}
                },
                "required": ["selector", "value"]
            },
            category="interaction"
        ))
        
        self.register(Tool(
            name="check",
            description="Check/uncheck a checkbox or radio button",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for input element"},
                    "checked": {"type": "boolean", "description": "Whether to check or uncheck", "default": True}
                },
                "required": ["selector"]
            },
            category="interaction"
        ))
        
        # Scroll tools
        self.register(Tool(
            name="scroll",
            description="Scroll the page",
            parameters={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down", "top", "bottom"], "description": "Scroll direction"},
                    "amount": {"type": "number", "description": "Number of viewport heights to scroll", "default": 1}
                }
            },
            category="scroll"
        ))
        
        self.register(Tool(
            name="scroll_to_element",
            description="Scroll until an element is visible",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for target element"}
                },
                "required": ["selector"]
            },
            category="scroll"
        ))
        
        # Wait tools
        self.register(Tool(
            name="wait",
            description="Wait for a specified number of seconds",
            parameters={
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "Seconds to wait", "default": 2}
                }
            },
            category="wait"
        ))
        
        self.register(Tool(
            name="wait_for_selector",
            description="Wait for an element to appear on the page",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector to wait for"},
                    "timeout": {"type": "number", "description": "Max wait time in seconds", "default": 30}
                },
                "required": ["selector"]
            },
            category="wait"
        ))
        
        self.register(Tool(
            name="wait_for_navigation",
            description="Wait for page navigation to complete",
            parameters={
                "type": "object",
                "properties": {
                    "timeout": {"type": "number", "description": "Max wait time in seconds", "default": 30}
                }
            },
            category="wait"
        ))
        
        # Screenshot tools
        self.register(Tool(
            name="screenshot",
            description="Take a screenshot of the current page",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to save screenshot"},
                    "full_page": {"type": "boolean", "description": "Capture full page", "default": False}
                }
            },
            category="debug"
        ))
        
        # Analysis tools
        self.register(Tool(
            name="analyze_page",
            description="Analyze the page structure and suggest extraction strategies",
            parameters={
                "type": "object",
                "properties": {
                    "focus": {"type": "string", "description": "Optional focus area (e.g., 'articles', 'products')"}
                }
            },
            category="analysis"
        ))
        
        self.register(Tool(
            name="get_page_info",
            description="Get information about the current page (title, URL, etc.)",
            parameters={"type": "object", "properties": {}},
            category="analysis"
        ))
    
    def register(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: str) -> list[Tool]:
        """Get all tools in a category"""
        return [t for t in self.tools.values() if t.category == category]
    
    def get_all_schemas(self) -> list[dict]:
        """Get all tool schemas for LLM function calling"""
        return [tool.to_schema() for tool in self.tools.values()]
    
    def list_tools(self) -> list[str]:
        """List all available tool names"""
        return list(self.tools.keys())


class ToolExecutor:
    """Executes tools using a browser context"""
    
    def __init__(self, browser_context=None):
        self.browser = browser_context
        self.registry = ToolRegistry()
        self.execution_log = []
    
    async def execute(self, tool_name: str, params: dict) -> dict:
        """Execute a tool with given parameters"""
        
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        # Log execution
        self._log_execution(tool_name, params)
        
        # If no browser, return mock data
        if not self.browser:
            return self._mock_execution(tool_name, params)
        
        try:
            # Execute based on tool type
            if tool_name == "navigate":
                page = self.browser
                await page.goto(params["url"])
                await page.wait_for_load_state("domcontentloaded")
                return {"success": True, "url": page.url}
            
            elif tool_name == "go_back":
                await self.browser.go_back()
                return {"success": True}
            
            elif tool_name == "go_forward":
                await self.browser.go_forward()
                return {"success": True}
            
            elif tool_name == "extract_text":
                return await self._extract_text(params)
            
            elif tool_name == "extract_links":
                return await self._extract_links(params)
            
            elif tool_name == "extract_attributes":
                return await self._extract_attributes(params)
            
            elif tool_name == "extract_structured":
                return await self._extract_structured(params)
            
            elif tool_name == "click":
                return await self._click(params)
            
            elif tool_name == "type":
                return await self._type(params)
            
            elif tool_name == "select_option":
                return await self._select_option(params)
            
            elif tool_name == "check":
                return await self._check(params)
            
            elif tool_name == "scroll":
                return await self._scroll(params)
            
            elif tool_name == "scroll_to_element":
                return await self._scroll_to_element(params)
            
            elif tool_name == "wait":
                await asyncio.sleep(params.get("seconds", 2))
                return {"success": True, "waited": params.get("seconds", 2)}
            
            elif tool_name == "wait_for_selector":
                return await self._wait_for_selector(params)
            
            elif tool_name == "wait_for_navigation":
                await self.browser.wait_for_load_state("networkidle")
                return {"success": True}
            
            elif tool_name == "screenshot":
                return await self._screenshot(params)
            
            elif tool_name == "analyze_page":
                return await self._analyze_page(params)
            
            elif tool_name == "get_page_info":
                return await self._get_page_info()
            
            return {"success": False, "error": "Tool not implemented"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _extract_text(self, params: dict) -> dict:
        """Extract text from elements"""
        selector = params["selector"]
        many = params.get("many", False)
        
        if many:
            elements = await self.browser.query_selector_all(selector)
            texts = []
            for el in elements:
                text = await el.text_content()
                if text:
                    texts.append(text.strip())
            return {"success": True, "data": texts, "count": len(texts)}
        else:
            element = await self.browser.query_selector(selector)
            if element:
                text = await element.text_content()
                return {"success": True, "data": text.strip() if text else ""}
            return {"success": False, "error": "Element not found"}
    
    async def _extract_links(self, params: dict) -> dict:
        """Extract links from the page"""
        selector = params.get("selector", "a[href]")
        elements = await self.browser.query_selector_all(selector)
        
        links = []
        for el in elements:
            href = await el.get_attribute("href")
            text = await el.text_content()
            if href:
                links.append({
                    "href": href,
                    "text": text.strip() if text else ""
                })
        
        return {"success": True, "data": links, "count": len(links)}
    
    async def _extract_attributes(self, params: dict) -> dict:
        """Extract attributes from elements"""
        selector = params["selector"]
        attribute = params["attribute"]
        many = params.get("many", True)
        
        elements = await self.browser.query_selector_all(selector)
        
        if many:
            values = []
            for el in elements:
                val = await el.get_attribute(attribute)
                if val is not None:
                    values.append(val)
            return {"success": True, "data": values, "count": len(values)}
        else:
            element = await self.browser.query_selector(selector)
            if element:
                val = await element.get_attribute(attribute)
                return {"success": True, "data": val}
            return {"success": False, "error": "Element not found"}
    
    async def _extract_structured(self, params: dict) -> dict:
        """Extract structured data based on schema"""
        container = await self.browser.query_selector(params["selector"])
        if not container:
            return {"success": False, "error": "Container not found"}
        
        schema = params["schema"]
        results = []
        
        # For each field in schema, extract corresponding data
        item_selector = schema.get("item_selector", "li, tr, .item")
        items = await container.query_selector_all(item_selector)
        
        for item in items:
            record = {}
            for field_name, field_config in schema.get("fields", {}).items():
                field_selector = field_config.get("selector")
                field_attr = field_config.get("attribute", "text")
                
                if field_selector:
                    field_el = await item.query_selector(field_selector)
                    if field_el:
                        if field_attr == "text":
                            record[field_name] = (await field_el.text_content()).strip()
                        else:
                            record[field_name] = await field_el.get_attribute(field_attr)
            
            if record:
                results.append(record)
        
        return {"success": True, "data": results, "count": len(results)}
    
    async def _click(self, params: dict) -> dict:
        """Click an element"""
        selector = params["selector"]
        element = await self.browser.query_selector(selector)
        
        if element:
            if params.get("wait_for_nav", False):
                async with self.browser.expect_navigation():
                    await element.click()
            else:
                await element.click()
            return {"success": True, "clicked": selector}
        
        return {"success": False, "error": f"Element not found: {selector}"}
    
    async def _type(self, params: dict) -> dict:
        """Type into an input"""
        selector = params["selector"]
        text = params["text"]
        
        element = await self.browser.query_selector(selector)
        if element:
            if params.get("clear_first", False):
                await element.fill("")
            await element.fill(text)
            return {"success": True, "typed": text[:50]}
        
        return {"success": False, "error": f"Input not found: {selector}"}
    
    async def _select_option(self, params: dict) -> dict:
        """Select option from dropdown"""
        selector = params["selector"]
        value = params["value"]
        
        element = await self.browser.query_selector(selector)
        if element:
            if params.get("by_label", False):
                await element.select_option(label=value)
            else:
                await element.select_option(value)
            return {"success": True, "selected": value}
        
        return {"success": False, "error": f"Select not found: {selector}"}
    
    async def _check(self, params: dict) -> dict:
        """Check/uncheck checkbox"""
        selector = params["selector"]
        checked = params.get("checked", True)
        
        element = await self.browser.query_selector(selector)
        if element:
            await element.set_checked(checked)
            return {"success": True, "checked": checked}
        
        return {"success": False, "error": f"Checkbox not found: {selector}"}
    
    async def _scroll(self, params: dict) -> dict:
        """Scroll the page"""
        direction = params.get("direction", "down")
        amount = params.get("amount", 1)
        
        if direction == "top":
            await self.browser.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            await self.browser.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        else:
            for _ in range(int(amount)):
                if direction == "down":
                    await self.browser.evaluate("window.scrollBy(0, window.innerHeight)")
                else:
                    await self.browser.evaluate("window.scrollBy(0, -window.innerHeight)")
                await asyncio.sleep(0.3)
        
        return {"success": True, "scrolled": direction}
    
    async def _scroll_to_element(self, params: dict) -> dict:
        """Scroll to element"""
        selector = params["selector"]
        element = await self.browser.query_selector(selector)
        
        if element:
            await element.scroll_into_view_if_needed()
            return {"success": True, "scrolled_to": selector}
        
        return {"success": False, "error": f"Element not found: {selector}"}
    
    async def _wait_for_selector(self, params: dict) -> dict:
        """Wait for selector"""
        selector = params["selector"]
        timeout = params.get("timeout", 30) * 1000
        
        try:
            await self.browser.wait_for_selector(selector, timeout=timeout)
            return {"success": True, "found": selector}
        except:
            return {"success": False, "error": f"Timeout waiting for: {selector}"}
    
    async def _screenshot(self, params: dict) -> dict:
        """Take screenshot"""
        path = params.get("path", "screenshot.png")
        full_page = params.get("full_page", False)
        
        await self.browser.screenshot(path=path, full_page=full_page)
        return {"success": True, "path": path}
    
    async def _analyze_page(self, params: dict) -> dict:
        """Analyze page structure"""
        focus = params.get("focus")
        
        # Get basic page info
        title = await self.browser.title()
        url = self.browser.url
        
        # Count common elements
        stats = {}
        for selector in ["a", "img", "button", "input", "form", "table", "article"]:
            elements = await self.browser.query_selector_all(selector)
            stats[selector] = len(elements)
        
        return {
            "success": True,
            "data": {
                "title": title,
                "url": url,
                "element_counts": stats,
                "focus": focus
            }
        }
    
    async def _get_page_info(self) -> dict:
        """Get page info"""
        return {
            "success": True,
            "data": {
                "url": self.browser.url,
                "title": await self.browser.title()
            }
        }
    
    def _mock_execution(self, tool_name: str, params: dict) -> dict:
        """Return mock data when no browser is available"""
        mock_responses = {
            "navigate": {"success": True, "url": params.get("url")},
            "extract_text": {"success": True, "data": ["Sample text 1", "Sample text 2"], "count": 2},
            "extract_links": {
                "success": True,
                "data": [
                    {"href": "https://example.com/1", "text": "Link 1"},
                    {"href": "https://example.com/2", "text": "Link 2"},
                ],
                "count": 2
            },
            "click": {"success": True, "clicked": params.get("selector")},
            "scroll": {"success": True, "scrolled": params.get("direction", "down")},
            "wait": {"success": True, "waited": params.get("seconds", 2)},
            "get_page_info": {"success": True, "data": {"url": "https://example.com", "title": "Example"}},
            "analyze_page": {"success": True, "data": {"element_counts": {"a": 10, "img": 5}}}
        }
        
        return mock_responses.get(tool_name, {"success": True, "mock": True})
    
    def _log_execution(self, tool_name: str, params: dict):
        """Log tool execution"""
        self.execution_log.append({
            "tool": tool_name,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_execution_log(self) -> list[dict]:
        """Get execution log"""
        return self.execution_log
