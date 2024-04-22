import unittest
from unittest.mock import MagicMock
from .create_setup_intent import CreateSetupIntent
from clearskies.authentication import Public
from clearskies.di import StandardDependencies
import clearskies

class CreateSetupIntentTest(unittest.TestCase):
    def setUp(self):
        self.stripe = MagicMock()
        self.stripe.setup_intents = MagicMock()
        self.stripe.setup_intents.create = MagicMock(return_value={"client_secret":"super secret","id":"seti_asdf"})
        self.stripe.get_publishable_key = MagicMock(return_value="pk_asdfer")

    def test_simple(self):
        create_setup_intent = clearskies.contexts.test(
            {
                "handler_class": CreateSetupIntent,
                "handler_config": {
                    "confirm": True,
                    "payment_method_options": {"hey":"sup"},
                },
            },
            bindings={
                "stripe": self.stripe
            },
        )
        response = create_setup_intent()
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual({"client_secret":"super secret", "id": "seti_asdf", "publishable_key": "pk_asdfer"}, response_data)
        self.stripe.setup_intents.create.assert_called_with({"confirm": True, "payment_method_options":{"hey": "sup"}})

    def paramaters_callable(self, input_output):
        return {
            "customer":  "cust_asdfer",
            "route": input_output.get_full_path(),
            "confirm": False,
        }

    def test_with_params_callable(self):
        create_setup_intent = clearskies.contexts.test(
            {
                "handler_class": CreateSetupIntent,
                "handler_config": {
                    "confirm": True,
                    "payment_method_options": {"hey":"sup"},
                    "parameters_callable": self.paramaters_callable,
                },
            },
            bindings={
                "stripe": self.stripe
            },
        )
        response = create_setup_intent(url="/path/to/my/route")
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual({"client_secret":"super secret", "id": "seti_asdf", "publishable_key": "pk_asdfer"}, response_data)
        self.stripe.setup_intents.create.assert_called_with({"confirm":False, "payment_method_options":{"hey": "sup"}, "customer":"cust_asdfer", "route": "/path/to/my/route"})

    def output_map(self, response, input_output):
        return {
            **response,
            "route": input_output.get_full_path(),
            "hello": "world",
        }

    def test_with_output_map(self):
        create_setup_intent = clearskies.contexts.test(
            {
                "handler_class": CreateSetupIntent,
                "handler_config": {
                    "confirm": True,
                    "payment_method_options": {"hey":"sup"},
                    "output_callable": self.output_map,
                },
            },
            bindings={
                "stripe": self.stripe
            },
        )
        response = create_setup_intent(url="/path/to/my/route")
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual({"client_secret":"super secret", "id": "seti_asdf", "publishable_key": "pk_asdfer", "route": "/path/to/my/route", "hello": "world"}, response_data)
        self.stripe.setup_intents.create.assert_called_with({"confirm":True, "payment_method_options":{"hey": "sup"}})
