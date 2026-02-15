# 🤖 Agentic Scraper

An intelligent web scraping agent that uses AI planning, tool-use, and memory to autonomously extract data from websites.

## Features

- **AI Planning**: Analyzes pages and creates extraction strategies
- **Tool-Use System**: 19+ tools for navigation, extraction, interaction
- **Memory & Learning**: Remembers successful selectors and strategies
- **Session Memory**: Temporary storage for current extraction session
- **Browser Automation**: Full Playwright support for real browser control

## Installation

```bash
# Clone or download this project
cd agentic-scraper

# Install dependencies (optional - for real browser automation)
pip install playwright
playwright install chromium
```

## Usage

### Command Line

```bash
# Basic scrape
python cli.py https://example.com "Extract all article titles"

# Save to file
python cli.py https://example.com "Extract links" -o results.json

# Interactive mode
python cli.py --interactive

# Show memory stats
python cli.py --memory-stats
```

### Python API

```python
import asyncio
from agent import AgenticScraperAgent

async def main():
    # Create agent (demo mode - no browser needed)
    agent = AgenticScraperAgent()
    await agent.initialize()
    
    # Scrape with a goal
    result = await agent.scrape(
        url="https://example.com",
        goal="Extract all article titles and links"
    )
    
    print(result)

asyncio.run(main())
```

### Using Tools Directly

```python
from tools import ToolExecutor

async def main():
    executor = ToolExecutor()
    
    # Execute a tool
    result = await executor.execute("extract_links", {"selector": "a[href]"})
    print(result)
```

### Using Memory System

```python
from memory import LearningEngine

# Initialize learning engine
learning = LearningEngine()

# Remember successful selectors
learning.remember_selector(
    url="https://example.com/articles",
    selector=".article-title",
    success=True,
    element_type="heading"
)

# Get recommendations for a URL
recommendations = learning.get_recommendations("https://example.com/articles")
```

## Available Tools

### Navigation
- `navigate` - Go to a URL
- `go_back` - Go back in history
- `go_forward` - Go forward in history

### Extraction
- `extract_text` - Extract text from elements
- `extract_links` - Extract all links
- `extract_attributes` - Extract attribute values
- `extract_structured` - Extract structured data (tables, lists)

### Interaction
- `click` - Click an element
- `type` - Type into input
- `select_option` - Select dropdown option
- `check` - Check/uncheck checkbox

### Scroll
- `scroll` - Scroll the page
- `scroll_to_element` - Scroll to element

### Wait
- `wait` - Wait seconds
- `wait_for_selector` - Wait for element
- `wait_for_navigation` - Wait for navigation

### Analysis
- `analyze_page` - Analyze page structure
- `get_page_info` - Get page title/URL
- `screenshot` - Take screenshot

## Architecture

```
agentic-scraper/
├── agent.py       # Core agent with planning & execution
├── tools.py       # Tool registry and executor
├── memory.py      # Memory & learning system
├── cli.py         # Command-line interface
├── example.py     # Usage examples
└── requirements.txt
```

## How It Works

1. **Initialize**: Agent starts and loads tools
2. **Navigate**: Agent visits the target URL
3. **Plan**: Agent analyzes page and creates extraction plan
4. **Execute**: Agent runs the plan using tools
5. **Learn**: Agent stores successful selectors in memory
6. **Return**: Results are returned with metadata

## Demo Mode

The agent works in demo mode without a browser, returning mock data. To use real browser automation:

1. Install Playwright: `pip install playwright && playwright install chromium`
2. The agent will automatically use the browser when available

## Memory System

The agent learns from each extraction:

- **Selectors**: Remembers CSS selectors that work
- **Strategies**: Remembers extraction strategies
- **Errors**: Remembers errors to avoid
- **Patterns**: Remembers page structure patterns

Memory persists in SQLite at `~/.agentic-scraper/memory.db`

## License

MIT
