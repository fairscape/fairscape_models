from pydantic import Field, ConfigDict
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, COMPUTATION_TYPE
from fairscape_models.activity import Activity

class Computation(Activity):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Computation", alias="@type")
    additionalType: Optional[str] = Field(default=COMPUTATION_TYPE)
    runBy: str
    dateCreated: str
    additionalDocumentation: Optional[str] = Field(default=None)
    command: Optional[Union[List[str], str]] = Field(default=None)
    usedSoftware: Optional[List[IdentifierValue]] = Field(default=[])
    usedMLModel: Optional[List[IdentifierValue]] = Field(default=[])
    usedDataset: Optional[List[IdentifierValue]] = Field(default=[])
