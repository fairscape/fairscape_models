from typing import Optional
from pydantic import BaseModel, Field
from fairscape_models.conversion.models.AIReady import SubCriterionScore

##########################################################################
# --- Datasheet Score Models ---------------------------------------------
##########################################################################


class MotivationScore(BaseModel):
    purpose: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Purpose for dataset creation not specified"
    ))
    creators: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Dataset creators not identified"
    ))
    funding: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Funding information not provided"
    ))
    other_comments: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No additional motivation comments"
    ))

class CompositionScore(BaseModel):
    instance_representation: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Instance types not described"
    ))
    instance_count: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Number of instances not specified"
    ))
    sampling_strategy: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Sampling strategy not documented"
    ))
    instance_data: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Instance data composition not described"
    ))
    labels_targets: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Labels or targets not documented"
    ))
    missing_information: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Missing information not documented"
    ))
    instance_relationships: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Relationships between instances not explicit"
    ))
    data_splits: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Recommended data splits not provided"
    ))
    errors_noise: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Errors, noise, or redundancies not documented"
    ))
    external_dependencies: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="External resource dependencies not documented"
    ))
    confidential_data: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Confidential data presence not documented"
    ))
    offensive_content: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Potentially offensive content not documented"
    ))
    subpopulations: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Subpopulations not identified"
    ))
    individual_identification: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Individual identification risk not assessed"
    ))
    sensitive_data: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Sensitive data categories not documented"
    ))
    other_comments: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No additional composition comments"
    ))

class CollectionProcessScore(BaseModel):
    data_acquisition: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Data acquisition method not documented"
    ))
    collection_mechanisms: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Collection mechanisms not specified"
    ))
    sampling_strategy: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Sampling strategy not documented"
    ))
    data_collectors: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Data collectors and compensation not specified"
    ))
    collection_timeframe: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Collection timeframe not documented"
    ))
    ethical_review: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Ethical review processes not documented"
    ))
    data_source: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Direct vs third-party data source not specified"
    ))
    individual_notification: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Individual notification not documented"
    ))
    individual_consent: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Individual consent not documented"
    ))
    consent_revocation: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Consent revocation mechanism not provided"
    ))
    impact_analysis: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Data protection impact analysis not conducted"
    ))
    other_comments: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No additional collection process comments"
    ))

class PreprocessingCleaningLabelingScore(BaseModel):
    preprocessing_done: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Preprocessing/cleaning/labeling not documented"
    ))
    raw_data_saved: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Raw data preservation not documented"
    ))
    preprocessing_software: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Preprocessing software not available"
    ))
    other_comments: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No additional preprocessing comments"
    ))

class UsesScore(BaseModel):
    prior_usage: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Prior usage not documented"
    ))
    usage_repository: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Usage repository not available"
    ))
    potential_tasks: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Potential use cases not specified"
    ))
    composition_impact: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Composition impact on future uses not documented"
    ))
    prohibited_uses: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Prohibited uses not specified"
    ))
    other_comments: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No additional usage comments"
    ))

class DistributionScore(BaseModel):
    third_party_distribution: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Third-party distribution not specified"
    ))
    distribution_method: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Distribution method not documented"
    ))
    distribution_timing: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Distribution timing not specified"
    ))
    licensing_terms: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Licensing terms not provided"
    ))
    third_party_restrictions: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Third-party IP restrictions not documented"
    ))
    regulatory_restrictions: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Export controls or regulatory restrictions not documented"
    ))
    other_comments: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No additional distribution comments"
    ))

class MaintenanceScore(BaseModel):
    maintainer: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Dataset maintainer not identified"
    ))
    contact_information: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Contact information not provided"
    ))
    erratum: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No erratum available"
    ))
    update_plan: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Dataset update plan not specified"
    ))
    retention_limits: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Data retention limits not specified"
    ))
    version_support: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Version support plan not documented"
    ))
    contribution_mechanism: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Contribution mechanism not available"
    ))
    other_comments: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No additional maintenance comments"
    ))

class DatasheetScore(BaseModel):
    motivation: MotivationScore = Field(default_factory=MotivationScore)
    composition: CompositionScore = Field(default_factory=CompositionScore)
    collection_process: CollectionProcessScore = Field(default_factory=CollectionProcessScore)
    preprocessing_cleaning_labeling: PreprocessingCleaningLabelingScore = Field(default_factory=PreprocessingCleaningLabelingScore)
    uses: UsesScore = Field(default_factory=UsesScore)
    distribution: DistributionScore = Field(default_factory=DistributionScore)
    maintenance: MaintenanceScore = Field(default_factory=MaintenanceScore)