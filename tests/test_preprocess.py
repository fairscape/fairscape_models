import logging

import pytest
from pydantic import BaseModel, ConfigDict, Field

from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.rocrate import GenericMetadataElem, ROCrateV1_2
from fairscape_models.processing.preprocess import (
    EVI_NAMESPACE,
    GenerateInputsOutput,
    GenerateInversesBetweenCrate,
    GenerateInversesWithinCrate,
    GenerateIO,
    INVERSE_OF,
    INVERSE_PAIRS,
    _replace,
    calculate_inputs_outputs,
    crate_root,
)

ROOT_ID = "ark:59853/rocrate-test"


def ids(value):
    return [v.guid if isinstance(v, BaseModel) else v["@id"] for v in value]


def node(crate, guid):
    return next(n for n in crate.metadataGraph if n.guid == guid)


def root_elem(guid=ROOT_ID, **extra):
    return {
        "@id": guid,
        "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
        "name": "Test crate",
        "description": "A crate used by the preprocessing tests.",
        "keywords": ["test"],
        "version": "1.0",
        "author": "Tester",
        "license": "MIT",
        "hasPart": [],
        **extra,
    }


def descriptor(about=ROOT_ID):
    return {
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
        "about": {"@id": about},
    }


def dataset(guid, **extra):
    return {
        "@id": guid,
        "@type": ["prov:Entity", "https://w3id.org/EVI#Dataset"],
        "name": guid,
        "author": "Tester",
        "datePublished": "2024-01-01",
        "description": "A dataset used by the preprocessing tests.",
        "keywords": ["test"],
        "format": "text/csv",
        **extra,
    }


def computation(guid, **extra):
    return {
        "@id": guid,
        "@type": ["prov:Activity", "https://w3id.org/EVI#Computation"],
        "name": guid,
        "runBy": "Tester",
        "dateCreated": "2024-01-01",
        "description": "A computation used by the preprocessing tests.",
        **extra,
    }


def sample(guid):
    return {
        "@id": guid,
        "@type": ["prov:Entity", "https://w3id.org/EVI#Sample"],
        "name": guid,
        "author": "Tester",
        "description": "A sample.",
        "keywords": ["test"],
    }


def crate(*entities, with_descriptor=True, root=None):
    graph = ([descriptor()] if with_descriptor else []) + [root or root_elem(), *entities]
    return ROCrateV1_2.model_validate({"@graph": graph})


def ref(guid):
    return {"@id": guid}


# --------------------------------------------------------------------------
# Inverse table


def test_inverse_table_is_symmetric():
    assert len(INVERSE_OF) == 2 * len(INVERSE_PAIRS)
    for a, b in INVERSE_PAIRS:
        assert INVERSE_OF[a] == b and INVERSE_OF[b] == a


# --------------------------------------------------------------------------
# Inverses within a crate


def test_within_adds_generated_and_dataset_used_by():
    c = crate(
        dataset("ark:59853/in"),
        dataset("ark:59853/out", generatedBy=ref("ark:59853/comp")),
        computation("ark:59853/comp", usedDataset=[ref("ark:59853/in")]),
    )
    GenerateInversesWithinCrate([c]).process()

    assert ids(node(c, "ark:59853/comp").generated) == ["ark:59853/out"]
    assert ids(node(c, "ark:59853/in").model_extra["datasetUsedBy"]) == ["ark:59853/comp"]
    # Computation's own PROV mirror is untouched.
    assert ids(node(c, "ark:59853/comp").used) == ["ark:59853/in"]


def test_within_is_idempotent():
    c = crate(
        dataset("ark:59853/out", generatedBy=ref("ark:59853/comp")),
        computation("ark:59853/comp"),
    )
    proc = GenerateInversesWithinCrate([c])
    proc.process()
    proc.process()
    assert ids(node(c, "ark:59853/comp").generated) == ["ark:59853/out"]


def test_within_refreshes_prov_mirror_on_target():
    c = crate(
        dataset("ark:59853/out"),
        computation("ark:59853/comp", generated=[ref("ark:59853/out")]),
    )
    GenerateInversesWithinCrate([c]).process()
    out = node(c, "ark:59853/out")
    assert ids(out.generatedBy) == ["ark:59853/comp"]
    assert ids(out.wasGeneratedBy) == ["ark:59853/comp"]


def test_within_scalar_value_becomes_list():
    c = crate(
        dataset("ark:59853/out", generatedBy=ref("ark:59853/a")),
        computation("ark:59853/a"),
        computation("ark:59853/b", generated=[ref("ark:59853/out")]),
    )
    GenerateInversesWithinCrate([c]).process()
    assert ids(node(c, "ark:59853/out").generatedBy) == ["ark:59853/a", "ark:59853/b"]


