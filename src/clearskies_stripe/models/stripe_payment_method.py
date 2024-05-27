import clearskies
from clearskies.column_types import boolean, json, string, timestamp
from collections import OrderedDict


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
                string("object"),
                json("billing_details"),
                json("card"),
                string("customer"),
                timestamp("created"),
                boolean("livemode"),
                json("metadata"),
                string("type"),
            ]
        )

    def charge_off_session(self, amount):
        """
        Make an off session charge against the payment method.

        The amount should be in USD.

        Note that this will not work for more advanced payment methods/forms that require customer interaction.
        """
        if not self.exists:
            raise ValueError("Cannot create a charge for a non-existent payment method")

        # grab the stripe object from our backend so I can be lazy and not inject another parameter
        return self.backend.stripe.payment_intents.create(params={
            "amount": amount*100,
            "currency": "usd",
            "confirm": True,
            "payment_method": self.id,
        })
