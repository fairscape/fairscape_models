"""
tabular.py — the `tabular` schema type: csv / tsv / parquet.

Inference and row-level validation both run through frictionless for all three
formats (frictionless's parquet parser reads via pyarrow + pandas). Field types
are stored canonically (the six JSON-Schema types); when frictionless infers a
richer type (datetime, year, ...) the original is kept under 'source-type' so
validation can rebuild the native frictionless field.
"""

import pathlib
from typing import Dict, List, Literal, Optional

from pydantic import Field

from fairscape_models.schema.base import (
    Property,
    Schema,
    ValidationErrorRecord,
    frictionless_error_to_record,
    generate_schema_guid,
)

CANONICAL_TYPES = {'integer', 'number', 'string', 'array', 'boolean', 'object'}
SOURCE_TYPE_KEY = 'source-type'

_CSV_EXTENSIONS = {'csv', 'tsv'}


def frictionless_type_to_json_schema(field_type: str) -> str:
    """Convert Frictionless types to JSON Schema types"""
    type_mapping = {
        'string': 'string',
        'integer': 'integer',
        'number': 'number',
        'boolean': 'boolean',
        'date': 'string',
        'datetime': 'string',
        'year': 'integer',
        'yearmonth': 'string',
        'duration': 'string',
        'geopoint': 'array',
        'geojson': 'object',
        'array': 'array',
        'object': 'object',
        'time': 'string'
    }
    return type_mapping.get(field_type, 'string')


def _get_either(prop_details: dict, *keys):
    for key in keys:
        if prop_details.get(key) is not None:
            return prop_details[key]
    return None


def build_frictionless_schema(properties: Dict[str, Property]):
    """Rebuild a frictionless Schema from canonical Properties for row validation."""
    from frictionless import Schema as FrictionlessSchema, fields

    type_to_field = {
        'string': fields.StringField,
        'integer': fields.IntegerField,
        'number': fields.NumberField,
        'boolean': fields.BooleanField,
    }
    # A 'source-type' stamped at infer time wins over the canonical type, so
    # e.g. a datetime column validates as datetime cells (parquet yields real
    # datetime objects, which would fail a plain StringField).
    source_type_to_field = {
        'date': fields.DateField,
        'datetime': fields.DatetimeField,
        'time': fields.TimeField,
        'year': fields.YearField,
        'yearmonth': fields.YearmonthField,
        'duration': fields.DurationField,
    }

    properties_input = {
        name: prop.model_dump(by_alias=True, exclude_none=True)
        for name, prop in properties.items()
    }

    frictionless_schema_obj = FrictionlessSchema()

    sorted_prop_items = []
    spanning_array_prop_name = None
    spanning_array_prop_details = None

    for name, prop_details in properties_input.items():
        index_val = prop_details.get("index")
        if prop_details.get("type") == "array" and isinstance(index_val, str) and "::" in index_val:
            if spanning_array_prop_name is not None:
                raise ValueError("Multiple spanning array properties (index: 'X::') are not supported.")
            spanning_array_prop_name = name
            spanning_array_prop_details = prop_details
        elif isinstance(index_val, int):
            sorted_prop_items.append((name, prop_details, index_val))
        else:
            sorted_prop_items.append((name, prop_details, float('inf')))

    sorted_prop_items.sort(key=lambda x: x[2])

    for name, prop_details, _ in sorted_prop_items:
        field_class = source_type_to_field.get(prop_details.get(SOURCE_TYPE_KEY))
        if field_class is None:
            field_class = type_to_field.get(prop_details.get('type', 'string'), fields.StringField)

        constraints = {}
        if 'minimum' in prop_details: constraints['minimum'] = prop_details['minimum']
        if 'maximum' in prop_details: constraints['maximum'] = prop_details['maximum']
        if 'pattern' in prop_details: constraints['pattern'] = prop_details['pattern']
        if 'minLength' in prop_details: constraints['minLength'] = prop_details['minLength']
        if 'maxLength' in prop_details: constraints['maxLength'] = prop_details['maxLength']

        if prop_details.get('type') == 'array':
            field = fields.ArrayField(name=name, description=prop_details.get('description', ''), constraints=constraints)
        else:
            field = field_class(name=name, description=prop_details.get('description', ''), constraints=constraints)
        frictionless_schema_obj.add_field(field)

    if spanning_array_prop_name and spanning_array_prop_details:
        prop_name_original = spanning_array_prop_name
        details = spanning_array_prop_details
        item_details = details.get('items', {})
        item_type = item_details.get('type', 'number')
        item_field_class = type_to_field.get(item_type, fields.NumberField)

        # min/max item counts appear as 'min-items'/'max-items' (canonical alias)
        # or 'minItems'/'maxItems' (CLI property models) depending on origin
        num_items = _get_either(details, 'min-items', 'minItems')
        max_items = _get_either(details, 'max-items', 'maxItems')
        if num_items is None or num_items != max_items:
            raise ValueError(f"Spanning array '{prop_name_original}' must have equal and defined minItems and maxItems.")

        for i in range(num_items):
            field_name_for_frictionless = f"{prop_name_original}_{i}"  # e.g., embed_0, embed_1, ...
            field = item_field_class(name=field_name_for_frictionless, description=f"Element {i} of {prop_name_original}")
            frictionless_schema_obj.add_field(field)

    return frictionless_schema_obj


