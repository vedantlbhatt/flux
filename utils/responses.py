"""Pretty-printed JSON response for readable API output.

Used as response_class on routes so /docs and curl get readable JSON.
"""
import json
from fastapi.responses import JSONResponse


class PrettyJSONResponse(JSONResponse):
    """JSON response with 2-space indent; UTF-8, no NaN."""

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            separators=(", ", ": "),
        ).encode("utf-8")
