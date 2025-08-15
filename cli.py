import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the CLI
from src.cli.cli import main

if __name__ == "__main__":
    main()
