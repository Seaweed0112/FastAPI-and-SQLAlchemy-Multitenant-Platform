import logging
from io import BytesIO

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.utils.captcha import generate_captcha, get_captcha_image, validate_captcha

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_captcha():
    logger.info("Generating CAPTCHA")

    key = generate_captcha()

    logger.info(f"CAPTCHA generated with key: {key}")

    return {"key": key, "image_url": f"/captcha/image/{key}"}


@router.get("/image/{key}")
async def get_captcha_image_endpoint(key: str):
    buf = get_captcha_image(key)
    if buf is None:
        raise HTTPException(status_code=404, detail="CAPTCHA not found")
    return StreamingResponse(buf, media_type="image/png")


@router.post("/validate")
async def validate_captcha_endpoint(key: str, captcha_text: str):
    if validate_captcha(key, captcha_text):
        return {"message": "CAPTCHA validated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA")
