import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

API_BASE = config["api"]["base_url"]
API_KEY = config["api"]["api_key"]

VISION_MODEL = config["models"]["vision"] 
TEXT_MODEL = config["models"]["text"]

INPUT_DIR = Path(config["paths"]["input_pdfs"])
RAW_DIR = Path(config["paths"]["output_raw"])
TEXT_DIR = Path(config["paths"]["output_texts"] )
TEMP_IMG_DIR = Path(config["paths"]["temp_images"])

DPI = config["processing"]["dpi"] 
MAX_RETRY = config["processing"]["max_retry"]
RETRY_DELAY = config["processing"]["retry_delay"]