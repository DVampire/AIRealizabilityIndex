from __future__ import annotations
import os
import sys
import base64
import os
import json
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from anthropic import AsyncAnthropic
from anthropic.types import ToolUseBlock
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field


from src.agents.prompt import REVIEWER_SYSTEM_PROMPT, EVALUATION_PROMPT_TEMPLATE, TOOLS, TOOL_CHOICE
from src.database import db
from src.config import config
from src.logger import logger


class ConversationState(BaseModel):
    """State for the conversation graph"""
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    response_text: str = ""
    tool_result: Optional[Dict[str, Any]] = None
    arxiv_id: Optional[str] = None
    pdf_path: Optional[str] = None
    output_file: Optional[str] = None


def _load_pdf_as_content(pdf_path: str) -> Dict[str, Any]:
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            data_b64 = base64.b64encode(f.read()).decode("utf-8")
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": data_b64,
            },
        }
    if pdf_path.startswith("http"):
        return {
            "type": "document",
            "source": {
                "type": "url",
                "url": pdf_path,
            },
        }
    raise FileNotFoundError(f"PDF not found or invalid path: {pdf_path}")


class Evaluator:
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required. Please set HF_SECRET_ANTHROPIC_API_KEY in Hugging Face Spaces secrets or ANTHROPIC_API_KEY environment variable.")
        self.client = AsyncAnthropic(api_key=api_key)
        self.system_prompt = REVIEWER_SYSTEM_PROMPT
        self.eval_template = EVALUATION_PROMPT_TEMPLATE

    async def __call__(self, state: ConversationState) -> ConversationState:
        """Evaluate the paper using the conversation state"""
        # Prepare messages for the API call
        messages = []
        messages.extend(state.messages)
        
        # Load PDF content if pdf_path is provided
        if state.pdf_path:
            try:
                pdf_content = _load_pdf_as_content(state.pdf_path)
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please evaluate this academic paper:"},
                        pdf_content
                    ]
                })
            except Exception as e:
                state.response_text = f"Error loading PDF: {str(e)}"
                return state
        
        # Add the evaluation prompt
        messages.append({
            "role": "user", 
            "content": self.eval_template
        })
        
        try:
            # Call Anthropic API with tools (async)
            response = await self.client.messages.create(
                model=config.model_id,
                max_tokens=4000,
                system=self.system_prompt,
                messages=messages,
                tools=TOOLS,
                tool_choice=TOOL_CHOICE
            )
            
            # Process the response
            # Check if response is a tool use or text
            if response.content and isinstance(response.content[0], ToolUseBlock):
                # This is a tool use response
                tool_use = response.content[0]
                if tool_use:
                    tool_result = tool_use.input
                    
                    # set metadata
                    tool_result['metadata'] = {
                        'assessed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'model': config.model_id,
                        'version': config.version,
                        'paper_path': state.pdf_path
                    }
                    
                    state.tool_result = tool_result
                    state.response_text = json.dumps(tool_result, ensure_ascii=False, indent=4)
                    
                    # Add tool use to messages
                    state.messages.append({
                        "role": "assistant",
                        "content": f"Tool use: {tool_use.name}"
                    })
                else:
                    state.response_text = "Error: Tool use response but no tool_use found"
            else:
                # This is a text response
                text_content = response.content[0].text if response.content else ""
                state.messages.append({
                    "role": "assistant",
                    "content": text_content
                })
                state.response_text = text_content
                
        except Exception as e:
            state.response_text = f"Error during evaluation: {str(e)}"
        
        return state


