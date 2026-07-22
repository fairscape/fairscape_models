"""
signal.py — the `signal` schema type: WFDB / EDF+ waveforms & biosignals.

`properties` are channels (`ChannelProperty`). Inference reads a WFDB `.hea`
header (signal-specification lines: name / units / gain / baseline / ADC
resolution) via the `wfdb` library. Nothing is invented — units link to
QUDT/UCUM only where verified, and the record-level LOINC panel code is attached
only when the channel set is exactly the 12 standard ECG leads.
"""

import os
import re
from typing import Dict, List, Literal, Optional

from pydantic import Field

from fairscape_models.schema.base import (
    NonTabularSchema,
    Property,
    ValidationErrorRecord,
    compare_scalar,
    generate_schema_guid,
)
from fairscape_models.schema.ontology import (
    LOINC_12LEAD,
    STD_12_LEADS,
    as_num,
    unit_terms,
)


class ChannelProperty(Property):
    """
    One channel of a `signal` schema (a WFDB signal-spec line or an EDF+ signal).

    A channel's samples are continuous so `type` is "number". Carries both
    WFDB-style calibration (gain / baseline / adcResolution) and EDF-style
    calibration (physical/digital min-max) — all optional, since a given record
    uses one convention or the other.
    """
    unit: Optional[str] = Field(default=None, description="UCUM unit code, e.g. 'mV', 'uV'")
    unitURL: Optional[str] = Field(default=None, description="Resolvable unit URI (QUDT), where a verified term exists")

    # WFDB calibration (GAIN(BASELINE)/UNITS + ADC resolution)
    gain: Optional[float] = Field(default=None, description="WFDB ADC gain (ADC units per physical unit)")
    baseline: Optional[int] = Field(default=None, description="WFDB ADC value corresponding to 0 physical units")
    adcResolution: Optional[int] = Field(default=None, description="WFDB ADC resolution in bits")

    # EDF+ calibration (physical<->digital linear map) + signal provenance
    physicalMinimum: Optional[float] = Field(default=None)
    physicalMaximum: Optional[float] = Field(default=None)
    digitalMinimum: Optional[int] = Field(default=None)
    digitalMaximum: Optional[int] = Field(default=None)
    transducer: Optional[str] = Field(default=None, description="EDF transducer type, e.g. 'AgAgCl cup electrode'")
    prefiltering: Optional[str] = Field(default=None, description="EDF prefiltering, e.g. 'HP:0.1Hz LP:75Hz N:60Hz'")


class SignalSchema(NonTabularSchema):
    """`signal` — WFDB / EDF+ waveforms & biosignals. `properties` are channels."""

    evi_schema_type: Literal["signal"] = Field(default="signal", alias="EVI:schemaType")
    properties: Dict[str, ChannelProperty]

    samplingFrequency: Optional[float] = Field(default=None, description="Record sampling frequency")
    samplingFrequencyUnit: Optional[str] = Field(default="Hz")
    samplingFrequencyUnitURL: Optional[str] = Field(default=None, description="QUDT hertz is upper-case 'HZ'")
    numberOfSamples: Optional[int] = Field(default=None, description="Samples per channel")
    duration: Optional[float] = Field(default=None)
    durationUnit: Optional[str] = Field(default=None)
    durationUnitURL: Optional[str] = Field(default=None)
    startTime: Optional[str] = Field(default=None, description="Record base time/date (ISO-8601 where known)")

    @classmethod
    def infer(cls, filepath: str, name: str, description: str,
              guid: Optional[str] = None) -> "SignalSchema":
        import wfdb

        record_dir = os.path.dirname(filepath) or "."
        record_name = os.path.splitext(os.path.basename(filepath))[0]
        rec = wfdb.rdheader(os.path.join(record_dir, record_name))

        props: Dict[str, ChannelProperty] = {}
        for i in range(rec.n_sig):
            # Header description fields can carry trailing punctuation (BIDMC: 'RESP,').
            channel = re.sub(r"[^\w+-]+$", "", (rec.sig_name[i] or f"sig_{i}").strip())
            ucum, qudt = unit_terms(rec.units[i] if rec.units else None)
            props[channel] = ChannelProperty(
                description=f"Signal channel '{channel}'",
                index=i,
                type="number",
                unit=ucum,
                unitURL=qudt,
                gain=as_num(rec.adc_gain[i]) if rec.adc_gain else None,
                baseline=rec.baseline[i] if rec.baseline else None,
                adcResolution=rec.adc_res[i] if rec.adc_res else None,
            )

        fs = as_num(rec.fs)
        n = rec.sig_len
        duration = round(n / fs, 6) if (fs and n) else None
        names_uc = {k.upper() for k in props}
        record_value_url = LOINC_12LEAD if STD_12_LEADS <= names_uc else None

        start = None
        if getattr(rec, "base_time", None):
            start = str(rec.base_date) + "T" + str(rec.base_time) if getattr(rec, "base_date", None) else str(rec.base_time)

        return cls.model_validate({
            "@id": guid or generate_schema_guid(name),
            "name": name,
            "description": description,
            "conformsTo": {"@id": "https://physionet.org/physiotools/wag/header-5.htm"},
            "samplingFrequency": fs,
            "samplingFrequencyUnit": "Hz",
            "samplingFrequencyUnitURL": "http://qudt.org/vocab/unit/HZ",
            "numberOfSamples": n,
            "duration": duration,
            "durationUnit": "s",
            "durationUnitURL": "http://qudt.org/vocab/unit/SEC",
            "unitSystem": "http://unitsofmeasure.org",
            "startTime": start,
            "valueURL": record_value_url,
            "properties": props,
            "required": list(props),
        })

    def validate(self, filepath: str) -> List[ValidationErrorRecord]:
        """
        Structural validation: re-infer from the file header and compare the
        fields this schema actually declares (a None on either side means
        "unconstrained"). Reports missing channels and calibration/rate drift.
        """
        observed = type(self).infer(filepath, name=self.name, description="revalidation probe")
        errors: List[ValidationErrorRecord] = []

        # Record-level scalar comparisons.
        for attr in ("samplingFrequency", "numberOfSamples"):
            compare_scalar(errors, getattr(self, attr), getattr(observed, attr),
                           path=None, field=attr)

        for channel, declared in self.properties.items():
            found = observed.properties.get(channel)
            if found is None:
                errors.append(ValidationErrorRecord(
                    message=f"Declared channel '{channel}' is absent from the file",
                    failed_keyword="required", field=channel, path=channel,
                ))
                continue
            for attr in ("unit", "gain", "baseline", "adcResolution"):
                compare_scalar(errors, getattr(declared, attr), getattr(found, attr),
                               path=channel, field=f"{channel}.{attr}")

        if self.additionalProperties is False:
            for channel in observed.properties:
                if channel not in self.properties:
                    errors.append(ValidationErrorRecord(
                        message=f"File has undeclared channel '{channel}'",
                        failed_keyword="additionalProperties", field=channel, path=channel,
                    ))
        return errors
