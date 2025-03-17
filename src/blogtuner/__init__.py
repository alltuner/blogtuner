import logging


logger = logging.getLogger(__name__)

# FIXME: Remove when done debugging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
__all__ = ["logger"]
