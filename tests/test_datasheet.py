# tests/test_datasheet.py

import copy
import difflib
import json
import pathlib

import pytest

pytest.importorskip("jinja2")

from fairscape_models.rocrate import ROCrateV1_2  # noqa: E402
from fairscape_models.datasheet import DatasheetPage, GenerateDatasheet  # noqa: E402
from fairscape_models.datasheet import generate as gen  # noqa: E402

TESTS = pathlib.Path(__file__).parent
CHORUS = TESTS / "datasheet" / "chorus"
LAKEDB = TESTS / "test_rocrates" / "LakeDB" / "ro-crate-metadata.json"
RELEASE = TESTS / "test_rocrates" / "release" / "ro-crate-metadata.json"
GENERATED_AT = "2026-11-11 15:56"


def load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def crate_from(path, **patch):
    data = load(path)
    data.update(patch)
    return ROCrateV1_2.model_validate(data)


def root_elem(**overrides):
    """A minimal valid ROCrateMetadataElem as a dict."""
    elem = {
        "@id": "ark:59852/rocrate-test",
        "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
        "name": "Test crate",
        "description": "A crate used by the datasheet tests.",
        "keywords": ["test"],
        "version": "1.0",
        "hasPart": [],
        "author": "Test Author",
        "license": "https://creativecommons.org/licenses/by/4.0/",
    }
    elem.update(overrides)
    return elem


def descriptor(about):
    return {
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
        "about": {"@id": about},
    }


def dataset(guid, fmt="csv", **overrides):
    elem = {
        "@id": guid,
        "@type": "https://w3id.org/EVI#Dataset",
        "name": guid.rsplit("/", 1)[-1],
        "author": "Test Author",
        "datePublished": "2024-01-01",
        "description": "A dataset used by the datasheet tests.",
        "keywords": ["test"],
        "format": fmt,
    }
    elem.update(overrides)
    return elem


def computation(guid, used=(), generated=(), **overrides):
    elem = {
        "@id": guid,
        "@type": "https://w3id.org/EVI#Computation",
        "name": guid.rsplit("/", 1)[-1],
        "runBy": "Test Runner",
        "dateCreated": "2024-01-01",
        "description": "A computation used by the datasheet tests.",
        "usedDataset": [{"@id": u} for u in used],
        "generated": [{"@id": g} for g in generated],
    }
    elem.update(overrides)
    return elem


def crate(*graph):
    return ROCrateV1_2.model_validate({"@graph": list(graph)})


@pytest.fixture(scope="module")
def chorus():
    return crate_from(CHORUS / "ro-crate-metadata.json")


@pytest.fixture(scope="module")
def chorus_page(chorus):
    return GenerateDatasheet(chorus, None, generated_at=GENERATED_AT).format()


# -- the CHORUS fixture -------------------------------------------------------

def test_chorus_datasheet_regenerates_exactly(chorus):
    expected = (CHORUS / "ro-crate-datasheet.html").read_text(encoding="utf-8").replace("\r\n", "\n")
    html = GenerateDatasheet(chorus, None, generated_at=GENERATED_AT).generate(None)
    if html != expected:  # pragma: no cover - only runs on a regression
        diff = difflib.unified_diff(expected.splitlines(), html.splitlines(),
                                    "ro-crate-datasheet.html", "generated", lineterm="", n=2)
        pytest.fail("\n".join(list(diff)[:60]))


