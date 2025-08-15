import os
import sys
from dotenv import load_dotenv
load_dotenv(verbose=True)

from pathlib import Path
import argparse
from mmengine import DictAction
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
from bs4 import BeautifulSoup
import json
import asyncio
import uvicorn

root = str(Path(__file__).parent)
sys.path.append(root)

from src.database import db
from src.logger import logger
from src.config import config
from src.crawl import HuggingFaceDailyPapers
from src.agents.evaluator import run_evaluation

app = FastAPI(title="PaperAgent")

# Local development: allow same-origin and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Remove the find_next_available_date function since we're using HuggingFace's redirect mechanism


@app.get("/api/daily")
async def get_daily(date_str: Optional[str] = None, direction: Optional[str] = None) -> Dict[str, Any]:
    target_date = date_str or date.today().isoformat()
    
    # Initialize HuggingFaceDailyPapers
    hf_daily = HuggingFaceDailyPapers()
    
    # First, check if we have fresh cache for the requested date
    cached_data = await db.get_cached_papers(target_date)
    if cached_data and await db.is_cache_fresh(target_date):
        print(f"Using cached data for {target_date}")
        return {
            "date": target_date,
            "requested_date": target_date,
            "cards": cached_data['cards'],
            "fallback_used": False,
            "cached": True,
            "cached_at": cached_data['cached_at']
        }
    
    # Handle different navigation directions
    if direction == "prev":
        # For previous navigation, use redirect mechanism to find the most recent available date
        try:
            actual_date, html = await hf_daily.fetch_daily_html(target_date)
            print(f"Previous navigation: fetched {actual_date} (requested {target_date})")
            
            # If we got redirected to a different date, that's our fallback
            if actual_date != target_date:
                print(f"Redirected from {target_date} to {actual_date}")
                
                # Check if the redirected date has fresh cache
                cached_data = await db.get_cached_papers(actual_date)
                if cached_data and await db.is_cache_fresh(actual_date):
                    print(f"Using cached data for redirected date {actual_date}")
                    return {
                        "date": actual_date,
                        "requested_date": target_date,
                        "cards": cached_data['cards'],
                        "fallback_used": True,
                        "cached": True,
                        "cached_at": cached_data['cached_at']
                    }
                
                # Process the HTML we got
                cards = hf_daily.parse_daily_cards(html)
                enriched_cards = await enrich_cards(cards)
                
                # Cache the results for the redirected date
                await db.cache_papers(actual_date, html, enriched_cards)
                
                return {
                    "date": actual_date,
                    "requested_date": target_date,
                    "cards": enriched_cards,
                    "fallback_used": True,
                    "cached": False
                }
            
            # If we got the exact date we requested, process normally
            cards = hf_daily.parse_daily_cards(html)
            enriched_cards = await enrich_cards(cards)
            await db.cache_papers(actual_date, html, enriched_cards)
            
            return {
                "date": actual_date,
                "requested_date": target_date,
                "cards": enriched_cards,
                "fallback_used": False,
                "cached": False
            }
            
        except Exception as e:
            print(f"Failed to fetch {target_date} for previous navigation: {e}")
            # Fallback to cached data if available
            cached_data = await db.get_cached_papers(target_date)
            if cached_data:
                return {
                    "date": target_date,
                    "requested_date": target_date,
                    "cards": cached_data['cards'],
                    "fallback_used": False,
                    "cached": True,
                    "cached_at": cached_data['cached_at']
                }
            raise HTTPException(status_code=503, detail="Unable to fetch papers and no cache available")
    
    elif direction == "next":
        # For next navigation, we need to find the next available date
        # First try the exact date
        try:
            actual_date, html = await hf_daily.fetch_daily_html(target_date)
            print(f"Next navigation: fetched {actual_date} (requested {target_date})")
            
            # If we got the exact date we requested, that's perfect
            if actual_date == target_date:
                cards = hf_daily.parse_daily_cards(html)
                enriched_cards = await enrich_cards(cards)
                await db.cache_papers(actual_date, html, enriched_cards)
                
                return {
                    "date": actual_date,
                    "requested_date": target_date,
                    "cards": enriched_cards,
                    "fallback_used": False,
                    "cached": False
                }
            
            # If we got redirected, it means the requested date doesn't exist
            # We need to find the next available date by incrementing
            print(f"Requested date {target_date} doesn't exist, searching for next available date")
            
            # Try to find the next available date by incrementing
            next_date = await find_next_available_date_forward(target_date)
            if next_date:
                cached_data = await db.get_cached_papers(next_date)
                if cached_data and await db.is_cache_fresh(next_date):
                    print(f"Using cached data for next available date {next_date}")
                    return {
                        "date": next_date,
                        "requested_date": target_date,
                        "cards": cached_data['cards'],
                        "fallback_used": True,
                        "cached": True,
                        "cached_at": cached_data['cached_at']
                    }
                
                # Fetch the next available date
                actual_date, html = await hf_daily.fetch_daily_html(next_date)
                cards = hf_daily.parse_daily_cards(html)
                enriched_cards = await enrich_cards(cards)
                await db.cache_papers(actual_date, html, enriched_cards)
                
                return {
                    "date": actual_date,
                    "requested_date": target_date,
                    "cards": enriched_cards,
                    "fallback_used": True,
                    "cached": False
                }
            
            # If no next date found, return empty
            return {
                "date": target_date,
                "requested_date": target_date,
                "cards": [],
                "fallback_used": False,
                "cached": False
            }
            
        except Exception as e:
            print(f"Failed to fetch {target_date} for next navigation: {e}")
            # Try to find next available date
            next_date = await find_next_available_date_forward(target_date)
            if next_date:
                cached_data = await db.get_cached_papers(next_date)
                if cached_data:
                    return {
                        "date": next_date,
                        "requested_date": target_date,
                        "cards": cached_data['cards'],
                        "fallback_used": True,
                        "cached": True,
                        "cached_at": cached_data['cached_at']
                    }
            
            # If no cache available, return error
            raise HTTPException(status_code=503, detail="Unable to fetch papers and no cache available")
    
    else:
        # No direction specified, try the exact date first
        try:
            actual_date, html = await hf_daily.fetch_daily_html(target_date)
            print(f"Direct fetch: fetched {actual_date} (requested {target_date})")
            
            # If we got redirected, that's our fallback
            if actual_date != target_date:
                print(f"Redirected from {target_date} to {actual_date}")
                
                # Check if the redirected date has fresh cache
                cached_data = await db.get_cached_papers(actual_date)
                if cached_data and await db.is_cache_fresh(actual_date):
                    print(f"Using cached data for redirected date {actual_date}")
                    return {
                        "date": actual_date,
                        "requested_date": target_date,
                        "cards": cached_data['cards'],
                        "fallback_used": True,
                        "cached": True,
                        "cached_at": cached_data['cached_at']
                    }
                
                # Process the HTML we got
                cards = hf_daily.parse_daily_cards(html)
                enriched_cards = await enrich_cards(cards)
                
                # Cache the results for the redirected date
                await db.cache_papers(actual_date, html, enriched_cards)
                
                return {
                    "date": actual_date,
                    "requested_date": target_date,
                    "cards": enriched_cards,
                    "fallback_used": True,
                    "cached": False
                }
            
            # If we got the exact date we requested, process normally
            cards = hf_daily.parse_daily_cards(html)
            enriched_cards = await enrich_cards(cards)
            await db.cache_papers(actual_date, html, enriched_cards)
            
            return {
                "date": actual_date,
                "requested_date": target_date,
                "cards": enriched_cards,
                "fallback_used": False,
                "cached": False
            }
            
        except Exception as e:
            print(f"Failed to fetch {target_date}: {e}")
            
            # If everything fails, return cached data if available
            cached_data = await db.get_cached_papers(target_date)
            if cached_data:
                return {
                    "date": target_date,
                    "requested_date": target_date,
                    "cards": cached_data['cards'],
                    "fallback_used": False,
                    "cached": True,
                    "cached_at": cached_data['cached_at']
                }
            
            # If no cache available, return error
            raise HTTPException(status_code=503, detail="Unable to fetch papers and no cache available")


