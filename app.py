#!/usr/bin/env python
"""Alis Studio — local image-generation studio for Apple silicon.

    python3 -m pip install -r requirements.txt
    python3 app.py            # opens http://localhost:7860 in your browser
"""

from studio.server import serve

if __name__ == "__main__":
    serve()
