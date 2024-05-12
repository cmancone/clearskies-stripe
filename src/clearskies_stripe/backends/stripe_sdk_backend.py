from typing import Any, Callable, Dict, List, Tuple
from clearskies.backends.backend import Backend
import clearskies

class StripeSdkBackend(Backend):
    _allowed_configs = [
        "table_name",
        "wheres",
        "limit",
        "pagination",
        "model_columns",
    ]

    _required_configs = [
        "table_name",
    ]


    def __init__(self, stripe):
        self.stripe = stripe

    def update(self, id: str, data: Dict[str, Any], model: clearskies.Model) -> Dict[str, Any]:
        return getattr(self.stripe, model.table_name()).update(model.get(model.id_column_alt_name), data)

    def create(self, data: Dict[str, Any], model: clearskies.Model) -> Dict[str, Any]:
        return getattr(self.stripe, model.table_name()).create(data)

    def delete(self, id: str, model: clearskies.Model) -> bool:
        return getattr(self.stripe, model.table_name()).delete(model.get(model.id_column_alt_name))

    def count(self, configuration: Dict[str, Any], model: clearskies.Model) -> int:
        raise ValueError("Not Supported")

    def records(
        self, configuration: Dict[str, Any], model: clearskies.Model, next_page_data: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        params = {where["column"]: where["values"][0] for where in configuration.get("wheres", [])}
        options = {}
        if configuration.get("limit"):
            params["limit"] = configuration.get("limit")
        starting_after = configuration.get('pagination', {}).get('starting_after')
        if starting_after:
            params["starting_after"] = starting_after

        results = getattr(self.stripe, model.table_name()).list(params=params, options=options)

        if results.get("has_more"):
            next_page_data["starting_after"] = results["data"][-1]["id"]

        return results["data"]

    def validate_pagination_kwargs(self, kwargs: Dict[str, Any], case_mapping: Callable) -> str:
        extra_keys = set(kwargs.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping('starting_after')
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if 'starting_after' not in kwargs:
            key_name = case_mapping('starting_after')
            return f"You must specify '{key_name}' when setting pagination"
        return ''

    def allowed_pagination_keys(self) -> List[str]:
        return ["starting_after"]

    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> List[Any]:
        return [AutoDocString(case_mapping('starting_after'))]

    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> Dict[str, Any]:
        return {case_mapping('starting_after'): 'cus_asdfer'}

    def documentation_pagination_parameters(self, case_mapping: Callable) -> List[Tuple[Any]]:
        return [(
            AutoDocString(case_mapping('starting_after'),
                          example='cus_asdfer'), 'A token to fetch the next page of results'
        )]
