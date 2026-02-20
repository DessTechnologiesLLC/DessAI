import os
import logging
from datetime import datetime

class CustomLogger:
    def __init__(self, log_dir="logs"):
        """
        Initializes a CustomLogger with a specified log directory.

        Args:
            log_dir (str, optional): The directory to store logs. Defaults to "logs".

        Creates a logger with INFO level, a formatter, and two handlers: one for a file and one for the stream.
        The file handler stores logs in a file named after the current time in the format "MM_DD_YYYY_HH_MM_SS.log".
        The stream handler prints logs to the console.
        Both handlers use the same formatter.
        If the logger does not already have handlers, it adds the file and stream handlers.
        """
        self.logs_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.logs_dir, exist_ok=True)

        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        log_file_path = os.path.join(self.logs_dir, log_file)

        # Create a logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter("[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s")

        # File Handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)

        # Stream Handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

    def get_logger(self, name=__file__):
        """
        Returns a logger with the name of the given file.

        Args:
            name (str, optional): The name of the file to use as the logger name. Defaults to __file__.

        Returns:
            logging.Logger: A logger with the name of the given file.
        """
        return logging.getLogger(os.path.basename(name))

# Usage example
if __name__ == "__main__":
    logger = CustomLogger().get_logger(__file__)
    logger.info("Custom logger initialized - file + console logging enabled.")