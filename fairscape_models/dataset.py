from pydantic import BaseModel, Field, ConfigDict, AliasChoices, model_validator
from typing import Optional, List, Union
from enum import Enum

from fairscape_models.fairscape_base import IdentifierValue, DATASET_TYPE
from fairscape_models.digital_object import DigitalObject


class SplitType(str, Enum):
    """Croissant-aligned split type semantics.

    Maps to:
      cr:TrainingSplit   -> "train"
      cr:ValidationSplit -> "validation"
      cr:TestSplit       -> "test"
      custom             -> "other"
    """
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
    OTHER = "other"


class Split(BaseModel):
    """A named partition or subset of a Dataset.

    Unifies concepts from D4D DataSubset/SamplingStrategy and Croissant cr:Split.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Identity 
    name: str
    description: Optional[str] = Field(default=None)

    # Croissant split semantics (maps to cr:TrainingSplit, etc.)
    splitType: Optional[SplitType] = Field(default=None)

    # Query information SQL or croissant extract transform
    query: Optional[str] = Field(default=None)
    queryType: Optional[str] = Field(default=None)

    sourceDatasets: Optional[List[IdentifierValue]] = Field(default=None)

    # D4D sampling strategy (flat, all optional)
    isSample: Optional[bool] = Field(default=None)
    isRandom: Optional[bool] = Field(default=None)
    samplingStrategy: Optional[str] = Field(default=None)

class Dataset(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#Dataset"], alias="@type")
    additionalType: Optional[str] = Field(default=DATASET_TYPE)
    datePublished: str = Field(...)
    keywords: List[str] = Field(...)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[IdentifierValue] = Field(
        validation_alias=AliasChoices('evi:Schema', 'EVI:Schema', 'schema', 'evi:schema'),
        serialization_alias='evi:Schema',
        default=None
    )
    generatedBy: Optional[Union[IdentifierValue, List[IdentifierValue]]] = Field(default=[])
    derivedFrom: Optional[List[IdentifierValue]] = Field(default=[])
    splits: Optional[List[Split]] = Field(default=None)

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""
        # Map generatedBy → prov:wasGeneratedBy
        if self.generatedBy:
            if isinstance(self.generatedBy, list):
                self.wasGeneratedBy = self.generatedBy
            else:
                self.wasGeneratedBy = [self.generatedBy]
        else:
            self.wasGeneratedBy = []

        # Map derivedFrom → prov:wasDerivedFrom
        self.wasDerivedFrom = self.derivedFrom or []

        # Map author
        if self.author:
            if isinstance(self.author, str):
                self.wasAttributedTo = [self.author]
            elif isinstance(self.author, list):
                self.wasAttributedTo = [a for a in self.author]
        else:
            self.wasAttributedTo = []

        return self