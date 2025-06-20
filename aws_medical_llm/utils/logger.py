import logging
from pathlib import Path
from flask import Flask

# Initialize Flask app
app = Flask(__name__)

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Main app logger
    app_logger = logging.getLogger('medical_app')
    app_logger.setLevel(logging.INFO)

    # File handler for all logs
    file_handler = logging.FileHandler(log_dir / 'app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)

    # Error file handler
    error_handler = logging.FileHandler(log_dir / 'errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # Add handlers to app logger
    app_logger.addHandler(file_handler)
    app_logger.addHandler(error_handler)
    app_logger.addHandler(console_handler)

    # Add handlers to Flask's built-in logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    return app_logger

# Run only if this script is executed directly
if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Logging setup complete.")
    app.logger.info("This is a Flask logger test.")