def test_within_scalar_extra_becomes_list():
    c = crate(
        dataset("ark:59853/d", datasetUsedBy=ref("ark:59853/a")),
        computation("ark:59853/a", usedDataset=[ref("ark:59853/d")]),
        computation("ark:59853/b", usedDataset=[ref("ark:59853/d")]),
    )
    GenerateInversesWithinCrate([c]).process()
    assert ids(node(c, "ark:59853/d").model_extra["datasetUsedBy"]) == [
        "ark:59853/a", "ark:59853/b"]


def test_within_keeps_prefixed_spelling():
    c = crate(
        dataset("ark:59853/d", **{"evi:datasetUsedBy": [ref("ark:59853/c")]}),
        computation("ark:59853/c"),
        dataset("ark:59853/e", **{f"{EVI_NAMESPACE}describes": [ref("ark:59853/c")]}),
    )
    GenerateInversesWithinCrate([c]).process()
    comp = node(c, "ark:59853/c")
    assert ids(comp.model_extra["evi:usedDataset"]) == ["ark:59853/d"]
    assert ids(comp.model_extra[f"{EVI_NAMESPACE}describedBy"]) == ["ark:59853/e"]


def test_within_ignores_foreign_vocab_strings_and_missing_targets():
    c = crate(
        dataset("ark:59853/d", **{
            "schema:generatedBy": [ref("ark:59853/c")],
            "describes": ["ark:59853/c"],          # bare string, not a link
            "supports": [ref("ark:59853/absent")],  # not in the graph
        }),
        computation("ark:59853/c"),
    )
    GenerateInversesWithinCrate([c]).process()
    comp = node(c, "ark:59853/c")
    assert comp.generated == []
    assert "describedBy" not in comp.model_extra


def test_within_dedupes_duplicate_links():
    c = crate(
        dataset("ark:59853/d", generatedBy=[ref("ark:59853/c"), ref("ark:59853/c")]),
        computation("ark:59853/c"),
    )
    GenerateInversesWithinCrate([c]).process()
    assert ids(node(c, "ark:59853/c").generated) == ["ark:59853/d"]


def test_within_skips_targets_without_extras():
    # The descriptor model allows no extra keys, so `describedBy` can't land there.
    c = crate(dataset("ark:59853/d", describes=[ref("ro-crate-metadata.json")]))
    GenerateInversesWithinCrate([c]).process()
    assert not hasattr(node(c, "ro-crate-metadata.json"), "describedBy")


def test_within_skips_entities_without_id():
    c = crate(dataset("ark:59853/d"))
    c.metadataGraph.append(GenericMetadataElem.model_construct(
        guid="", metadataType="Thing", isPartOf=[]))
    GenerateInversesWithinCrate([c]).process()


# --------------------------------------------------------------------------
# Inverses between crates


def test_between_links_into_other_crates():
    upstream = crate(dataset("ark:59853/shared"))
    downstream = crate(
        computation("ark:59853/c", usedDataset=[ref("ark:59853/shared")]),
        root=root_elem("ark:59853/rocrate-down"),
    )
    GenerateInversesWithinCrate([upstream, downstream]).process()
    assert "datasetUsedBy" not in node(upstream, "ark:59853/shared").model_extra

    GenerateInversesBetweenCrate([upstream, downstream]).process()
    assert ids(node(upstream, "ark:59853/shared").model_extra["datasetUsedBy"]) == [
        "ark:59853/c"]


def test_between_does_not_link_within_same_crate():
    c = crate(
        dataset("ark:59853/out", generatedBy=ref("ark:59853/comp")),
        computation("ark:59853/comp"),
    )
    GenerateInversesBetweenCrate([c]).process()
    assert node(c, "ark:59853/comp").generated == []


# --------------------------------------------------------------------------
# Inputs and outputs


def test_inputs_outputs_basic_pipeline():
    c = crate(
        dataset("ark:59853/raw"),
        dataset("ark:59853/result", generatedBy=ref("ark:59853/comp")),
        dataset("ark:59853/standalone"),
        computation("ark:59853/comp", usedDataset=[ref("ark:59853/raw"), ref("ark:59853/external")]),
    )
    GenerateInputsOutput([c]).process()
    root = node(c, ROOT_ID)
    extra = root.model_extra
    assert ids(extra[f"{EVI_NAMESPACE}inputs"]) == [
        "ark:59853/external", "ark:59853/raw", "ark:59853/standalone"]
    assert ids(extra[f"{EVI_NAMESPACE}outputs"]) == [
        "ark:59853/result", "ark:59853/standalone"]
    dumped = c.model_dump(by_alias=True)["@graph"][1]
    assert dumped[f"{EVI_NAMESPACE}outputs"][0] == {"@id": "ark:59853/result"}


