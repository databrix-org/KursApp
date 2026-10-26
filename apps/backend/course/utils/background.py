# utils/background.py
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=4)   # pick your pool size

def run_in_background(fn, *args, **kwargs):
    """
    Submit *fn* to the shared thread-pool and forget.
    Use only for short-lived, IO-bound tasks – not CPU hogs.
    """
    _executor.submit(fn, *args, **kwargs)
