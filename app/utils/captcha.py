import logging
import random
import string
from io import BytesIO

from captcha.image import ImageCaptcha

from app.config import DISABLE_CAPTCHA
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


def generate_captcha():
    image = ImageCaptcha()
    captcha_text = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    captcha_image = image.generate_image(captcha_text)

    # Store the captcha text in Redis with a TTL of 5 minutes
    key = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    buf = BytesIO()
    captcha_image.save(buf, format="PNG")
    buf.seek(0)
    redis_client.setex(f"captcha_text_{key}", 300, captcha_text)
    redis_client.setex(f"captcha_image_{key}", 300, buf.getvalue())
    return key


def validate_captcha(key: str, captcha_text: str) -> bool:
    if DISABLE_CAPTCHA:
        return True
    stored_captcha = redis_client.get(f"captcha_text_{key}")
    logger.info(f"Stored CAPTCHA: {stored_captcha}")
    logger.info(f"Received CAPTCHA: {captcha_text}")
    if stored_captcha is None:
        return False
    return stored_captcha.decode("utf-8").lower() == captcha_text.strip().lower()


def get_captcha_image(key: str) -> BytesIO:
    stored_image = redis_client.get(f"captcha_image_{key}")
    if stored_image is None:
        return None
    buf = BytesIO(stored_image)
    buf.seek(0)
    return buf
