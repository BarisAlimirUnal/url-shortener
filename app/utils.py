# app/utils.py
import random
import string
from app.logger import get_logger

logger = get_logger(__name__)


def generate_short_code(length=6):
    """
    Generates a random 6-character code using letters and numbers.
    Example output: 'aB3xZ9', 'Kp2mQr'

    62 possible characters ^ 6 = 56 billion possible combinations
    so collisions are extremely rare.
    """
    chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    code = ''.join(random.choices(chars, k=length))
    logger.info(f"Generated short_code={code}")
    return code