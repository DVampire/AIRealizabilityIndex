import os
import json
import aiosqlite
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager


class PapersDatabase():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_path = None
    
    async def init_db(self, config):
        """Initialize the database with required tables"""
        
        self.db_path = config.db_path
        
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            
            # Create papers cache table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers_cache (
                    date_str TEXT PRIMARY KEY,
                    html_content TEXT NOT NULL,
                    parsed_cards TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create papers table for individual arXiv papers
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    arxiv_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    abstract TEXT,
                    categories TEXT,
                    published_date TEXT,
                    evaluation_content TEXT,
                    evaluation_score REAL,
                    overall_score REAL,
                    evaluation_tags TEXT,
                    evaluation_status TEXT DEFAULT 'not_started',
                    is_evaluated BOOLEAN DEFAULT FALSE,
                    evaluation_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create latest_date table to track the most recent available date
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS latest_date (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    date_str TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default latest_date record if it doesn't exist
            await cursor.execute('''
                INSERT OR IGNORE INTO latest_date (id, date_str) 
                VALUES (1, ?)
            ''', (date.today().isoformat(),))
            
            await conn.commit()
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database connections"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row  # Enable dict-like access
        # Enable WAL mode for better concurrency
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=10000")
        await conn.execute("PRAGMA temp_store=MEMORY")
        try:
            yield conn
        finally:
            await conn.close()
    
    async def get_cached_papers(self, date_str: str) -> Optional[Dict[str, Any]]:
        """Get cached papers for a specific date"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                SELECT parsed_cards, created_at 
                FROM papers_cache 
                WHERE date_str = ?
            ''', (date_str,))
            
            row = await cursor.fetchone()
            if row:
                return {
                    'cards': json.loads(row['parsed_cards']),
                    'cached_at': row['created_at']
                }
            return None
    
    async def cache_papers(self, date_str: str, html_content: str, parsed_cards: List[Dict[str, Any]]):
        """Cache papers for a specific date"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                INSERT OR REPLACE INTO papers_cache 
                (date_str, html_content, parsed_cards, updated_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (date_str, html_content, json.dumps(parsed_cards)))
            await conn.commit()
    
    async def get_latest_cached_date(self) -> Optional[str]:
        """Get the latest cached date"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('SELECT date_str FROM latest_date WHERE id = 1')
            row = await cursor.fetchone()
            return row['date_str'] if row else None
    
    async def update_latest_date(self, date_str: str):
        """Update the latest available date"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                UPDATE latest_date 
                SET date_str = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = 1
            ''', (date_str,))
            await conn.commit()
    
    async def is_cache_fresh(self, date_str: str, max_age_hours: int = 24) -> bool:
        """Check if cache is fresh (within max_age_hours)"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                SELECT updated_at 
                FROM papers_cache 
                WHERE date_str = ?
            ''', (date_str,))
            
            row = await cursor.fetchone()
            if not row:
                return False
            
            cached_time = datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
            age = datetime.now(cached_time.tzinfo) - cached_time
            return age.total_seconds() < max_age_hours * 3600
    
    async def cleanup_old_cache(self, days_to_keep: int = 7):
        """Clean up old cache entries"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                DELETE FROM papers_cache 
                WHERE updated_at < ?
            ''', (cutoff_date,))
            await conn.commit()

    # Papers table methods
    async def insert_paper(self, arxiv_id: str, title: str, authors: str, abstract: str = None, 
                    categories: str = None, published_date: str = None):
        """Insert a new paper into the papers table"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                INSERT OR REPLACE INTO papers 
                (arxiv_id, title, authors, abstract, categories, published_date, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (arxiv_id, title, authors, abstract, categories, published_date))
            await conn.commit()
    
    async def get_paper(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get a paper by arxiv_id"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                SELECT * FROM papers WHERE arxiv_id = ?
            ''', (arxiv_id,))
            
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    async def get_papers_by_evaluation_status(self, is_evaluated: bool = None) -> List[Dict[str, Any]]:
        """Get papers by evaluation status"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            if is_evaluated is None:
                await cursor.execute('SELECT * FROM papers ORDER BY created_at DESC')
            else:
                await cursor.execute('''
                    SELECT * FROM papers 
                    WHERE is_evaluated = ? 
                    ORDER BY created_at DESC
                ''', (is_evaluated,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_paper_evaluation(self, arxiv_id: str, evaluation_content: str, 
                               evaluation_score: float = None, overall_score: float = None, evaluation_tags: str = None):
        """Update paper with evaluation content"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                UPDATE papers 
                SET evaluation_content = ?, 
                    evaluation_score = ?, 
                    overall_score = ?,
                    evaluation_tags = ?, 
                    is_evaluated = TRUE, 
                    evaluation_status = 'completed',
                    evaluation_date = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE arxiv_id = ?
            ''', (evaluation_content, evaluation_score, overall_score, evaluation_tags, arxiv_id))
            await conn.commit()
    
    async def update_paper_status(self, arxiv_id: str, status: str):
        """Update paper evaluation status"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                UPDATE papers 
                SET evaluation_status = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE arxiv_id = ?
            ''', (status, arxiv_id))
            await conn.commit()
    
    async def get_unevaluated_papers(self) -> List[Dict[str, Any]]:
        """Get all papers that haven't been evaluated yet"""
        return await self.get_papers_by_evaluation_status(is_evaluated=False)
    
    async def get_evaluated_papers(self) -> List[Dict[str, Any]]:
        """Get all papers that have been evaluated"""
        return await self.get_papers_by_evaluation_status(is_evaluated=True)
    
    async def search_papers(self, query: str) -> List[Dict[str, Any]]:
        """Search papers by title, authors, or abstract"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            search_pattern = f'%{query}%'
            await cursor.execute('''
                SELECT * FROM papers 
                WHERE title LIKE ? OR authors LIKE ? OR abstract LIKE ?
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern, search_pattern))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def delete_paper(self, arxiv_id: str):
        """Delete a paper from the database"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('DELETE FROM papers WHERE arxiv_id = ?', (arxiv_id,))
            await conn.commit()
    
    async def get_papers_count(self) -> Dict[str, int]:
        """Get count of papers by evaluation status"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute('SELECT COUNT(*) as total FROM papers')
            total_row = await cursor.fetchone()
            total = total_row['total']
            
            await cursor.execute('SELECT COUNT(*) as evaluated FROM papers WHERE is_evaluated = TRUE')
            evaluated_row = await cursor.fetchone()
            evaluated = evaluated_row['evaluated']
            
            return {
                'total': total,
                'evaluated': evaluated,
                'unevaluated': total - evaluated
            }

    def __str__(self):
        return f"PapersDatabase(db_path={self.db_path})"

    def __repr__(self):
        return self.__str__()

db = PapersDatabase()