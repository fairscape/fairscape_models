from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field

DEFAULT_CROISSANT_CONTEXT = {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "cr": "http://mlcommons.org/croissant/",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "sc": "https://schema.org/",
    "dct": "http://purl.org/dc/terms/",
    "citeAs": "cr:citeAs",
    "column": "cr:column",
    "conformsTo": "dct:conformsTo",
    "data": {
      "@id": "cr:data",
      "@type": "@json"
    },
    "dataBiases": "cr:dataBiases",
    "dataCollection": "cr:dataCollection",
    "dataType": {
      "@id": "cr:dataType",
      "@type": "@vocab"
    },
    "extract": "cr:extract",
    "field": "cr:field",
    "fileObject": "cr:fileObject",
    "fileSet": "cr:fileSet",
    "includes": "cr:includes",
    "isLiveDataset": "cr:isLiveDataset",
    "jsonPath": "cr:jsonPath",
    "key": "cr:key",
    "md5": "cr:md5",
    "parentField": "cr:parentField",
    "recordSet": "cr:recordSet",
    "references": "cr:references",
    "regex": "cr:regex",
    "repeated": "cr:repeated",
    "replace": "cr:replace",
    "separator": "cr:separator",
    "source": "cr:source",
    "subField": "cr:subField",
    "transform": "cr:transform",
}

class CroissantIdentifier(BaseModel):
    id: str = Field(alias="@id")

class CroissantSource(BaseModel):
    file_object: Optional[CroissantIdentifier] = Field(default=None, alias="fileObject")
    file_set: Optional[CroissantIdentifier] = Field(default=None, alias="fileSet")
    extract: Optional[Dict[str, Any]] = Field(default=None)
    transform: Optional[Dict[str, Any]] = Field(default=None)

class CroissantReferences(BaseModel):
    file_object: Optional[CroissantIdentifier] = Field(default=None, alias="fileObject")
    column: Optional[str] = Field(default=None)

class CroissantField(BaseModel):
    id: Optional[str] = Field(default=None, alias="@id")
    type: str = Field(default="cr:Field", alias="@type")
    name: str
    description: Optional[str] = None
    data_type: str = Field(alias="dataType")
    source: Optional[CroissantSource] = None
    references: Optional[CroissantReferences] = None
    sub_field: Optional[List['CroissantField']] = Field(default=None, alias="subField")
    repeated: Optional[bool] = None

class CroissantRecordSet(BaseModel):
    id: Optional[str] = Field(default=None, alias="@id")
    type: str = Field(default="cr:RecordSet", alias="@type")
    name: str
    description: Optional[str] = None
    key: Optional[Union[str, List[str]]] = None
    field: List[CroissantField] = Field(alias="field")

class CroissantFileObject(BaseModel):
    id: str = Field(alias="@id")
    type: str = Field(default="cr:FileObject", alias="@type")
    name: Optional[str] = None
    description: Optional[str] = None
    content_url:  Optional[Union[str, List[str]]] = Field(default=None, alias="contentUrl")
    encoding_format: str = Field(alias="encodingFormat")
    sha256: Optional[str] = None
    md5: Optional[str] = None

class CroissantFileSet(BaseModel):
    id: str = Field(alias="@id")
    type: str = Field(default="cr:FileSet", alias="@type")
    name: Optional[str] = None
    description: Optional[str] = None
    encoding_format: str = Field(alias="encodingFormat")
    includes: str
    excludes: Optional[str] = None
    contained_in: Optional[CroissantIdentifier] = Field(default=None, alias="containedIn")

class CroissantDataset(BaseModel):
    context: Any = Field(default=DEFAULT_CROISSANT_CONTEXT, alias="@context")
    type: str = Field(default="sc:Dataset", alias="@type")
    name: str
    description: str
    conforms_to: Optional[str] = Field(default=None, alias="dct:conformsTo")
    license: Optional[str] = None
    cite_as: Optional[str] = Field(default=None, alias="citeAs")
    url: Optional[str] = None
    keywords: Optional[List[str]] = Field(default_factory=list)
    version: Optional[str] = None
    creator: Optional[List[Dict[str, Any]]] = None
    publisher: Optional[Dict[str, Any]] = None
    date_published: Optional[str] = Field(default=None, alias="datePublished")
    distribution: Optional[List[Union[CroissantFileObject, CroissantFileSet]]] = Field(default_factory=list)
    record_set: Optional[List[CroissantRecordSet]] = Field(default=None, alias="recordSet")

    # RAI Properties
    data_collection: Optional[str] = Field(default=None, alias="rai:dataCollection")
    data_collection_type: Optional[List[str]] = Field(default=None, alias="rai:dataCollectionType")
    data_collection_missing_data: Optional[str] = Field(default=None, alias="rai:dataCollectionMissingData")
    data_collection_raw_data: Optional[str] = Field(default=None, alias="rai:dataCollectionRawData")
    data_imputation_protocol: Optional[str] = Field(default=None, alias="rai:dataImputationProtocol")
    data_manipulation_protocol: Optional[List[str]] = Field(default=None, alias="rai:dataManipulationProtocol")
    data_preprocessing_protocol: Optional[List[str]] = Field(default=None, alias="rai:dataPreprocessingProtocol")
    data_annotation_protocol: Optional[str] = Field(default=None, alias="rai:dataAnnotationProtocol")
    data_annotation_platform: Optional[List[str]] = Field(default=None, alias="rai:dataAnnotationPlatform")
    data_annotation_analysis: Optional[List[str]] = Field(default=None, alias="rai:dataAnnotationAnalysis")
    data_release_maintenance_plan: Optional[List[str]] = Field(default=None, alias="rai:dataReleaseMaintenancePlan")
    personal_sensitive_information: Optional[List[str]] = Field(default=None, alias="rai:personalSensitiveInformation")
    data_social_impact: Optional[str] = Field(default=None, alias="rai:dataSocialImpact")
    data_biases: Optional[List[str]] = Field(default=None, alias="rai:dataBiases")
    data_limitations: Optional[List[str]] = Field(default=None, alias="rai:dataLimitations")
    data_use_cases: Optional[List[str]] = Field(default=None, alias="rai:dataUseCases")
    annotations_per_item: Optional[str] = Field(default=None, alias="rai:annotationsPerItem")
    annotator_demographics: Optional[List[str]] = Field(default=None, alias="rai:annotatorDemographics")
    machine_annotation_tools: Optional[List[str]] = Field(default=None, alias="rai:machineAnnotationTools")

    class Config:
        populate_by_name = True
        extra = 'allow'

CroissantField.model_rebuild()