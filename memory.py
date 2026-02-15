"""
Memory and Learning System for Agentic Scraper

The agent learns from past extractions and can recall:
- What selectors work for different page types
- Successful extraction strategies
- Error patterns to avoid
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib


@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: str
    memory_type: str  # "selector", "strategy", "error", "pattern"
    content: dict
    url_pattern: str  # Regex pattern for URLs this applies to
    success_rate: float
    times_used: int
    created_at: str
    last_used: str
    tags: list[str] = field(default_factory=list)


class MemoryStore:
    """Persistent memory storage using SQLite"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".agentic-scraper" / "memory.db")
        
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                url_pattern TEXT,
                success_rate REAL DEFAULT 1.0,
                times_used INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_used TEXT NOT NULL,
                tags TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_url_pattern ON memories(url_pattern)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
        """)
        
        conn.commit()
        conn.close()
    
    def add(self, memory: MemoryEntry):
        """Add a memory entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, memory_type, content, url_pattern, success_rate, times_used, created_at, last_used, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.id,
            memory.memory_type,
            json.dumps(memory.content),
            memory.url_pattern,
            memory.success_rate,
            memory.times_used,
            memory.created_at,
            memory.last_used,
            json.dumps(memory.tags)
        ))
        
        conn.commit()
        conn.close()
    
    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a memory by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_memory(row)
        return None
    
    def find_by_url(self, url: str, memory_type: str = None) -> list[MemoryEntry]:
        """Find memories that match a URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE url_pattern = ? AND memory_type = ?
                ORDER BY success_rate DESC, times_used DESC
            """, (url, memory_type))
        else:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE url_pattern = ?
                ORDER BY success_rate DESC, times_used DESC
            """, (url,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_memory(row) for row in rows]
    
    def find_by_tag(self, tag: str) -> list[MemoryEntry]:
        """Find memories by tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memories WHERE tags LIKE ?", (f'%"{tag}"%',))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_memory(row) for row in rows]
    
    def get_all(self, memory_type: str = None, limit: int = 100) -> list[MemoryEntry]:
        """Get all memories, optionally filtered by type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE memory_type = ?
                ORDER BY success_rate DESC, times_used DESC
                LIMIT ?
            """, (memory_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM memories 
                ORDER BY success_rate DESC, times_used DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_memory(row) for row in rows]
    
    def update_usage(self, memory_id: str, success: bool):
        """Update memory usage stats"""
        memory = self.get(memory_id)
        if not memory:
            return
        
        # Update success rate
        total = memory.times_used + 1
        if success:
            success_count = memory.success_rate * memory.times_used + 1
        else:
            success_count = memory.success_rate * memory.times_used
        
        memory.success_rate = success_count / total
        memory.times_used = total
        memory.last_used = datetime.now().isoformat()
        
        self.add(memory)
    
    def delete(self, memory_id: str):
        """Delete a memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()
    
    def _row_to_memory(self, row: tuple) -> MemoryEntry:
        """Convert database row to MemoryEntry"""
        return MemoryEntry(
            id=row[0],
            memory_type=row[1],
            content=json.loads(row[2]),
            url_pattern=row[3],
            success_rate=row[4],
            times_used=row[5],
            created_at=row[6],
            last_used=row[7],
            tags=json.loads(row[8]) if row[8] else []
        )


class LearningEngine:
    """The learning engine that helps the agent improve over time"""
    
    def __init__(self, memory_store: MemoryStore = None):
        self.memory = memory_store or MemoryStore()
        self.session_memories = []  # In-memory for current session
    
    def remember_selector(self, url: str, selector: str, success: bool, 
                         element_type: str = None, context: str = None):
        """Remember a selector that was used"""
        url_pattern = self._extract_url_pattern(url)
        
        entry = MemoryEntry(
            id=self._generate_id(url_pattern, "selector", selector),
            memory_type="selector",
            content={
                "selector": selector,
                "element_type": element_type,
                "context": context
            },
            url_pattern=url_pattern,
            success_rate=1.0 if success else 0.0,
            times_used=1,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=[element_type] if element_type else []
        )
        
        self.memory.add(entry)
        self.session_memories.append(entry)
    
    def remember_strategy(self, url: str, strategy: dict, success: bool):
        """Remember an extraction strategy"""
        url_pattern = self._extract_url_pattern(url)
        
        entry = MemoryEntry(
            id=self._generate_id(url_pattern, "strategy", json.dumps(strategy)),
            memory_type="strategy",
            content=strategy,
            url_pattern=url_pattern,
            success_rate=1.0 if success else 0.0,
            times_used=1,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=[strategy.get("type", "unknown")]
        )
        
        self.memory.add(entry)
        self.session_memories.append(entry)
    
    def remember_error(self, url: str, error: str, context: dict = None):
        """Remember an error to avoid in the future"""
        url_pattern = self._extract_url_pattern(url)
        
        entry = MemoryEntry(
            id=self._generate_id(url_pattern, "error", error),
            memory_type="error",
            content={
                "error": error,
                "context": context or {}
            },
            url_pattern=url_pattern,
            success_rate=0.0,
            times_used=1,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=["error"]
        )
        
        self.memory.add(entry)
        self.session_memories.append(entry)
    
    def remember_pattern(self, url: str, pattern: dict):
        """Remember a page pattern"""
        url_pattern = self._extract_url_pattern(url)
        
        entry = MemoryEntry(
            id=self._generate_id(url_pattern, "pattern", json.dumps(pattern)),
            memory_type="pattern",
            content=pattern,
            url_pattern=url_pattern,
            success_rate=1.0,
            times_used=1,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=pattern.get("tags", [])
        )
        
        self.memory.add(entry)
        self.session_memories.append(entry)
    
    def recall_selectors(self, url: str) -> list[dict]:
        """Recall useful selectors for a URL"""
        memories = self.memory.find_by_url(url, "selector")
        
        return [
            {
                "selector": m.content.get("selector"),
                "element_type": m.content.get("element_type"),
                "success_rate": m.success_rate,
                "times_used": m.times_used
            }
            for m in memories if m.success_rate > 0.5
        ]
    
    def recall_strategies(self, url: str) -> list[dict]:
        """Recall successful strategies for a URL"""
        memories = self.memory.find_by_url(url, "strategy")
        
        return [
            {
                "strategy": m.content,
                "success_rate": m.success_rate,
                "times_used": m.times_used
            }
            for m in memories if m.success_rate > 0.5
        ]
    
    def recall_errors(self, url: str) -> list[str]:
        """Recall known errors for a URL"""
        memories = self.memory.find_by_url(url, "error")
        
        return [m.content.get("error") for m in memories]
    
    def recall_patterns(self, url: str) -> list[dict]:
        """Recall known page patterns"""
        memories = self.memory.find_by_url(url, "pattern")
        
        return [m.content for m in memories]
    
    def get_recommendations(self, url: str) -> dict:
        """Get recommendations for a URL based on memory"""
        selectors = self.recall_selectors(url)
        strategies = self.recall_strategies(url)
        errors = self.recall_errors(url)
        
        return {
            "recommended_selectors": selectors[:5],
            "recommended_strategies": strategies[:3],
            "errors_to_avoid": errors,
            "confidence": self._calculate_confidence(url)
        }
    
    def learn_from_extraction(self, url: str, extraction_result: dict):
        """Learn from an extraction result"""
        if extraction_result.get("success"):
            # Remember successful selectors
            for selector_info in extraction_result.get("selectors_used", []):
                self.remember_selector(
                    url=url,
                    selector=selector_info.get("selector"),
                    success=True,
                    element_type=selector_info.get("type"),
                    context=selector_info.get("context")
                )
            
            # Remember successful strategy
            self.remember_strategy(
                url=url,
                strategy=extraction_result.get("strategy", {}),
                success=True
            )
        else:
            # Remember the error
            self.remember_error(
                url=url,
                error=extraction_result.get("error", "Unknown error"),
                context=extraction_result.get("context")
            )
    
    def get_statistics(self) -> dict:
        """Get memory statistics"""
        all_memories = self.memory.get_all()
        
        by_type = {}
        for m in all_memories:
            if m.memory_type not in by_type:
                by_type[m.memory_type] = {"count": 0, "avg_success": 0}
            by_type[m.memory_type]["count"] += 1
            by_type[m.memory_type]["avg_success"] += m.success_rate
        
        for t in by_type:
            if by_type[t]["count"] > 0:
                by_type[t]["avg_success"] /= by_type[t]["count"]
        
        return {
            "total_memories": len(all_memories),
            "by_type": by_type,
            "session_memories": len(self.session_memories)
        }
    
    def _extract_url_pattern(self, url: str) -> str:
        """Extract a pattern from URL for matching"""
        # Simple pattern: domain + path structure
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Get domain
        domain = parsed.netloc
        
        # Get path pattern (replace numbers and IDs with placeholders)
        path = parsed.path
        import re
        path_pattern = re.sub(r'\d+', '#', path)
        
        return f"{domain}{path_pattern}"
    
    def _generate_id(self, url_pattern: str, memory_type: str, content: str) -> str:
        """Generate a unique ID for a memory"""
        raw = f"{url_pattern}:{memory_type}:{content}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]
    
    def _calculate_confidence(self, url: str) -> float:
        """Calculate confidence in recommendations based on memory"""
        memories = self.memory.find_by_url(url)
        
        if not memories:
            return 0.0
        
        total_weight = sum(m.success_rate * m.times_used for m in memories)
        max_weight = sum(m.times_used for m in memories) * 1.0
        
        return min(total_weight / max_weight if max_weight > 0 else 0, 1.0)


# In-memory cache for quick access during a session
class SessionMemory:
    """In-memory cache for session data"""
    
    def __init__(self):
        self.current_url: str = None
        self.page_structure: dict = {}
        self.extracted_data: list[dict] = []
        self.action_history: list[dict] = []
        self.context: dict = {}
    
    def store_page_analysis(self, url: str, structure: dict):
        """Store page structure analysis"""
        self.current_url = url
        self.page_structure = structure
    
    def add_extracted_data(self, data: dict):
        """Add extracted data to session"""
        self.extracted_data.append(data)
    
    def add_action(self, action: dict):
        """Record an action"""
        action["timestamp"] = datetime.now().isoformat()
        self.action_history.append(action)
    
    def set_context(self, key: str, value: Any):
        """Set context value"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value"""
        return self.context.get(key, default)
    
    def clear(self):
        """Clear session memory"""
        self.current_url = None
        self.page_structure = {}
        self.extracted_data = []
        self.action_history = []
        self.context = {}
    
    def summarize(self) -> dict:
        """Get a summary of session"""
        return {
            "url": self.current_url,
            "data_items": len(self.extracted_data),
            "actions": len(self.action_history),
            "context_keys": list(self.context.keys())
        }
