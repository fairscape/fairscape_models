"""
fairscape_models.schema — the EVI Schema family.

The import path `fairscape_models.schema` is preserved from the days this was a
single module: `Schema`, `Property`, and `ItemTypeEnum` re-export from here,
alongside the typed schema variants, the file-dispatch entry points, and the
legacy-document loader.

No heavy dependency (frictionless / h5py / wfdb / pydicom) is imported at module
load time — each is imported lazily inside the infer/validate method that needs
it, so `import fairscape_models.schema` stays light for the API server.
"""

from fairscape_models.schema.base import (
    AxisProperty,
    ItemTypeEnum,
    NonTabularSchema,
    Property,
    Schema,
    ValidationErrorRecord,
    compare_scalar,
    frictionless_error_to_record,
    generate_schema_guid,
)
from fairscape_models.schema.tabular import (
    SOURCE_TYPE_KEY,
    TabularSchema,
    build_frictionless_schema,
    frictionless_type_to_json_schema,
)
from fairscape_models.schema.hdf5 import DatasetProperty, HDF5Schema
from fairscape_models.schema.signal import ChannelProperty, SignalSchema
from fairscape_models.schema.image import ImageSchema
from fairscape_models.schema.ndarray import NDArraySchema
from fairscape_models.schema.registry import (
    EXTENSION_MAP,
    SCHEMA_TYPE_MODELS,
    infer_schema,
    load_schema,
    normalize_schema_document,
    parse_schema,
    schema_class_for_file,
    validate_schema,
)

__all__ = [
    # canonical models
    'Schema',
    'Property',
    'ItemTypeEnum',
    'NonTabularSchema',
    'AxisProperty',
    # typed variants
    'TabularSchema',
    'HDF5Schema',
    'DatasetProperty',
    'SignalSchema',
    'ChannelProperty',
    'ImageSchema',
    'NDArraySchema',
    # validation + helpers
    'ValidationErrorRecord',
    'frictionless_error_to_record',
    'compare_scalar',
    'generate_schema_guid',
    'SOURCE_TYPE_KEY',
    'frictionless_type_to_json_schema',
    'build_frictionless_schema',
    # dispatch + loading
    'SCHEMA_TYPE_MODELS',
    'EXTENSION_MAP',
    'schema_class_for_file',
    'parse_schema',
    'load_schema',
    'normalize_schema_document',
    'infer_schema',
    'validate_schema',
]
