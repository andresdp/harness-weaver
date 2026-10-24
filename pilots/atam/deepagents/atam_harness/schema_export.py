"""Export the ATAM report contract as JSON Schema for the pilot's authored sources."""

from __future__ import annotations

import json
from typing import Any

from .models import AtamReportDocument
from .paths import EXAMPLE_DIR

REPORT_SCHEMA_PATH = EXAMPLE_DIR.parent / "sources/domain/contracts/atam-report.schema.json"
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


def report_json_schema() -> dict[str, Any]:
    """Return the serialized report contract, keyed by the JSON field names reports use."""
    schema = AtamReportDocument.model_json_schema(by_alias=True)
    # Runtime-neutral consumers validate with a standard dialect, so name it explicitly.
    return {"$schema": SCHEMA_DIALECT, **schema}


def main() -> int:
    REPORT_SCHEMA_PATH.write_text(json.dumps(report_json_schema(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {REPORT_SCHEMA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
