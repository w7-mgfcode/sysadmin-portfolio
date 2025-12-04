"""
Network Health Checker - Package entry point.

Lehetővé teszi a csomag közvetlen futtatását:
    python -m network_health_checker [command]
"""

from .cli import main

if __name__ == "__main__":
    main()
