"""Process finished ROCrates to normalize inputs, outputs, and inverse links
for evidence graph visualization.

Three steps, each a `CrateProcessing` subclass that edits the `ROCrateV1_2`
objects it is given in place:

* `GenerateInversesWithinCrate` -- complete inverse EVI links whose two ends
  are both described in the same crate (the old CLI's `augment link-inverses`).
* `GenerateInversesBetweenCrate` -- complete inverse EVI links whose target is
  described in a *different* crate of the batch.
* `GenerateInputsOutput` -- derive `EVI:inputs` / `EVI:outputs` on each crate's
  root (the old CLI's `augment add-io`).

`GenerateIO.process_all` runs all three.

Graph entities are read and written by their JSON-LD key: a key that is a
declared field's alias (or name, when it has no alias) goes through that
field; any other key lives in the model's extras. After an entity gains a
link, its `populate_prov_fields` validator (where it has one) is re-run so
the PROV-O mirror fields stay in step.

Inverse rule (inherited from `fairscape_cli.entailments.inverse`): for every
`owl:inverseOf` pair `(p, q)` in the EVI ontology and every entity that carries
`p: {"@id": T}` where `T` is described, make sure `T` carries
`q: {"@id": <the entity>}`. Existing values are kept -- the link is appended, a
scalar becomes a list -- and nothing is ever removed. A crate that spells a
property `evi:generatedBy` gets its inverse in the same spelling.

Inputs / outputs rule (inherited from
`fairscape_cli.entailments.find_outputs.calculate_inputs_outputs`):

* **outputs** -- every dataset (or MLModel) not consumed by an activity.
* **inputs** -- every sample; every dataset an activity used that was not
  itself generated (or derived) in the crate, including ids referenced but
  absent from the graph; and every dataset neither used nor generated.

PROV-only crates (`prov:Entity` / `prov:Activity`, `prov:used`,
`prov:wasGeneratedBy`) are read through the same rules, but only where no EVI
reading applies, and the crate root is never its own output.
"""

from __future__ import annotations

from functools import lru_cache
from logging import Logger
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Type

from pydantic import BaseModel

from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.rocrate import (
    ROCrateMetadataElem,
    ROCrateMetadataFileElem,
    ROCrateV1_2,
)

EVI_NAMESPACE = "https://w3id.org/EVI#"

# ---------------------------------------------------------------------------
# Reading and writing graph entities by JSON-LD key


@lru_cache(maxsize=None)
def _field_keys(model: Type[BaseModel]) -> Dict[str, str]:
    """`{JSON-LD key: attribute name}` for a model's declared fields."""
    return {info.alias or name: name for name, info in model.model_fields.items()}


def _keys(node: BaseModel) -> List[str]:
    """Every JSON-LD key the entity carries: declared fields, then extras."""
    return list(_field_keys(type(node))) + list(node.model_extra or {})


def _get(node: BaseModel, key: str) -> Any:
    attr = _field_keys(type(node)).get(key)
    if attr is not None:
        return getattr(node, attr)
    return (node.model_extra or {}).get(key)


def _can_set(node: BaseModel, key: str) -> bool:
    return key in _field_keys(type(node)) or node.model_extra is not None


def _set(node: BaseModel, key: str, value: Any) -> None:
    attr = _field_keys(type(node)).get(key)
    if attr is not None:
        setattr(node, attr, value)
    else:
        node.model_extra[key] = value


def _delete(node: BaseModel, key: str) -> None:
    attr = _field_keys(type(node)).get(key)
    if attr is not None:
        setattr(node, attr, None)
    else:
        node.model_extra.pop(key, None)


def _guid(node: BaseModel) -> Optional[str]:
    return getattr(node, "guid", None)


def _ref(item: Any, strings: bool) -> Optional[str]:
    """The `@id` an item of a property value points at, if any."""
    if isinstance(item, BaseModel):
        ref = getattr(item, "guid", None)
    elif isinstance(item, dict):
        ref = item.get("@id")
    else:
        ref = item if strings else None
    return ref if isinstance(ref, str) and ref else None


def _items(value: Any) -> list:
    return value if isinstance(value, list) else [value]


def _link_ids(value: Any) -> List[str]:
    """The `@id`s a property value links to; bare strings are not links."""
    return [r for r in (_ref(i, strings=False) for i in _items(value)) if r]


def _ref_ids(node: BaseModel, *keys: str) -> List[str]:
    """The `@id`s the given keys point at, tolerating bare strings."""
    return [r for key in keys for i in _items(_get(node, key))
            if (r := _ref(i, strings=True))]