async def find_next_available_date_forward(start_date: str, max_attempts: int = 30) -> Optional[str]:
    """Find the next available date by incrementing and checking"""
    from datetime import datetime, timedelta
    
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    for i in range(max_attempts):
        current_date += timedelta(days=1)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Check if we have cache for this date
        cached_data = await db.get_cached_papers(date_str)
        if cached_data:
            return date_str
            
        # Try to fetch this date (but don't wait too long)
        try:
            import httpx
            from src.crawl.huggingface_daily import HuggingFaceDailyPapers
            
            hf_daily = HuggingFaceDailyPapers()
            
            # Use a shorter timeout for quick checks
            async with httpx.AsyncClient(timeout=5) as client:
                actual_date, html = await hf_daily.fetch_daily_html(date_str)
                if actual_date == date_str:
                    return date_str
                    
        except Exception as e:
            print(f"Failed to check {date_str}: {e}")
            continue
    
    return None


async def enrich_cards(cards):
    """Enrich cards with paper details from database"""
    for c in cards:
        arxiv_id = c.get("arxiv_id")
        if arxiv_id:
            paper = await db.get_paper(arxiv_id)
            if paper:
                # Add evaluation status
                c["has_eval"] = paper.get('is_evaluated', False)
                c["is_evaluated"] = paper.get('is_evaluated', False)
                
                # Add evaluation details if available
                if paper.get('is_evaluated'):
                    c["evaluation_score"] = paper.get('evaluation_score')
                    c["overall_score"] = paper.get('overall_score')
                    c["evaluation_date"] = paper.get('evaluation_date')
                    c["evaluation_tags"] = paper.get('evaluation_tags')
                
                # Add paper details (use cached data as fallback)
                if not c.get("title") and paper.get("title"):
                    c["title"] = paper["title"]
                if not c.get("authors") and paper.get("authors"):
                    c["authors"] = paper["authors"]
                if not c.get("abstract") and paper.get("abstract"):
                    c["abstract"] = paper["abstract"]
            else:
                c["has_eval"] = False
                c["is_evaluated"] = False
        else:
            c["has_eval"] = False
            c["is_evaluated"] = False
    
    return cards


