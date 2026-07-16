"""
conftest.py — makes `backend/` the import root so `from app.core.cache import ...`
works when pytest is run from the backend/ directory.
"""
import sys
import os

# Ensure the backend directory itself is on the path
sys.path.insert(0, os.path.dirname(__file__))
