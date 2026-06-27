#!/usr/bin/env python
"""Launch Alis Studio as a native desktop app.

    python3 -m pip install -r requirements.txt pywebview
    python3 desktop.py
"""

from studio.desktop import main

if __name__ == "__main__":
    main()
