#!/usr/bin/env python3
"""
Generate an RDFS/OWL profile (Turtle) from the fairscape_models Pydantic classes.

Usage:
    python scripts/generate_profile.py [output.ttl]

Writes to stdout when no output path is given.
"""

import inspect
import sys
import typing
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, get_args, get_origin

from pydantic import AliasChoices, AliasPath, BaseModel
from pydantic.fields import FieldInfo

# ── namespace registry ────────────────────────────────────────────────────────

PREFIXES: Dict[str, str] = {
    "rdf":    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs":   "http://www.w3.org/2000/01/rdf-schema#",
    "owl":    "http://www.w3.org/2002/07/owl#",
    "xsd":    "http://www.w3.org/2001/XMLSchema#",
    "evi":    "https://w3id.org/EVI#",
    "schema": "https://schema.org/",
    "prov":   "http://www.w3.org/ns/prov#",
    "rai":    "http://mlcommons.org/croissant/RAI/",
    "d4d":    "https://data-datasheet.github.io/data-datasheet#",
}

EVI_BASE = PREFIXES["evi"]

# Sorted longest-first so more specific namespaces match before shorter ones.
_REVERSE: Dict[str, str] = dict(
    sorted({v: k for k, v in PREFIXES.items()}.items(), key=lambda kv: -len(kv[0]))
)


def curie_or_uri(uri: str) -> str:
    """Return a CURIE like ``evi:Dataset`` when possible, otherwise ``<uri>``."""
    for base, prefix in _REVERSE.items():
        if uri.startswith(base):
            return f"{prefix}:{uri[len(base):]}"
    return f"<{uri}>"


def expand_curie(token: str) -> Optional[str]:
    """Expand ``prov:used`` → full URI; returns None if not a known prefix."""
    if not token or token.startswith("http") or ":" not in token:
        return None
    prefix, local = token.split(":", 1)
    ns = PREFIXES.get(prefix)
    return (ns + local) if ns else None


# ── class URI derivation ──────────────────────────────────────────────────────

def class_uri(cls: Type[BaseModel]) -> str:
    """
    Return the canonical RDF URI for a Pydantic model class.

    Takes the **last** HTTP URI found in the ``metadataType`` field default,
    which is the most specific type in lists like::

        ['prov:Entity', 'https://w3id.org/EVI#Annotation',
         'https://w3id.org/EVI#AnnotatedComputation']

    Falls back to ``evi:{ClassName}`` when no HTTP URI is present.
    """
    field = cls.model_fields.get("metadataType")
    if field is not None:
        default = field.default
        candidates = default if isinstance(default, list) else ([default] if default else [])
        http_uris = [c for c in candidates if isinstance(c, str) and c.startswith("http")]
        if http_uris:
            return http_uris[-1]
    return EVI_BASE + cls.__name__


# ── property URI derivation ───────────────────────────────────────────────────

def _alias_string(fi: FieldInfo) -> Optional[str]:
    """
    Return the single most-specific alias string for a field, or None.

    Checks ``alias`` first, then the first string in ``validation_alias``
    (which may be an ``AliasChoices``).
    """
    if fi.alias:
        return fi.alias
    va = fi.validation_alias
    if va is None:
        return None
    if isinstance(va, str):
        return va
    if isinstance(va, AliasChoices):
        for ch in va.choices:
            if isinstance(ch, str):
                return ch
            if isinstance(ch, AliasPath) and ch.path:
                first = ch.path[0]
                return first if isinstance(first, str) else None
    return None


def prop_uri(field_name: str, fi: FieldInfo) -> Optional[str]:
    """
    Return the RDF property URI for a field.

    Returns None for JSON-LD keywords (``@id``, ``@type``, ``@context``,
    ``@graph``), which are not custom properties.
    """
    alias = _alias_string(fi)
    if alias:
        if alias.startswith("@"):
            return None
        if alias.startswith("http"):
            return alias
        expanded = expand_curie(alias)
        if expanded:
            return expanded
    return EVI_BASE + field_name


# ── type → rdfs:range ─────────────────────────────────────────────────────────

def _strip_optional(tp: Any) -> Tuple[Any, bool]:
    if get_origin(tp) is Union:
        args = get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        is_opt = type(None) in args
        inner = non_none[0] if len(non_none) == 1 else Union[tuple(non_none)]
        return inner, is_opt
    return tp, False


def _strip_list(tp: Any) -> Tuple[Any, bool]:
    if get_origin(tp) is list:
        args = get_args(tp)
        return (args[0] if args else Any), True
    return tp, False


_SCALAR_MAP: Dict[Any, str] = {
    str:   "xsd:string",
    int:   "xsd:integer",
    float: "xsd:decimal",
    bool:  "xsd:boolean",
}


