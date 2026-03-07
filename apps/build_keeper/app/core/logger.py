import logging
import sys
import os


class ColorFormatter(logging.Formatter):
    """Logging Formatter to add colors to terminal output"""

    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(
            record.levelno, self.grey + self.format_str + self.reset
        )
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Logs to stdout with colors natively and optionally to a file if LOG_FILE env is set.
    """
    logger = logging.getLogger(name)

    # Evita adicionar múltiplos handlers caso o logger já tenha sido instanciado
    if not logger.handlers:
        logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        logger.propagate = False

        # Console Handler (stdout)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(ColorFormatter())
        logger.addHandler(ch)

        # File Handler (optional file structure)
        log_file = os.environ.get("LOG_FILE", "")
        if log_file:
            fh = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger
