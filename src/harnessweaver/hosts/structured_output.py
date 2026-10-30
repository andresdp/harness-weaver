"""Build Pydantic response models from the JSON Schemas in a generated bundle."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from harnessweaver.wiring import Wiring, WiringStage, load_wiring


def _safe_class_name(value: str) -> str:
    name = re.sub(r"\W+", "_", value).strip("_") or "Artifact"
    if name[0].isdigit():
        name = f"Artifact_{name}"
    return name


def _model_from_schema(schema: dict[str, Any], model_name: str) -> type[Any]:
    """Convert the JSON Schema subset emitted by HarnessWeaver into strict Pydantic models."""
    try:
        from pydantic import ConfigDict, Field, create_model
    except ImportError as exc:
        raise RuntimeError("Pydantic is required for structured DeepAgents outputs; install the 'deepagents' extra") from exc

    cache: dict[str, Any] = {}
    def ref_schema(ref: str) -> tuple[str, dict[str, Any]]:
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"unsupported non-local JSON Schema reference: {ref}")
        key = ref.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")
        target = schema.get("$defs", {}).get(key)
        if not isinstance(target, dict):
            raise ValueError(f"JSON Schema reference does not resolve: {ref}")
        return key, target

    def constraints(node: dict[str, Any]) -> dict[str, Any]:
        result = {key: node[key] for key in ("title", "description", "pattern") if key in node}
        for source, target in (("minLength", "min_length"), ("maxLength", "max_length"),
                               ("minItems", "min_length"), ("maxItems", "max_length"),
                               ("minimum", "ge"), ("maximum", "le"),
                               ("exclusiveMinimum", "gt"), ("exclusiveMaximum", "lt")):
            if source in node:
                result[target] = node[source]
        return result

    def make_object(node: dict[str, Any], name: str) -> type[Any]:
        properties = node.get("properties") or {}
        additional = node.get("additionalProperties", True)
        if not properties:
            if additional is False:
                return create_model(name, __config__=ConfigDict(extra="forbid"))
            if isinstance(additional, dict):
                return dict[str, schema_type(additional, f"{name}Value")]
            return dict[str, Any]

        required = set(node.get("required") or [])
        fields: dict[str, tuple[Any, Any]] = {}
        for index, (property_name, property_schema) in enumerate(properties.items(), start=1):
            field_name = f"field_{index}"
            field_type = schema_type(property_schema, f"{name}{_safe_class_name(property_name)}")
            default = ... if property_name in required else property_schema.get("default", None)
            field_info = Field(default, alias=property_name)
            fields[field_name] = (field_type, field_info)

        if additional is False:
            extra = "forbid"
        else:
            extra = "allow"
        config = ConfigDict(extra=extra, populate_by_name=True, title=node.get("title", name))
        return create_model(name, __config__=config, **fields)

    def schema_type(node: dict[str, Any], name: str) -> Any:
        if "$ref" in node:
            ref = node["$ref"]
            if ref in cache:
                return cache[ref]
            key, target = ref_schema(ref)
            result = schema_type(target, _safe_class_name(key))
            cache[ref] = result
            return result

        for composition in ("allOf",):
            if composition in node:
                raise ValueError(f"JSON Schema {composition} is not supported for structured outputs")
        alternatives = node.get("anyOf") or node.get("oneOf")
        if alternatives:
            choices = [schema_type(option, f"{name}Option{index}") for index, option in enumerate(alternatives)]
            if len(choices) == 1:
                result = choices[0]
            else:
                from typing import Union
                result = Union[tuple(choices)]
            return result

        declared_type = node.get("type")
        if isinstance(declared_type, list):
            choices = [schema_type({**node, "type": item}, f"{name}{_safe_class_name(str(item))}")
                       for item in declared_type]
            from typing import Union
            return Union[tuple(choices)]

        if "enum" in node:
            from typing import Literal
            result = Literal.__getitem__(tuple(node["enum"]))
        elif "const" in node:
            from typing import Literal
            result = Literal.__getitem__((node["const"],))
        elif declared_type == "object":
            result = make_object(node, name)
        elif declared_type == "array":
            result = list[schema_type(node.get("items") or {}, f"{name}Item")]
        elif declared_type == "string":
            result = str
        elif declared_type == "integer":
            result = int
        elif declared_type == "number":
            result = float
        elif declared_type == "boolean":
            result = bool
        elif declared_type == "null":
            result = type(None)
        else:
            result = Any

        field_constraints = constraints(node)
        if field_constraints:
            from typing import Annotated
            result = Annotated[result, Field(**field_constraints)]
        return result

    root_name = _safe_class_name(model_name)
    result_model = schema_type(schema, root_name)
    from typing import Annotated, get_args, get_origin
    if get_origin(result_model) is Annotated:
        result_model = get_args(result_model)[0]
    if not isinstance(result_model, type):
        raise ValueError(f"artifact schema root must describe an object; got {type(result_model).__name__}")
    return result_model


def stage_response_model(bundle: str | Path, stage_dir: str) -> tuple[type[Any], tuple[str, ...]]:
    """Return a Pydantic response model plus the artifact order it represents."""
    from pydantic import ConfigDict, Field, create_model

    wiring: Wiring = load_wiring(bundle)
    stage = next((item for item in wiring.stages if item.dir == stage_dir), None)
    if stage is None:
        raise ValueError(f"stage {stage_dir!r} is not declared by {wiring.root / 'wiring.yaml'}")

    artifact_models: list[type[Any]] = []
    for artifact in stage.artifacts:
        schema_ref = stage.schemas.get(artifact) or (
            wiring.output_schema if artifact == wiring.output_artifact else None
        )
        if schema_ref:
            schema_path = wiring.root / schema_ref
            artifact_models.append(
                _model_from_schema(json_load(schema_path), f"{_safe_class_name(artifact)}Output")
            )
        else:
            artifact_models.append(dict[str, Any])

    if len(artifact_models) == 1:
        return artifact_models[0], stage.artifacts

    fields = {
        f"artifact_{index}": (
            model,
            Field(..., description=f"Structured contents to persist to /artifacts/{artifact}"),
        )
        for index, (artifact, model) in enumerate(zip(stage.artifacts, artifact_models), start=1)
    }
    wrapper = create_model(
        f"{_safe_class_name(stage.dir)}Output",
        __config__=ConfigDict(extra="forbid"),
        **fields,
    )
    return wrapper, stage.artifacts


def json_load(path: Path) -> dict[str, Any]:
    import json

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact schema must be a JSON object: {path}")
    return value


def stage_artifact_writer_tools(bundle: str | Path, stage_dir: str, workspace: str | Path) -> list[Any]:
    """Create one Pydantic-validated writer tool per declared stage artifact."""
    from langchain_core.tools import StructuredTool
    from pydantic import BaseModel

    wiring: Wiring = load_wiring(bundle)
    stage = next((item for item in wiring.stages if item.dir == stage_dir), None)
    if stage is None:
        raise ValueError(f"stage {stage_dir!r} is not declared by {wiring.root / 'wiring.yaml'}")

    tools = []
    for artifact in stage.artifacts:
        schema_ref = stage.schemas.get(artifact) or (
            wiring.output_schema if artifact == wiring.output_artifact else None
        )
        if not schema_ref:
            raise ValueError(f"stage artifact {artifact!r} has no JSON Schema for validated writing")
        artifact_model = _model_from_schema(json_load(wiring.root / schema_ref), f"{_safe_class_name(artifact)}Writer")
        if not isinstance(artifact_model, type) or not issubclass(artifact_model, BaseModel):
            raise ValueError(f"stage artifact {artifact!r} must have an object schema for validated writing")

        def make_writer(filename: str, model: type[BaseModel]):
            def write_artifact(**fields: Any) -> str:
                payload = model.model_validate(fields).model_dump(mode="json", by_alias=True, exclude_unset=True)
                target = Path(workspace) / "artifacts" / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
                temporary.write_text(json_dumps(payload), encoding="utf-8")
                os.replace(temporary, target)
                return f"Pydantic validated and wrote /artifacts/{filename}."

            return write_artifact

        tool_slug = re.sub(r"[^a-z0-9_]+", "_", artifact.removesuffix(".json").lower()).strip("_")
        tool_name = f"write_{tool_slug}"
        tools.append(StructuredTool.from_function(
            func=make_writer(artifact, artifact_model),
            name=tool_name,
            description=(
                f"Write /artifacts/{artifact}. The tool accepts exactly the fields in that artifact's "
                "Pydantic schema, validates them, and persists the JSON only when validation succeeds. "
                "Call this tool again to revise the artifact."
            ),
            args_schema=artifact_model,
            handle_validation_error=True,
        ))
    return tools


def json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"
