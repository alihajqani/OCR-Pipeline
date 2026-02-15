from pathlib import Path

from src.logger import logger
from src.config import INPUT_DIR
from pdf2image import pdfinfo_from_path
from src.ocr_client import SharifClient
from src.utils import create_progress
from src.pdf_processor import find_all_pdfs, process_single_pdf


def run_pipeline(input_dir: Path = INPUT_DIR, force_all: bool = False) -> None:
    pdfs = find_all_pdfs(input_dir)
    if not pdfs:
        logger.warning("No PDFs to process. Exiting.")
        return

    client = SharifClient()

    pdf_progress = create_progress(len(pdfs), desc="PDF files", leave=True, position=0)

    total_processed_pages = 0

    for pdf in pdfs:
        pdf_progress.set_postfix({"current": pdf.name})

        try:
            info = pdfinfo_from_path(pdf)
            total_pages = info["Pages"]
        except:
            total_pages = None

        page_progress = create_progress(
            total=total_pages,
            desc=f"Pages in {pdf.name}",
            leave=False,
            position=1
        )

        processed = process_single_pdf(pdf, client, force_all=force_all, page_pbar=page_progress)
        
        total_processed_pages += processed

        if total_pages is None:
            page_progress.total = processed
            page_progress.n = processed
        page_progress.close()

        pdf_progress.update(1)

    pdf_progress.close()
    logger.info(f"Pipeline completed. Processed {total_processed_pages} new pages in total.")