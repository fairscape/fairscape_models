from typing import Optional
from pydantic import BaseModel, Field

##########################################################################
# --- AI-Readiness Score Models ------------------------------------------
##########################################################################

class SubCriterionScore(BaseModel):
    """Score for an individual sub-criterion."""
    has_content: bool = Field(default=False, description="Whether the sub-criterion has content/evidence")
    details: Optional[str] = Field(default=None, description="Details about evidence or reasoning")

class FairnessScore(BaseModel):
    findable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No persistent identifier found. To add an identifier, set 'identifier' (for DOI) or '@id' in root dataset"
    ))
    accessible: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="The RO-Crate's JSON-LD metadata is machine-readable and publicly accessible by design."
    ))
    interoperable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="The dataset uses the schema.org vocabulary within the RO-Crate framework and conforms to the Croissant RAI specification for interoperability."
    ))
    reusable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No license specified. To add a license, set 'license' in root dataset"
    ))

class ProvenanceScore(BaseModel):
    transparent: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No root datasets identified. To document datasets, add entities with @type 'Dataset' to metadata graph"
    ))
    traceable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No transformation steps documented. To document workflows, add entities with @type 'Computation' or 'Experiment' to metadata graph"
    ))
    interpretable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No software documented. To document software, add entities with @type 'Software' to metadata graph"
    ))
    key_actors_identified: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No key actors identified. To add actors, set 'author', 'publisher', or 'principalInvestigator' in root dataset"
    ))

class CharacterizationScore(BaseModel):
    semantics: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="Data is semantically described using the schema.org vocabulary within a machine-readable RO-Crate."
    ))
    statistics: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No statistical characterization available. To add statistics, set 'contentSize' and/or 'hasSummaryStatistics' in Dataset/ROCrate entities"
    ))
    standards: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No schemas provided for datasets. To document schemas, add entities with @type 'schema' to metadata graph"
    ))
    potential_sources_of_bias: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No bias description provided. To document biases, set 'rai:dataBiases' in root dataset"
    ))
    data_quality: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Data quality procedures not documented. To document quality, set 'rai:dataCollectionMissingData' in root dataset"
    ))

class PreModelExplainabilityScore(BaseModel):
    data_documentation_template: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="Documentation is provided via the RO-Crate's structured JSON-LD metadata, this HTML Datasheet, and Croissant RAI properties."
    ))
    fit_for_purpose: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No use cases or limitations specified. To document purpose, set 'rai:dataUseCases' and/or 'rai:dataLimitations' in root dataset"
    ))
    verifiable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No checksums available. To add checksums for verification, set 'md5' or 'MD5' in Dataset/Software/ROCrate entities"
    ))

class EthicsScore(BaseModel):
    ethically_acquired: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No ethical acquisition information. To document data collection, set 'rai:dataCollection' and/or additionalProperty with name='Human Subject' in root dataset"
    ))
    ethically_managed: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No ethical management information. To document ethical oversight, set 'ethicalReview' and/or additionalProperty with name='Data Governance Committee' in root dataset"
    ))
    ethically_disseminated: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No dissemination controls specified. To document usage controls, set 'license', 'rai:personalSensitiveInformation', and/or additionalProperty with name='Prohibited Uses' in root dataset"
    ))
    secure: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No security requirements specified. To document security level, set 'confidentialityLevel' in root dataset"
    ))

class SustainabilityScore(BaseModel):
    persistent: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No persistent identifier found. To add an identifier, set 'identifier' (for DOI) or '@id' in root dataset"
    ))
    domain_appropriate: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Data release plan not documented. To add a release plan, set 'rai:dataReleaseMaintenancePlan' in root dataset"
    ))
    well_governed: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No governance structure specified. To document governance, set additionalProperty with name='Data Governance Committee' in root dataset"
    ))
    associated: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="All data, software, and computations are explicitly linked within the RO-Crate's provenance graph."
    ))

class ComputabilityScore(BaseModel):
    standardized: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No format information available. To document file formats, set 'format' in Dataset/Software entities"
    ))
    computationally_accessible: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No publisher provided. To specify publisher, set 'publisher' in root dataset"
    ))
    portable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="The dataset is packaged as a self-contained RO-Crate, a standard designed for portability across systems."
    ))
    contextualized: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="Context is provided by the RO-Crate's graph structure and detailed in properties such as rai:dataLimitations."
    ))

class AIReadyScore(BaseModel):
    name: str = "AI-Ready Score"
    fairness: FairnessScore = Field(default_factory=FairnessScore)
    provenance: ProvenanceScore = Field(default_factory=ProvenanceScore)
    characterization: CharacterizationScore = Field(default_factory=CharacterizationScore)
    pre_model_explainability: PreModelExplainabilityScore = Field(default_factory=PreModelExplainabilityScore)
    ethics: EthicsScore = Field(default_factory=EthicsScore)
    sustainability: SustainabilityScore = Field(default_factory=SustainabilityScore)
    computability: ComputabilityScore = Field(default_factory=ComputabilityScore)