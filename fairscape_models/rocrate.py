import urllib.parse
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator


from fairscape_models.fairscape_base import IdentifierValue
from fairscape_models.schema import Schema
from fairscape_models.biochem_entity import BioChemEntity
from fairscape_models.medical_condition import MedicalCondition
from fairscape_models.computation import Computation
from fairscape_models.dataset import Dataset
from fairscape_models.software import Software

class GenericMetadataElem(BaseModel):
    """Generic Metadata Element of an ROCrate"""
    guid: str = Field(alias="@id")
    metadataType: Union[str, List[str]] = Field(alias="@type")    
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
 
    model_config = ConfigDict(extra="allow")

class ROCrateMetadataFileElem(BaseModel):
    """Metadata Element of an ROCrate cooresponding to the `ro-crate-metadata.json` file itself

    Example

        ```
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {
                "@id": "https://w3id.org/ro/crate/1.2-DRAFT"
            },
            "about": {
                "@id": "https://fairscape.net/ark:59852/rocrate-2.cm4ai_chromatin_mda-mb-468_untreated_apmsembed_initialrun0.1alpha"
            }
        }
        ```
    """
    guid: str = Field(alias="@id")
    metadataType: Literal["CreativeWork"] = Field(alias="@type")
    conformsTo: IdentifierValue
    about: IdentifierValue


class ROCrateMetadataElem(BaseModel):
    """Metadata Element of ROCrate that represents the crate as a whole

    Example
        ```
        {
            '@id': 'https://fairscape.net/ark:59852/rocrate-2.cm4ai_chromatin_mda-mb-468_untreated_imageembedfold1_initialrun0.1alpha',
            '@type': ['Dataset', 'https://w3id.org/EVI#ROCrate'],
            'name': 'Initial integration run',
            'description': 'Ideker Lab CM4AI 0.1 alpha MDA-MB-468 untreated chromatin Initial integration run IF Image Embedding IF microscopy images embedding fold1',
            'keywords': ['Ideker Lab', 'fold1'],
            'isPartOf': [
                {'@id': 'ark:/Ideker_Lab'}, 
                {'@id': 'ark:/Ideker_Lab/CM4AI'}
                ],
            'version': '0.5alpha',
            'license': 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en',
            'associatedPublication': 'Clark T, Schaffer L, Obernier K, Al Manir S, Churas CP, Dailamy A, Doctor Y, Forget A, Hansen JN, Hu M, Lenkiewicz J, Levinson MA, Marquez C, Mohan J, Nourreddine S, Niestroy J, Pratt D, Qian G, Thaker S, Belisle-Pipon J-C, Brandt C, Chen J, Ding Y, Fodeh S, Krogan N, Lundberg E, Mali P, Payne-Foster P, Ratcliffe S, Ravitsky V, Sali A, Schulz W, Ideker T. Cell Maps for Artificial Intelligence: AI-Ready Maps of Human Cell Architecture from Disease-Relevant Cell Lines. BioRXiv 2024.',
            'author': ['Test']
            'conditionsOfAccess': 'This dataset was created by investigators and staff of the Cell Maps for Artificial Intelligence project (CM4AI - https://cm4ai.org), a Data Generation Project of the NIH Bridge2AI program, and is copyright (c) 2024 by The Regents of the University of California and, for cellular imaging data, by The Board of Trustees of the Leland Stanford Junior University. It is licensed for reuse under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC-BY-NC-SA 4.0) license, whose terms are summarized here: https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en.  Proper attribution credit as required by the license includes citation of the copyright holders and of the attribution parties, which includes citation of the following article: Clark T, Schaffer L, Obernier K, Al Manir S, Churas CP, Dailamy A, Doctor Y, Forget A, Hansen JN, Hu M, Lenkiewicz J, Levinson MA, Marquez C, Mohan J, Nourreddine S, Niestroy J, Pratt D, Qian G, Thaker S, Belisle-Pipon J-C, Brandt C, Chen J, Ding Y, Fodeh S, Krogan N, Lundberg E, Mali P, Payne-Foster P, Ratcliffe S, Ravitsky V, Sali A, Schulz W, Ideker T. Cell Maps for Artificial Intelligence: AI-Ready Maps of Human Cell Architecture from Disease-Relevant Cell Lines. BioRXiv 2024."',
            'copyrightNotice': 'Copyright (c) 2024 by The Regents of the University of California',
            'hasPart': [
                {'@id': 'https://fairscape.net/ark:59852/software-cellmaps_image_embedding-N2ux5jg'},
                {'@id': 'https://fairscape.net/ark:59852/dataset-cellmaps_image_embedding-output-file-N2ux5jg'},
                {'@id': 'https://fairscape.net/ark:59852/dataset-Densenet-model-file-N2ux5jg'},
                {'@id': 'https://fairscape.net/ark:59852/computation-IF-Image-Embedding-N2ux5jg'}
            ]
        }
        ```
    """ 
    model_config = ConfigDict(extra="allow")
    
    guid: str = Field(alias="@id")
    metadataType: List[str] = Field(alias="@type")
    name: str
    description: str
    keywords: List[str]
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[])
    version: str
    hasPart: List[IdentifierValue]
    author: Union[str, List[str]]
    dataLicense: Optional[str] = Field(alias="license")
    associatedPublication: Optional[Union[str, List[str]]] = Field(default=None)
    conditionsOfAccess: Optional[str] = Field(default=None)
    copyrightNotice: Optional[str] = Field(default=None)
    
    rai_data_limitations: Optional[str] = Field(alias="rai:dataLimitations", default=None)
    rai_data_biases: Optional[str] = Field(alias="rai:dataBiases", default=None)
    rai_data_use_cases: Optional[str] = Field(alias="rai:dataUseCases", default=None)
    rai_data_release_maintenance_plan: Optional[str] = Field(alias="rai:dataReleaseMaintenancePlan", default=None)
    rai_data_collection: Optional[str] = Field(alias="rai:dataCollection", default=None)
    rai_data_collection_type: Optional[List[str]] = Field(alias="rai:dataCollectionType", default=None)
    rai_data_collection_missing_data: Optional[str] = Field(alias="rai:dataCollectionMissingData", default=None)
    rai_data_collection_raw_data: Optional[str] = Field(alias="rai:dataCollectionRawData", default=None)
    rai_data_collection_timeframe: Optional[List[str]] = Field(alias="rai:dataCollectionTimeframe", default=None)
    rai_data_imputation_protocol: Optional[str] = Field(alias="rai:dataImputationProtocol", default=None)
    rai_data_manipulation_protocol: Optional[str] = Field(alias="rai:dataManipulationProtocol", default=None)
    rai_data_preprocessing_protocol: Optional[List[str]] = Field(alias="rai:dataPreprocessingProtocol", default=None)
    rai_data_annotation_protocol: Optional[str] = Field(alias="rai:dataAnnotationProtocol", default=None)
    rai_data_annotation_platform: Optional[List[str]] = Field(alias="rai:dataAnnotationPlatform", default=None)
    rai_data_annotation_analysis: Optional[List[str]] = Field(alias="rai:dataAnnotationAnalysis", default=None)
    rai_personal_sensitive_information: Optional[List[str]] = Field(alias="rai:personalSensitiveInformation", default=None)
    rai_data_social_impact: Optional[str] = Field(alias="rai:dataSocialImpact", default=None)
    rai_annotations_per_item: Optional[str] = Field(alias="rai:annotationsPerItem", default=None)
    rai_annotator_demographics: Optional[List[str]] = Field(alias="rai:annotatorDemographics", default=None)
    rai_machine_annotation_tools: Optional[List[str]] = Field(alias="rai:machineAnnotationTools", default=None)

    
    
    
