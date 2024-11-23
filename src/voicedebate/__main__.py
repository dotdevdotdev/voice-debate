"""Main entry point for VoiceDebate."""

import logging
from .ui.app import run

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    run()
