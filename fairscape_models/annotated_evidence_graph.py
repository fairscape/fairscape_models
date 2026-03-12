from pydantic import Field, model_validator
from typing import Optional, List, Union, Dict, Any

from fairscape_models.fairscape_base import IdentifierValue, ANNOTATED_EVIDENCE_GRAPH_TYPE
from fairscape_models.digital_object import DigitalObject


class AnnotatedEvidenceGraph(DigitalObject):
    """Full annotated condensed evidence graph -- the graph-level LLM output.

    Contains all original crate entities plus AnnotatedComputation nodes
    in a flat dict keyed by @id. Computation nodes are replaced by their
    annotated supersets. DAG is reconstructable from cross-references
    (generatedBy, usedDataset, evi:annotates, etc.).
    """
    metadataType: Optional[Union[List[str], str]] = Field(
        default=[
            'prov:Entity',
            "https://w3id.org/EVI#EvidenceGraph",
            "https://w3id.org/EVI#AnnotatedEvidenceGraph",
        ],
        alias="@type",
    )
    additionalType: Optional[str] = Field(default=ANNOTATED_EVIDENCE_GRAPH_TYPE)

    # Reference to the original evidence graph or RO-Crate root
    annotates: IdentifierValue = Field(..., alias="evi:annotates")

    # Flat entity lookup -- all entities keyed by ARK @id
    graph: Dict[str, Any] = Field(..., alias="@graph")

    # Graph-level LLM outputs
    executiveSummary: str = Field(..., alias="evi:executiveSummary")
    narrativeSummary: str = Field(..., alias="evi:narrativeSummary")
    keyFindings: Optional[List[str]] = Field(default=[], alias="evi:keyFindings")
    concerns: Optional[List[str]] = Field(default=[], alias="evi:concerns")

    # Quick index of all AnnotatedComputation @ids in the graph
    stepAnnotations: Optional[List[IdentifierValue]] = Field(default=[], alias="evi:stepAnnotations")

    # Provenance of the graph-level analysis
    llmModel: str = Field(alias="evi:llmModel")
    llmTemperature: Optional[float] = Field(default=None, alias="evi:llmTemperature")
    dateCreated: str
    interpreterVersion: Optional[str] = Field(default=None, alias="evi:interpreterVersion")

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields."""
        # prov:wasDerivedFrom -> the original evidence graph
        self.wasDerivedFrom = [self.annotates]

        # prov:wasAttributedTo -> the LLM
        self.wasAttributedTo = [self.llmModel]

        return self
