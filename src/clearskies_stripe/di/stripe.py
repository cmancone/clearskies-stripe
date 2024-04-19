from typing import List
from clearskies.secrets.secrets import Secrets
import stripe

class Stripe:
    """
    A wrapper around the stripe library to manage authentication.

    So, we have a lot to do here.  The key is that we want full control over Stripe authentication
    so we can both cache our API key and automatically re-load it when needed.  A normal call to
    the stripe library might look something like this:

    from stripe import StripeClient
    client = StripeClient("key_here")
    client.customers.list()

    So, the stripe class we're building here is meant to be a wrapper around stripe, so you could
    think of something like this:

    client = Stripe(StripeClient("key_here"))
    client.customers.list()

    The problem is that we need a wrapper around the `customers` object so that we can control
    the `list` call.  Our goal is to catch any authentication failures from the stripe library,
    so that we can then re-fetch our API key and retry the call.  We'll use two classes to make
    this happen.  We could really do this with just one class, but it's a bit easier to have
    two classes so the constructor of one can be determined by the needs of dependency injection
    and the constructor of the second can be designed to ease how we wrap around stripe.
    """
    def __init__(self, secrets: Secrets):
        self.secrets = secrets
        self._stripe = None

    def configure(self, path_to_api_key: str, path_to_publishable_key: str):
        self.path_to_api_key = path_to_api_key
        self.path_to_publishable_key = path_to_publishable_key

    def __getattr__(self, name: str):
        return StripeWrapper(self, [name])

    def get_stripe(self, cache=True):
        if self._stripe is not None and cache:
            return self._stripe

        self._stripe = stripe.StripeClient(self.secrets.get(self.path_to_api_key))
        self._stripe.set_app_info("clear-skies-stripe", url="https://github.com/cmancone/clearskies-stripe")
        return self._stripe

    def get_publishable_key(self) -> str:
        return self.secrets.get(self.path_to_publishable_key)

class StripeWrapper:
    def __init__(self, stripe_auth: Stripe, path: List[str]=[]):
        self.stripe_auth = stripe_auth
        self.path = path

    def __getattr__(self, name):
        return StripeWrapper(self.stripe_auth, [*self.path, name])

    def __call__(self, *args, **kwargs):
        cache = True
        if cache in kwargs:
            cache = kwargs[cache]
            del kwargs[cache]

        chain = self.stripe_auth.get_stripe(cache=cache)
        for name in self.path:
            chain = getattr(chain, name, None)
            if chain is None:
                raise ValueError("Requested non-existent function from stripe: stripe." + ".".join(self.name))

        try:
            response = chain(*args, **kwargs)
        except stripe.error.AuthenticationError as e:
            # try again without the cache (e.g. fetch a new api key)
            if cache:
                return self.__call__(*args, **kwargs, cache=False)
            else:
                # otherwise re-throw.  Don't keep trying forever.
                raise e

        return response
