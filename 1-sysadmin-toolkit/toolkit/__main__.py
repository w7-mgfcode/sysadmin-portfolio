"""
SysAdmin Toolkit - Package entry point.

Allows running the toolkit as a module:
    python -m toolkit

Lehetővé teszi a toolkit futtatását modulként:
    python -m toolkit
"""

from .cli import main

if __name__ == "__main__":
    main()