def _refresh_prov(node: BaseModel) -> None:
    """Re-run the EVI -> PROV-O mirroring validator after editing `node`."""
    populate = getattr(node, "populate_prov_fields", None)
    if callable(populate):
        populate()


# ---------------------------------------------------------------------------
# Inverse links

#: Every `owl:inverseOf` pair in the EVI ontology, as the bare JSON keys the
#: FAIRSCAPE context maps them to. Order within a pair is alphabetical; the
#: rule is symmetric so it does not matter which side is declared.
INVERSE_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("associateFor", "associatedWith"),
    ("challengedBy", "challenges"),
    ("containedBy", "contains"),
    ("created", "createdBy"),
    ("datasetUsedBy", "usedDataset"),
    ("derivedFrom", "derivedTo"),
    ("describedBy", "describes"),
    ("directlyChallengedBy", "directlyChallenges"),
    ("directlySupportedBy", "directlySupports"),
    ("distributedFrom", "hasDistribution"),
    ("generated", "generatedBy"),
    ("indirectlyChallengedBy", "indirectlyChallenges"),
    ("packagedBy", "packages"),
    ("representedBy", "represents"),
    ("serviceUsedBy", "usedService"),
    ("softwareUsedBy", "usedSoftware"),
    ("supportedBy", "supports"),
    ("used", "usedBy"),
)

#: `{property: its inverse}` in both directions.
INVERSE_OF: Dict[str, str] = {}
for _a, _b in INVERSE_PAIRS:
    INVERSE_OF[_a] = _b
    INVERSE_OF[_b] = _a

#: How a crate may spell an EVI property key: bare (the FAIRSCAPE context),
#: prefixed, or as the full IRI. The inverse is written in the same style.
_SPELLINGS = ("", "evi:", EVI_NAMESPACE)

#: (entity to write on, property key, id to link)
Addition = Tuple[BaseModel, str, str]


def _inverse_key(key: str) -> Optional[str]:
    """The inverse of an EVI key, in the same spelling, or None."""
    for prefix in _SPELLINGS[:0:-1]:  # full IRI, then `evi:`
        if key.startswith(prefix):
            inverse = INVERSE_OF.get(key[len(prefix):])
            return prefix + inverse if inverse else None
    if ":" in key or "/" in key:
        return None  # a prefixed key of some other vocabulary
    return INVERSE_OF.get(key)


def _inverse_links(node: BaseModel) -> Iterable[Tuple[str, str]]:
    """`(inverse key, target id)` for every EVI inverse-paired link on `node`."""
    for key in _keys(node):
        inverse_key = _inverse_key(key)
        if inverse_key is None:
            continue
        for target_id in _link_ids(_get(node, key)):
            yield inverse_key, target_id


def _index(nodes: Iterable[BaseModel]) -> Dict[str, List[BaseModel]]:
    """`{@id: [every entity with that id]}` -- an id may be described twice."""
    index: Dict[str, List[BaseModel]] = {}
    for node in nodes:
        guid = _guid(node)
        if guid:
            index.setdefault(guid, []).append(node)
    return index


def calculate_inverses(
    sources: Sequence[BaseModel], targets: Dict[str, List[BaseModel]]
) -> List[Addition]:
    """The inverse links missing from `targets` implied by links on `sources`.

    Deterministic: sources in order, their keys in declaration order, targets
    in value order. Each `(target, key, id)` appears once even when several
    declared links imply it. A link to an id `targets` does not describe is
    left alone -- there is no entity to write the inverse on.
    """
    # (target, key) -> ids it already links to or is queued to; built lazily
    # so a target with thousands of links isn't rescanned per addition.
    linked: Dict[Tuple[int, str], set] = {}
    additions: List[Addition] = []
    for node in sources:
        source_id = _guid(node)
        if not source_id:
            continue
        for inverse_key, target_id in _inverse_links(node):
            for target in targets.get(target_id, []):
                if not _can_set(target, inverse_key):
                    continue
                slot = (id(target), inverse_key)
                if slot not in linked:
                    linked[slot] = set(_link_ids(_get(target, inverse_key)))
                if source_id in linked[slot]:
                    continue
                linked[slot].add(source_id)
                additions.append((target, inverse_key, source_id))
    return additions


