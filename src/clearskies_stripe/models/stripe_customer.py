import clearskies
from clearskies.column_types import boolean, integer, string, timestamp
from .column_types import stripe_object
from collections import OrderedDict


class StripeCustomer(clearskies.Model):
    id_column_alt_name = "customer"

    def __init__(self, stripe_sdk_backend, columns):
        super().__init__(stripe_sdk_backend, columns)

    @classmethod
    def table_name(cls):
        return "customers"

    def columns_configuration(self):
        return OrderedDict(
            [
                string("id"),
                string("environment"),
                string("address"),
                string("currency"),
                timestamp("created"),
                string("default_source"),
                boolean("delinquent"),
                string("description"),
                string("discount"),
                string("email"),
                string("invoice_prefix"),
                stripe_object("invoice_settings"),
                boolean("livemode"),
                stripe_object("metadata"),
                string("name"),
                string("phone"),
                integer("next_invoice_sequence"),
                string("object"),
                stripe_object("preferred_locales"),
                string("shipping"),
                string("tax_exempt"),
                string("test_clock"),
            ]
        )
