"""Main entry point for VoiceDebate."""

import asyncio
from .ui.app import main

if __name__ == "__main__":
    asyncio.run(main())
