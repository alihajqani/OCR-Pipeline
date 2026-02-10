import sys
import logging
from tqdm import tqdm
from pathlib import Path

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("ocr_pipeline")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

fh = logging.FileHandler(log_dir / "ocr_pipeline.log")
fh.setFormatter(formatter)
logger.addHandler(fh)

class TqdmLoggingHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg, file=sys.stderr)
            self.flush()
        except Exception:
            self.handleError(record)

tqdm_handler = TqdmLoggingHandler()
tqdm_handler.setFormatter(formatter)
logger.addHandler(tqdm_handler)