def _append_link(entity: BaseModel, key: str, link_id: str) -> None:
    """Add `{"@id": link_id}` under `key`, keeping whatever is there."""
    link = IdentifierValue.model_validate({"@id": link_id})
    current = _get(entity, key)
    if current is None:
        _set(entity, key, [link])
    elif isinstance(current, list):
        current.append(link)
    else:
        _set(entity, key, [current, link])


def apply_inverses(additions: Iterable[Addition]) -> None:
    """Write every addition onto its entity, then refresh PROV-O mirrors."""
    touched: Dict[int, BaseModel] = {}
    for entity, key, link_id in additions:
        _append_link(entity, key, link_id)
        touched[id(entity)] = entity
    for entity in touched.values():
        _refresh_prov(entity)


# ---------------------------------------------------------------------------
# Inputs and outputs

#: Where a crate root records what it consumed / produced, in precedence order.
INPUT_FIELDS = (f"{EVI_NAMESPACE}inputs", "EVI:inputs", "inputs")
OUTPUT_FIELDS = (f"{EVI_NAMESPACE}outputs", "EVI:outputs", "outputs")

_SAMPLE_TYPES = (f"{EVI_NAMESPACE}Sample", "EVI:Sample")
_COMPUTATION_TYPES = (f"{EVI_NAMESPACE}Computation", "EVI:Computation")

EVI_TYPES = {
    "Dataset", "Software", "MLModel", "Computation", "Annotation",
    "Experiment", "ROCrate", "CreativeWork", "Schema", "Sample",
    "Instrument", "DatasetGroup",
}

_PROV_NS = "http://www.w3.org/ns/prov#"

#: PROV type -> the EVI type it is read as, for entities carrying no EVI type.
PROV_TYPE_FALLBACK = {
    "prov:Activity": "Computation", "prov:Entity": "Dataset",
    f"{_PROV_NS}Activity": "Computation", f"{_PROV_NS}Entity": "Dataset",
}

GENERATED_BY_FIELDS = ("generatedBy", "prov:wasGeneratedBy", "wasGeneratedBy",
                       f"{_PROV_NS}wasGeneratedBy")
DERIVED_FROM_FIELDS = ("derivedFrom", "prov:wasDerivedFrom", "wasDerivedFrom",
                       f"{_PROV_NS}wasDerivedFrom")
#: PROV's untyped consumption edge, read only when `usedDataset` is empty.
PROV_USED_FIELDS = ("prov:used", "used", f"{_PROV_NS}used")


def _raw_types(node: BaseModel) -> List[str]:
    raw = _get(node, "@type") or []
    return [raw] if isinstance(raw, str) else [str(t) for t in raw]


def _evi_type(node: BaseModel) -> Optional[str]:
    """The entity's primary EVI type, falling back to the PROV reading."""
    shorts = []
    for t in _raw_types(node):
        short = t.split("#")[-1] if "#" in t else t.split(":")[-1]
        if short in EVI_TYPES:
            shorts.append(short)
    if not shorts:
        for raw in _raw_types(node):
            if raw in PROV_TYPE_FALLBACK:
                return PROV_TYPE_FALLBACK[raw]
        return None
    for preferred in ("ROCrate", "Computation", "Software", "MLModel",
                      "Experiment", "Annotation", "Schema"):
        if preferred in shorts:
            return preferred
    return shorts[0]


def _last_type(node: BaseModel) -> str:
    """The single `@type` string the original rules are applied to."""
    types = _raw_types(node)
    return types[-1] if types else ""


def crate_root(crate: ROCrateV1_2) -> Optional[BaseModel]:
    """The crate root: what the metadata descriptor is `about`, else the
    first `ROCrateMetadataElem`."""
    graph = crate.metadataGraph
    for node in graph:
        if isinstance(node, ROCrateMetadataFileElem):
            for candidate in graph:
                if _guid(candidate) == node.about.guid:
                    return candidate
    for node in graph:
        if isinstance(node, ROCrateMetadataElem):
            return node
    return None


def _dedupe(refs: Sequence[IdentifierValue]) -> List[IdentifierValue]:
    seen, out = set(), []
    for ref in refs:
        if ref.guid not in seen:
            seen.add(ref.guid)
            out.append(ref)
    return out


def _ids_to_refs(ids: Iterable[str]) -> List[IdentifierValue]:
    return [IdentifierValue.model_validate({"@id": i}) for i in ids]