def range_curie(tp: Any) -> str:
    """Map a Python annotation to a Turtle range value."""
    tp, _ = _strip_optional(tp)
    tp, _ = _strip_list(tp)
    tp, _ = _strip_optional(tp)  # Optional[List[Optional[X]]]

    if tp in _SCALAR_MAP:
        return _SCALAR_MAP[tp]

    if get_origin(tp) is Union:
        # prefer a Pydantic model reference (→ object property) over literals
        for a in get_args(tp):
            a, _ = _strip_optional(a)
            if inspect.isclass(a) and issubclass(a, BaseModel):
                return curie_or_uri(class_uri(a))
        return "xsd:string"

    if inspect.isclass(tp) and issubclass(tp, BaseModel):
        return curie_or_uri(class_uri(tp))

    # Dict, Any, or other complex types
    return "rdfs:Literal"


# ── own-field filtering ───────────────────────────────────────────────────────

# Fields that are RDF keywords, Pydantic internals, or implementation artefacts
# that carry no domain-model semantics.
_SKIP = frozenset({
    "metadataType",    # serialised as @type
    "context",         # serialised as @context
    "fairscapeVersion",
    "additionalType",  # duplicates metadataType
})


def own_fields(cls: Type[BaseModel]) -> Dict[str, FieldInfo]:
    """Return fields declared directly on *cls* (not inherited from parents)."""
    own_ann = cls.__annotations__ if hasattr(cls, "__annotations__") else {}
    return {
        name: fi
        for name, fi in cls.model_fields.items()
        if name in own_ann and name not in _SKIP
    }


# ── class collection ──────────────────────────────────────────────────────────

def collect_classes() -> List[Type[BaseModel]]:
    """Import and return every Pydantic model class in fairscape_models."""
    from fairscape_models.fairscape_base import (
        IdentifierValue, IdentifierPropertyValue, Identifier,
        FairscapeBaseModel, FairscapeEVIBaseModel,
    )
    from fairscape_models.digital_object import DigitalObject
    from fairscape_models.activity import Activity
    from fairscape_models.dataset import Dataset, Split
    from fairscape_models.software import Software
    from fairscape_models.mlmodel import MLModel
    from fairscape_models.computation import Computation
    from fairscape_models.annotation import Annotation
    from fairscape_models.experiment import Experiment
    from fairscape_models.schema import Schema, Property
    from fairscape_models.biochem_entity import BioChemEntity
    from fairscape_models.medical_condition import MedicalCondition
    from fairscape_models.sample import Sample
    from fairscape_models.instrument import Instrument
    from fairscape_models.patient import Patient
    from fairscape_models.model_card import ModelCard
    from fairscape_models.annotated_computation import (
        AnnotatedComputation, CodeAnalysis, DatasetSummary,
    )
    from fairscape_models.annotated_evidence_graph import AnnotatedEvidenceGraph
    from fairscape_models.rocrate import (
        ContactPoint, PostalAddress, IRB, GenericMetadataElem,
        ROCrateMetadataElem, ROCrateMetadataFileElem,
        ROCrateDistribution, ROCrateV1_2,
    )

    ordered: List[Type[BaseModel]] = [
        # infrastructure / base hierarchy
        IdentifierValue, IdentifierPropertyValue, Identifier,
        FairscapeBaseModel, FairscapeEVIBaseModel,
        DigitalObject, Activity,
        # embedded / helper models
        Split, Property, CodeAnalysis, DatasetSummary,
        ContactPoint, PostalAddress, IRB, GenericMetadataElem,
        # concrete domain classes
        Dataset, Software, MLModel,
        Computation, Annotation, Experiment,
        Schema, BioChemEntity, MedicalCondition,
        Sample, Instrument, Patient, ModelCard,
        AnnotatedComputation, AnnotatedEvidenceGraph,
        # RO-Crate containers
        ROCrateMetadataElem, ROCrateMetadataFileElem,
        ROCrateDistribution, ROCrateV1_2,
    ]

    seen: Set[Type] = set()
    result: List[Type[BaseModel]] = []
    for c in ordered:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


# ── Turtle serialisation ──────────────────────────────────────────────────────

def _direct_parent_curies(cls: Type[BaseModel]) -> List[str]:
    """rdfs:subClassOf targets for the direct Pydantic parent classes."""
    parents = []
    for base in cls.__bases__:
        if base in (object, BaseModel):
            continue
        if inspect.isclass(base) and issubclass(base, BaseModel):
            parents.append(curie_or_uri(class_uri(base)))
    return parents


def _ttl_subject_block(subject: str, predicate_objects: List[Tuple[str, str]]) -> List[str]:
    """
    Render a Turtle subject block::

        <subject>
            pred1 obj1 ;
            pred2 obj2 .
    """
    lines = [subject]
    for i, (pred, obj) in enumerate(predicate_objects):
        sep = " ;" if i < len(predicate_objects) - 1 else " ."
        lines.append(f"    {pred} {obj}{sep}")
    return lines


def _ttl_literal(value: str) -> str:
    """Wrap *value* in triple-quoted Turtle literal to avoid escaping issues."""
    # triple-double-quote for safety; escape any internal triple-double-quotes
    safe = value.replace('"""', "'''")
    return f'"""{safe}"""'


