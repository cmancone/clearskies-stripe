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
        kwargs = {where["column"]: where["values"][0] for where in configuration.get("wheres", [])}
        if configuration.get("limit"):
            kwargs["limit"] = configuration.get("limit")
        next_page = configuration.get('pagination', {}).get('next_page')
        if next_page:
            kwargs["page"] = next_page
        return getattr(self.stripe, model.table_name()).list(**kwargs)

    def validate_pagination_kwargs(self, kwargs: Dict[str, Any]) -> str:
        extra_keys = set(kwargs.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping('next_page')
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if 'next_page' not in kwargs:
            key_name = case_mapping('next_page')
            return f"You must specify '{key_name}' when setting pagination"
        return ''

    def allowed_pagination_keys(self) -> List[str]:
        return ["next_page"]

    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> List[Any]:
        return [AutoDocString(case_mapping('next_page'))]

    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> Dict[str, Any]:
        return {case_mapping('next_page'): 'eyJpZCI6IHsiUyI6ICIzODM0MyJ9fQ=='}

    def documentation_pagination_parameters(self, case_mapping: Callable) -> List[Tuple[Any]]:
        return [(
            AutoDocString(case_mapping('next_page'),
                          example='eyJpZCI6IHsiUyI6ICIzODM0MyJ9fQ=='), 'A token to fetch the next page of results'
        )]
