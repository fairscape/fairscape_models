import urllib.parse
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator

from fairscape_models.fairscape_base import IdentifierValue, DEFAULT_CONTEXT
from fairscape_models.schema import Schema
from fairscape_models.biochem_entity import BioChemEntity
from fairscape_models.medical_condition import MedicalCondition
from fairscape_models.computation import Computation
from fairscape_models.annotation import Annotation
from fairscape_models.experiment import Experiment
from fairscape_models.dataset import Dataset
from fairscape_models.software import Software
from fairscape_models.mlmodel import MLModel
from fairscape_models.patient import Patient
from fairscape_models.instrument import Instrument
from fairscape_models.model_card import ModelCard
from fairscape_models.sample import Sample
from fairscape_models.activity import Activity
from fairscape_models.digital_object import DigitalObject
from fairscape_models._version import __version__

class ContactPoint(BaseModel):
    """Schema.org ContactPoint for structured contact information."""
    metadataType: str = Field(default="ContactPoint", alias="@type")
    contactType: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    telephone: Optional[str] = Field(default=None)
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PostalAddress(BaseModel):
    """Schema.org PostalAddress for structured address information."""
    metadataType: str = Field(default="PostalAddress", alias="@type")
    streetAddress: Optional[str] = Field(default=None)
    addressLocality: Optional[str] = Field(default=None)
    addressRegion: Optional[str] = Field(default=None)
    postalCode: Optional[str] = Field(default=None)
    addressCountry: Optional[str] = Field(default=None)
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class IRB(BaseModel):
    """Institutional Review Board with structured contact and address info."""
    metadataType: str = Field(default="IRB", alias="@type")
    name: str
    contactPoint: Optional[ContactPoint] = Field(default=None)
    address: Optional[PostalAddress] = Field(default=None)
    model_config = ConfigDict(extra="allow", populate_by_name=True)


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
    fairscapeVersion: str = __version__


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

    # Core identity
    guid: str = Field(alias="@id", description="Persistent unique identifier for this RO-Crate (ARK, DOI, URL, etc.).")
    metadataType: List[str] = Field(alias="@type", description="RO-Crate type list; always includes 'Dataset' and 'https://w3id.org/EVI#ROCrate'.")
    name: str = Field(description="A human-readable name for the dataset.")
    description: str = Field(description="A human-readable description of the dataset.")
    keywords: List[str] = Field(description="Keywords or tags describing the dataset, used for discovery and search.")
    version: str = Field(description="Version string for this release of the dataset (e.g. '1.0', '2.3.1').")
    datePublished: Optional[str] = Field(default=None, description="Date the dataset was published or made publicly available (ISO 8601).")

    # Relationships
    isPartOf: Optional[List[IdentifierValue]] = Field(default=[], description="Parent organization(s) or project(s) this crate belongs to, referenced by identifier.")
    hasPart: List[IdentifierValue] = Field(description="Dataset, Software, Computation, and other entities that are part of this RO-Crate, referenced by identifier.")

    # Attribution — D4D_Motivation: Creator, FundingMechanism
    author: Union[str, List[str]] = Field(description="Who created the dataset (e.g. which team, research group) and on behalf of which entity (e.g. company, institution, organization).")
    publisher: Optional[str] = Field(default=None, description="Organization or person responsible for publishing or distributing the dataset.")
    principalInvestigator: Optional[str] = Field(default=None, description="A key individual (Principal Investigator) responsible for or overseeing dataset creation.")
    funder: Optional[str] = Field(default=None, description="Who funded the creation of the dataset? Include grant names and numbers where applicable.")
    contactEmail: Optional[str] = Field(default=None, description="Email address for questions or correspondence about the dataset.")
    citation: Optional[str] = Field(default=None, description="Preferred citation string for this dataset.")
    associatedPublication: Optional[Union[str, List[str]]] = Field(default=None, description="Publication(s) associated with or describing this dataset.")
    identifier: Optional[str] = Field(default=None, description="DOI or other external persistent identifier for the dataset (used for Findability and Sustainability scoring).")

    # Licensing — D4D_Data_Governance: LicenseAndUseTerms
    dataLicense: Optional[str] = Field(alias="license", description="Will the dataset be distributed under a copyright or other IP license? Provide a link to or copy of the license terms (e.g. CC BY 4.0, MIT).")
    conditionsOfAccess: Optional[str] = Field(default=None, description="Terms and conditions governing access to and use of this dataset, including any data use agreements required.")
    copyrightNotice: Optional[str] = Field(default=None, description="Copyright statement for the dataset, including year and rights holder.")

    # Content info
    contentSize: Optional[str] = Field(default=None, description="Total size of the dataset content (e.g. '2.4 GB', '150 MB'). Used in AI-Ready Characterization scoring.")
    usageInfo: Optional[str] = Field(default=None, description="Additional usage information or instructions for working with this dataset.")
    hasSummaryStatistics: Optional[Union[str, IdentifierValue]] = Field(default=None, description="Reference to a summary statistics entity describing distributions, counts, and key statistics for this dataset.")
    additionalProperty: Optional[List[Dict[str, Any]]] = Field(default=None, description="Additional schema.org PropertyValue entries for metadata not covered by other fields (e.g. [{\"name\": \"Human Subject\", \"value\": \"Yes\"}]).")

    # Compliance / ethics — D4D_Ethics, D4D_Human, D4D_Data_Governance
    ethicalReview: Optional[str] = Field(default=None, description="Were any ethical or compliance review processes conducted (e.g. by an Institutional Review Board)? If so, describe the process, frequency of review, and outcomes. Or provide a contact for ethical review information.")
    confidentialityLevel: Optional[str] = Field(default=None, description="HL7 Confidentiality code indicating the level of confidentiality or sensitivity of the dataset (e.g. 'normal', 'restricted', 'very restricted').")
    irb: Optional[Union[str, IRB]] = Field(default=None, description="Institutional Review Board (IRB) information — approval status, approving institution, and contact details.")
    irbProtocolId: Optional[str] = Field(default=None, description="IRB protocol identifier number assigned by the reviewing institution.")
    humanSubjectExemption: Optional[str] = Field(default=None, description="If human subjects research qualifies for exemption from full IRB review, the applicable exemption category (e.g. 45 CFR 46 Exemption 4).")
    fdaRegulated: Optional[bool] = Field(default=None, description="Whether this dataset is subject to FDA regulations (e.g. clinical trial data, medical device data).")
    deidentified: Optional[bool] = Field(default=None, description="Whether the dataset has been de-identified to remove or obscure personally identifiable information.")
    humanSubjectResearch: Optional[str] = Field(default=None, description="Does this dataset involve human subjects? Indicate Yes/No and describe the nature of human subjects involvement.")
    dataGovernanceCommittee: Optional[str] = Field(default=None, description="Name or contact for the data governance committee responsible for oversight, access control, and policy enforcement for this dataset.")

    # Checksums
    md5: Optional[str] = Field(default=None, description="MD5 checksum of the digital object content")
    hash: Optional[str] = Field(default=None, description="Hash of the digital object content (if not MD5)")
    sha256: Optional[Union[str,List[str]]] = Field(default=None, description="SHA-256 checksum of the digital object content")


    # RAI fields (Croissant RAI 1.0 — http://mlcommons.org/croissant/RAI/1.0)
    # Descriptions drawn from the D4D schema (data-sheets-schema) exact_mappings where available.
    rai_data_limitations: Optional[Union[str, List[str]]] = Field(
        alias="rai:dataLimitations", default=None,
        description="Documents known limitations of the dataset that may affect its use or interpretation — data generalization limits (e.g. related to data distribution, data quality issues, or data sources) and non-recommended uses. Distinct from biases (systematic errors) and anomalies (data quality issues). (rai:dataLimitations)"
    )
    rai_data_biases: Optional[Union[str, List[str]]] = Field(
        alias="rai:dataBiases", default=None,
        description="Documents known biases present in the dataset — systematic errors or prejudices that may affect the representativeness or fairness of the data. Distinct from anomalies (data quality issues) and limitations (scope constraints). (rai:dataBiases)"
    )
    rai_data_use_cases: Optional[Union[str, List[str]]] = Field(
        alias="rai:dataUseCases", default=None,
        description="Explicit statement of intended uses for this dataset, focusing on positive, recommended applications. Recommended use categories: Training, Testing, Validation, Development or Production Use, Fine Tuning, others. Include usage guidelines and caveats. (rai:dataUseCases)"
    )
    rai_data_release_maintenance_plan: Optional[Union[str, List[str]]] = Field(
        alias="rai:dataReleaseMaintenancePlan", default=None,
        description="Will the dataset be updated (e.g. to correct labeling errors, add new instances, delete instances)? If so, how often, by whom, and how will updates be communicated? Covers versioning timeframe, maintainers, and deprecation policies. (rai:dataReleaseMaintenancePlan)"
    )
    rai_data_collection: Optional[str] = Field(
        alias="rai:dataCollection", default=None,
        description="What mechanisms or procedures were used to collect the data (e.g. hardware sensors, manual curation, software APIs)? Also covers how these mechanisms were validated. (rai:dataCollection)"
    )
    rai_data_collection_type: Optional[List[str]] = Field(
        alias="rai:dataCollectionType", default=None,
        description="Data collection type(s). Recommended values: Surveys, Secondary Data Analysis, Physical Data Collection, Direct Measurement, Document Analysis, Manual Human Curator, Software Collection, Experiments, Web Scraping, Web API, Focus Groups, Self-Reporting, Customer Feedback Data, User-Generated Content Data, Passive Data Collection, Others. (rai:dataCollectionType)"
    )
    rai_data_collection_missing_data: Optional[str] = Field(
        alias="rai:dataCollectionMissingData", default=None,
        description="Documentation of missing data in the dataset, including patterns (e.g. MCAR, MAR, MNAR), known or suspected causes (e.g. sensor failures, participant dropout, privacy constraints), and strategies used to handle missing values. (rai:dataCollectionMissingData)"
    )
    rai_data_collection_raw_data: Optional[str] = Field(
        alias="rai:dataCollectionRawData", default=None,
        description="Description of raw data sources before preprocessing, cleaning, or labeling. Documents where the original data comes from and how it can be accessed. (rai:dataCollectionRawData)"
    )
    rai_data_collection_timeframe: Optional[List[str]] = Field(
        alias="rai:dataCollectionTimeframe", default=None,
        description="Over what timeframe was the data collected, and does this timeframe match the creation timeframe of the underlying data? Provide start and end dates where possible. (rai:dataCollectionTimeframe)"
    )
    rai_data_imputation_protocol: Optional[str] = Field(
        alias="rai:dataImputationProtocol", default=None,
        description="Description of data imputation methodology, including techniques used to handle missing values (e.g. mean/median imputation, forward fill, model-based imputation) and rationale for chosen approaches. (rai:dataImputationProtocol)"
    )
    rai_data_manipulation_protocol: Optional[Union[str, List[str]]] = Field(
        alias="rai:dataManipulationProtocol", default=None,
        description="Was any cleaning of the data done (e.g. removal of instances, processing of missing values, deduplication, filtering)? If so, describe the cleaning procedures applied. (rai:dataManipulationProtocol)"
    )
    rai_data_preprocessing_protocol: Optional[List[str]] = Field(
        alias="rai:dataPreprocessingProtocol", default=None,
        description="Was any preprocessing of the data done (e.g. discretization or bucketing, tokenization, feature extraction, normalization)? Describe the steps required to bring collected data to a state that can be processed by an ML model or algorithm. (rai:dataPreprocessingProtocol)"
    )
    rai_data_annotation_protocol: Optional[str] = Field(
        alias="rai:dataAnnotationProtocol", default=None,
        description="Annotation methodology, tasks, and protocols followed during labeling. Includes annotation guidelines, quality control procedures, task definitions, workforce type, annotation characteristics, and label distributions. (rai:dataAnnotationProtocol)"
    )
    rai_data_annotation_platform: Optional[List[str]] = Field(
        alias="rai:dataAnnotationPlatform", default=None,
        description="Platform or tool used for annotation (e.g. Label Studio, Prodigy, Amazon Mechanical Turk, custom annotation tool). (rai:dataAnnotationPlatform)"
    )
    rai_data_annotation_analysis: Optional[List[str]] = Field(
        alias="rai:dataAnnotationAnalysis", default=None,
        description="Analysis of annotation quality, inter-annotator agreement metrics (e.g. Cohen's kappa, Fleiss' kappa), and systematic patterns in disagreements between annotators of different socio-demographic groups. Covers how final dataset labels relate to individual annotator responses. (rai:dataAnnotationAnalysis)"
    )
    rai_personal_sensitive_information: Optional[List[str]] = Field(
        alias="rai:personalSensitiveInformation", default=None,
        description="Does the dataset contain data that might be considered sensitive (e.g. race, sexual orientation, religion, biometrics)? List sensitive attribute types present: Gender, Socio-economic status, Geography, Language, Age, Culture, Experience or Seniority, others. (rai:personalSensitiveInformation)"
    )
    rai_data_social_impact: Optional[str] = Field(
        alias="rai:dataSocialImpact", default=None,
        description="Is there anything about the dataset's composition or collection that might impact future uses or create risks/harm (e.g. unfair treatment, legal or financial risks)? Describe potential impacts and any mitigation strategies. (rai:dataSocialImpact)"
    )
    rai_annotations_per_item: Optional[str] = Field(
        alias="rai:annotationsPerItem", default=None,
        description="Number of annotations collected per data item. Multiple annotations per item enable calculation of inter-annotator agreement. (rai:annotationsPerItem)"
    )
    rai_annotator_demographics: Optional[List[str]] = Field(
        alias="rai:annotatorDemographics", default=None,
        description="Demographic information about annotators, if available and relevant (e.g. geographic location, language background, expertise level, age group, gender). (rai:annotatorDemographics)"
    )
    rai_machine_annotation_tools: Optional[List[str]] = Field(
        alias="rai:machineAnnotationTools", default=None,
        description="Automated or machine-learning-based annotation tools used in dataset creation, including NLP pipelines, computer vision models, or other automated labeling systems. Format each entry as 'ToolName version' (e.g. 'spaCy 3.5.0'). (rai:machineAnnotationTools)"
    )
    completeness: Optional[str] = Field(alias="completeness", default=None, description="Assessment of how complete the dataset is relative to its intended scope (e.g. percentage of expected records present, known gaps).")
    prohibitedUses: Optional[str] = Field(alias="prohibitedUses", default=None, description="Explicit statement of prohibited or forbidden uses for this dataset — uses that are not permitted by license, ethics, or policy. Stronger than discouraged uses.")

    # Aggregated metrics for AI-Ready scoring (roll-up properties from release-level sub-crates)
    evi_dataset_count: Optional[int] = Field(alias="evi:datasetCount", default=None, description="Pre-aggregated count of Dataset entities across all sub-crates. Used in AI-Ready Provenance scoring in place of counting entities at query time.")
    evi_computation_count: Optional[int] = Field(alias="evi:computationCount", default=None, description="Pre-aggregated count of Computation and Experiment entities across all sub-crates. Used in AI-Ready Provenance scoring.")
    evi_software_count: Optional[int] = Field(alias="evi:softwareCount", default=None, description="Pre-aggregated count of Software entities across all sub-crates. Used in AI-Ready Provenance scoring.")
    evi_schema_count: Optional[int] = Field(alias="evi:schemaCount", default=None, description="Pre-aggregated count of Schema entities across all sub-crates. Used in AI-Ready Characterization scoring.")
    evi_total_content_size_bytes: Optional[int] = Field(alias="evi:totalContentSizeBytes", default=None, description="Pre-aggregated total content size in bytes across all sub-crate datasets. Used in AI-Ready Characterization scoring.")
    evi_entities_with_summary_stats: Optional[int] = Field(alias="evi:entitiesWithSummaryStats", default=None, description="Pre-aggregated count of entities that have hasSummaryStatistics set. Used in AI-Ready Characterization scoring.")
    evi_entities_with_checksums: Optional[int] = Field(alias="evi:entitiesWithChecksums", default=None, description="Pre-aggregated count of entities that have md5, sha256, or hash set. Used with evi:totalEntities to compute checksum coverage percentage.")
    evi_total_entities: Optional[int] = Field(alias="evi:totalEntities", default=None, description="Pre-aggregated total count of Dataset and Software entities. Used as denominator for checksum coverage in AI-Ready Pre-Model Explainability scoring.")
    evi_formats: Optional[List[str]] = Field(alias="evi:formats", default=None, description="Pre-aggregated list of unique file format values (up to 5) across all entities. Used in AI-Ready Computability scoring.")
    evi_proccesed: Optional[bool] = Field(alias="evi:processed", default=None, description="Flag indicating whether this release-level RO-Crate has been processed and aggregated metrics computed.")

    # D4D Placeholders — flat string versions of D4D_Motivation / D4D_Composition / D4D_Human classes
    addressingGaps: Optional[str] = Field(alias="d4d:addressingGaps", default=None, description="Was there a specific knowledge or resource gap that needed to be filled by creation of this dataset? (D4D_Motivation: AddressingGap)")
    dataAnomalies: Optional[str] = Field(alias="d4d:dataAnomalies", default=None, description="Are there any errors, sources of noise, or redundancies in the dataset? (D4D_Composition: DataAnomaly)")
    contentWarning: Optional[str] = Field(alias="d4d:contentWarning", default=None, description="Does the dataset contain any data that might be offensive, insulting, threatening, or otherwise anxiety-provoking if viewed directly? (D4D_Composition: ContentWarning)")
    informedConsent: Optional[str] = Field(alias="d4d:informedConsent", default=None, description="Details about informed consent procedures used in human subjects research — consent type, documentation, withdrawal mechanisms, and scope. (D4D_Human: InformedConsent)")
    atRiskPopulations: Optional[str] = Field(alias="d4d:atRiskPopulations", default=None, description="Information about protections for at-risk populations (e.g. children, pregnant women, prisoners, cognitively impaired individuals) included in human subjects research. (D4D_Human: AtRiskPopulations)")

    def generateFileElem(self) -> ROCrateMetadataFileElem:
        """ Given an ROCrate Element create an appropriate ROCrateMetadataFileElem
        """
        return ROCrateMetadataFileElem.model_validate({
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {
                "@id": "https://w3id.org/ro/crate/1.2"
            },
            "about": {
                "@id": self.guid
            }
        })

    def get_aiready_warnings(self) -> List[str]:
        """Return a list of warnings for properties recommended for AI-Ready scoring that are missing."""
        warnings = []

        # Fairness / Sustainability
        if not self.identifier:
            warnings.append("Missing 'identifier' (DOI) — affects Findability and Sustainability scoring")
        if not self.dataLicense:
            warnings.append("Missing 'license' — affects Reusability and Ethics scoring")

        # Provenance
        if not self.publisher and not self.principalInvestigator:
            warnings.append("Missing 'publisher' or 'principalInvestigator' — affects Provenance and Computability scoring")

        # Characterization
        if not self.rai_data_biases:
            warnings.append("Missing 'rai:dataBiases' — affects Characterization: potential_sources_of_bias")
        if not self.rai_data_collection_missing_data:
            warnings.append("Missing 'rai:dataCollectionMissingData' — affects Characterization: data_quality")
        if not self.contentSize and not self.hasSummaryStatistics:
            warnings.append("Missing 'contentSize' and 'hasSummaryStatistics' — affects Characterization: statistics")

        # Pre-model explainability
        if not self.rai_data_use_cases and not self.rai_data_limitations:
            warnings.append("Missing 'rai:dataUseCases' and 'rai:dataLimitations' — affects Pre-model: fit_for_purpose")

        # Ethics
        if not self.rai_data_collection:
            warnings.append("Missing 'rai:dataCollection' — affects Ethics: ethically_acquired")
        if not self.ethicalReview:
            warnings.append("Missing 'ethicalReview' — affects Ethics: ethically_managed")
        if not self.confidentialityLevel:
            warnings.append("Missing 'confidentialityLevel' — affects Ethics: secure")

        # Sustainability
        if not self.rai_data_release_maintenance_plan:
            warnings.append("Missing 'rai:dataReleaseMaintenancePlan' — affects Sustainability: domain_appropriate")

        return warnings


