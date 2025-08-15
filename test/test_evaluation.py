#!/usr/bin/env python3
"""
Test script: Verify that the run_evaluation function works correctly
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import argparse
from mmengine import DictAction

# 加载环境变量
load_dotenv(verbose=True)

# 设置根目录路径
root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.database import db
from src.logger import logger
from src.config import config
from src.agents.evaluator import run_evaluation


def parse_args():
    """Parse command line arguments"""
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


async def test_evaluation():
    """Test evaluation functionality"""
    print("=== Starting Evaluation Test ===")
    
    # Test parameters
    test_arxiv_id = "2508.09889"  # Use existing paper in database
    test_pdf_url = f"https://arxiv.org/pdf/{test_arxiv_id}.pdf"
    
    print(f"Test paper ID: {test_arxiv_id}")
    print(f"PDF URL: {test_pdf_url}")
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not found")
        return False
    
    print(f"✅ API key is set: {api_key[:20]}...")
    
    try:
        # Check if paper exists in database
        paper = await db.get_paper(test_arxiv_id)
        if paper:
            print(f"✅ Paper found in database: {paper['title']}")
        else:
            print(f"⚠️  Paper not in database, creating new record")
            # Insert test paper
            await db.insert_paper(
                arxiv_id=test_arxiv_id,
                title="Test Paper for Evaluation",
                authors="Test Author",
                abstract="This is a test paper for evaluation.",
                categories="cs.AI",
                published_date="2024-08-01"
            )
            print(f"✅ Test paper inserted into database")
        
        print("\n=== Starting Evaluation ===")
        
        # Run evaluation
        result = await run_evaluation(
            pdf_path=test_pdf_url,
            arxiv_id=test_arxiv_id,
            api_key=api_key
        )
        
        print(f"\n=== Evaluation Results ===")
        print(f"Result length: {len(result)} characters")
        print(f"First 500 characters: {result[:500]}...")
        
        # Check if result contains expected content
        if "AI Automation Assessment" in result or "Executive Summary" in result:
            print("✅ Evaluation result contains expected content")
        else:
            print("⚠️  Evaluation result may be incomplete")
        
        # Check evaluation status in database
        updated_paper = await db.get_paper(test_arxiv_id)
        if updated_paper and updated_paper.get('is_evaluated'):
            print("✅ Evaluation saved to database")
            print(f"Evaluation score: {updated_paper.get('evaluation_score')}")
            print(f"Evaluation tags: {updated_paper.get('evaluation_tags')}")
        else:
            print("❌ Evaluation not saved to database")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_operations():
    """Test database operations"""
    print("\n=== Testing Database Operations ===")
    
    try:
        # Test getting paper
        paper = await db.get_paper("2508.09889")
        if paper:
            print(f"✅ Database connection OK, found paper: {paper['title']}")
        else:
            print("⚠️  Test paper not found in database")
        
        # Test getting paper statistics
        stats = await db.get_papers_count()
        print(f"✅ Paper statistics: Total={stats['total']}, Evaluated={stats['evaluated']}, Unevaluated={stats['unevaluated']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operation error: {str(e)}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Evaluation System Test")
    
    # Parse command line arguments
    args = parse_args()

    # Initialize configuration
    config.init_config(args.config, args)

    # Initialize logger
    logger.init_logger(config=config)
    logger.info(f"| Logger initialized at: {config.log_path}")
    logger.info(f"| Config:\n{config.pretty_text}")

    # Initialize database
    await db.init_db(config=config)
    logger.info(f"| Database initialized at: {config.db_path}")
    
    print(f"✅ Database initialized: {config.db_path}")
    
    # Test database operations
    db_success = await test_database_operations()
    
    # Test evaluation functionality
    eval_success = await test_evaluation()
    
    print("\n=== Test Summary ===")
    print(f"Database operations: {'✅ Success' if db_success else '❌ Failed'}")
    print(f"Evaluation functionality: {'✅ Success' if eval_success else '❌ Failed'}")
    
    if db_success and eval_success:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed, please check error messages")


if __name__ == "__main__":
    asyncio.run(main())
