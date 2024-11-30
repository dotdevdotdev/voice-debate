"""Main entry point for VoiceDebate."""

import asyncio
import logging
from kivy.config import Config

# Configure Kivy before other imports
Config.set("kivy", "exit_on_escape", "0")  # Disable escape key exit
Config.set("graphics", "multisamples", "0")  # Fix potential OpenGL issues

from .ui.app import VoiceDebateApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run the application."""
    try:
        # Set up asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create and run the app
        app = VoiceDebateApp()

        # Run the app with asyncio support
        async def run_app():
            await app.async_run(async_lib="asyncio")

        loop.run_until_complete(run_app())

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()