def test_inputs_include_samples_and_mlmodels_and_derivation():
    c = crate(
        sample("ark:59853/s"),
        dataset("ark:59853/derived", derivedFrom=[ref("ark:59853/src")]),
        dataset("ark:59853/src"),
        {
            "@id": "ark:59853/model",
            "@type": ["prov:Entity", "https://w3id.org/EVI#MLModel"],
            "name": "m", "author": "Tester", "description": "A trained model here.",
            "keywords": ["m"], "format": "pt",
        },
        computation("ark:59853/c", usedDataset=[ref("ark:59853/s")],
                    usedMLModel=[ref("ark:59853/model")]),
    )
    inputs, outputs = calculate_inputs_outputs(c)
    assert ids(inputs) == ["ark:59853/s", "ark:59853/model", "ark:59853/src"]
    assert ids(outputs) == ["ark:59853/derived"]


def test_inputs_outputs_prov_only_crate():
    graph = [
        descriptor("ark:59853/prov-root"),
        {"@id": "ark:59853/prov-root", "@type": "Thing", "name": "root"},
        {"@id": "ark:59853/e1", "@type": "prov:Entity"},
        {"@id": "ark:59853/e2", "@type": "prov:Entity",
         "prov:wasGeneratedBy": [ref("ark:59853/act")]},
        {"@id": "ark:59853/act", "@type": "prov:Activity", "name": "act",
         "description": "A PROV-only activity.", "prov:used": [ref("ark:59853/e1")]},
        {"@id": "ark:59853/person", "@type": "Person-ish"},
    ]
    c = ROCrateV1_2.model_validate({"@graph": graph})
    assert crate_root(c).guid == "ark:59853/prov-root"
    inputs, outputs = calculate_inputs_outputs(c)
    assert ids(inputs) == ["ark:59853/e1"]
    assert ids(outputs) == ["ark:59853/e2"]


def test_root_fallbacks():
    no_descriptor = crate(dataset("ark:59853/d"), with_descriptor=False)
    assert crate_root(no_descriptor).guid == ROOT_ID

    dangling = ROCrateV1_2.model_validate(
        {"@graph": [descriptor("ark:59853/missing"), root_elem()]})
    assert crate_root(dangling).guid == ROOT_ID


def test_entity_with_empty_type_is_ignored():
    c = crate(dataset("ark:59853/d"))
    c.metadataGraph.append(GenericMetadataElem.model_construct(
        guid="ark:59853/x", metadataType=[], isPartOf=[]))
    inputs, outputs = calculate_inputs_outputs(c)
    assert ids(outputs) == ["ark:59853/d"]


def test_no_root_is_skipped(caplog):
    c = ROCrateV1_2.model_validate({"@graph": [dataset("ark:59853/d")]})
    with caplog.at_level(logging.INFO):
        GenerateInputsOutput([c], logging.getLogger("preprocess")).process()
    assert "no root entity" in caplog.text
    assert "inputs" not in node(c, "ark:59853/d").model_extra


def test_existing_spelling_is_reused_and_duplicates_dropped():
    c = crate(
        dataset("ark:59853/d"),
        root=root_elem(**{"EVI:outputs": [ref("stale")], "outputs": [ref("stale")]}),
    )
    GenerateInputsOutput([c]).process()
    extra = node(c, ROOT_ID).model_extra
    assert ids(extra["EVI:outputs"]) == ["ark:59853/d"]
    assert "outputs" not in extra
    assert f"{EVI_NAMESPACE}outputs" not in extra


def test_replace_clears_declared_field_spellings():
    class Root(BaseModel):
        model_config = ConfigDict(extra="allow")
        outputs: list = Field(default=None)

    r = Root.model_validate({"EVI:outputs": [ref("a")], "outputs": [ref("b")]})
    _replace(r, ("EVI:outputs", "outputs"), [IdentifierValue.model_validate(ref("c"))])
    assert ids(r.model_extra["EVI:outputs"]) == ["c"]
    assert r.outputs is None


# --------------------------------------------------------------------------
# Full run


def test_process_all(caplog):
    upstream = crate(dataset("ark:59853/shared"))
    downstream = crate(
        dataset("ark:59853/result"),
        computation("ark:59853/c", usedDataset=[ref("ark:59853/shared")],
                    generated=[ref("ark:59853/result")]),
        root=root_elem("ark:59853/rocrate-down"),
    )
    with caplog.at_level(logging.INFO):
        GenerateIO([upstream, downstream], logging.getLogger("preprocess")).process_all()

    # `generated` on the computation became `generatedBy` on the dataset
    # before inputs/outputs were derived, so the result is not also an input.
    down = node(downstream, "ark:59853/rocrate-down").model_extra
    assert ids(down[f"{EVI_NAMESPACE}inputs"]) == ["ark:59853/shared"]
    assert ids(down[f"{EVI_NAMESPACE}outputs"]) == ["ark:59853/result"]
    assert ids(node(upstream, "ark:59853/shared").model_extra["datasetUsedBy"]) == [
        "ark:59853/c"]
    assert "within crate" in caplog.text
    assert "into other crates" in caplog.text
