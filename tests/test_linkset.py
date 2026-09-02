"""Tests for RO-Crate -> RFC 9264 linkset conversion."""

import json
import pathlib

import pytest

from fairscape_models.conversion.mapping.linkset import rocrate_to_linkset
from fairscape_models.conversion.models.linkset import LINKSET_MEDIA_TYPE, Linkset
from fairscape_models.rocrate import ROCrateV1_2

TEST_ROCRATES_PATH = pathlib.Path(__file__).parent / "test_rocrates"

ANCHOR = "https://fairscape.net/view/ark:59852/test"
CITE_AS = "https://fairscape.net/ark:59852/test"
DESCRIBEDBY = "https://fairscape.net/api/rocrate/ark:59852/test"


def _context(crate, **kwargs):
    """Convert and return the single anchored link context as plain JSON."""
    linkset = rocrate_to_linkset(crate, anchor=ANCHOR, **kwargs)
    payload = linkset.to_json()
    assert list(payload.keys()) == ["linkset"]
    assert len(payload["linkset"]) == 1
    return payload["linkset"][0]


def _load(name: str) -> ROCrateV1_2:
    with open(TEST_ROCRATES_PATH / name / "ro-crate-metadata.json") as f:
        return ROCrateV1_2(**json.load(f))


def _crate(graph_extra, root_extra=None):
    """Build a minimal valid crate around the given parts."""
    root = {
        "@id": "ark:59852/test",
        "@type": ["Dataset", "https://w3id.org/EVI#ROCrate"],
        "name": "Test crate",
        "description": "A crate for linkset tests.",
        "keywords": ["test"],
        "version": "1.0",
        "author": "Plain Name",
        # `license` is required on the root element; tests that care override it.
        "license": "Not a URI",
        "hasPart": [{"@id": e["@id"]} for e in graph_extra],
    }
    root.update(root_extra or {})
    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
            "about": {"@id": "ark:59852/test"},
        },
        root,
        *graph_extra,
    ]
    return ROCrateV1_2(**{"@context": {"@vocab": "https://schema.org/"}, "@graph": graph})


def _dataset(guid, content_url, fmt="csv", name="A file"):
    return {
        "@id": guid,
        "@type": ["prov:Entity", "https://w3id.org/EVI#Dataset"],
        "name": name,
        "description": "A file used in linkset conversion tests.",
        "keywords": ["test"],
        "author": "Test Author",
        "datePublished": "2026-01-01",
        "version": "1.0",
        "format": fmt,
        "contentUrl": content_url,
    }


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------


def test_linkset_serializes_relation_names_as_keys():
    """cite-as must serialize hyphenated, and empty relations must be absent."""
    crate = _crate([_dataset("ark:59852/d1", "https://example.org/a.csv")])
    ctx = _context(crate, cite_as=CITE_AS, describedby_url=DESCRIBEDBY)

    assert ctx["anchor"] == ANCHOR
    assert ctx["cite-as"] == [{"href": CITE_AS}]
    assert "citeAs" not in ctx
    # Nothing in the crate populates `collection`, so the key must not appear.
    assert "collection" not in ctx


def test_media_type_constant():
    assert LINKSET_MEDIA_TYPE == "application/linkset+json"


def test_empty_graph_still_yields_anchored_context():
    crate = ROCrateV1_2(
        **{
            "@context": {"@vocab": "https://schema.org/"},
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
                    "about": {"@id": "ark:59852/missing"},
                }
            ],
        }
    )
    ctx = _context(crate)
    assert ctx["anchor"] == ANCHOR


# --------------------------------------------------------------------------
# item links
# --------------------------------------------------------------------------


def test_item_links_carry_href_and_media_type():
    crate = _crate(
        [
            _dataset("ark:59852/d1", "https://example.org/a.csv", "csv", "A"),
            _dataset("ark:59852/d2", "https://example.org/b.parquet", "parquet", "B"),
        ]
    )
    items = _context(crate)["item"]
    assert {i["href"] for i in items} == {
        "https://example.org/a.csv",
        "https://example.org/b.parquet",
    }
    by_href = {i["href"]: i for i in items}
    assert by_href["https://example.org/a.csv"]["type"] == "text/csv"
    assert by_href["https://example.org/b.parquet"]["type"] == "application/x-parquet"


def test_embargoed_content_is_not_advertised():
    """An `item` link to embargoed bytes would promise access we don't grant."""
    crate = _crate(
        [
            _dataset("ark:59852/d1", "Embargoed"),
            _dataset("ark:59852/d2", "embargoed"),
            _dataset("ark:59852/d3", "https://example.org/open.csv"),
        ]
    )
    items = _context(crate)["item"]
    assert [i["href"] for i in items] == ["https://example.org/open.csv"]


def test_non_dereferenceable_urls_are_skipped():
    crate = _crate(
        [
            _dataset("ark:59852/d1", "file:///local/path.csv"),
            _dataset("ark:59852/d2", "relative/path.csv"),
            _dataset("ark:59852/d3", "https://example.org/real.csv"),
        ]
    )
    assert [i["href"] for i in _context(crate)["item"]] == ["https://example.org/real.csv"]


def test_items_are_deduped_by_url():
    crate = _crate(
        [
            _dataset("ark:59852/d1", "https://example.org/same.csv"),
            _dataset("ark:59852/d2", "https://example.org/same.csv"),
        ]
    )
    assert len(_context(crate)["item"]) == 1


def test_max_items_caps_output():
    parts = [_dataset(f"ark:59852/d{i}", f"https://example.org/{i}.csv") for i in range(10)]
    assert len(_context(_crate(parts), max_items=4)["item"]) == 4
    assert len(_context(_crate(parts))["item"]) == 10


