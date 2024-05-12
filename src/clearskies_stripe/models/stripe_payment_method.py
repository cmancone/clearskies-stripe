import clearskies
from clearskies.column_types import json, string
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
            ]
        )
