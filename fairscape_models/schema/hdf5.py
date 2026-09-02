"""
hdf5.py — the `hdf5` schema type: a whole HDF5 file as a tree of datasets.

`properties` map each dataset's HDF5 path to a `DatasetProperty` carrying its
array structure (shape / dtype / chunks / compression) — the same NDArray-style
description used by `NDArraySchema`, one per dataset. This replaces the old
"flatten every dataset into a pandas DataFrame and validate column_0..n as a
table" approach: inference reads structure only (attrs / shape / dtype), never
the array data, and validation compares that structure back against the file.

Reader lib: h5py.
"""

from typing import Dict, List, Literal, Optional

from pydantic import Field

from fairscape_models.schema.base import (
    NonTabularSchema,
    Property,
    ValidationErrorRecord,
    generate_schema_guid,
)

# numpy dtype kind -> canonical JSON-Schema type, for compound-dtype fields.
_NUMPY_KIND_TO_JSON = {
    'i': 'integer', 'u': 'integer',
    'f': 'number', 'c': 'number',
    'b': 'boolean',
    'S': 'string', 'U': 'string', 'O': 'string',
    'V': 'object',
}


def _json_type_for_kind(kind: str) -> str:
    return _NUMPY_KIND_TO_JSON.get(kind, 'string')


class DatasetProperty(Property):
    """
    One HDF5 dataset described structurally. `type` is "array" for a plain
    dataset and "object" for a compound (structured) dtype, whose fields become
    nested `properties`.
    """
    hdf5Path: Optional[str] = Field(default=None, alias="hdf5-path")
    shape: Optional[List[int]] = Field(default=None)
    dtype: Optional[str] = Field(default=None, description="numpy dtype string, e.g. 'float64', or the compound descr")
    chunks: Optional[List[int]] = Field(default=None)
    compression: Optional[str] = Field(default=None)


class HDF5Schema(NonTabularSchema):
    """`hdf5` — a whole HDF5 file. `properties` map dataset path -> structure."""

    evi_schema_type: Literal["hdf5"] = Field(default="hdf5", alias="EVI:schemaType")
    properties: Dict[str, DatasetProperty] = Field(default_factory=dict)

    @classmethod
    def infer(cls, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> "HDF5Schema":
        import h5py

        props: Dict[str, DatasetProperty] = {}

        def visit(path, obj):
            if not isinstance(obj, h5py.Dataset):
                return  # groups are structure, not leaves; skip
            dt = obj.dtype
            nested = None
            if dt.names:  # compound / structured dtype -> field columns
                nested = {
                    fname: Property(
                        description=f"Field '{fname}' of dataset {path}",
                        index=i,
                        type=_json_type_for_kind(dt.fields[fname][0].kind),
                    )
                    for i, fname in enumerate(dt.names)
                }
            props[path] = DatasetProperty(
                description=f"Dataset at {path}",
                index=len(props),
                type="object" if dt.names else "array",
                **{"hdf5-path": path},
                shape=list(obj.shape),
                dtype=str(dt),
                chunks=list(obj.chunks) if obj.chunks else None,
                compression=obj.compression,
                properties=nested,
            )

        with h5py.File(filepath, "r") as fh:
            fh.visititems(visit)

        return cls.model_validate({
            "@id": guid or generate_schema_guid(name),
            "name": name,
            "description": description,
            "properties": props,
            "required": list(props),
        })

    def validate(self, filepath: str, deep: bool = False) -> List[ValidationErrorRecord]:
        """
        Structural validation: re-open the file and compare each declared
        dataset's path / shape / dtype / chunks against the file. Reads structure
        only (never array data). No deep tier yet — `deep` is accepted and ignored.
        """
        import h5py

        errors: List[ValidationErrorRecord] = []
        with h5py.File(filepath, "r") as fh:
            for path, declared in self.properties.items():
                obj = fh.get(path)
                if obj is None:
                    errors.append(ValidationErrorRecord(
                        message=f"Declared dataset '{path}' is absent from the file",
                        failed_keyword="required", field=path, path=path,
                    ))
                    continue
                if not isinstance(obj, h5py.Dataset):
                    errors.append(ValidationErrorRecord(
                        message=f"'{path}' is a group in the file but declared as a dataset",
                        failed_keyword="type", field=path, path=path,
                    ))
                    continue

                if declared.shape is not None and list(obj.shape) != list(declared.shape):
                    errors.append(ValidationErrorRecord(
                        message=f"{path}: expected shape {declared.shape}, file has {list(obj.shape)}",
                        failed_keyword="const", field=f"{path}.shape", path=path,
                    ))
                if declared.dtype is not None and str(obj.dtype) != declared.dtype:
                    errors.append(ValidationErrorRecord(
                        message=f"{path}: expected dtype {declared.dtype!r}, file has {str(obj.dtype)!r}",
                        failed_keyword="type", field=f"{path}.dtype", path=path,
                    ))
                if declared.chunks is not None:
                    file_chunks = list(obj.chunks) if obj.chunks else None
                    if file_chunks != list(declared.chunks):
                        errors.append(ValidationErrorRecord(
                            message=f"{path}: expected chunks {declared.chunks}, file has {file_chunks}",
                            failed_keyword="const", field=f"{path}.chunks", path=path,
                        ))
                # Compound-dtype fields: every declared field must be present.
                # Only enforced when the file dataset is actually compound — a
                # plain array declared with nested columns (legacy flattened
                # form) has no dtype fields to check against.
                file_names = set(obj.dtype.names or ())
                if declared.properties and file_names:
                    for fname in declared.properties:
                        if fname not in file_names:
                            errors.append(ValidationErrorRecord(
                                message=f"{path}: declared field '{fname}' absent from compound dtype",
                                failed_keyword="required", field=fname, path=path,
                            ))

            if self.additionalProperties is False:
                declared_paths = set(self.properties)
                seen = []

                def collect(path, obj):
                    if isinstance(obj, h5py.Dataset) and path not in declared_paths:
                        seen.append(path)

                fh.visititems(collect)
                for path in seen:
                    errors.append(ValidationErrorRecord(
                        message=f"File has undeclared dataset '{path}'",
                        failed_keyword="additionalProperties", field=path, path=path,
                    ))
        return errors
