"""
image.py — the `image` schema type: DICOM (and, by extension, NIfTI / OME-Zarr).

`properties` are named, typed axes (`AxisProperty`, shared from base.py). Modality
and anatomy carry real coded values (SNOMED CT / RadLex). `nativeMetadata` passes
a whitelist of technical/acquisition tags through verbatim as the PS3.18 Annex F
DICOM JSON Model. Patient/identity tags are excluded by design — the schema
describes structure, not the subject.

Reader lib: pydicom (headers only — pixels are never read).
"""

import os
from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from fairscape_models.schema.base import (
    AxisProperty,
    NonTabularSchema,
    ValidationErrorRecord,
    compare_scalar,
    generate_schema_guid,
)
from fairscape_models.schema.ontology import MODALITY_MAP, anatomy_terms

# (group, element, keyword, VR) whitelist of technical/acquisition tags to pass
# through as nativeMetadata. Patient/identity tags are deliberately excluded.
_DICOM_PASSTHROUGH = [
    (0x0008, 0x0060, "Modality", "CS"),
    (0x0008, 0x0070, "Manufacturer", "LO"),
    (0x0018, 0x0050, "SliceThickness", "DS"),
    (0x0028, 0x0002, "SamplesPerPixel", "US"),
    (0x0028, 0x0004, "PhotometricInterpretation", "CS"),
    (0x0028, 0x0010, "Rows", "US"),
    (0x0028, 0x0011, "Columns", "US"),
    (0x0028, 0x0030, "PixelSpacing", "DS"),
    (0x0028, 0x0100, "BitsAllocated", "US"),
    (0x0028, 0x0101, "BitsStored", "US"),
    (0x0028, 0x0103, "PixelRepresentation", "US"),
    (0x0028, 0x1052, "RescaleIntercept", "DS"),
    (0x0028, 0x1053, "RescaleSlope", "DS"),
]
_NUMERIC_VR = {"US", "SS", "UL", "SL", "FL", "FD", "DS", "IS"}
_MM_URL = "http://qudt.org/vocab/unit/MilliM"


def _anatomy(ds):
    """
    (anatomy_label, snomed_url) for a DICOM image. Prefer the coded
    AnatomicRegionSequence (0008,2218); fall back to the free-text
    BodyPartExamined (0018,0015) resolved through the Annex L crosswalk.
    (None, None) if neither is present.
    """
    seq = ds.get("AnatomicRegionSequence")
    if seq:
        item = seq[0]
        code = str(getattr(item, "CodeValue", "") or "")
        scheme = str(getattr(item, "CodingSchemeDesignator", "") or "").upper()
        meaning = str(getattr(item, "CodeMeaning", "") or "") or None
        if code and scheme in ("SCT", "SRT", "SNOMED"):  # SNOMED CT (current/retired designators)
            return meaning, f"http://snomed.info/id/{code}"
    return anatomy_terms(str(ds.get("BodyPartExamined", "")) or None)


def _dicom_json_value(elem):
    """Render a pydicom element as a DICOM JSON Model Value array (PS3.18 Annex F)."""
    v = elem.value
    seq = list(v) if isinstance(v, (list, tuple)) or elem.VM > 1 else [v]
    if elem.VR in _NUMERIC_VR:
        out = []
        for x in seq:
            fx = float(x)
            out.append(int(fx) if fx.is_integer() else fx)
        return out
    return [str(x) for x in seq]


