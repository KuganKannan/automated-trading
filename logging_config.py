import logging

def setup_logging():
    """Configure logging for the trading application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [Line %(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler('trading.log'),
            logging.StreamHandler()
        ]
    )

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)
