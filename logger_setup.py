import logging
import os


def setup_logging(log_file="pokedex.log", log_level=logging.DEBUG):
    """Configures the logging system."""

    log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_directory, exist_ok=True)  # Ensure log directory exists

    # Get the root logger
    logger = logging.getLogger()  # gets the root logger instead of hardcoded logger name
    logger.setLevel(log_level)

    # Create file handler (writes to file)
    file_handler = logging.FileHandler(os.path.join(log_directory, log_file), mode='w')
    file_handler.setLevel(logging.DEBUG)  # Log everything to file

    # Create console handler (writes to console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Log INFO and above to the console.

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Root logging initialized.")  # logs confirmation of initialisation