async def save_node(state: ConversationState) -> ConversationState:
    """Save the evaluation result to database"""
    try:
        if not state.arxiv_id:
            state.response_text += f"\n\nError: No arxiv_id provided for database save"
            return state
        
        # Parse the evaluation result
        evaluation_content = state.response_text
        evaluation_score = None
        overall_score = None
        evaluation_tags = None
        
        # Try to extract score and tags from tool_result if available
        if state.tool_result:
            try:
                # Extract overall automatability score from scorecard
                if 'scorecard' in state.tool_result and 'overall_automatability' in state.tool_result['scorecard']:
                    evaluation_score = state.tool_result['scorecard']['overall_automatability']
                
                # Extract overall score from scorecard
                if 'scorecard' in state.tool_result and 'overall_automatability' in state.tool_result['scorecard']:
                    overall_score = state.tool_result['scorecard']['overall_automatability']
                
                # Create tags from key dimensions in scorecard
                tags = []
                if 'scorecard' in state.tool_result:
                    scorecard = state.tool_result['scorecard']
                    if 'three_year_feasibility_pct' in scorecard:
                        tags.append(f"3yr_feasibility:{scorecard['three_year_feasibility_pct']}%")
                    if 'task_formalization' in scorecard:
                        tags.append(f"task_formalization:{scorecard['task_formalization']}/4")
                    if 'data_resource_availability' in scorecard:
                        tags.append(f"data_availability:{scorecard['data_resource_availability']}/4")
                
                evaluation_tags = ",".join(tags) if tags else None
                
            except Exception as e:
                logger.warning(f"Warning: Could not extract structured data from tool_result: {e}")
        else:
            # Try to parse evaluation_content as JSON to extract structured data
            try:
                evaluation_json = json.loads(evaluation_content)
                # Extract overall automatability score from scorecard
                if 'scorecard' in evaluation_json and 'overall_automatability' in evaluation_json['scorecard']:
                    evaluation_score = evaluation_json['scorecard']['overall_automatability']
                
                # Extract overall score from scorecard
                if 'scorecard' in evaluation_json and 'overall_automatability' in evaluation_json['scorecard']:
                    overall_score = evaluation_json['scorecard']['overall_automatability']
                
                # Create tags from key dimensions in scorecard
                tags = []
                if 'scorecard' in evaluation_json:
                    scorecard = evaluation_json['scorecard']
                    if 'three_year_feasibility_pct' in scorecard:
                        tags.append(f"3yr_feasibility:{scorecard['three_year_feasibility_pct']}%")
                    if 'task_formalization' in scorecard:
                        tags.append(f"task_formalization:{scorecard['task_formalization']}/4")
                    if 'data_resource_availability' in scorecard:
                        tags.append(f"data_availability:{scorecard['data_resource_availability']}/4")
                
                evaluation_tags = ",".join(tags) if tags else None
                
            except Exception as e:
                logger.warning(f"Warning: Could not parse evaluation_content as JSON: {e}")
        
        # Save to database
        await db.update_paper_evaluation(
            arxiv_id=state.arxiv_id,
            evaluation_content=evaluation_content,
            evaluation_score=evaluation_score,
            overall_score=overall_score,
            evaluation_tags=evaluation_tags
        )
        
        state.response_text += f"\n\nEvaluation saved to database for paper: {state.arxiv_id}"
        
    except Exception as e:
        state.response_text += f"\n\nError saving evaluation to database: {str(e)}"
    
    return state


def build_graph(api_key: Optional[str] = None):
    """Build the evaluation graph"""
    graph = StateGraph(ConversationState)
    evaluator = Evaluator(api_key=api_key)
    graph.add_node("evaluate", evaluator)
    graph.add_node("save", save_node)
    
    # Define the flow
    graph.set_entry_point("evaluate")
    graph.add_edge("evaluate", "save")
    graph.add_edge("save", END)
    
    return graph.compile()


async def run_evaluation(pdf_path: str, arxiv_id: Optional[str] = None, output_file: Optional[str] = None, api_key: Optional[str] = None) -> str:
    app = build_graph(api_key=api_key)
    initial = ConversationState(pdf_path=pdf_path, arxiv_id=arxiv_id, output_file=output_file)
    # Ensure compatibility with LangGraph's dict-based state
    final_state = await app.ainvoke(initial.model_dump())
    if isinstance(final_state, dict):
        return str(final_state.get("response_text", ""))
    if isinstance(final_state, ConversationState):
        return final_state.response_text
    return str(getattr(final_state, "response_text", ""))


