from .stripe_object import StripeObject
from clearskies.column_types import build_column_config

def stripe_object(name, **kwargs):
    return build_column_config(name, StripeObject, **kwargs)

__all__ = ["StripeObject", "stripe_object"]
