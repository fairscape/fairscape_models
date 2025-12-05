from pydantic import (
    BaseModel, 
    ConfigDict,
    Field,
    BeforeValidator
)
from pydantic.networks import AnyUrl
from typing import (
    List,
    Optional,
    Dict,
    Union
)
from typing_extensions import Annotated
from enum import Enum


IdentifierPattern = "^ark:[0-9]{5}\\/[a-zA-Z0-9_\\-]*.$"

DATASET_TYPE = "Dataset"
DATASET_CONTAINER_TYPE = "DatasetContainer"
SOFTWARE_TYPE = "Software"
MLMODEL_TYPE = "MLModel"
COMPUTATION_TYPE = "Computation"
ANNOTATION_TYPE = "Annotation"
ROCRATE_TYPE = "ROCrate"

# TODO get from config
DEFAULT_ARK_NAAN = "59853"
DEFAULT_LICENSE = "https://creativecommons.org/licenses/by/4.0/"
defaultContext = {
    "@vocab": "https://schema.org/",
    "evi": "https://w3id.org/EVI#",
    "rai": "http://mlcommons.org/croissant/RAI/",

    # TODO fully specify default context
    "usedSoftware": {
        "@id": "https://w3id.org/EVI#",
        "@type": "@id"
    },
    "usedDataset": {
        "@id": "https://w3id.org/EVI#",
        "@type": "@id"
    },
    "generatedBy": {
        "@id": "https://w3id.org/EVI#generatedBy",
        "@type": "@id"
    },
    "generated": {
        "@id": "https://w3id.org/EVI#generated",
        "@type": "@id"
    },
    "hasDistribution": {
        "@id": "https://w3id.org/EVI#hasDistribution",
        "@type": "@id"
    }
}

class ClassType(str, Enum):
    DATASET = 'Dataset'
    SOFTWARE = 'Software'
    MLMODEL = 'MLModel'
    COMPUTATION = 'Computation'
    ANNOTATION = 'Annotation'
    SCHEMA = 'Schema'
    EVIDENCE_GRAPH = 'EvidenceGraph'
    ROCRATE = 'ROCrate' #TODO: Add ROCrate concept to EVI ontology and publish a new version

def normalize_class_type(value: Union[str, ClassType]) -> ClassType:
    """Normalizes various formats of class type identifiers to standard form.
    
    Handles formats like:
    - Plain name: "ROCrate"
    - URL: "https://w3id.org/EVI#ROCrate"
    - Prefixed: "EVI:ROCrate"
    """
    if isinstance(value, ClassType):
        return value
        
    value_str = str(value).strip()
    
    # Handle URL format
    if value_str.startswith('https://') or value_str.startswith('http://'):
        value_str = value_str.split('#')[-1].split('/')[-1]
    
    # Handle prefixed format (e.g., EVI:ROCrate)
    if ':' in value_str:
        value_str = value_str.split(':')[-1]

    try:
        return ClassType(value_str)
    except ValueError:
        for enum_value in ClassType:
            if enum_value.value.lower() == value_str.lower():
                return enum_value
                
        raise ValueError(f"Invalid class type: {value_str}")
    
ValidatedClassType = Annotated[ClassType, BeforeValidator(normalize_class_type)]

class IdentifierValue(BaseModel):
    guid: str = Field(alias="@id")
    model_config = ConfigDict(extra="allow")


class IdentifierPropertyValue(BaseModel):
    metadataType: str = Field(default="PropertyValue", alias="@type")
    value: str
    name: str


class Identifier(BaseModel):
    model_config = ConfigDict(extra='allow')
    guid: str = Field(
        title="guid",
        alias="@id"
    )
    metadataType: ValidatedClassType = Field(
        title="metadataType",
        alias="@type"
    )
    name: str = Field(...)


class FairscapeBaseModel(Identifier):
    """Refers to the Fairscape BaseModel inherited from Pydantic

    Args:
        BaseModel (Default Pydantic): Every instance of the Fairscape BaseModel must contain
        an id, a type, and a name
    """
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra='allow'
    )
    context: Optional[Dict[str, str]] = Field(
        default=defaultContext,
        title="context",
        alias="@context"
    )
    url: Optional[AnyUrl] = Field(default=None)


class FairscapeEVIBaseModel(FairscapeBaseModel):
    description: str = Field(min_length=5)
    workLicense: Optional[str] = Field(default=DEFAULT_LICENSE, alias="license")
    keywords: List[str] = Field(default=[])
    published: bool = Field(default=True)