class ROCrateDistribution(BaseModel):
    extractedROCrateBucket: Optional[str] = Field(default=None)
    archivedROCrateBucket: Optional[str] = Field(default=None)
    extractedObjectPath: Optional[List[str]] = Field(default=[])
    archivedObjectPath: Optional[str] = Field(default=None)

    

class ROCrateV1_2(BaseModel):
    context: Optional[Dict] = Field(alias="@context")
    metadataGraph: List[Union[
        Dataset,
        Software,
        Computation,
        ROCrateMetadataElem,
        ROCrateMetadataFileElem,
        Schema,
        BioChemEntity,
        MedicalCondition,
        GenericMetadataElem
    ]] = Field(alias="@graph")
    
    @model_validator(mode="before")
    @classmethod
    def validate_metadata_graph(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "@graph" not in values:
            return values
        
        type_map = {
            "Dataset": Dataset,
            "Software": Software,
            "Computation": Computation,
            "CreativeWork": ROCrateMetadataFileElem,
            "Schema": Schema,
            "BioChemEntity": BioChemEntity,
            "MedicalCondition": MedicalCondition,
            "ROCrate": ROCrateMetadataElem
        }
        
        def normalize_type(type_str):
            if "#" in type_str:
                return type_str.split("#")[-1]
            if ":" in type_str:
                return type_str.split(":")[-1]
            return type_str
        
        new_graph = []
        for item in values["@graph"]:
            if not isinstance(item, dict):
                new_graph.append(item)
                continue
                
            if "@type" not in item:
                raise ValueError("Metadata element must have @type field")
                
            item_type = item["@type"]
            
            if isinstance(item_type, list):
                normalized_types = [normalize_type(t) for t in item_type]
                if "ROCrate" in normalized_types or "Dataset" in normalized_types:
                    new_graph.append(ROCrateMetadataElem.model_validate(item))
                    continue
            
            elif isinstance(item_type, str):
                normalized_type = normalize_type(item_type)
                model_class_to_use = type_map.get(normalized_type)

            # If we found a specific class, use it. Let it raise a
            if model_class_to_use:
                new_graph.append(model_class_to_use.model_validate(item))
            # Only if no specific class was matched, use the generic one.
            else:
                new_graph.append(GenericMetadataElem.model_validate(item))
        
        values["@graph"] = new_graph
        return values

    def cleanIdentifiers(self):
        """ Clean metadata guid property from full urls to ark:{NAAN}/{postfix} 
        """

        def cleanGUID(metadata):
            """ Clean metadata guid property from full urls to ark:{NAAN}/{postfix} 
            """
            if "http" in metadata.guid:
                metadata.guid = urllib.parse.urlparse(metadata.guid).path.lstrip('/')
 
        #clean ROCrate metadata identifier
        rocrateMetadata = self.getCrateMetadata()
        cleanGUID(rocrateMetadata)
        
        # clean identifiers and evi properties
        for elem in self.getEVIElements():
            if "ark:" in elem.guid:  # Only clean if contains "ark:"
                cleanGUID(elem)
                
            if isinstance(elem, Dataset):
                # usedByComputation
                for usedByComputation in elem.usedByComputation:
                    if "ark:" in usedByComputation.guid:
                        cleanGUID(usedByComputation)
                        
                # generatedBy
                for generatedBy in elem.generatedBy:
                    if "ark:" in generatedBy.guid:
                        cleanGUID(generatedBy)
                        
            if isinstance(elem, Software):
                for usedByElem in elem.usedByComputation:
                    if "ark:" in usedByElem.guid:
                        cleanGUID(usedByElem)
                        
            if isinstance(elem, Computation):
                # elem.usedDataset
                for usedDataset in elem.usedDataset:
                    if "ark:" in usedDataset.guid:
                        cleanGUID(usedDataset)
                        
                # elem.generated
                for generated in elem.generated:
                    if "ark:" in generated.guid:
                        cleanGUID(generated)
                        
                # elem.usedSoftware
                for usedSoftware in elem.usedSoftware:
                    if "ark:" in usedSoftware.guid:
                        cleanGUID(usedSoftware)

    def getCrateMetadata(self)-> ROCrateMetadataElem:
        """ Filter the Metadata Graph for the Metadata Element Describing the Toplevel ROCrate

        :param self
        :return: The RO Crate Metadata Elem describing the toplevel ROCrate
        :rtype fairscape_mds.models.rocrate.ROCrateMetadataElem
        """
        filterResults = list(filter(
            lambda x: isinstance(x, ROCrateMetadataElem),
            self.metadataGraph
        ))

        # TODO support for nested crates 
        # must find the ROCrateMetadataElem with '@id' == 'ro-crate-metadata.json'
        if len(filterResults) == 0:
            # TODO more detailed exception
            raise Exception
        else:
            return filterResults[0]

    def getSchemas(self) -> List[Schema]:
        # TODO filter schemas
        filterResults = list(filter(
            lambda x: isinstance(x, Schema), 
            self.metadataGraph
        ))

        return filterResults

    def getDatasets(self) -> List[Dataset]:
        """ Filter the Metadata Graph for Dataset Elements

        :param self
        :return: All dataset metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.Dataset]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, Dataset) and not isinstance(x, ROCrateMetadataElem), 
            self.metadataGraph
        ))

        return filterResults


    def getSoftware(self) -> List[Software]:
        """ Filter the Metadata Graph for Software Elements

        :param self
        :return: All Software metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.Software]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, Software), 
            self.metadataGraph
        ))

        return filterResults


    def getComputations(self) -> List[Computation]:
        """ Filter the Metadata Graph for Computation Elements

        :param self
        :return: All Computation metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.Computation]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, Computation), 
            self.metadataGraph
        ))

        return filterResults


    def getBioChemEntities(self) -> List[BioChemEntity]:
        """ Filter the Metadata Graph for BioChemEntity Elements

        :param self
        :return: All BioChemEntity metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.BioChemEntity]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, BioChemEntity), 
            self.metadataGraph
        ))

        return filterResults


    def getMedicalConditions(self) -> List[MedicalCondition]:
        """ Filter the Metadata Graph for MedicalCondition Elements

        :param self
        :return: All MedicalCondition metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.MedicalCondition]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, MedicalCondition), 
            self.metadataGraph
        ))

        return filterResults


    def getEVIElements(self) -> List[Union[
        Computation, 
        Dataset, 
        Software, 
        Schema,
        BioChemEntity,
        MedicalCondition
        ]]:
        """ Query the metadata graph for elements which require minting identifiers
        """
        return self.getDatasets() + self.getSoftware() + self.getComputations() + self.getSchemas()
