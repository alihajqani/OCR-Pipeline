from pathlib import Path
from typing import Generator, Tuple, List

from PIL import Image
from pdf_processor import convert_from_path

from src.logger import logger
from src.ocr_client import SharifClient
from src.config import INPUT_DIR, RAW_DIR, TEXT_DIR, DPI

def find_all_pdfs(input_dir: Path = INPUT_DIR) -> List[Path]:
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return []

    pdfs = list(input_dir.glob("**/*.pdf"))
    logger.info(f"Found {len(pdfs)} PDF files in {input_dir}")
    return sorted(pdfs)

def get_output_paths(pdf_path: Path, page_num: int) -> Tuple[Path, Path]:
    base_name = pdf_path.stem
    raw_dir = RAW_DIR / base_name
    text_dir = TEXT_DIR / base_name

    raw_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / f"{base_name}_page_{page_num}_raw.txt"
    final_path = text_dir / f"{base_name}_page_{page_num}.txt"

    return raw_path, final_path

def convert_pdf_to_images(pdf_path: Path, dpi: int = DPI) -> Generator[Tuple[int, Image.Image], None, None]:
    try:
        logger.info(f"Converting PDF to images: {pdf_path.name}")
        images = convert_from_path(pdf_path, dpi=dpi, fmt="jpg")

        for i, img in enumerate(images, 1):
            yield i, img

        logger.info(f"Successfully converted {len(images)} pages from {pdf_path.name}")

    except Exception as e:
        logger.error(f"Failed to convert PDF {pdf_path.name}: {e}", exc_info=True)
        yield from []

def process_single_pdf(pdf_path: Path, client: SharifClient, force_all: bool = False, page_pbar = None) -> int:

    processed_count = 0

    for page_num, image in convert_pdf_to_images(pdf_path):
        raw_path, final_path = get_output_paths(pdf_path, page_num)

        if final_path.exists() and not force_all:
            logger.info(f"Page {page_num} already processed, skipping: {final_path.name}")
            if page_pbar:
                page_pbar.update(1)
                continue

        logger.info(f"Processing page {page_num} of {pdf_path.name}")

        raw_text = client.extract_ocr(image)
        if not raw_text:
                logger.error(f"OCR failed for page {page_num} of {pdf_path.name}")
                continue

        raw_path.write_text(raw_text, encoding="utf-8")
        logger.info(f"Raw text saved: {raw_path}")

        refined = client.refine_markdown(raw_text)
        if not refined:
                logger.error(f"Markdown refinement failed for page {page_num} of {pdf_path.name}")
                continue


        final_path.write_text(refined, encoding="utf-8")
        logger.info(f"Final markdown saved: {final_path}")

        processed_count += 1

        if page_pbar:
            page_pbar.update(1)
            page_pbar.set_postfix({"page": page_num})

    return processed_count