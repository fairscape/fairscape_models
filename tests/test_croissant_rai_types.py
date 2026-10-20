"""The Croissant model's rai:* fields accept the same shapes as the crate model.

ROCrateMetadataElem types every RAI field as ``Union[str, List[str]]``; the
Croissant export passes those values through, so the Croissant model has to
accept both shapes too (D1 in fairscape_conversion/bugs.md).
"""

import pytest

from fairscape_models.conversion.models.croissant import CroissantDataset
from fairscape_models.rocrate import ROCrateMetadataElem

CROISSANT_RAI = sorted(
    f.alias for f in CroissantDataset.model_fields.values()
    if f.alias and f.alias.startswith("rai:"))
CRATE_RAI = sorted(
    f.alias for f in ROCrateMetadataElem.model_fields.values()
    if f.alias and f.alias.startswith("rai:"))


@pytest.mark.parametrize("alias", CROISSANT_RAI)
@pytest.mark.parametrize("value", ["one statement", ["first", "second"]])
def test_croissant_rai_field_accepts_str_and_list(alias, value):
    ds = CroissantDataset.model_validate(
        {"name": "x", "description": "y", alias: value})
    assert ds.model_dump(by_alias=True)[alias] == value


def test_croissant_model_declares_every_crate_rai_field():
    assert set(CRATE_RAI) <= set(CROISSANT_RAI)
