import asyncio
import sys

from .run import main

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
