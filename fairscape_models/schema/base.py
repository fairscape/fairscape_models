"""
base.py — the canonical Schema/Property models and the shared pieces of the
schema-type family.

The class hierarchy:

    Property ── AxisProperty            (labeled axis: image / ndarray / hdf5)
    Schema ──── TabularSchema           (csv / tsv / parquet, tabular.py)
           └─── NonTabularSchema ────── SignalSchema   (signal.py)
                                  ├──── ImageSchema    (image.py)
                                  ├──── NDArraySchema  (ndarray.py)
                                  └──── HDF5Schema     (hdf5.py)

Every concrete schema type overrides `infer` (build a schema from a data file)
and `validate` (check a data file against this schema). Heavy per-format
dependencies (frictionless, h5py, wfdb, pydicom) are imported lazily inside
those methods so importing fairscape_models stays light.
"""

import math
import re
import uuid
from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from fairscape_models.fairscape_base import (
    DEFAULT_ARK_NAAN,
    Identifier,
    IdentifierValue,
)
from fairscape_models._version import __version__


class ItemTypeEnum(Enum):
    integer = 'integer'
    number = 'number'
    string = 'string'
    array = 'array'
    boolean = 'boolean'
    object = 'object'


class Property(BaseModel):
    description: str = Field(...)
    index: Union[str, int] = Field(...)
    type: str = Field(...)
    value_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('valueURL', 'value-url', 'value_url'),
        serialization_alias='valueURL',
    )
    pattern: Optional[str] = Field(default=None)
    min_items: Optional[int] = Field(default=None, alias='min-items')
    max_items: Optional[int] = Field(default=None, alias='max-items')
    unique_items: Optional[bool] = Field(default=None, alias='unique-items')
    properties: Optional[Dict[str, 'Property']] = Field(default=None)

    model_config = ConfigDict(extra='allow', populate_by_name=True)

    @field_validator('index', mode='before')
    def validate_index(cls, value):
        if isinstance(value, str):
            # Allow something like int::int for index. Raise error if else
            pattern = r'^\d+$|^-?\d+::|^-?\d+::-?\d+$|^::-?\d+'
            if not re.match(pattern, value):
                raise ValueError("Index must match the pattern 'int::int'")
        return value

    @field_validator('pattern', mode='before')
    def validate_pattern(cls, value):
        if value is not None:
            try:
                re.compile(value)
            except re.error:
                raise ValueError("Pattern must be a valid regular expression")
        return value

    @field_validator('type', mode='before')
    def validate_property_type(cls, value):
        valid_types = {'integer', 'number', 'string', 'array', 'boolean', 'object'}
        if value is not None:
            if value not in valid_types:
                raise ValueError(f"Type must be one of {valid_types}")
        return value


class AxisProperty(Property):
    """
    One axis of an `image`, `ndarray`, or `hdf5` schema — the OME-NGFF / CF
    "labeled axis" primitive: a named, typed axis with a size, a unit, and a
    physical scale.

    An axis index is discrete so `type` is "integer". `axisType` follows OME-NGFF
    (space | time | channel); `standardName` follows CF (a Standard Name Table
    term) for the generic-N-D case.
    """
    axisType: Optional[Literal["space", "time", "channel"]] = Field(
        default=None, description="OME-NGFF axis type"
    )
    size: Optional[int] = Field(default=None, description="Number of elements along this axis")
    spacing: Optional[float] = Field(
        default=None, description="Physical spacing per element (voxel/pixel size, or time step)"
    )
    unit: Optional[str] = Field(
        default=None,
        description="Axis unit. UCUM for DICOM/NIfTI; UDUNITS-2 for OME-NGFF/CF (e.g. 'micrometer', 'degrees_north')",
    )
    unitURL: Optional[str] = Field(default=None, description="Resolvable unit URI (QUDT), where a verified term exists")
    standardName: Optional[str] = Field(
        default=None, description="CF Standard Name for this coordinate (ndarray/netCDF), e.g. 'latitude'"
    )


class ValidationErrorRecord(BaseModel):
    message: str
    failed_keyword: str = "error"
    error_type: str = "ValidationError"
    field: Optional[str] = None
    row: Optional[int] = None
    path: Optional[str] = None

    @property
    def location(self) -> str:
        parts = [
            part for part in (
                self.path,
                f"row {self.row}" if self.row is not None else None,
                self.field,
            ) if part
        ]
        return " / ".join(parts) or "-"


