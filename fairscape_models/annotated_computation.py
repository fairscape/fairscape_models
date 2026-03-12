from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, ANNOTATED_COMPUTATION_TYPE
from fairscape_models.digital_object import DigitalObject


class CodeAnalysis(BaseModel):
    """Analysis of a software entity used in the computation."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    software: IdentifierValue
    name: Optional[str] = Field(default=None)
    summary: str
    keyFunctions: Optional[List[str]] = Field(default=None)
    concerns: Optional[List[str]] = Field(default=None)


class DatasetSummary(BaseModel):
    """Summary of a dataset's role in the computation."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    dataset: IdentifierValue
    name: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


class AnnotatedComputation(DigitalObject):
    """LLM-generated annotation of a single evi:Computation step.

    A DigitalObject (Document) that annotates an evi:Computation.
    The original Computation stays in the graph in its original form;
    this annotation points to it via evi:annotates.
    """
    metadataType: Optional[Union[List[str], str]] = Field(
        default=[
            'prov:Entity',
            "https://w3id.org/EVI#Annotation",
            "https://w3id.org/EVI#AnnotatedComputation",
        ],
        alias="@type",
    )
    additionalType: Optional[str] = Field(default=ANNOTATED_COMPUTATION_TYPE)

    # Points to the original Computation this annotates
    annotates: IdentifierValue = Field(..., alias="evi:annotates")

    # LLM-generated content
    stepSummary: str = Field(..., alias="evi:stepSummary")
    codeAnalysis: Optional[List[CodeAnalysis]] = Field(default=[], alias="evi:codeAnalysis")
    inputSummaries: Optional[List[DatasetSummary]] = Field(default=[], alias="evi:inputSummaries")
    outputSummaries: Optional[List[DatasetSummary]] = Field(default=[], alias="evi:outputSummaries")
    concerns: Optional[List[str]] = Field(default=[], alias="evi:concerns")

    # Provenance of the annotation itself
    llmModel: str = Field(alias="evi:llmModel")
    llmTemperature: Optional[float] = Field(default=None, alias="evi:llmTemperature")
    dateCreated: str
    interpreterVersion: Optional[str] = Field(default=None, alias="evi:interpreterVersion")

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields."""
        # prov:wasDerivedFrom -> the computation being annotated
        self.wasDerivedFrom = [self.annotates]

        # prov:wasAttributedTo -> the LLM model
        self.wasAttributedTo = [self.llmModel]

        return self
