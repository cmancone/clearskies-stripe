import stripe
import clearskies
from clearskies.column_types import boolean, string, timestamp
from .column_types import stripe_object
from collections import OrderedDict
from ..exceptions import PaymentFailure

class StripePaymentMethod(clearskies.Model):
    id_column_alt_name = "payment_method"

    def __init__(self, stripe_sdk_backend, columns):
        super().__init__(stripe_sdk_backend, columns)

    @classmethod
    def table_name(cls):
        return "payment_methods"

    def columns_configuration(self):
        return OrderedDict(
            [
                string("id"),
                string("environment"),
                string("object"),
                stripe_object("billing_details"),
                stripe_object("card"),
                string("customer"),
                timestamp("created"),
                boolean("livemode"),
                stripe_object("metadata"),
                string("type"),
            ]
        )

    def charge_off_session(self, amount, environment=None):
        """
        Make an off session charge against the payment method.

        The amount should be in USD.

        Note that this will not work for more advanced payment methods/forms that require customer interaction.
        """
        if not self.exists:
            raise ValueError("Cannot create a charge for a non-existent payment method")

        # grab the stripe object from our backend so I can be lazy and not inject another parameter
        try:
            return self._backend.stripe.payment_intents.create(
                environment=environment,
                params={
                    "customer": self.customer,
                    "amount": int(round(amount*100, 0)),
                    "currency": "usd",
                    "confirm": True,
                    "payment_method": self.id,
                    "automatic_payment_methods": {
                        "enabled": True,
                        "allow_redirects": "never",
                    },
                }
            )
        except stripe._error.StripeError as e:
            raise PaymentFailure(str(e))