@app.get("/api/evals")
async def list_evals() -> Dict[str, Any]:
    # Get evaluated papers from database
    evaluated_papers = await db.get_evaluated_papers()
    items: List[Dict[str, Any]] = []
    
    for paper in evaluated_papers:
        items.append({
            "arxiv_id": paper['arxiv_id'],
            "title": paper['title'],
            "authors": paper['authors'],
            "evaluation_date": paper['evaluation_date'],
            "evaluation_score": paper['evaluation_score'],
            "evaluation_tags": paper['evaluation_tags']
        })
    
    return {"count": len(items), "items": items}


@app.get("/api/has-eval/{paper_id}")
async def has_eval(paper_id: str) -> Dict[str, bool]:
    paper = await db.get_paper(paper_id)
    exists = paper is not None and paper.get('is_evaluated', False)
    return {"exists": exists}


@app.get("/api/paper/{paper_id}")
async def get_paper_details(paper_id: str) -> Dict[str, Any]:
    """Get detailed paper information from database"""
    paper = await db.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "arxiv_id": paper.get('arxiv_id'),
        "title": paper.get('title'),
        "authors": paper.get('authors'),
        "abstract": paper.get('abstract'),
        "categories": paper.get('categories'),
        "published_date": paper.get('published_date'),
        "is_evaluated": paper.get('is_evaluated', False),
        "evaluation_date": paper.get('evaluation_date'),
        "created_at": paper.get('created_at'),
        "updated_at": paper.get('updated_at')
    }


