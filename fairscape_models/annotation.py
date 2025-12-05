from pydantic import Field, ConfigDict
from typing import Optional, List

from fairscape_models.fairscape_base import IdentifierValue, ANNOTATION_TYPE
from fairscape_models.activity import Activity

class Annotation(Activity):
    metadataType: Optional[str] = Field(default="https://w3id.org/EVI#Annotation", alias="@type")
    additionalType: Optional[str] = Field(default=ANNOTATION_TYPE)
    createdBy: str
    dateCreated: str
    usedDataset: Optional[List[IdentifierValue]] = Field(default=[])
