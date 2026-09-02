"""
signal.py — the `signal` schema type: WFDB / EDF+ waveforms & biosignals.

`properties` are channels (`ChannelProperty`). Inference reads a WFDB `.hea`
header (signal-specification lines: name / units / gain / baseline / ADC
resolution) via the `wfdb` library. Nothing is invented — units link to
QUDT/UCUM only where verified, and the record-level LOINC panel code is attached
only when the channel set is exactly the 12 standard ECG leads.

`validate` runs in three tiers, cheapest first:

    tier 0  schema <-> header   always      diff the header against what this
                                            schema declares
    tier 1  header <-> file     always      decode the final frame; catches a
                                            truncated or missing .dat
    tier 2  data   <-> header   deep=True   read the record, verify the
                                            per-channel checksum (~200 MB/s)

Only tier 2 sees corruption in the middle of a record: a WFDB gap is stored
in-band as a sentinel sample, so nothing about the file's length changes.
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


# A header may store the checksum as the signed or the unsigned residue of the
# sample sum, so compare modulo this rather than by equality.
_CHECKSUM_MODULUS = 65536


def _record_stem(filepath: str) -> str:
    """WFDB addresses a record by extensionless path ('.../rec', not 'rec.hea')."""
    return os.path.join(
        os.path.dirname(filepath) or ".",
        os.path.splitext(os.path.basename(filepath))[0],
    )


def _channel_name(raw: Optional[str], index: int) -> str:
    """Header description fields can carry trailing punctuation (BIDMC: 'RESP,')."""
    return re.sub(r"[^\w+-]+$", "", (raw or f"sig_{index}").strip())


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

        rec = wfdb.rdheader(_record_stem(filepath))
        if isinstance(rec, wfdb.MultiRecord):
            # A layout header has no signal-spec lines of its own — sig_name,
            # units and gain are all None.
            raise ValueError(
                f"'{os.path.basename(filepath)}' is a multi-segment WFDB record "
                f"({len(rec.seg_name or ())} segments); signal schema inference "
                "supports single-segment records only"
            )

        props: Dict[str, ChannelProperty] = {}
        for i in range(rec.n_sig):
            channel = _channel_name(rec.sig_name[i], i)
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

    def validate(self, filepath: str, deep: bool = False) -> List[ValidationErrorRecord]:
        """
        Tier 0 + tier 1 by default; `deep=True` adds tier 2 (see module docstring).

        Tier 0 re-infers from the file header and compares the fields this schema
        actually declares (a None on either side means "unconstrained"), reporting
        missing channels and calibration/rate drift. Tiers 1 and 2 compare the
        header against the signal file itself.
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

        errors.extend(self._validate_signal_file(filepath, deep=deep))
        return errors

    def _validate_signal_file(self, filepath: str,
                              deep: bool = False) -> List[ValidationErrorRecord]:
        """Tier 1 (always) and tier 2 (`deep`): the header against the .dat itself."""
        import wfdb

        stem = _record_stem(filepath)
        header = wfdb.rdheader(stem)
        errors: List[ValidationErrorRecord] = []

        # The channel set is identity, so this is always enforced; record length
        # is not, and is only checked when the schema states it.
        declared_channels = len(self.properties)
        if declared_channels != header.n_sig:
            errors.append(ValidationErrorRecord(
                message=(f"Schema declares {declared_channels} channel(s), "
                         f"header declares {header.n_sig}"),
                failed_keyword="const", field="numberOfSignals",
            ))

        if not header.sig_len:
            return errors

        signal_files = ", ".join(sorted(set(header.file_name or ()))) or "<unnamed>"

        # Tier 1 — decode only the final frame; wfdb raises if the file is short.
        try:
            wfdb.rdrecord(stem, sampfrom=header.sig_len - 1, physical=False)
        except FileNotFoundError:
            errors.append(ValidationErrorRecord(
                message=f"Signal file is missing: {signal_files}",
                failed_keyword="required", field="signalFile", path=signal_files,
            ))
            return errors
        except ValueError:
            errors.append(ValidationErrorRecord(
                message=(f"Signal file {signal_files} is shorter than the header declares "
                         f"({header.sig_len} samples x {header.n_sig} channel(s))"),
                failed_keyword="fileLength", field="signalFile", path=signal_files,
            ))
            return errors

        if not deep:
            return errors

        # Tier 2. smooth_frames=False because the smoothed view averages each
        # frame down to one value and so cannot reproduce the stored checksum of
        # a multi-frequency channel (MIMIC-I 03700001 MCL1 is 4x oversampled).
        record = wfdb.rdrecord(stem, physical=False, smooth_frames=False)
        channels = record.e_d_signal
        observed_checksums = record.calc_checksum(expanded=True)
        declared_checksums = header.checksum or ()

        if len(channels) != header.n_sig:
            errors.append(ValidationErrorRecord(
                message=(f"Decoded {len(channels)} channel(s), header declares "
                         f"{header.n_sig}"),
                failed_keyword="const", field="shape",
            ))

        for i, samples in enumerate(channels):
            channel = _channel_name(header.sig_name[i] if header.sig_name else None, i)

            expected_length = header.sig_len * (header.samps_per_frame[i] or 1)
            if len(samples) != expected_length:
                errors.append(ValidationErrorRecord(
                    message=(f"{channel}: decoded {len(samples)} samples, header "
                             f"declares {expected_length}"),
                    failed_keyword="const", field=f"{channel}.length", path=channel,
                ))

            declared_checksum = declared_checksums[i] if i < len(declared_checksums) else None
            if declared_checksum is None:
                continue  # optional field in a WFDB signal spec line
            if header.skew and header.skew[i]:
                # Stored time-shifted, read back aligned: these are not the samples
                # that were summed (MIMIC-I 03700001 RESP is 'fmt 212:4').
                continue
            observed_checksum = observed_checksums[i]
            if (observed_checksum - declared_checksum) % _CHECKSUM_MODULUS != 0:
                errors.append(ValidationErrorRecord(
                    message=(f"{channel}: samples do not match the header checksum "
                             f"(header {declared_checksum}, data {observed_checksum})"),
                    failed_keyword="checksum", field=f"{channel}.checksum", path=channel,
                ))
        return errors