class ImageSchema(NonTabularSchema):
    """`image` — DICOM. `properties` are named spatial axes."""

    evi_schema_type: Literal["image"] = Field(default="image", alias="EVI:schemaType")
    properties: Dict[str, AxisProperty]

    modality: Optional[str] = Field(default=None, description="Acquisition modality, e.g. 'CT', 'MR'")
    modalityURL: Optional[str] = Field(default=None, description="SNOMED CT modality URI")
    modalityRadLexURL: Optional[str] = Field(default=None)
    dicomModalityCode: Optional[str] = Field(default=None, description="DICOM (0008,0060) modality code — the canonical modality identity")
    dicomModalityCodeSystem: Optional[str] = Field(default=None, description="Coding-system URI for dicomModalityCode (the DICOM 'DCM' scheme)")
    anatomy: Optional[str] = Field(default=None)
    anatomyURL: Optional[str] = Field(default=None, description="Uberon / FMA anatomy URI")
    anatomyRadLexURL: Optional[str] = Field(default=None)

    dtype: Optional[str] = Field(default=None)
    bitsAllocated: Optional[int] = Field(default=None)

    nativeMetadata: Optional[Dict[str, Any]] = Field(default=None)

    @classmethod
    def infer(cls, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> "ImageSchema":
        import pydicom

        ds = pydicom.dcmread(filepath, stop_before_pixels=True)

        rows = int(ds.Rows)
        cols = int(ds.Columns)
        ps = list(ds.get("PixelSpacing", [None, None]))  # DICOM order: [row(dy), col(dx)]
        dy, dx = (float(ps[0]), float(ps[1])) if ps[0] is not None else (None, None)

        props: Dict[str, AxisProperty] = {}
        props["x"] = AxisProperty(description="Column axis (in-plane)", index=0, type="integer",
                                  axisType="space", size=cols, spacing=dx,
                                  unit="mm" if dx is not None else None,
                                  unitURL=_MM_URL if dx is not None else None)
        props["y"] = AxisProperty(description="Row axis (in-plane)", index=1, type="integer",
                                  axisType="space", size=rows, spacing=dy,
                                  unit="mm" if dy is not None else None,
                                  unitURL=_MM_URL if dy is not None else None)
        n_frames = int(ds.get("NumberOfFrames", 1) or 1)
        if n_frames > 1:
            thick = ds.get("SliceThickness")
            props["z"] = AxisProperty(description="Slice axis (through-plane)", index=2, type="integer",
                                      axisType="space", size=n_frames,
                                      spacing=float(thick) if thick is not None else None,
                                      unit="mm" if thick is not None else None,
                                      unitURL=_MM_URL if thick is not None else None)

        modality = str(ds.get("Modality", "")) or None
        mt = MODALITY_MAP.get(modality)
        # The DCM code (dicomModalityCode) is the canonical modality identity;
        # dcm_system_uri is its coding system. SNOMED/RadLex are enrichment.
        dcm_system = mt.dcm_system_uri if mt else None
        snomed = mt.snomed_uri if mt else None
        radlex = mt.radlex_uri if mt else None
        anatomy, anatomy_url = _anatomy(ds)
        bits = int(ds.get("BitsAllocated", 0)) or None
        signed = int(ds.get("PixelRepresentation", 0)) == 1
        dtype = (f"int{bits}" if signed else f"uint{bits}") if bits else None

        native = {}
        for g, e, _kw, _vr in _DICOM_PASSTHROUGH:
            if (g, e) in ds:
                elem = ds[g, e]
                native[f"{g:04X}{e:04X}"] = {"vr": elem.VR, "Value": _dicom_json_value(elem)}

        return cls.model_validate({
            "@id": guid or generate_schema_guid(name),
            "name": name,
            "description": description,
            "conformsTo": {"@id": "https://dicom.nema.org/medical/dicom/current/output/chtml/part18/chapter_f.html"},
            "modality": modality,
            "modalityURL": snomed,
            "modalityRadLexURL": radlex,
            "dicomModalityCode": modality,
            "dicomModalityCodeSystem": dcm_system,
            "anatomy": anatomy,
            "anatomyURL": anatomy_url,
            "dtype": dtype,
            "bitsAllocated": bits,
            "unitSystem": "http://unitsofmeasure.org",
            "nativeMetadata": native or None,
            "properties": props,
            "required": list(props),
        })

    def validate(self, filepath: str) -> List[ValidationErrorRecord]:
        """
        Structural validation: re-infer from the DICOM header and compare the
        fields this schema declares. Reports missing axes and geometry/modality
        drift (a None on either side means "unconstrained").
        """
        observed = type(self).infer(filepath, name=self.name, description="revalidation probe")
        errors: List[ValidationErrorRecord] = []

        for attr in ("dicomModalityCode", "dtype", "bitsAllocated"):
            compare_scalar(errors, getattr(self, attr), getattr(observed, attr),
                           path=None, field=attr)

        for axis, declared in self.properties.items():
            found = observed.properties.get(axis)
            if found is None:
                errors.append(ValidationErrorRecord(
                    message=f"Declared axis '{axis}' is absent from the file",
                    failed_keyword="required", field=axis, path=axis,
                ))
                continue
            for attr in ("size", "spacing"):
                compare_scalar(errors, getattr(declared, attr), getattr(found, attr),
                               path=axis, field=f"{axis}.{attr}")

        if self.additionalProperties is False:
            for axis in observed.properties:
                if axis not in self.properties:
                    errors.append(ValidationErrorRecord(
                        message=f"File has undeclared axis '{axis}'",
                        failed_keyword="additionalProperties", field=axis, path=axis,
                    ))
        return errors
