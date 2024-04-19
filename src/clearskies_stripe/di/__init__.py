import clearskies
from .stripe import Stripe

def stripe(path_to_api_key: str, path_to_publishable_key: str) -> clearskies.BindingConfig:
    return clearskies.BindingConfig(Stripe, path_to_api_key, path_to_publishable_key)

__all__ = [
    "stripe",
    "Stripe",
]
