from pydantic import Field, ConfigDict
from typing import Optional, List, Union

from fairscape_models.fairscape_base import IdentifierValue, MLMODEL_TYPE
from fairscape_models.digital_object import DigitalObject

class MLModel(DigitalObject):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#MLModel", alias="@type")
    additionalType: Optional[str] = Field(default=MLMODEL_TYPE)
    dateModified: Optional[str] = Field(default=None)
    fileFormat: str = Field(alias="format")
    modelTask: Optional[str] = Field(default=None)
    modelArchitecture: Optional[str] = Field(default=None)
    trainedOn: Optional[List[IdentifierValue]] = Field(default=[])
