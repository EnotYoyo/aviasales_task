import importlib
import pkgutil
from pathlib import Path


def import_all_agents():
    current_dir = Path(__file__).parent
    for mi in pkgutil.iter_modules([current_dir]):
        importlib.import_module(f".{mi.name}", __package__)

