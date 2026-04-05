"""
Routes Package
Central route registration for all modules.

Usage:
    from src.routes import setup_remctl, setup_database
    
    app = FastAPI()
    setup_remctl(app)
    setup_database(app)
"""

from .remctl import setup_remctl
from .database import setup_database

__all__ = ["setup_remctl", "setup_database"]