class TabularSchema(Schema):
    """`tabular` — csv / tsv / parquet. `properties` are columns."""

    # Match the rest of the EVI:Schema family (and the CLI's historical output).
    metadataType: str = Field(default="EVI:Schema", alias="@type")
    evi_schema_type: Literal["tabular"] = Field(default="tabular", alias="EVI:schemaType")

    @classmethod
    def infer(cls, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> "TabularSchema":
        from frictionless import describe

        ext = pathlib.Path(filepath).suffix.lower().lstrip('.')

        resource = describe(filepath)

        properties = {}
        required_fields = []

        for i, field in enumerate(resource.schema.fields):
            json_schema_type = frictionless_type_to_json_schema(field.type)
            extra = {}
            if json_schema_type != field.type:
                extra[SOURCE_TYPE_KEY] = field.type

            properties[field.name] = Property(
                type=json_schema_type,
                description=field.description or f"Column {field.name}",
                index=i,
                **extra,
            )
            required_fields.append(field.name)

        document = {
            "@id": guid or generate_schema_guid(name),
            "name": name,
            "description": description,
            "properties": properties,
            "required": required_fields,
        }
        if ext in _CSV_EXTENSIONS:
            document["separator"] = '\t' if ext == 'tsv' else ','
            document["header"] = True
        else:
            # separator/header are csv concepts; prune them for parquet
            document["separator"] = None
            document["header"] = None
        return cls.model_validate(document)

    def validate(self, filepath: str) -> List[ValidationErrorRecord]:
        from frictionless import Resource, Dialect, formats

        frictionless_schema = build_frictionless_schema(self.properties)

        # frictionless rejects absolute paths as "not safe"; anchor on the file's
        # directory as basepath and reference it by name to allow either form.
        path = pathlib.Path(filepath)
        name = path.name
        basepath = str(path.parent)
        ext = path.suffix.lower().lstrip('.')

        if ext in _CSV_EXTENSIONS:
            # Delimiter and header row are csv dialect settings; parquet has neither.
            file_dialect = Dialect()
            file_dialect.header = self.header if self.header is not None else True
            csv_control = formats.csv.CsvControl(delimiter=self.separator or ',')
            file_dialect.add_control(csv_control)
            resource = Resource(path=name, basepath=basepath,
                                schema=frictionless_schema, dialect=file_dialect)
        else:
            resource = Resource(path=name, basepath=basepath, schema=frictionless_schema)

        report = resource.validate()
        errors_list = []
        if not report.valid:
            for task in report.tasks:
                for error_detail in task.errors:
                    errors_list.append(frictionless_error_to_record(error_detail))

        return errors_list
