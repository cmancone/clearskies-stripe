from typing import Dict, List
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
        self._stripe_by_environment = {}

    def configure(self, path_to_api_key: str, path_to_publishable_key: str, environments: Dict[str, Dict[str, str]] = {}):
        self.path_to_api_key = path_to_api_key
        self.path_to_publishable_key = path_to_publishable_key
        if environments:
            key_suffix = 'Try something like: environments={"development": {"path_to_api_key": "", "path_to_publishable_key": ""}}'
            for (key, value) in environments.items():
                if not isinstance(key, str):
                    raise ValueError(f"All keys for the environment config in the stripe DI class must be strings, but a non-string  was found.  {key_suffix}")
                if not isinstance(value, dict):
                    raise ValueError(f"The environments dictionary should contain dictionaries, but a non-dictionary was found for key {key}. {error_suffix}'")
                if len(value) != 2:
                    raise ValueError(f"Each inner environment dictionary should contain two values: 'path_to_api_key' and 'path_to_publishable_key'.  However, the environment '{key}' contained the wrong number of keys. {error_suffix}'")
                if not value.get("path_to_api_key"):
                    raise ValueError(f"Each inner environment dictionary should define a key named 'path_to_api_key', but this config does not exist (or is a non-value) for key '{key}'. {error_suffix}'")
                if not value.get("path_to_publishable_key"):
                    raise ValueError(f"Each inner environment dictionary should define a key named 'path_to_publishable_key', but this config does not exist (or is a non-value) for key '{key}'. {error_suffix}'")
        self.environments = environments

    def __getattr__(self, name: str):
        return StripeWrapper(self, [name])

    def get_stripe(self, cache=True, environment=None):
        if cache:
            if not environment and self._stripe:
                return self._stripe
            if environment and self._stripe_by_environment.get(environment):
                return self._stripe_by_environment.get(environment)

        # this call has to go to the module itself
        stripe.set_app_info("clear-skies-stripe", url="https://github.com/cmancone/clearskies-stripe")
        # but the easiest way to have flexible credentials is to directly instantiate a StripeClient
        # rather than using the module directly
        [path_to_api_key, path_to_publishable_key] = self.paths_for_environment(environment)
        api_key = self.secrets.get(path_to_api_key)
        print(api_key)
        if not environment:
            self._stripe = stripe.StripeClient(api_key)
            return self._stripe

        self._stripe_by_environment[environment] = stripe.StripeClient(api_key)
        return self._stripe_by_environment[environment]

    def paths_for_environment(self, environment):
        if not environment:
            return [self.path_to_api_key, self.path_to_publishable_key]

        if environment not in self.environments:
            if not self.environments:
                raise ValueError(f"I received a request for a stripe environment, '{environment}', but no environments have been configured")
            allowed_environments = "'" + "', '".join(list(self.environments.keys())) + "'"
            raise ValueError(f"I received a request for a non-existent stripe environment: '{environment}'.  The configured environments are {allowed_environments}")

        return [self.environments[environment]["path_to_api_key"], self.environments[environment]["path_to_publishable_key"]]

    def get_publishable_key(self, environment=None) -> str:
        [path_to_api_key, path_to_publishable_key] = self.paths_for_environment(environment)
        return self.secrets.get(path_to_publishable_key)

class StripeWrapper:
    def __init__(self, stripe_auth: Stripe, path: List[str]=[]):
        self.stripe_auth = stripe_auth
        self.path = path

    def __getattr__(self, name):
        return StripeWrapper(self.stripe_auth, [*self.path, name])

    def __call__(self, *args, **kwargs):
        cache = True
        environment = None
        if cache in kwargs:
            cache = kwargs["cache"]
            del kwargs["cache"]
        if environment in kwargs:
            environment = kwargs["environment"]
            del kwargs["environment"]

        chain = self.stripe_auth.get_stripe(cache=cache, environment=environment)
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