def frictionless_error_to_record(error, path: Optional[str] = None) -> ValidationErrorRecord:
    """Convert a frictionless error object to a ValidationErrorRecord.

    Frictionless 5.x exposes row/field attributes under both snake_case and
    camelCase depending on error class and minor version, so check both.
    """
    row = getattr(error, 'row_number', None)
    if row is None:
        row = getattr(error, 'rowNumber', None)
    field = getattr(error, 'field_name', None)
    if field is None:
        field = getattr(error, 'fieldName', None)
    return ValidationErrorRecord(
        message=error.message,
        row=row,
        field=field,
        failed_keyword=getattr(error, 'type', 'error') or 'error',
        path=path,
    )


def generate_schema_guid(name: str, naan: str = DEFAULT_ARK_NAAN) -> str:
    """Generate a unique identifier for a schema."""
    slug = re.sub(r'[^a-zA-Z0-9_-]+', '-', name.lower()).strip('-')
    return f"ark:{naan}/schema-{slug}-{uuid.uuid4().hex[:10]}"


_REL_TOL = 1e-6


def compare_scalar(errors: List[ValidationErrorRecord], declared, observed,
                   path: Optional[str], field: str) -> None:
    """
    Append a `const`/`type` mismatch when a declared (non-None) value disagrees
    with what was observed in the file. A None `declared` means "unconstrained".
    Shared by the non-tabular validate() implementations.
    """
    if declared is None:
        return
    if isinstance(declared, float) and isinstance(observed, (int, float)) and not isinstance(observed, bool):
        if not math.isclose(declared, observed, rel_tol=_REL_TOL):
            errors.append(ValidationErrorRecord(
                message=f"{field}: expected {declared}, file has {observed}",
                failed_keyword="const", field=field, path=path,
            ))
    elif declared != observed:
        errors.append(ValidationErrorRecord(
            message=f"{field}: expected {declared!r}, file has {observed!r}",
            failed_keyword="const", field=field, path=path,
        ))


class Schema(Identifier):
    context: Dict[str, str] = Field(
        default={"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"},
        alias="@context"
    )
    metadataType: str = Field(alias="@type", default="evi:Schema")
    conformsTo: Optional[Union[List[IdentifierValue], IdentifierValue]] = Field(default={"@id": "https://json-schema.org/draft/2020-12/schema"})
    properties: Dict[str, Property]
    schemaType: Optional[str] = Field(default="object", alias="type")
    additionalProperties: Optional[bool] = Field(default=True)
    required: Optional[List[str]] = []
    separator: Optional[str] = Field(default=",")
    header: Optional[bool] = Field(default=True)
    examples: Optional[List[Dict]] = []
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    fairscapeVersion: str = __version__

    model_config = ConfigDict(extra='allow', populate_by_name=True)

    @classmethod
    def infer(cls, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> "Schema":
        """Build a schema of this type by inspecting a data file."""
        raise NotImplementedError(f"{cls.__name__} does not support inference")

    def validate(self, filepath: str, deep: bool = False) -> List[ValidationErrorRecord]:
        """
        Validate a data file against this schema.

        `deep` opts in to checks that read the whole payload rather than just
        its structural metadata. Only `SignalSchema` implements a deep tier so
        far; the other types accept the flag and ignore it.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support file validation")


class NonTabularSchema(Schema):
    """
    Shared base for the non-tabular schema types. Subclasses `Schema` so it
    keeps `conformsTo`, `required`, `examples`, `isPartOf`, and
    `fairscapeVersion` for free, and keeps `@type == "EVI:Schema"`.

    Differences from the tabular default:
      * `@context` and `@type` default to the upper-case `EVI` casing (both
        casings resolve to the same IRI).
      * The tabular-only fields `separator`, `header`, `type` (schemaType), and
        `additionalProperties` default to None so they drop out under
        `exclude_none=True` — they are meaningless for signal/image/ndarray/hdf5.
      * Adds the `EVI:schemaType` discriminator (concrete Literal per subclass).
    """
    context: Dict[str, str] = Field(
        default={"@vocab": "https://schema.org/", "EVI": "https://w3id.org/EVI#"},
        alias="@context",
    )
    metadataType: str = Field(default="EVI:Schema", alias="@type")
    evi_schema_type: str = Field(alias="EVI:schemaType")

    # Neutralize the tabular-only defaults inherited from Schema.
    schemaType: Optional[str] = Field(default=None, alias="type")
    additionalProperties: Optional[bool] = Field(default=None)
    separator: Optional[str] = Field(default=None)
    header: Optional[bool] = Field(default=None)

    unitSystem: Optional[str] = Field(
        default=None, description="Unit system IRI for UCUM codes, e.g. 'http://unitsofmeasure.org'"
    )