def test_chorus_format_structure(chorus_page):
    page = chorus_page
    assert isinstance(page, DatasheetPage)
    assert page.title == "CHoRUS Production Release V3"
    assert page.ark_href == "https://doi.org/10.18130/V3/ATG0DP"
    assert [b.label for b in page.badges] == ["Version 3.0", "License", "Released 10/29/2026"]
    assert page.badges[1].href == ""  # the licence is prose, not a URL

    assert page.composition.is_release
    assert page.composition.count == 3 and page.composition.show_index
    assert [c.anchor for c in page.composition.cards] == ["subcrate-1", "subcrate-2", "subcrate-3"]
    assert all(not c.published for c in page.composition.cards)
    assert all(c.notes == [gen.NOTE_UNPUBLISHED] for c in page.composition.cards)
    assert page.composition.cards[0].meta.access_href == "http://chorus4ai.org/dataset"
    assert page.composition.cards[0].search.endswith("https://id.nlm.nih.gov/mesh/d008279 ")

    assert page.summary.truncated and len(page.summary.description) == 497
    assert [s.n for s in page.summary.stats] == ["—", "0", "0", "0"]
    assert page.summary.extra[0].n == "3"

    by_id = {r.id: r for r in page.overview}
    assert by_id["doi"].kind == "missing"
    assert by_id["accession"].href == "https://doi.org/10.18130/V3/ATG0DP"
    assert by_id["conforms-to"].entries[0].href == "https://w3id.org/fairscape/profile/0.1"
    assert by_id["license"].href == ""

    assert page.regulatory.deidentified == "Yes" and page.regulatory.fda_regulated == "Yes"
    assert page.regulatory.irb["contactPoint"]["email"] == "irbreliance@mgb.org"

    assert [r.label for r in page.use_cases] == [
        "Limitations", "Potential Sources of Bias", "Maintenance Plan",
        "Data Collection", "Missing Data", "Personal / Sensitive Information",
    ]
    assert [n.label for n in page.nav] == [
        "Datasheet Summary", "Release Overview", "AI Ready Details", "Composition", "Distribution",
    ]
    assert [n.label for n in page.nav[3].children][:2] == ["All datasets", "CHoRUS Production V3 Image Subcrate"]


def test_generate_writes_file(chorus, tmp_path):
    target = tmp_path / "out.html"
    html = GenerateDatasheet(chorus, generated_at=GENERATED_AT).generate(str(target))
    assert target.read_text(encoding="utf-8") == html
    assert "<title>CHoRUS Production Release V3</title>" in html


def test_generated_at_defaults_to_now(chorus):
    sheet = GenerateDatasheet(chorus)
    assert len(sheet.generated_at) == len(GENERATED_AT)
    assert sheet.source == "ro-crate-metadata.json"


# -- published crates ---------------------------------------------------------

def test_single_crate_is_published():
    page = GenerateDatasheet(crate_from(LAKEDB), generated_at=GENERATED_AT).format()
    assert not page.composition.is_release
    assert page.composition.count == 1 and not page.composition.show_index
    card = page.composition.cards[0]
    assert card.published and card.anchor == "subcrate-1"
    d = card.details
    assert (d.files, d.software, d.computations, d.with_provenance) == (2, 1, 1, 1)
    assert d.activities == 1 and d.inputs == 0
    assert [t.label for t in d.file_formats] == ["csv"]
    assert d.file_access[0].label == "Embargoed"
    assert d.computation_patterns.rows[0].inputs[0].formats == ["R", "csv"]
    assert d.computation_patterns.rows[0].outputs == []
    assert {r.kind for r in card.contents} == {"Dataset", "Software", "Computation"}
    assert "csv" in card.search
    assert [s.n for s in page.summary.stats] == ["—", "2", "1", "1"]
    assert page.summary.formats == ["csv"] and page.summary.extra == []
    assert "All datasets" not in [n.label for n in page.nav[2].children]
    assert "Datasets at a glance" not in GenerateDatasheet(crate_from(LAKEDB)).generate()


def test_release_with_subcrates_supplied():
    release = crate_from(RELEASE)
    part = "ark:59852/rocrate-paclitaxel-if-data-release"
    lake = load(LAKEDB)
    lake["@graph"][0]["about"]["@id"] = part
    lake["@graph"][1]["@id"] = part
    sub = ROCrateV1_2.model_validate(lake)

    page = GenerateDatasheet(release, [sub], generated_at=GENERATED_AT).format()
    cards = {c.meta.id: c for c in page.composition.cards}
    assert page.composition.count == 6
    assert cards[part].published and cards[part].details.files == 2
    assert sum(c.published for c in cards.values()) == 1
    # Sizes come from the release's description of each part.
    assert cards["ark:59852/rocrate-untreated-if-data-release"].size == "3.2 GB"
    assert [s.n for s in page.summary.stats] == ["19.1 TB", "2", "1", "1"]
    assert page.overview[1].id == "doi" and page.overview[1].href.startswith("https://doi.org/")
    assert page.distribution[-2].label == "DOI"
    assert page.distribution[-1].label == "Content Size"
    html = GenerateDatasheet(release, [sub], generated_at=GENERATED_AT).generate()
    assert "Datasets at a glance" in html and "Not published with this release" in html


