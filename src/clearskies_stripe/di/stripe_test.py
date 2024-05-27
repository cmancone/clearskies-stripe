import unittest
from unittest.mock import MagicMock
from .stripe import Stripe
import clearskies

class StripeTest(unittest.TestCase):
    def setUp(self):
        self.secrets = MagicMock()
        self.secrets.get = MagicMock(return_value='st_12345')
        self.stripe = Stripe(self.secrets)

    def testNoEnvironment(self):
        self.stripe.configure(
            "/path/to/private",
            "/path/to/public",
        )
        stripe = self.stripe.get_stripe()
        self.secrets.get.assert_called_with("/path/to/private")
        assert stripe._requestor.api_key == "st_12345"

        stripe2 = self.stripe.get_stripe()
        assert id(stripe) == id(stripe2)

    def testWithEnvironment(self):
        self.secrets.get = MagicMock()
        self.secrets.get.side_effect = ["st_12345", "ev_asdf"]
        self.stripe.configure(
            "/prod/private",
            "/prod/public",
            environments={
                "dev": {
                    "path_to_api_key": "/dev/private",
                    "path_to_publishable_key": "/dev/public",
                },
            },
        )

        stripe_default = self.stripe.get_stripe()
        assert id(self.stripe.get_stripe()) == id(stripe_default)
        stripe_dev = self.stripe.get_stripe(environment="dev")
        assert id(self.stripe.get_stripe(environment="dev")) == id(stripe_dev)

        assert self.secrets.get.call_count == 2
        calls = self.secrets.get.call_args_list
        assert calls[0].args == ("/prod/private",)
        assert calls[1].args == ("/dev/private",)

        assert stripe_default._requestor.api_key == "st_12345"
        assert stripe_dev._requestor.api_key == "ev_asdf"