def generate_turtle(classes: List[Type[BaseModel]]) -> str:
    out: List[str] = []

    # ── prefix declarations ──
    for pfx, ns in PREFIXES.items():
        out.append(f"@prefix {pfx}: <{ns}> .")
    out.append("")

    # ── ontology header ──
    out.extend(_ttl_subject_block(
        "<https://w3id.org/EVI>",
        [
            ("a", "owl:Ontology"),
            ("rdfs:label", '"FAIRSCAPE EVI Ontology"'),
            ("rdfs:comment", '"RDFS/OWL profile auto-generated from fairscape_models."'),
        ],
    ))
    out.append("")

    # ── pass 1: emit class declarations and accumulate property metadata ──
    #
    # property_uri → {
    #   "domains": [class_uri, ...],
    #   "ranges":  {range_curie, ...},
    #   "label":   str,
    #   "comment": str,
    #   "required_domains": [class_uri, ...],
    # }
    prop_meta: Dict[str, Dict[str, Any]] = {}

    out.append("#" + "─" * 78)
    out.append("# Classes")
    out.append("#" + "─" * 78)
    out.append("")

    for cls in classes:
        cls_u = class_uri(cls)
        cls_t = curie_or_uri(cls_u)
        parents = _direct_parent_curies(cls)

        doc = (cls.__doc__ or "").strip()
        first_line = doc.split("\n")[0].strip() if doc else ""

        pos: List[Tuple[str, str]] = [("a", "rdfs:Class, owl:Class")]
        pos.append(("rdfs:label", f'"{cls.__name__}"'))
        if first_line:
            pos.append(("rdfs:comment", _ttl_literal(first_line)))
        for p in parents:
            pos.append(("rdfs:subClassOf", p))

        out.append(f"### {cls.__name__}")
        out.extend(_ttl_subject_block(cls_t, pos))
        out.append("")

        # ── gather property data for pass 2 ──
        try:
            type_hints = typing.get_type_hints(cls)
        except Exception:
            type_hints = getattr(cls, "__annotations__", {})

        for field_name, fi in own_fields(cls).items():
            uri = prop_uri(field_name, fi)
            if uri is None:
                continue

            rng = range_curie(type_hints.get(field_name, Any))
            desc = (fi.description or "").strip().replace("\n", " ")
            required = fi.is_required()

            # Use the local name from the alias (e.g. "dataAnnotationAnalysis" from
            # "rai:dataAnnotationAnalysis") so the label matches the serialised key,
            # not the Python snake_case attribute name.
            alias = _alias_string(fi)
            if alias and not alias.startswith("@") and not alias.startswith("http") and ":" in alias:
                label = alias.split(":", 1)[1]
            else:
                label = field_name

            if uri not in prop_meta:
                prop_meta[uri] = {
                    "domains": [],
                    "ranges": set(),
                    "label": label,
                    "comment": desc,
                    "required_domains": [],
                }
            entry = prop_meta[uri]
            entry["domains"].append(cls_u)
            entry["ranges"].add(rng)
            # prefer the first non-empty description we encounter
            if not entry["comment"] and desc:
                entry["comment"] = desc
            if required:
                entry["required_domains"].append(cls_u)

    # ── pass 2: emit property declarations ──
    out.append("#" + "─" * 78)
    out.append("# Properties")
    out.append("#" + "─" * 78)
    out.append("")

    for uri in sorted(prop_meta):
        entry = prop_meta[uri]
        prop_t = curie_or_uri(uri)
        label = entry["label"]
        comment = entry["comment"]
        domains = entry["domains"]
        ranges = entry["ranges"]
        required_domains = entry["required_domains"]

        # When a property has multiple inferred ranges (e.g. Union[str, IdentifierValue]
        # resolved differently per subclass), fall back to rdfs:Literal.
        if len(ranges) == 1:
            rng_val = next(iter(ranges))
        else:
            rng_val = "rdfs:Literal"

        pos: List[Tuple[str, str]] = [("a", "rdf:Property")]
        pos.append(("rdfs:label", f'"{label}"'))
        if comment:
            pos.append(("rdfs:comment", _ttl_literal(comment)))
        for d in domains:
            pos.append(("rdfs:domain", curie_or_uri(d)))
        pos.append(("rdfs:range", rng_val))

        out.append(f"### {label}")
        out.extend(_ttl_subject_block(prop_t, pos))
        out.append("")

        # Emit owl:Restriction blank nodes for required properties.
        # These declare that every instance of the domain class must have
        # at least one value for this property.
        for d in required_domains:
            restriction = [
                ("a", "owl:Restriction"),
                ("owl:onProperty", prop_t),
                ("owl:minCardinality", '"1"^^xsd:nonNegativeInteger'),
                ("rdfs:subClassOf", curie_or_uri(d)),
            ]
            out.extend(_ttl_subject_block("[]", restriction))
            out.append("")

    return "\n".join(out) + "\n"


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    classes = collect_classes()
    ttl = generate_turtle(classes)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(ttl, encoding="utf-8")
        print(f"Wrote {len(ttl)} bytes to {out_path}", file=sys.stderr)
    else:
        sys.stdout.write(ttl)


if __name__ == "__main__":
    main()
