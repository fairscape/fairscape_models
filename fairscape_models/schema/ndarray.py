"""
ndarray.py — the `ndarray` schema type: generic HDF5 / netCDF / Zarr tensors.

Described the CF way: named coordinate axes with a controlled `standardName` and
a UDUNITS unit (shared `AxisProperty` from base.py), plus the variable's own
`measures` (standard_name) and `unit`. A native N-D descriptor that replaces the
lossy HDF5-as-tabular adapter (which flattened axes into column_i).

Model-only in this version: there is no single-file format that maps one file to
one ndarray, so `infer`/`validate` are not overridden yet. `HDF5Schema`
(hdf5.py) is the concrete container that describes real .h5 files; a single
ndarray uses these fields as an `HDF5Schema` member. Zarr/netCDF inference can
add a classmethod here later.
"""

from typing import Dict, List, Literal, Optional

from pydantic import Field

from fairscape_models.schema.base import AxisProperty, NonTabularSchema


class NDArraySchema(NonTabularSchema):
    """
    `ndarray` — generic HDF5 / netCDF / Zarr tensors. `properties` are named
    coordinate axes.
    """
    evi_schema_type: Literal["ndarray"] = Field(default="ndarray", alias="EVI:schemaType")
    properties: Dict[str, AxisProperty] = Field(default_factory=dict)

    shape: Optional[List[int]] = Field(default=None)
    dtype: Optional[str] = Field(default=None)
    chunks: Optional[List[int]] = Field(default=None)
    compression: Optional[str] = Field(default=None)
    standardNameVocabulary: Optional[str] = Field(default=None, description="CF Standard Name Table URL")
    measures: Optional[str] = Field(default=None, description="The array variable's CF standard_name")
    unit: Optional[str] = Field(default=None, description="The array variable's unit")
