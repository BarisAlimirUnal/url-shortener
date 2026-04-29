# app/logger.py
import logging
import json
import os

class JSONFormatter(logging.Formatter):
    """
    Formats every log line as a JSON object.
    This makes logs searchable and parseable in
    Railway's log dashboard and any monitoring tool.
    """
    def format(self, record):
        log_entry = {
            'level': record.levelname,
            'message': record.getMessage(),
            'time': self.formatTime(record),
            'environment': os.getenv('ENVIRONMENT', 'dev'),
            'logger': record.name
        }
        # Include exception details if there is one
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # StreamHandler sends logs to stdout
    # Railway captures stdout automatically and shows it in the logs dashboard
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        logger.addHandler(handler)

    return logger