@app.get("/api/paper-score/{paper_id}")
async def get_paper_score(paper_id: str) -> Dict[str, Any]:
    paper = await db.get_paper(paper_id)
    print(f"Paper data for {paper_id}:", paper)
    
    if not paper or not paper.get('is_evaluated', False):
        print(f"Paper {paper_id} not found or not evaluated")
        return {"has_score": False}
    
    # Calculate overall score as average of all dimensions (same as radar chart)
    try:
        evaluation_content = paper.get('evaluation_content')
        if evaluation_content:
            evaluation_json = json.loads(evaluation_content)
            if 'scorecard' in evaluation_json:
                scorecard = evaluation_json['scorecard']
                values = [
                    scorecard.get('task_formalization', 0),
                    scorecard.get('data_resource_availability', 0),
                    scorecard.get('input_output_complexity', 0),
                    scorecard.get('real_world_interaction', 0),
                    scorecard.get('existing_ai_coverage', 0),
                    scorecard.get('human_originality', 0),
                    scorecard.get('safety_ethics', 0),
                    scorecard.get('technical_maturity_needed', 0),
                    scorecard.get('three_year_feasibility_pct', 0) / 25,  # Convert percentage to 0-4 scale
                    scorecard.get('overall_automatability', 0)
                ]
                valid_scores = [v for v in values if v > 0]
                overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
                print(f"Calculated overall score: {overall_score}")
                
                return {
                    "has_score": True,
                    "score": overall_score,
                    "evaluation_date": paper.get('evaluation_date')
                }
    except Exception as e:
        print(f"Error calculating overall score: {e}")
    
    # Fallback to stored values
    overall_score = paper.get('overall_score')
    evaluation_score = paper.get('evaluation_score')
    print(f"Fallback - Overall score: {overall_score}, Evaluation score: {evaluation_score}")
    
    return {
        "has_score": True,
        "score": overall_score if overall_score is not None else evaluation_score,
        "evaluation_date": paper.get('evaluation_date')
    }


@app.get("/api/eval/{paper_id}")
async def get_eval(paper_id: str) -> Any:
    paper = await db.get_paper(paper_id)
    if not paper or not paper.get('is_evaluated', False):
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Parse evaluation content if it's JSON
    evaluation_content = paper['evaluation_content']
    try:
        evaluation_json = json.loads(evaluation_content)
    except json.JSONDecodeError:
        # If not JSON, create a simple structure
        evaluation_json = {
            "evaluation_content": evaluation_content,
            "arxiv_id": paper_id,
            "evaluation_date": paper['evaluation_date'],
            "evaluation_score": paper['evaluation_score'],
            "evaluation_tags": paper['evaluation_tags']
        }
    
    return evaluation_json


@app.get("/api/available-dates")
async def get_available_dates() -> Dict[str, Any]:
    """Get list of available dates in the cache"""
    async with db.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('SELECT date_str FROM papers_cache ORDER BY date_str DESC LIMIT 30')
        rows = await cursor.fetchall()
        dates = [row['date_str'] for row in rows]
        
        return {
            "available_dates": dates,
            "count": len(dates)
        }


@app.get("/api/cache/status")
async def get_cache_status() -> Dict[str, Any]:
    """Get cache status and statistics"""
    async with db.get_connection() as conn:
        cursor = await conn.cursor()
        
        # Get total cached dates
        await cursor.execute('SELECT COUNT(*) as count FROM papers_cache')
        total_cached = (await cursor.fetchone())['count']
        
        # Get latest cached date
        await cursor.execute('SELECT date_str, updated_at FROM latest_date WHERE id = 1')
        latest_info = await cursor.fetchone()
        
        # Get cache age distribution
        await cursor.execute('''
            SELECT 
                CASE 
                    WHEN updated_at > datetime('now', '-1 hour') THEN '1 hour'
                    WHEN updated_at > datetime('now', '-24 hours') THEN '24 hours'
                    WHEN updated_at > datetime('now', '-7 days') THEN '7 days'
                    ELSE 'older'
                END as age_group,
                COUNT(*) as count
            FROM papers_cache 
            GROUP BY age_group
        ''')
        rows = await cursor.fetchall()
        age_distribution = {row['age_group']: row['count'] for row in rows}
        
        return {
            "total_cached_dates": total_cached,
            "latest_cached_date": latest_info['date_str'] if latest_info else None,
            "latest_updated": latest_info['updated_at'] if latest_info else None,
            "age_distribution": age_distribution
        }


@app.get("/api/papers/status")
async def get_papers_status() -> Dict[str, Any]:
    """Get papers database status and statistics"""
    papers_count = await db.get_papers_count()
    
    # Get recent evaluations
    recent_papers = await db.get_evaluated_papers()
    recent_evaluations = []
    for paper in recent_papers[:10]:  # Get last 10 evaluations
        recent_evaluations.append({
            "arxiv_id": paper['arxiv_id'],
            "title": paper['title'],
            "evaluation_date": paper['evaluation_date'],
            "evaluation_score": paper['evaluation_score']
        })
    
    return {
        "papers_count": papers_count,
        "recent_evaluations": recent_evaluations
    }