def calculate_inputs_outputs(
    crate: ROCrateV1_2,
) -> Tuple[List[IdentifierValue], List[IdentifierValue]]:
    """Return `(inputs, outputs)` for a crate."""
    # dataset id -> did it come from something in the crate
    datasets: Dict[str, bool] = {}
    order: List[str] = []
    samples: List[str] = []
    used: set = set()

    root = crate_root(crate)
    root_id = _guid(root) if root is not None else None

    for node in crate.metadataGraph:
        etype = _last_type(node)
        node_id = _guid(node)
        kind = _evi_type(node)

        # Substring match on the last type is load-bearing: a root typed
        # `[..., "ROCrate"]` must not be collected as a dataset.
        if node_id and node_id != root_id and (
                "Dataset" in etype or kind in ("Dataset", "MLModel")):
            if node_id not in datasets:
                order.append(node_id)
            derived = _ref_ids(node, *DERIVED_FROM_FIELDS)
            datasets[node_id] = bool(_ref_ids(node, *GENERATED_BY_FIELDS) or derived)
            used.update(derived)

        if etype in _SAMPLE_TYPES and node_id:
            samples.append(node_id)

        if etype in _COMPUTATION_TYPES or kind in ("Computation", "Annotation", "Experiment"):
            used.update(_ref_ids(node, "usedDataset") or _ref_ids(node, *PROV_USED_FIELDS))
            used.update(_ref_ids(node, "usedMLModel"))

    input_ids: List[str] = list(samples)
    # Sorted so re-running never reorders the persisted list. Used and not
    # produced in this crate (or not in it at all) -> input.
    input_ids.extend(u for u in sorted(used) if datasets.get(u, False) is False)

    output_ids: List[str] = []
    for dataset_id in order:
        if dataset_id not in used:
            output_ids.append(dataset_id)
            if not datasets[dataset_id]:
                input_ids.append(dataset_id)

    return _dedupe(_ids_to_refs(input_ids)), _dedupe(_ids_to_refs(output_ids))


def _replace(root: BaseModel, spellings: Sequence[str], value: list) -> None:
    """Set one key under a single spelling: the one the root already used,
    else the full IRI. Every other spelling is dropped."""
    present = [key for key in spellings if _get(root, key) is not None]
    keep = present[0] if present else spellings[0]
    for key in present[1:]:
        _delete(root, key)
    _set(root, keep, value)


# ---------------------------------------------------------------------------
# Processing steps


class CrateProcessing:
    def __init__(
        self,
        crates: List[ROCrateV1_2],
        logger: Optional[Logger] = None,
    ):
        self.crates = crates
        self.logger = logger

    def _log(self, message: str) -> None:
        if self.logger is not None:
            self.logger.info(message)


class GenerateInputsOutput(CrateProcessing):
    def process(self) -> None:
        """Set `EVI:inputs` / `EVI:outputs` on the root of every crate."""
        for crate in self.crates:
            root = crate_root(crate)
            if root is None:
                self._log("Skipping inputs/outputs: crate has no root entity")
                continue
            inputs, outputs = calculate_inputs_outputs(crate)
            _replace(root, INPUT_FIELDS, inputs)
            _replace(root, OUTPUT_FIELDS, outputs)
            self._log(f"Added {len(inputs)} inputs and {len(outputs)} outputs "
                      f"to {_guid(root)}")


class GenerateInversesWithinCrate(CrateProcessing):
    def process(self) -> None:
        """Within every crate, add inverse links whose target is in the same crate."""
        for crate in self.crates:
            graph = crate.metadataGraph
            additions = calculate_inverses(graph, _index(graph))
            apply_inverses(additions)
            if additions:
                self._log(f"Added {len(additions)} inverse link(s) within crate")


class GenerateInversesBetweenCrate(CrateProcessing):
    def process(self) -> None:
        """Add inverse links whose target is described in another crate."""
        for i, crate in enumerate(self.crates):
            others = _index(
                node for j, other in enumerate(self.crates) if j != i
                for node in other.metadataGraph
            )
            additions = calculate_inverses(crate.metadataGraph, others)
            apply_inverses(additions)
            if additions:
                self._log(f"Added {len(additions)} inverse link(s) from crate {i} "
                          f"into other crates")


class GenerateIO(CrateProcessing):
    def process_all(self) -> None:
        # Inverses first: inputs/outputs read `generatedBy` and `usedDataset`,
        # which a crate may only have recorded as `generated` / `datasetUsedBy`.
        GenerateInversesWithinCrate(self.crates, self.logger).process()
        GenerateInversesBetweenCrate(self.crates, self.logger).process()
        GenerateInputsOutput(self.crates, self.logger).process()
