import tkinter as tk
import logging
from datetime import datetime

class TextHandler(logging.Handler):
    """
    A custom logging handler that appends messages to a Tkinter Text widget.
    Ensures thread-safe updates to the GUI widget.
    """
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        """Emits a log record."""
        msg = self.format(record)
        
        def append_to_widget():
            """Appends the formatted message to the text widget."""
            try:
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
            except tk.TclError as e:
                print(f"Tkinter error in TextHandler: {e}")

        self.text_widget.after(0, append_to_widget)

def setup_logging(text_widget):
    """
    Configures the root logger to use the custom TextHandler.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = TextHandler(text_widget)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)

def log_message(message, level="info"):
    """
    Helper function to log messages with a specified level.
    """
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    else:
        logging.info(message)
# --- END OF FILE logging_config.py ---```