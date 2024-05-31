import clearskies
from typing import Dict, Optional
from .stripe import Stripe

def stripe(path_to_api_key: str, path_to_publishable_key: str, environments: Dict[str, Dict[str, str]] = {}) -> clearskies.BindingConfig:
    return clearskies.BindingConfig(Stripe, path_to_api_key=path_to_api_key, path_to_publishable_key=path_to_publishable_key, environments=environments)

__all__ = [
    "stripe",
    "Stripe",
]
