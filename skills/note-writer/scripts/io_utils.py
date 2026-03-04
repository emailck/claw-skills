from __future__ import annotations

import sys


def print_utf8(text: str) -> None:
    """Print text as UTF-8 bytes to avoid Windows console mojibake.

    On Windows PowerShell 5.1, sys.stdout.encoding is often GBK. Printing
    UTF-8 bytes ensures the caller (or capture) can decode correctly.
    """

    data = (text + "\n").encode("utf-8", errors="replace")
    try:
        sys.stdout.buffer.write(data)
    except Exception:
        sys.stdout.write(text + "\n")
