import os
import sys
import logging

# Set up global logging before importing app
def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("rekvia")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    fh = logging.FileHandler(os.path.join(log_dir, 'rekvia.log'), encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

setup_logging()

from rekvia.gui.app import GSTApp

def main():
    logger = logging.getLogger("rekvia.main")
    logger.info("Starting Rekvia Application")
    app = GSTApp()
    app.mainloop()
    logger.info("Application closed")

if __name__ == "__main__":
    main()