class ROCrateDistribution(BaseModel):
    extractedROCrateBucket: Optional[str] = Field(default=None)
    archivedROCrateBucket: Optional[str] = Field(default=None)
    extractedObjectPath: Optional[List[str]] = Field(default=[])
    archivedObjectPath: Optional[str] = Field(default=None)


class ROCrateV1_2(BaseModel):
    context: Optional[Dict] = Field(alias="@context", default=DEFAULT_CONTEXT)
    metadataGraph: List[Union[
        Dataset,
        Software,
        MLModel,
        Computation,
        Annotation,
        Experiment,
        ROCrateMetadataElem,
        ROCrateMetadataFileElem,
        Schema,
        BioChemEntity,
        MedicalCondition,
        Patient,
        Instrument,
        ModelCard,
        Sample,
        Activity,
        Annotation,
        DigitalObject,
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
            "MLModel": MLModel,
            "Computation": Computation,
            "Annotation": Annotation,
            "Experiment": Experiment,
            "Activity": Activity,
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
                item_type = item_type[-1]
            
            if isinstance(item_type, str):
                normalized_type = normalize_type(item_type)
                model_class_to_use = type_map.get(normalized_type)

            # If we found a specific class, use it.
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
            if hasattr(metadata, 'guid') and isinstance(metadata.guid, str) and "http" in metadata.guid:
                metadata.guid = urllib.parse.urlparse(metadata.guid).path.lstrip('/')

        def cleanIdentifierList(identifier_list):
            """Helper to clean a list of identifiers"""
            if identifier_list is None:
                return
            for item in identifier_list:
                if hasattr(item, 'guid') and isinstance(item.guid, str) and "ark:" in item.guid:
                    cleanGUID(item)

        def cleanIdentifierUnion(identifier_union):
            """Helper to clean a Union[IdentifierValue, List[IdentifierValue]] field"""
            if identifier_union is None:
                return
            if isinstance(identifier_union, list):
                cleanIdentifierList(identifier_union)
            elif hasattr(identifier_union, 'guid') and isinstance(identifier_union.guid, str) and "ark:" in identifier_union.guid:
                cleanGUID(identifier_union)

        #clean ROCrate metadata identifier
        rocrateMetadata = self.getCrateMetadata()
        cleanGUID(rocrateMetadata)

        for elem in self.getEVIElements():

            if "ark:" in elem.guid:  
                cleanGUID(elem)

            if isinstance(elem, Dataset):

                cleanIdentifierList(elem.usedByComputation)

                cleanIdentifierList(elem.derivedFrom)

                cleanIdentifierUnion(elem.generatedBy)

                # Clean PROV fields
                cleanIdentifierList(elem.wasGeneratedBy)
                cleanIdentifierList(elem.wasDerivedFrom)
                cleanIdentifierList(elem.wasAttributedTo)

            if isinstance(elem, Software):
                cleanIdentifierList(elem.usedByComputation)

                # Clean PROV fields
                cleanIdentifierList(elem.wasAttributedTo)

            if isinstance(elem, MLModel):
                cleanIdentifierList(elem.usedByComputation)

                cleanIdentifierList(elem.trainedOn)

                # Clean PROV fields
                cleanIdentifierList(elem.wasAttributedTo)

            if isinstance(elem, Computation):

                cleanIdentifierList(elem.usedDataset)

                cleanIdentifierList(elem.generated)

                cleanIdentifierList(elem.usedSoftware)

                cleanIdentifierList(elem.usedMLModel)

                # Clean PROV fields
                cleanIdentifierList(elem.used)
                cleanIdentifierList(elem.wasAssociatedWith)

            if isinstance(elem, Annotation):

                cleanIdentifierList(elem.usedDataset)

                cleanIdentifierList(elem.generated)

                # Clean PROV fields
                cleanIdentifierList(elem.used)
                cleanIdentifierList(elem.wasAssociatedWith)

            if isinstance(elem, Experiment):

                cleanIdentifierList(elem.usedInstrument)

                cleanIdentifierList(elem.usedSample)

                cleanIdentifierList(elem.usedTreatment)

                cleanIdentifierList(elem.usedStain)

                cleanIdentifierList(elem.generated)

                # Clean PROV fields
                cleanIdentifierList(elem.used)
                cleanIdentifierList(elem.wasAssociatedWith)

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

    def getAnnotations(self) -> List[Annotation]:
        """ Filter the Metadata Graph for Annotation Elements

        :param self
        :return: All Annotation metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.Annotation]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, Annotation),
            self.metadataGraph
        ))

        return filterResults

    def getExperiments(self) -> List[Experiment]:
        """ Filter the Metadata Graph for Experiment Elements

        :param self
        :return: All Experiment metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.Experiment]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, Experiment),
            self.metadataGraph
        ))

        return filterResults

    def getMLModels(self) -> List[MLModel]:
        """ Filter the Metadata Graph for MLModel Elements

        :param self
        :return: All MLModel metadata records within the ROCrate
        :rtype List[fairscape_mds.models.rocrate.MLModel]
        """
        filterResults = list(filter(
            lambda x: isinstance(x, MLModel),
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
        Annotation,
        Experiment,
        Dataset,
        Software,
        MLModel,
        Schema,
        BioChemEntity,
        MedicalCondition
        ]]:
        """ Query the metadata graph for elements which require minting identifiers
        """
        return (self.getDatasets() + self.getSoftware() + self.getMLModels() +
                self.getComputations() + self.getAnnotations() + self.getExperiments() +
                self.getSchemas())
