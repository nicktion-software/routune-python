from __future__ import annotations

from typing import Any

import pydantic


class BaseModel(pydantic.BaseModel):
    """Base for response objects. Fields the library does not know yet are kept, not dropped."""

    model_config = pydantic.ConfigDict(extra="allow", populate_by_name=True, protected_namespaces=())

    def to_dict(self) -> dict[str, Any]:
        """The object as plain JSON-compatible data (what the API sent)."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)
