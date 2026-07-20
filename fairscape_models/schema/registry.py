"""
registry.py — schema-type dispatch: file extension -> class, and schema document
-> the right typed model.

Dispatch is a plain dict lookup keyed on the `EVI:schemaType` discriminator, not
a pydantic discriminated union — a legacy document has no discriminator, and an
alias-keyed union over `extra='allow'` models is fragile. `parse_schema` decides:

    1. known `EVI:schemaType` tag           -> that class
    2. no tag + legacy HDF5 dataset shape    -> HDF5Schema (normalized)
    3. otherwise                             -> TabularSchema (the legacy default)

An unknown tag falls back to the base `Schema` rather than erroring.
"""

import json
import pathlib
import re
from typing import Dict, List, Optional, Type, Union

from fairscape_models.schema.base import Schema, ValidationErrorRecord
from fairscape_models.schema.tabular import (
    CANONICAL_TYPES,
    SOURCE_TYPE_KEY,
    TabularSchema,
    frictionless_type_to_json_schema,
)
from fairscape_models.schema.hdf5 import HDF5Schema
from fairscape_models.schema.signal import SignalSchema
from fairscape_models.schema.image import ImageSchema
from fairscape_models.schema.ndarray import NDArraySchema

SCHEMA_TYPE_MODELS: Dict[str, Type[Schema]] = {
    "tabular": TabularSchema,
    "hdf5": HDF5Schema,
    "signal": SignalSchema,
    "image": ImageSchema,
    "ndarray": NDArraySchema,
}

EXTENSION_MAP: Dict[str, Type[Schema]] = {
    "csv": TabularSchema,
    "tsv": TabularSchema,
    "parquet": TabularSchema,
    "h5": HDF5Schema,
    "hdf5": HDF5Schema,
    "hea": SignalSchema,
    "dcm": ImageSchema,
}


def schema_class_for_file(filepath: str) -> Type[Schema]:
    ext = pathlib.Path(filepath).suffix.lower().lstrip('.')
    try:
        return EXTENSION_MAP[ext]
    except KeyError:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Supported extensions: {', '.join(sorted(EXTENSION_MAP))}"
        )


def infer_schema(filepath: str, name: str, description: str,
                 guid: Optional[str] = None) -> Schema:
    """Infer a typed schema from a data file, dispatching by extension."""
    return schema_class_for_file(filepath).infer(filepath, name, description, guid=guid)


def validate_schema(schema: Schema, filepath: str) -> List[ValidationErrorRecord]:
    """Validate a data file against a schema, dispatching on the schema's type."""
    return schema.validate(filepath)


# --------------------------------------------------------------------------- #
# Legacy normalization (tabular + legacy-HDF5 documents without a discriminator)
# --------------------------------------------------------------------------- #

_INDEX_PATTERN = re.compile(r'^\d+$|^-?\d+::|^-?\d+::-?\d+$|^::-?\d+')


def _valid_index(value) -> bool:
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return bool(_INDEX_PATTERN.match(value))
    return False


def _is_legacy_hdf5(data: dict) -> bool:
    """
    A pre-discriminator HDF5 schema is a dict of per-dataset entries, each a full
    sub-schema (nested 'properties' but no valid scalar 'index'), or carrying an
    'hdf5-path'.
    """
    for prop in (data.get('properties') or {}).values():
        if not isinstance(prop, dict):
            continue
        if 'hdf5-path' in prop:
            return True
        if isinstance(prop.get('properties'), dict) and not _valid_index(prop.get('index')):
            return True
    return False


def _normalize_column(name: str, prop: dict, index_fallback: int) -> dict:
    """Normalize a leaf/column property to canonical Property shape (legacy types)."""
    normalized = dict(prop)
    prop_type = normalized.get('type')
    if prop_type is None:
        normalized['type'] = 'string'
    elif prop_type not in CANONICAL_TYPES:
        normalized.setdefault(SOURCE_TYPE_KEY, prop_type)
        normalized['type'] = frictionless_type_to_json_schema(prop_type)
    if not _valid_index(normalized.get('index')):
        normalized['index'] = index_fallback
    if not normalized.get('description'):
        normalized['description'] = f"Column {name}"
    return normalized


def _normalize_hdf5_dataset(name: str, prop: dict, index_fallback: int) -> dict:
    """Rebuild a legacy per-dataset entry as a DatasetProperty-shaped dict."""
    nested = prop.get('properties')
    out = {
        'type': 'object' if isinstance(nested, dict) else 'array',
        'index': index_fallback,
        'description': prop.get('description') or f"Dataset at {name}",
        'hdf5-path': prop.get('hdf5-path', name),
    }
    if isinstance(nested, dict):
        out['properties'] = {
            child: _normalize_column(child, child_prop if isinstance(child_prop, dict) else {}, i)
            for i, (child, child_prop) in enumerate(nested.items())
        }
    return out


def normalize_schema_document(data: dict) -> dict:
    """Normalize a legacy tabular schema document so it validates canonically."""
    data = dict(data)
    data.setdefault('@type', 'evi:Schema')
    data.setdefault('separator', ',')
    data.setdefault('header', True)
    data['properties'] = {
        name: _normalize_column(name, prop, i) if isinstance(prop, dict) else prop
        for i, (name, prop) in enumerate((data.get('properties') or {}).items())
    }
    return data


def _normalize_legacy_hdf5_document(data: dict) -> dict:
    data = dict(data)
    data['properties'] = {
        name: _normalize_hdf5_dataset(name, prop, i) if isinstance(prop, dict) else prop
        for i, (name, prop) in enumerate((data.get('properties') or {}).items())
    }
    return data


def parse_schema(data: dict) -> Schema:
    """Parse a schema JSON document into the correct typed model."""
    tag = data.get("EVI:schemaType")
    if tag in SCHEMA_TYPE_MODELS:
        return SCHEMA_TYPE_MODELS[tag].model_validate(data)
    if tag is not None:
        # Unknown discriminator — keep it as an opaque base Schema, never error.
        return Schema.model_validate(data)
    if _is_legacy_hdf5(data):
        return HDF5Schema.model_validate(_normalize_legacy_hdf5_document(data))
    return TabularSchema.model_validate(normalize_schema_document(data))


def load_schema(path: Union[str, pathlib.Path]) -> Schema:
    """Read a schema JSON file into the correct typed model."""
    with open(path) as f:
        data = json.load(f)
    return parse_schema(data)