def test_subcrate_stub_without_description():
    """A hasPart typed as a crate but with no metadata element in the graph."""
    root = root_elem(hasPart=[{
        "@id": "ark:59852/rocrate-missing",
        "@type": "https://w3id.org/EVI#ROCrate",
        "name": "Missing crate",
    }])
    page = GenerateDatasheet(crate(descriptor(root["@id"]), root)).format()
    card = page.composition.cards[0]
    assert not card.published
    assert card.meta.name == "Missing crate" and card.meta.id == "ark:59852/rocrate-missing"
    assert card.metadata_path == "ro-crate-metadata.json"
    assert page.summary.extra[0].n == "1"


def test_root_is_the_element_the_descriptor_is_about():
    other = root_elem(**{"@id": "ark:59852/rocrate-other", "name": "Other"})
    root = root_elem(hasPart=[{"@id": other["@id"]}])
    c = crate(descriptor(root["@id"]), other, root)
    assert gen._root(c).name == "Test crate"
    # Without a descriptor the first metadata element is used.
    assert gen._root(crate(other, root)).name == "Other"


def test_summary_prefers_rollups_and_truncates_formats():
    root = root_elem(**{
        "evi:datasetCount": 12, "evi:computationCount": 3, "evi:softwareCount": 2,
        "evi:totalContentSizeBytes": 3 * 1024 ** 3,
        "evi:formats": [f"fmt{i}" for i in range(10)],
        "identifier": "https://example.org/id/1",
        "contactEmail": "someone@example.org",
        "associatedPublication": ["Paper A", "https://doi.org/10.1/b"],
        "isBasedOn": ["https://example.org/upstream"],
        "dateCreated": "2024-02-02", "datePublished": None,
        "MD5": "abc123",
        "conformsTo": [{"@id": "https://w3id.org/fairscape/profile/0.1"}],
        "irb": "Reviewed by the local IRB",
        "d4d:informedConsent": [{"@id": "ark:59852/consent"}],
        "d4d:atRiskPopulations": "None involved",
    })
    page = GenerateDatasheet(crate(descriptor(root["@id"]), root)).format()
    assert [s.n for s in page.summary.stats] == ["3.0 GB", "12", "3", "2"]
    assert page.summary.entities == 17
    assert len(page.summary.formats) == 8 and page.summary.formats_more == 2
    assert not page.summary.truncated
    by_id = {r.id: r for r in page.overview}
    assert by_id["doi"].label == "Identifier" and by_id["doi"].href == "https://example.org/id/1"
    assert by_id["contact-email"].href == "mailto:someone@example.org"
    assert [e.href for e in by_id["publications"].entries] == ["", "https://doi.org/10.1/b"]
    assert by_id["based-on"].entries[0].text == "https://example.org/upstream"
    assert "release-date" not in by_id
    assert page.composition.cards[0].meta.date == "2024-02-02"
    assert page.composition.cards[0].meta.md5 == "abc123"
    assert page.badges[1].href == "https://creativecommons.org/licenses/by/4.0/"
    assert page.regulatory.irb == "Reviewed by the local IRB"
    assert page.regulatory.informed_consent == ""
    assert page.regulatory.at_risk_populations == "None involved"
    assert "License &#8599;" in GenerateDatasheet(crate(descriptor(root["@id"]), root)).generate()


def test_computation_patterns_group_cap_and_external_inputs():
    datasets = [dataset(f"ark:59852/dataset-{i}", fmt=f"f{i}") for i in range(7)]
    comps = [
        computation(f"ark:59852/computation-{i}", used=[f"ark:59852/dataset-{i}"],
                    generated=["ark:59852/dataset-6"])
        for i in range(6)
    ]
    comps.append(computation("ark:59852/computation-dup", used=["ark:59852/dataset-0"],
                             generated=["ark:59852/dataset-6"]))
    comps.append(computation("ark:59852/computation-ext",
                             used=["ark:59852/dataset-elsewhere"], generated=["ark:59852/not-here"]))
    comps.append(computation("ark:59852/computation-empty"))
    root = root_elem(hasPart=[{"@id": d["@id"]} for d in datasets])
    person = {"@id": "https://orcid.org/0000-0000-0000-0000", "@type": "Person", "name": "Someone"}
    thing = {"@id": "ark:59852/thing", "@type": "Thing", "name": "An unclassified thing"}
    page = GenerateDatasheet(crate(descriptor(root["@id"]), root, person, thing, *datasets, *comps)).format()
    d = page.composition.cards[0].details
    assert d.computations == 9 and d.files == 7 and d.other == 1
    patterns = d.computation_patterns
    assert len(patterns.rows) == 5 and patterns.more == 2
    assert patterns.rows[0].n == 2 and patterns.rows[0].inputs[0].formats == ["f0"]
    assert patterns.rows[0].outputs == ["f6"]
    external = [p for p in patterns.rows if p.inputs and p.inputs[0].formats == ["external"]]
    assert external == [] or external[0].outputs == ["unknown"]
    assert d.input_datasets[0].label == "ark:59852/dataset-elsewhere" and d.inputs == 1
    assert d.with_provenance == 0
    kinds = [r.kind for r in page.composition.cards[0].contents]
    assert kinds.count("Other") == 1 and "Person" not in kinds and len(kinds) == 17
    html = GenerateDatasheet(crate(descriptor(root["@id"]), root, person, thing, *datasets, *comps)).generate()
    assert "+2 more patterns" in html


