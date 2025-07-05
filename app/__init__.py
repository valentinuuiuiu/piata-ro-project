

# Makes app a Python package
from .main import app
from .sql_agent import SQLAgent
from .inventory import InventorySystem

__all__ = ['app', 'SQLAgent', 'InventorySystem']

