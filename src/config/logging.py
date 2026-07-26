import logging
import sys

from src.config.settings import settings

def setup_logging():
    """Setup basic structured logging."""
    logger = logging.getLogger("careerpilot")
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()