@app.post("/api/papers/insert")
async def insert_paper(paper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new paper into the database"""
    try:
        required_fields = ['arxiv_id', 'title', 'authors']
        for field in required_fields:
            if field not in paper_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        await db.insert_paper(
            arxiv_id=paper_data['arxiv_id'],
            title=paper_data['title'],
            authors=paper_data['authors'],
            abstract=paper_data.get('abstract'),
            categories=paper_data.get('categories'),
            published_date=paper_data.get('published_date')
        )
        
        return {"message": f"Paper {paper_data['arxiv_id']} inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert paper: {str(e)}")


# Global task tracker for concurrent evaluations
evaluation_tasks = {}

@app.post("/api/papers/evaluate/{arxiv_id}")
async def evaluate_paper(arxiv_id: str, force_reevaluate: bool = False) -> Dict[str, Any]:
    """Evaluate a paper by its arxiv_id"""
    try:
        # Check if paper exists in database
        paper = await db.get_paper(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found in database")
        
        # Check if already evaluated (unless force_reevaluate is True)
        if not force_reevaluate and paper.get('is_evaluated', False):
            return {"message": f"Paper {arxiv_id} already evaluated", "status": "already_evaluated"}
        
        # Check if evaluation is already running
        if arxiv_id in evaluation_tasks and not evaluation_tasks[arxiv_id].done():
            return {"message": f"Evaluation already running for {arxiv_id}", "status": "already_running"}
        
        # Create PDF URL from arxiv_id
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        # Run evaluation in background task
        async def run_eval():
            try:
                # Update paper status to "evaluating"
                await db.update_paper_status(arxiv_id, "evaluating")
                logger.info(f"Started {'re-' if force_reevaluate else ''}evaluation for {arxiv_id}")
                
                result = await run_evaluation(
                    pdf_path=pdf_url,
                    arxiv_id=arxiv_id,
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                
                # Update paper status to "completed"
                await db.update_paper_status(arxiv_id, "completed")
                logger.info(f"{'Re-' if force_reevaluate else ''}evaluation completed for {arxiv_id}")
            except Exception as e:
                # Update paper status to "failed"
                await db.update_paper_status(arxiv_id, "failed")
                logger.error(f"{'Re-' if force_reevaluate else ''}evaluation failed for {arxiv_id}: {str(e)}")
            finally:
                # Clean up task from tracker
                if arxiv_id in evaluation_tasks:
                    del evaluation_tasks[arxiv_id]
        
        # Start evaluation in background and track it
        task = asyncio.create_task(run_eval())
        evaluation_tasks[arxiv_id] = task
        
        return {
            "message": f"{'Re-' if force_reevaluate else ''}evaluation started for paper {arxiv_id}", 
            "status": "started",
            "pdf_url": pdf_url,
            "concurrent_tasks": len(evaluation_tasks),
            "is_reevaluate": force_reevaluate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate paper: {str(e)}")


@app.get("/api/papers/evaluate/{arxiv_id}/status")
async def get_evaluation_status(arxiv_id: str) -> Dict[str, Any]:
    """Get evaluation status for a paper"""
    try:
        paper = await db.get_paper(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        status = paper.get('evaluation_status', 'not_started')
        is_evaluated = paper.get('is_evaluated', False)
        
        # Check if task is currently running
        is_running = arxiv_id in evaluation_tasks and not evaluation_tasks[arxiv_id].done()
        
        return {
            "arxiv_id": arxiv_id,
            "status": status,
            "is_evaluated": is_evaluated,
            "is_running": is_running,
            "evaluation_date": paper.get('evaluation_date'),
            "evaluation_score": paper.get('evaluation_score')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation status: {str(e)}")


@app.post("/api/papers/reevaluate/{arxiv_id}")
async def reevaluate_paper(arxiv_id: str) -> Dict[str, Any]:
    """Re-evaluate a paper by its arxiv_id"""
    try:
        # Check if paper exists in database
        paper = await db.get_paper(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found in database")
        
        # Check if evaluation is already running
        if arxiv_id in evaluation_tasks and not evaluation_tasks[arxiv_id].done():
            return {"message": f"Evaluation already running for {arxiv_id}", "status": "already_running"}
        
        # Create PDF URL from arxiv_id
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        # Run re-evaluation in background task
        async def run_reeval():
            try:
                # Update paper status to "evaluating"
                await db.update_paper_status(arxiv_id, "evaluating")
                logger.info(f"Started re-evaluation for {arxiv_id}")
                
                result = await run_evaluation(
                    pdf_path=pdf_url,
                    arxiv_id=arxiv_id,
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                
                # Update paper status to "completed"
                await db.update_paper_status(arxiv_id, "completed")
                logger.info(f"Re-evaluation completed for {arxiv_id}")
            except Exception as e:
                # Update paper status to "failed"
                await db.update_paper_status(arxiv_id, "failed")
                logger.error(f"Re-evaluation failed for {arxiv_id}: {str(e)}")
            finally:
                # Clean up task from tracker
                if arxiv_id in evaluation_tasks:
                    del evaluation_tasks[arxiv_id]
        
        # Start re-evaluation in background and track it
        task = asyncio.create_task(run_reeval())
        evaluation_tasks[arxiv_id] = task
        
        return {
            "message": f"Re-evaluation started for paper {arxiv_id}", 
            "status": "started",
            "pdf_url": pdf_url,
            "concurrent_tasks": len(evaluation_tasks),
            "is_reevaluate": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to re-evaluate paper: {str(e)}")


@app.get("/api/papers/evaluate/active-tasks")
async def get_active_evaluation_tasks() -> Dict[str, Any]:
    """Get list of currently running evaluation tasks"""
    active_tasks = {}
    for arxiv_id, task in evaluation_tasks.items():
        if not task.done():
            active_tasks[arxiv_id] = {
                "status": "running",
                "done": task.done(),
                "cancelled": task.cancelled()
            }
    
    return {
        "active_tasks": active_tasks,
        "total_active": len(active_tasks),
        "total_tracked": len(evaluation_tasks)
    }


@app.post("/api/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """Clear all cached data"""
    async with db.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('DELETE FROM papers_cache')
        await conn.commit()
    return {"message": "Cache cleared successfully"}


@app.post("/api/cache/refresh/{date_str}")
async def refresh_cache(date_str: str) -> Dict[str, Any]:
    """Force refresh cache for a specific date"""
    try:
        # Initialize HuggingFaceDailyPapers
        hf_daily = HuggingFaceDailyPapers()
        
        # Force fetch fresh data
        actual_date, html = await hf_daily.fetch_daily_html(date_str)
        cards = hf_daily.parse_daily_cards(html)
        
        # Cache the results
        await db.cache_papers(actual_date, html, cards)
        
        return {
            "message": f"Cache refreshed for {actual_date}",
            "cards_count": len(cards)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {str(e)}")


@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon to prevent 404 errors"""
    # Return a simple SVG favicon as text
    favicon_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect width="100" height="100" fill="#3b82f6"/>
        <text x="50" y="65" font-family="Arial, sans-serif" font-size="50" text-anchor="middle" fill="white">📄</text>
    </svg>'''
    
    from fastapi.responses import Response
    return Response(content=favicon_svg, media_type="image/svg+xml")


@app.get("/styles.css")
async def get_styles():
    """Serve CSS with no-cache headers to prevent caching issues during development"""
    response = FileResponse("frontend/styles.css", media_type="text/css")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

async def main():
    # Parse command line arguments
    args = parse_args()

    # Initialize the configuration
    config.init_config(args.config, args)

    # Initialize the logger
    logger.init_logger(config=config)
    logger.info(f"| Logger initialized at: {config.log_path}")
    logger.info(f"| Config:\n{config.pretty_text}")

    # Initialize the database
    await db.init_db(config=config)
    logger.info(f"| Database initialized at: {config.db_path}")
    
    # Load Frontend
    os.makedirs(config.frontend_path, exist_ok=True)
    app.mount("/", StaticFiles(directory=config.frontend_path, html=True), name="static")
    logger.info(f"| Frontend initialized at: {config.frontend_path}")
    
    # Use port 7860 for Hugging Face Spaces, fallback to 7860 for local development
    config_uvicorn = uvicorn.Config(app, host="0.0.0.0", port=7860)
    server = uvicorn.Server(config_uvicorn)
    await server.serve()
    
if __name__ == "__main__":
    asyncio.run(main())