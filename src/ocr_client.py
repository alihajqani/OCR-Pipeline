import io
import time
import base64
import urllib3
from typing import Optional

import requests
from PIL import Image

from src.logger import logger
from src.config import API_BASE, API_KEY, VISION_MODEL, TEXT_MODEL

urllib3.disable_warnings()

class SharifClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.verify = False
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

    def _base64_from_image(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return img_base64

    def _post(self, payload: dict, retries: int = 5) -> Optional[dict]:
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Sending request (attempt {attempt}) | model={payload.get('model')}")
                response = self.session.post(
                    API_BASE,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()

                usage = data.get("usage", {})
                if usage:
                    logger.info(f"Tokens → prompt: {usage.get('prompt_tokens')} | "
                                f"completion: {usage.get('completion_tokens')}")

                return data

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else None
                logger.warning(f"HTTP {status} | {e}")
                if status == 429:  # Rate limit
                    wait = 2 ** attempt * 10
                    logger.info(f"Rate limit hit → wait {wait}s")
                    time.sleep(wait)
                    continue
                elif status >= 500:
                    time.sleep(2 ** attempt * 5)
                    continue
                else:
                    logger.error(f"Non-retriable HTTP error: {e}")
                    return None

            except requests.exceptions.Timeout:
                logger.warning("Timeout → retry")
                time.sleep(2 ** attempt * 5)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt == retries:
                    return None
                time.sleep(2 ** attempt * 5)

        return None

    def extract_ocr(self, image: Image.Image) -> Optional[str]:
        base64_image = self._base64_from_image(image)

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "<image>\n<|grounding|>Convert the document to markdown."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4096
        }

        data = self._post(payload)
        if not data:
            return None

        try:
            text = data["choices"][0]["message"]["content"]
            logger.info("OCR extraction successful")
            return text.strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format: {e}")
            return None

    def refine_markdown(self, raw_text: str) -> Optional[str]:
        """رفاین متن خام به مارکداون ساختار یافته با مدل متنی"""
        prompt = f"""این متن از OCR یک صفحه دستورالعمل فارسی استخراج شده است.
        لطفاً آن را به مارکداون تمیز و ساختار یافته تبدیل کنید:
        - عنوان‌ها را با #، ## و غیره مشخص کنید
        - لیست‌ها را با - یا numbering
        - جدول‌ها را با markdown table
        - پاراگراف‌ها را جدا کنید
        - زبان فارسی را حفظ کنید
        - هیچ توضیح اضافی ننویسید، فقط مارکداون خروجی بدهید.

        متن:
        {raw_text}
        """

        payload = {
            "model": TEXT_MODEL,
            "messages": [
                {"role": "system", "content": "شما یک متخصص تبدیل متن به مارکداون هستید."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 8192
        }

        data = self._post(payload)
        if not data:
            return None

        try:
            text = data["choices"][0]["message"]["content"]
            logger.info("Markdown refinement successful")
            return text.strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format: {e}")
            return None