def test_haspart_refs_missing_from_graph_are_skipped():
    """Release crates reference parts that live in sub-crates."""
    crate = _crate([_dataset("ark:59852/d1", "https://example.org/a.csv")])
    crate.metadataGraph[1].hasPart.append(
        type(crate.metadataGraph[1].hasPart[0])(**{"@id": "ark:59852/elsewhere"})
    )
    assert len(_context(crate)["item"]) == 1


# --------------------------------------------------------------------------
# media types
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fmt,url,expected",
    [
        ("image/jpeg", "https://example.org/a.jpg", "image/jpeg"),  # already a media type
        ("csv", "https://example.org/a.csv", "text/csv"),
        (".parquet", "https://example.org/a.parquet", "application/x-parquet"),
        ("jpg", "https://example.org/a.bin", "image/jpeg"),  # via mimetypes
        (None, "https://example.org/a.png", "image/png"),  # from the URL
    ],
)
def test_media_type_resolution(fmt, url, expected):
    entity = _dataset("ark:59852/d1", url, fmt)
    if fmt is None:
        # Dataset and Software both require `format`; a generic entity may omit it.
        del entity["format"]
        entity["@type"] = "MediaObject"
    assert _context(_crate([entity]))["item"][0]["type"] == expected


def test_unknown_format_omits_media_type_rather_than_guessing():
    entity = _dataset("ark:59852/d1", "https://example.org/a.xyzzy", "xyzzy")
    assert "type" not in _context(_crate([entity]))["item"][0]


# --------------------------------------------------------------------------
# authors, license, cite-as, describedby
# --------------------------------------------------------------------------


def test_authors_resolved_from_person_entities_with_orcid():
    person = {
        "@id": "ark:59852/person-1",
        "@type": "Person",
        "name": "Jane Doe",
        "identifier": "https://orcid.org/0000-0002-1825-0097",
    }
    crate = _crate([person], root_extra={"author": [{"@id": "ark:59852/person-1"}]})
    authors = _context(crate)["author"]
    assert authors == [{"href": "https://orcid.org/0000-0002-1825-0097", "title": "Jane Doe"}]


def test_plain_string_authors_are_not_signposted():
    """A name is not a URI; partial author coverage is the honest outcome."""
    crate = _crate(
        [_dataset("ark:59852/d1", "https://example.org/a.csv")],
        root_extra={"author": ["Clark T", "Parker J"]},
    )
    assert "author" not in _context(crate)


def test_authors_deduped_across_author_and_pi():
    person = {
        "@id": "ark:59852/person-1",
        "@type": "Person",
        "name": "Jane Doe",
        "identifier": "https://orcid.org/0000-0002-1825-0097",
    }
    crate = _crate(
        [person],
        root_extra={
            "author": [{"@id": "ark:59852/person-1"}],
            "principalInvestigator": {"@id": "ark:59852/person-1"},
        },
    )
    assert len(_context(crate)["author"]) == 1


def test_license_only_when_uri():
    uri = _crate([], root_extra={"license": "https://spdx.org/licenses/Apache-2.0"})
    assert _context(uri)["license"] == [{"href": "https://spdx.org/licenses/Apache-2.0"}]

    text = _crate([], root_extra={"license": "Apache 2.0, see LICENSE.txt"})
    assert "license" not in _context(text)


def test_cite_as_prefers_caller_then_doi():
    crate = _crate([], root_extra={"identifier": "https://doi.org/10.1234/abc"})
    assert _context(crate, cite_as=CITE_AS)["cite-as"] == [{"href": CITE_AS}]
    # Without a caller-supplied PID, an http identifier (DOI) is used.
    assert _context(crate)["cite-as"] == [{"href": "https://doi.org/10.1234/abc"}]


def test_bare_ark_is_not_used_as_cite_as():
    """`ark:59852/x` is not dereferenceable, so it must not be advertised."""
    assert "cite-as" not in _context(_crate([]))


def test_describedby_carries_type_and_profile():
    crate = _crate([], root_extra={"conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"}})
    assert _context(crate, describedby_url=DESCRIBEDBY)["describedby"] == [
        {
            "href": DESCRIBEDBY,
            "type": "application/ld+json",
            "profile": "https://w3id.org/ro/crate/1.2",
        }
    ]


def test_type_relation_marks_dataset_and_landing_page():
    hrefs = [t["href"] for t in _context(_crate([]))["type"]]
    assert hrefs == ["https://schema.org/Dataset", "https://schema.org/AboutPage"]


def test_nested_linksets_for_subcrates():
    subs = ["https://fairscape.net/api/rocrate/linkset/ark:59852/sub1"]
    assert _context(_crate([]), extra_linksets=subs)["linkset"] == [
        {"href": subs[0], "type": "application/linkset+json"}
    ]


# --------------------------------------------------------------------------
# Real crates
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["LakeDB", "images", "release"])
def test_real_crates_convert_and_validate(name):
    ctx = _context(_load(name), cite_as=CITE_AS, describedby_url=DESCRIBEDBY)
    assert ctx["anchor"] == ANCHOR
    assert ctx["cite-as"] == [{"href": CITE_AS}]
    # Round-trips through the model.
    assert Linkset(**{"linkset": [ctx]}).to_json()["linkset"][0]["anchor"] == ANCHOR


def test_fully_embargoed_crate_yields_no_item_links():
    """Every part of the LakeDB fixture is embargoed."""
    assert "item" not in _context(_load("LakeDB"))


def test_images_crate_media_type_is_not_mislabeled():
    """format 'image/jpeg' must survive, not degrade to text/plain."""
    items = _context(_load("images"))["item"]
    assert all(i["type"] == "image/jpeg" for i in items)
