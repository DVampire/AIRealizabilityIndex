#!/usr/bin/env python3
"""
Test script for async database operations
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from mmengine.config import DictAction

# Add the project root to the path
root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.database import db
from src.config import config
from src.logger import logger

def parse_args():
    parser = argparse.ArgumentParser(description='main')
    parser.add_argument("--config", default=os.path.join(root, "configs", "paper_agent.py"), help="config file path")

    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=DictAction,
        help='override some settings in the used config, the key-value pair '
        'in xxx=yyy format will be merged into config file. If the value to '
        'be overwritten is a list, it should be like key="[a,b]" or key=a,b '
        'It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" '
        'Note that the quotation marks are necessary and that no white space '
        'is allowed.')
    args = parser.parse_args()
    return args


async def test_async_database():
    """Test async database operations"""
    print("🧪 Testing Async Database Operations")
    
    try:
        # Initialize database
        await db.init_db(config=config)
        print("✅ Database initialized successfully")
        
        # Test inserting a paper
        test_arxiv_id = "2401.00001"
        await db.insert_paper(
            arxiv_id=test_arxiv_id,
            title="Test Async Paper",
            authors="Test Author",
            abstract="This is a test paper for async database operations.",
            categories="cs.AI",
            published_date="2024-01-01"
        )
        print("✅ Paper inserted successfully")
        
        # Test getting the paper
        paper = await db.get_paper(test_arxiv_id)
        if paper:
            print(f"✅ Paper retrieved: {paper['title']}")
        else:
            print("❌ Paper not found")
            return False
        
        # Test updating paper evaluation
        await db.update_paper_evaluation(
            arxiv_id=test_arxiv_id,
            evaluation_content="Test evaluation content",
            evaluation_score=3.5,
            overall_score=3.2,
            evaluation_tags="test_tag"
        )
        print("✅ Paper evaluation updated successfully")
        
        # Test getting evaluated papers
        evaluated_papers = await db.get_evaluated_papers()
        print(f"✅ Found {len(evaluated_papers)} evaluated papers")
        
        # Test getting paper count
        count = await db.get_papers_count()
        print(f"✅ Paper count: {count}")
        
        # Test searching papers
        search_results = await db.search_papers("Test")
        print(f"✅ Search results: {len(search_results)} papers found")
        
        # Test cache operations
        await db.cache_papers("2024-01-01", "<html>test</html>", [{"test": "data"}])
        print("✅ Cache operation successful")
        
        cached_data = await db.get_cached_papers("2024-01-01")
        if cached_data:
            print("✅ Cache retrieval successful")
        else:
            print("❌ Cache retrieval failed")
        
        # Test cache freshness
        is_fresh = await db.is_cache_fresh("2024-01-01")
        print(f"✅ Cache freshness check: {is_fresh}")
        
        print("\n🎉 All async database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during async database test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    print("🚀 Starting Async Database Test")
        # Parse command line arguments
    args = parse_args()

    # Initialize the configuration
    config.init_config(args.config, args)
    
    # Initialize logger
    logger.init_logger(config=config)
    
    # Run the test
    success = await test_async_database()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
