import argparse
from pathlib import Path

from src.pipeline import run_pipeline
from src.logger import logger


def main():
    parser = argparse.ArgumentParser(
        description="OCR Pipeline: Extract structured markdown from PDFs using Sharif LLM API"
    )
    
    parser.add_argument(
        "--input_dir", type=str, default="input_pdfs",
        help="Directory containing PDF files (default: input_pdfs)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force re-processing all pages (ignore resume)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Increase logging verbosity (debug mode)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel("DEBUG")
    
    input_path = Path(args.input_dir)
    run_pipeline(input_path, force_all=args.force)


if __name__ == "__main__":
    main()