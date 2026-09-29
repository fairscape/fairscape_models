"""
shacl.py — validate an RO-Crate against the FAIRSCAPE profile's SHACL shapes.

The shapes add graph rules the Pydantic models can't express on their own, e.g.
`generatedBy` must point at a Computation/Experiment/Activity, ark: references
must resolve, and every Dataset names an author. The bundled copy lives in
`shapes/fairscape-shapes.ttl`; the published source is the profile repository.

Needs the optional `shacl` extra:

    pip install 'fairscape-models[shacl]'

`rdflib` and `pyshacl` are imported inside `validate_shacl()`, so importing this
module never requires them. A missing `pyshacl` raises ImportError at call time.
"""

import json
import pathlib
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

try:
    # importlib.resources.files() is Python 3.9+
    from importlib.resources import files as _resource_files
except ImportError:
    # Python 3.8 falls back to the importlib_resources backport
    from importlib_resources import files as _resource_files

__all__ = [
    "SHAPES_VERSION",
    "SHAPES_URI",
    "ShaclResult",
    "ShaclReport",
    "default_shapes_path",
    "resolve_metadata_path",
    "validate_shacl",
]

SHAPES_VERSION = "0.2"
SHAPES_URI = f"https://fairscape.github.io/profile/{SHAPES_VERSION}/fairscape-shapes.ttl"

_SHACL_NS = "http://www.w3.org/ns/shacl#"


class ShaclResult(BaseModel):
    severity: str          # "Violation", "Warning" or "Info"
    shape: str             # owning NodeShape, e.g. "DatasetAuthorShape"
    message: str
    focusNode: Optional[str] = None
    path: Optional[str] = None


class ShaclReport(BaseModel):
    """Outcome of a SHACL run.

    `passes` is True iff there are no sh:Violation results. pyshacl's own
    `conforms` is False on any result, but the profile uses sh:Warning for
    advisory findings (dangling refs, malformed ARKs) that must not fail an
    otherwise valid crate.
    """
    passes: bool
    violations: int
    warnings: int
    results: List[ShaclResult]
    text: str


def default_shapes_path() -> pathlib.Path:
    """Path to the bundled FAIRSCAPE shapes (profile `SHAPES_VERSION`)."""
    return pathlib.Path(str(_resource_files("fairscape_models.validation") / "shapes" / "fairscape-shapes.ttl"))


def resolve_metadata_path(crate_path: Union[str, pathlib.Path]) -> pathlib.Path:
    """Resolve a crate directory or metadata file path to its ro-crate-metadata.json."""
    crate_path = pathlib.Path(crate_path)
    if crate_path.name.endswith(".json"):
        return crate_path
    return crate_path / "ro-crate-metadata.json"


def _load_crate(crate: Any) -> Dict[str, Any]:
    if isinstance(crate, dict):
        return crate
    if isinstance(crate, BaseModel):
        return crate.model_dump(by_alias=True, exclude_none=True, mode="json")
    metadata_path = resolve_metadata_path(crate)
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def validate_shacl(
    crate: Union[str, pathlib.Path, Dict[str, Any], BaseModel],
    shapes: Optional[Union[str, pathlib.Path]] = None,
) -> ShaclReport:
    """Validate a crate's JSON-LD against the SHACL shapes.

    `crate` is a crate directory, a path to its metadata file, the parsed
    JSON-LD dict, or an `ROCrateV1_2` instance. `shapes` defaults to the bundled
    FAIRSCAPE shapes.

    Raises ImportError if the optional `pyshacl` (or `rdflib`) isn't installed,
    FileNotFoundError / json.JSONDecodeError for a missing or malformed file.
    """
    import rdflib
    from pyshacl import validate as pyshacl_validate

    data = _load_crate(crate)
    data_graph = rdflib.Graph()
    data_graph.parse(data=json.dumps(data), format="json-ld")

    shapes_graph = rdflib.Graph().parse(str(shapes or default_shapes_path()), format="turtle")

    _conforms, results_graph, results_text = pyshacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="none",          # parity with Pydantic: no RDFS/OWL entailment
        advanced=True,             # required for the SPARQL-based custom rules
        meta_shacl=False,
        debug=False,
    )

    sh = rdflib.Namespace(_SHACL_NS)

    def _local(term):
        return str(term).split("#")[-1] if term is not None else None

    results = []
    for r in results_graph.subjects(rdflib.RDF.type, sh.ValidationResult):
        shape = results_graph.value(r, sh.sourceShape)
        # A sh:property constraint reports the inner (blank) property shape as its
        # sourceShape; resolve it back to the owning named NodeShape so the label
        # is readable. sh:sparql constraints already report the NodeShape.
        if shape is not None:
            parent = shapes_graph.value(predicate=sh.property, object=shape)
            if parent is not None:
                shape = parent
        focus = results_graph.value(r, sh.focusNode)
        path = results_graph.value(r, sh.resultPath)
        msg = results_graph.value(r, sh.resultMessage)
        results.append(ShaclResult(
            severity=_local(results_graph.value(r, sh.resultSeverity)) or "?",
            shape=_local(shape) or "?",
            message=str(msg) if msg is not None else "",
            focusNode=str(focus) if focus is not None else None,
            path=str(path) if isinstance(path, rdflib.URIRef) else None,
        ))

    violations = sum(1 for r in results if r.severity == "Violation")
    warnings = sum(1 for r in results if r.severity == "Warning")
    return ShaclReport(
        passes=violations == 0,
        violations=violations,
        warnings=warnings,
        results=results,
        text=results_text,
    )
