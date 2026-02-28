"""Pretty-printed JSON response for readable API output."""
import json
from fastapi.responses import JSONResponse


class PrettyJSONResponse(JSONResponse):
    """JSON response with 2-space indent for readability."""

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            separators=(", ", ": "),
        ).encode("utf-8")
