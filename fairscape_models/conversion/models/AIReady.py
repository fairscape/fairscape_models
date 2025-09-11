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
        has_content=False, details="No persistent identifier found"
    ))
    accessible: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="The RO-Crate's JSON-LD metadata is machine-readable and publicly accessible by design."
    ))
    interoperable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="The dataset uses the schema.org vocabulary within the RO-Crate framework and conforms to the Croissant RAI specification for interoperability."
    ))
    reusable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No license specified"
    ))

class ProvenanceScore(BaseModel):
    transparent: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No root datasets identified"
    ))
    traceable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No transformation steps documented"
    ))
    interpretable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No software documented"
    ))
    key_actors_identified: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No key actors identified"
    ))

class CharacterizationScore(BaseModel):
    semantics: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="Data is semantically described using the schema.org vocabulary within a machine-readable RO-Crate."
    ))
    statistics: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No statistical characterization available"
    ))
    standards: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="This dataset adheres to the RO-Crate 1.2 and Croissant RAI 1.0 community standards."
    ))
    potential_sources_of_bias: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No bias description provided"
    ))
    data_quality: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="Data quality procedures not documented"
    ))

class PreModelExplainabilityScore(BaseModel):
    data_documentation_template: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="Documentation is provided via the RO-Crate's structured JSON-LD metadata, this HTML Datasheet, and Croissant RAI properties."
    ))
    fit_for_purpose: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No use cases or limitations specified"
    ))
    verifiable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No files to verify"
    ))

class EthicsScore(BaseModel):
    ethically_acquired: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No ethical acquisition information"
    ))
    ethically_managed: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No ethical management information"
    ))
    ethically_disseminated: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No dissemination controls specified"
    ))
    secure: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No security requirements specified"
    ))

class SustainabilityScore(BaseModel):
    persistent: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No persistent identifier found"
    ))
    domain_appropriate: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No maintenance plan specified"
    ))
    well_governed: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No governance structure specified"
    ))
    associated: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="All data, software, and computations are explicitly linked within the RO-Crate's provenance graph."
    ))

class ComputabilityScore(BaseModel):
    standardized: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=False, details="No format information available"
    ))
    computationally_accessible: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="Data is hosted in public repositories (e.g., NCBI, MassIVE, Dataverse) that support programmatic access."
    ))
    portable: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="The dataset is packaged as a self-contained RO-Crate, a standard designed for portability across systems."
    ))
    contextualized: SubCriterionScore = Field(default_factory=lambda: SubCriterionScore(
        has_content=True, details="Context is provided by the RO-Crate's graph structure and detailed in properties such as rai:dataLimitations."
    ))

class AIReadyScore(BaseModel):
    fairness: FairnessScore = Field(default_factory=FairnessScore)
    provenance: ProvenanceScore = Field(default_factory=ProvenanceScore)
    characterization: CharacterizationScore = Field(default_factory=CharacterizationScore)
    pre_model_explainability: PreModelExplainabilityScore = Field(default_factory=PreModelExplainabilityScore)
    ethics: EthicsScore = Field(default_factory=EthicsScore)
    sustainability: SustainabilityScore = Field(default_factory=SustainabilityScore)
    computability: ComputabilityScore = Field(default_factory=ComputabilityScore)