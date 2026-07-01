from pydantic import (
    BaseModel, 
    ConfigDict,
    Field,
    BeforeValidator,
    field_validator
)
from pydantic.networks import AnyUrl
from typing import (
    List,
    Optional,
    Dict,
    Union,
    Any
)
import re
from typing_extensions import Annotated
from enum import Enum


IdentifierPattern = "^ark:[0-9]{5}\\/[a-zA-Z0-9_\\-]+.$"

DATASET_TYPE = "Dataset"
DATASET_CONTAINER_TYPE = "DatasetContainer"
SOFTWARE_TYPE = "Software"
MLMODEL_TYPE = "MLModel"
COMPUTATION_TYPE = "Computation"
ANNOTATION_TYPE = "Annotation"
ANNOTATED_COMPUTATION_TYPE = "AnnotatedComputation"
ANNOTATED_EVIDENCE_GRAPH_TYPE = "AnnotatedEvidenceGraph"
ROCRATE_TYPE = "ROCrate"
ARTICLE_TYPE = "Article"
CLAIM_TYPE = "Claim"
CONTAINER_TYPE = "Container"
SERVICE_TYPE = "Service"

# TODO get from config
DEFAULT_ARK_NAAN = "59853"
DEFAULT_LICENSE = "https://creativecommons.org/licenses/by/4.0/"
DEFAULT_CONTEXT = {
    "@vocab": "https://schema.org/",
    "evi": "https://w3id.org/EVI#",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "prov": "http://www.w3.org/ns/prov#",

    # TODO fully specify default context
    "usedSoftware": {
        "@id": "https://w3id.org/EVI#usefdSoftware",
        "@type": "@id"
    },
    "usedDataset": {
        "@id": "https://w3id.org/EVI#usedDataset",
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
    "annotates": {
        "@id": "https://w3id.org/EVI#annotates",
        "@type": "@id"
    },
    "hasDistribution": {
        "@id": "https://w3id.org/EVI#hasDistribution",
        "@type": "@id"
    }
}

def extractGUID(inputString: str | None) -> str|None:
    """
    Given an input ARK extract the normalized ARK, if validation fails return the input.
    """
    try:
        match = re.search(
            pattern="ark:[0-9]{5}/.+$",
            string=inputString
        )
        return match.group()
    except AttributeError:
        return inputString


class ClassType(str, Enum):
    DATASET = 'Dataset'
    SOFTWARE = 'Software'
    MLMODEL = 'MLModel'
    COMPUTATION = 'Computation'
    ANNOTATION = 'Annotation'
    SCHEMA = 'Schema'
    EVIDENCE_GRAPH = 'EvidenceGraph'
    ANNOTATED_COMPUTATION = 'AnnotatedComputation'
    ANNOTATED_EVIDENCE_GRAPH = 'AnnotatedEvidenceGraph'
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
    """     
    The Base Model for any Metadata element in FAIRSCAPE.

    Every instance must have a GUID in the form of an ARK (archival resource key), 
    a metadata type (https://www.w3.org/TR/json-ld/#specifying-the-type), and a name specified as a string.
    Every model must have these attributes, and may have any other attributes as specified by the `ConfigDict(extra='allow')`.
    
    For the guid property, preprocessing is preformed by the field validator `Identifier.extract_guid`.
    This method preforms a regex search to find the identifier within the passed value. 
    As ARKs may be specified as full IRIS or URLs pointing to several different resolvers, arks are stripped.
    The guid for all fairscape_models clases should follow the regex `"ark:[0-9]{5}/.+$"`.

    This guid preprocessing is also preformed on isPartOf.
    """
    model_config = ConfigDict(extra='allow')
    guid: str = Field(
        title="guid",
        alias="@id",
        pattern=IdentifierPattern
    )
    metadataType: Optional[Union[List[str], str]] = Field(
        title="metadataType",
        alias="@type"
    )
    name: str = Field(...)
    isPartOf: Optional[List[IdentifierValue]]  = Field(default=[])

    @field_validator('guid', mode='before')
    @classmethod
    def extract_guid(cls, value: Any)-> Any:
        """ 
        Extract the ARK from the guid field, runs before validation against regex.
        """
        return extractGUID(value)


    @field_validator('isPartOf', mode='before')
    @classmethod
    def extract_guid_is_part_of(cls, value: Any)-> Any:
        """
        Extract GUID from isPartOf Properties, normalizing the form of the ark.
        """
        # TODO handle value of Optional[List[IdentifierValue]]

        #if value:
        #    if isinstance(value, str):
        #        return extractGUID(value)
        #    if isinstance(value, list):
        #        return [extractGUID(elem) for elem in value]
        #else:
        #    return value
        return value
