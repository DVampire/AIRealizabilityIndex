#!/usr/bin/env python3
"""
Test script for concurrent evaluation operations
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Add the project root to the path
root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

# Test papers (these should exist in your database)
TEST_PAPERS = [
    "2401.00001",
    "2401.00002", 
    "2401.00003"
]

BASE_URL = "http://localhost:7860"

async def test_concurrent_evaluations():
    """Test concurrent evaluation of multiple papers"""
    print("🧪 Testing Concurrent Evaluations")
    
    async with aiohttp.ClientSession() as session:
        # Start multiple evaluations concurrently
        tasks = []
        for arxiv_id in TEST_PAPERS:
            print(f"Starting evaluation for {arxiv_id}")
            task = asyncio.create_task(start_evaluation(session, arxiv_id))
            tasks.append(task)
        
        # Wait for all evaluations to start
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n=== Evaluation Start Results ===")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Error starting evaluation for {TEST_PAPERS[i]}: {result}")
            else:
                print(f"✅ Started evaluation for {TEST_PAPERS[i]}: {result.get('status')}")
        
        # Check active tasks
        print("\n=== Checking Active Tasks ===")
        async with session.get(f"{BASE_URL}/api/papers/evaluate/active-tasks") as response:
            if response.status == 200:
                active_tasks = await response.json()
                print(f"Active tasks: {active_tasks['total_active']}")
                print(f"Tracked tasks: {active_tasks['total_tracked']}")
                for arxiv_id, task_info in active_tasks['active_tasks'].items():
                    print(f"  - {arxiv_id}: {task_info['status']}")
            else:
                print(f"❌ Failed to get active tasks: {response.status}")
        
        # Monitor status for a few seconds
        print("\n=== Monitoring Status ===")
        for _ in range(5):
            await asyncio.sleep(2)
            for arxiv_id in TEST_PAPERS:
                async with session.get(f"{BASE_URL}/api/papers/evaluate/{arxiv_id}/status") as response:
                    if response.status == 200:
                        status = await response.json()
                        print(f"{arxiv_id}: {status['status']} (running: {status.get('is_running', False)})")
                    else:
                        print(f"❌ Failed to get status for {arxiv_id}")


async def start_evaluation(session, arxiv_id):
    """Start evaluation for a specific paper"""
    async with session.post(f"{BASE_URL}/api/papers/evaluate/{arxiv_id}") as response:
        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            raise Exception(f"HTTP {response.status}: {error_text}")


async def main():
    """Main function"""
    print("🚀 Starting Concurrent Evaluation Test")
    
    try:
        await test_concurrent_evaluations()
        print("\n✅ Concurrent evaluation test completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
