import logging
import sys

def setup_logging():
    """Configure logging for the trading application"""
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [Line %(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler('trading.log'),
            logging.StreamHandler(sys.stdout)  # Explicitly use stdout
        ],
        force=True  # Force reconfiguration
    )

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)
