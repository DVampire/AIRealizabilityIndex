import argparse
import os
import sys
import asyncio
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.evaluator import run_evaluation


console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Automation Evaluator (LangGraph) — evaluate a paper PDF or arXiv URL",
        epilog="Example: python cli.py https://arxiv.org/pdf/2507.14683 --arxiv-id 2507.14683 -o /abs/path/save_dir/eval_2507_14683",
    )
    parser.add_argument("pdf", help="Local PDF absolute path or URL (e.g., https://arxiv.org/pdf/xxxx)")
    parser.add_argument(
        "--arxiv-id",
        dest="arxiv_id",
        help="arXiv ID for the paper (e.g., 2507.14683)",
    )
    parser.add_argument(
        "-o",
        "--output-prefix",
        dest="output_prefix",
        help="Output file prefix (if provided, will save as <prefix>_YYYYMMDD_HHMMSS.md)",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=os.getenv("ANTHROPIC_API_KEY"),
        help="Anthropic API key (overrides ANTHROPIC_API_KEY env)",
    )
    return parser


async def main(argv: Optional[list[str]] = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    pdf_path: str = args.pdf
    arxiv_id: Optional[str] = args.arxiv_id
    output_prefix: Optional[str] = args.output_prefix
    api_key: Optional[str] = args.api_key or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        console.print("[yellow]Warning:[/yellow] ANTHROPIC_API_KEY not set and --api-key not provided.", highlight=False)

    console.print(Panel.fit(f"Evaluating: {pdf_path}"))
    if arxiv_id:
        console.print(f"arXiv ID: {arxiv_id}")
    
    try:
        result = await run_evaluation(pdf_path=pdf_path, arxiv_id=arxiv_id, output_file=output_prefix, api_key=api_key)
        console.print("\n[bold green]Done.[/bold green]\n")
        if output_prefix:
            console.print(f"Saved to prefix: {output_prefix}_<timestamp>.md")
        elif arxiv_id:
            console.print(f"Evaluation saved to database for paper: {arxiv_id}")
        else:
            console.print(result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())


