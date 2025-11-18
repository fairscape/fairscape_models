from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from fairscape_models.fairscape_base import IdentifierValue


class ModelCard(BaseModel):
    """Model Card for ML models as RO-Crate Dataset elements"""
    
    model_config = ConfigDict(extra="allow")
    
    guid: str = Field(alias="@id")
    metadataType: Union[str, List[str]] = Field(alias="@type",default="EVI:MLModel")
    name: str
    description: str
    author: Union[str, List[str]]
    keywords: List[str]
    version: str
    
    modelType: Optional[Union[str, List[str]]]
    framework: Optional[Union[str, List[str]]]
    modelFormat: Optional[Union[str, List[str]]]
    trainingDataset: Optional[Union[str, List[IdentifierValue]]]
    generatedBy: Optional[IdentifierValue]
    
    parameters: Optional[float] = Field(default=None)
    inputSize: Optional[str] = Field(default=None)
    hasBias: Optional[str] = Field(default=None)
    intendedUseCase: Optional[str] = Field(default=None)
    usageInformation: Optional[str] = Field(default=None)
    
    baseModel: Optional[str] = Field(default=None)
    associatedPublication: Optional[Union[str, List[str]]] = Field(default=None)
    contentUrl: Union[str, List[str]] = Field(default=None)
    url: Optional[str] = Field(default=None)
    dataLicense: Optional[str] = Field(alias="license", default=None)
    citation: Optional[str] = Field(default=None)

    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
