import base64
import logging

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from app.core.config import CLOUDINARY_URL

logger = logging.getLogger(__name__)

# Configure Cloudinary if URL is provided
if CLOUDINARY_URL:
    try:
        cloudinary.config(cloudinary_url=CLOUDINARY_URL)
        logger.info("Cloudinary configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Cloudinary: {e}")
else:
    logger.warning("CLOUDINARY_URL not set. Falling back to database storage for photos.")

def upload_base64_image(base64_data: str, public_id: str | None = None) -> str | None:
    """
    Uploads a base64 encoded image to Cloudinary.
    Returns the secure URL if successful, otherwise None.
    """
    if not CLOUDINARY_URL:
        return None

    try:
        # Prepend prefix if missing for cloudinary to recognize base64
        if not base64_data.startswith("data:image"):
            # Assume jpeg for raw base64 uploads without prefix in this fallback context
            base64_data = f"data:image/jpeg;base64,{base64_data}"

        upload_kwargs = {"folder": "loan_server_items"}
        if public_id:
            upload_kwargs["public_id"] = public_id

        result = cloudinary.uploader.upload(base64_data, **upload_kwargs)
        return result.get("secure_url")
    except Exception as e:
        logger.error(f"Error uploading image to Cloudinary: {e}")
        return None

def destroy_image(public_id: str) -> bool:
    """
    Deletes an image from Cloudinary by its public_id.
    """
    if not CLOUDINARY_URL:
        return False
        
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        logger.error(f"Error deleting image from Cloudinary: {e}")
        return False
