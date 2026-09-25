"""Unit and anatomy ontology crosswalks. Stdlib only, always runs."""

from fairscape_models.schema.ontology import anatomy_terms, unit_terms


def test_unit_terms_known_and_unknown():
    ucum, qudt = unit_terms("mV")
    assert ucum == "mV"
    assert qudt == "http://qudt.org/vocab/unit/MilliV"
    assert unit_terms("notaunit") == ("notaunit", None)
    assert unit_terms(None) == (None, None)


def test_anatomy_terms_crosswalk():
    label, url = anatomy_terms("CHEST")
    assert url and url.startswith("http://snomed.info/id/")
    assert anatomy_terms("madeuppart") == ("madeuppart", None)
