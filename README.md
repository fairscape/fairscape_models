# fairscape-models

The FAIRSCAPE data model. Pydantic classes for every entity in a FAIRSCAPE
RO-Crate (`Dataset`, `Software`, `Computation`, `MLModel`, `Experiment`,
`Sample`, `Instrument`, …). Use it to build crate metadata in Python and to
validate a `ro-crate-metadata.json`.

It is the **create** step of [FAIRSCAPE](https://fairscape.github.io), next to
[fairscape_conversion](https://github.com/fairscape/fairscape_conversion).

## Install

```bash
pip install fairscape-models
```

## Example

Describe a dataset:

```python
from fairscape_models import Dataset

ds = Dataset.model_validate({
    "@id": "ark:59852/dataset-counts",
    "name": "Cell counts",
    "author": "Jane Doe",
    "description": "Per-well cell counts from the imaging run.",
    "keywords": ["imaging", "counts"],
    "datePublished": "2026-09-25",
    "format": "csv",
    "contentUrl": "file:///data/counts.csv",
})
print(ds.model_dump_json(by_alias=True, exclude_none=True, indent=2))
```

Validate a whole crate:

```python
import json
from fairscape_models import ROCrateV1_2

crate = ROCrateV1_2.model_validate(json.load(open("ro-crate-metadata.json")))
```

## Details

- **Profile.** Crates built from these models conform to the FAIRSCAPE Release
  RO-Crate Profile v0.1 (`https://w3id.org/fairscape/profile/0.1`). The root
  entity declares it with `dct:conformsTo`. The PROF manifest is
  [`profiles/profile.ttl`](profiles/profile.ttl) and the EVI vocabulary is
  [`profiles/evi-vocabulary.ttl`](profiles/evi-vocabulary.ttl).
- **Generated files.** [`json-schemas/`](json-schemas),
  [`typescript-types/`](typescript-types) and the EVI vocabulary are all
  generated from the Python classes:

  ```bash
  python scripts/generate_json_schemas.py
  python scripts/generate_ts_types.py
  python scripts/generate_profile.py profiles/evi-vocabulary.ttl
  ```

- **Crosswalks.** `fairscape_models/conversion/` maps to and from Datasheets
  for Datasets and Croissant / Croissant-RAI.
- **Tests.** `pytest`. The fixtures in `tests/test_rocrates/` are real crates
  that conform to the profile.