# -- helpers ------------------------------------------------------------------

def test_href_and_mailto():
    assert gen._href("https://x.org/a") == "https://x.org/a"
    assert gen._href(" http://x.org ") == "http://x.org"
    assert gen._href("file:///x") == "" and gen._href(None) == ""
    assert gen._mailto("a@b.org") == "mailto:a@b.org"
    assert gen._mailto("Name, a@b.org") == "" and gen._mailto("") == ""


def test_text_names_and_prose():
    from fairscape_models.fairscape_base import IdentifierValue
    from fairscape_models.person import Person
    assert gen._text(None) == "" and gen._text("x") == "x" and gen._text(3) == "3"
    assert gen._text(["a", None, "b"]) == "a, b"
    assert gen._text({"name": "N"}) == "N" and gen._text({"@id": "ark:1"}) == "ark:1"
    assert gen._text(Person(**{"@id": "https://orcid.org/1", "name": "P"})) == "P"
    assert gen._text(IdentifierValue(**{"@id": "ark:59852/x", "name": "Named"})) == "Named"
    assert gen._text(IdentifierValue(**{"@id": "ark:59852/x"})) == "ark:59852/x"
    assert gen._names(None) == [] and gen._names("A") == ["A"] and gen._names(["A", "B"]) == ["A", "B"]
    assert gen._prose(["plain", "text"]) == "plain, text"
    assert gen._prose([IdentifierValue(**{"@id": "ark:59852/x"})]) == ""
    assert gen._prose([{"@id": "ark:59852/x"}]) == ""


def test_yes_no_and_lead():
    assert gen._yes_no(None) == "" and gen._yes_no(True) == "Yes" and gen._yes_no(False) == "No"
    assert gen._yes_no("Partly") == "Partly"
    assert gen._lead("  short  ") == ("short", False)
    long = "word " * 120
    text, truncated = gen._lead(long)
    assert truncated and len(text) <= gen.LEAD_LENGTH and not text.endswith(" ")
    text, truncated = gen._lead("x" * 600)
    assert truncated and len(text) == gen.LEAD_LENGTH


def test_search_kind_and_access():
    assert gen._search("Name", ["K1", "k2"], []) == "name k1 k2 "
    assert gen._search("Name", [], ["csv"]) == "name  csv"
    from fairscape_models.rocrate import GenericMetadataElem
    from fairscape_models.person import Person
    named = GenericMetadataElem.model_validate({"@id": "ark:59852/thing", "@type": "Thing", "name": "T"})
    assert gen._kind(named) == "Other"
    assert gen._kind(GenericMetadataElem.model_validate({"@id": "ark:59852/anon", "@type": "Thing"})) is None
    assert gen._kind(Person(**{"@id": "https://orcid.org/1", "name": "P"})) is None
    assert gen._access_label(named) == "Not specified"
    url = GenericMetadataElem.model_validate({"@id": "ark:59852/u", "@type": "T", "contentUrl": "https://x.org/f"})
    assert gen._access(url) == ("https://x.org/f", "https://x.org/f")
    assert gen._access_label(url) == "Available"


def test_preview_models_computed_fields():
    """The preview page models ship with the datasheet package; their
    computed fields are data-only."""
    from fairscape_models.datasheet.models import ComputationDetails, Entry, PreviewPage, RefRow, Tab
    assert not ComputationDetails().any
    assert ComputationDetails(command="run").any
    assert ComputationDetails(inputs=[RefRow(id="ark:59852/a", name="a")]).any
    tab = Tab(key="datasets", label="Datasets", entries=[Entry(id="ark:59852/a", name="a")])
    assert tab.n == 1
    page = PreviewPage(kicker="Preview", title="T", rows=[], tabs=[tab, Tab(key="x", label="X", entries=[])])
    assert page.entity_total == 1
