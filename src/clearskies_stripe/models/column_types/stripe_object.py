from clearskies.column_types import JSON


class StripeObject(JSON):
    def from_backend(self, value):
        return value
