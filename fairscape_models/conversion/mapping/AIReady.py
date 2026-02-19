from typing import Any, Dict, List, Union
from pathlib import Path
import json
from fairscape_models.conversion.models.AIReady import AIReadyScore, FairnessScore, ProvenanceScore, CharacterizationScore, PreModelExplainabilityScore, EthicsScore, SustainabilityScore, ComputabilityScore, SubCriterionScore
from fairscape_models.rocrate import ROCrateV1_2

def score_rocrate(crate_data: Union[Dict[str, Any], ROCrateV1_2]) -> AIReadyScore:
    """
    Score a single RO-Crate or a release (RO-Crate of RO-Crates).
    
    Args:
        crate_data: Either a parsed RO-Crate dict or ROCrateV1_2 model
    
    Returns:
        AIReadyScore with all criteria evaluated
    """
    if isinstance(crate_data, dict):
        crate = ROCrateV1_2.model_validate(crate_data)
    else:
        crate = crate_data
    
    metadata_graph = []
    
    for entity in crate.metadataGraph:
        entity_dict = entity.model_dump(by_alias=True)
        metadata_graph.append(entity_dict)
    
    for entity in crate.metadataGraph:
        if hasattr(entity, 'ro-crate-metadata'):
            metadata_path = Path(getattr(entity, 'ro-crate-metadata'))
            try:
                with metadata_path.open("r") as f:
                    sub_crate_dict = json.load(f)
                sub_rocrate = ROCrateV1_2.model_validate(sub_crate_dict)
                
                for sub_item in sub_rocrate.metadataGraph:
                    sub_dict = sub_item.model_dump(by_alias=True)
                    metadata_graph.append(sub_dict)
            except:
                pass
    root_data = None
    for entity_dict in metadata_graph:
        if entity_dict.get("@id") == "ro-crate-metadata.json":
            about_ref = entity_dict.get("about", {})
            root_id = about_ref.get("@id") if isinstance(about_ref, dict) else about_ref
            if root_id:
                for e in metadata_graph:
                    if e.get("@id") == root_id:
                        root_data = e
                        break
                break
    
    if not root_data:
        raise ValueError("Root entity not found in RO-Crate metadata graph.")
    
    score = AIReadyScore(name=f"AI-Ready Score for {root_data.get('name')}")
    _score_fairness(score.fairness, root_data)
    _score_provenance(score.provenance, root_data, metadata_graph)
    _score_characterization(score.characterization, root_data, metadata_graph)
    _score_pre_model(score.pre_model_explainability, root_data, metadata_graph)
    _score_ethics(score.ethics, root_data)
    _score_sustainability(score.sustainability, root_data)
    _score_computability(score.computability, root_data, metadata_graph)
    
    return score

def _get_type(entity: Dict[str, Any]) -> List[str]:
    """Get type from either @type or metadataType field."""
    type_val = entity.get("@type") or entity.get("metadataType") or []
    if isinstance(type_val, str):
        return type_val
    return type_val[-1]

def _get_format(entity: Dict[str, Any]) -> str:
    """Get format from either fileFormat field."""
    return entity.get("format", "")

def _score_fairness(fairness: FairnessScore, root_data: Dict[str, Any]):
    """Score FAIRness criteria."""
    id_val = root_data.get("@id", "")
    doi = root_data.get("identifier", "")
    
    if doi and str(doi).strip():
        findable_score = SubCriterionScore(
            has_content=True,
            details=f"Dataset has DOI: {doi}"
        )
        fairness.findable = findable_score
    elif id_val and str(id_val).strip():
        findable_score = SubCriterionScore(
            has_content=True,
            details=f"Dataset has persistent identifier: {id_val}"
        )
        fairness.findable = findable_score
    
    license_val = root_data.get("license", "")
    if license_val and str(license_val).strip():
        fairness.reusable = SubCriterionScore(
            has_content=True,
            details=f"License: {license_val}"
        )

def _score_provenance(provenance: ProvenanceScore, root_data: Dict[str, Any], metadata_graph: List[Dict]):
    """Score Provenance criteria - simplified to just count entities."""
    actors = []
    author = root_data.get("author")
    if author:
        if isinstance(author, list):
            actors.append(f"{len(author)} authors")
        else:
            actors.append("Author specified")
    
    publisher = root_data.get("publisher")
    if publisher:
        if isinstance(publisher, dict):
            actors.append(f"Publisher: {publisher.get('name', 'Unknown')}")
        else:
            actors.append(f"Publisher: {publisher}")
    
    pi = root_data.get("principalInvestigator")
    if pi:
        actors.append(f"PI: {pi}")
    
    if actors:
        provenance.key_actors_identified = SubCriterionScore(
            has_content=True,
            details=", ".join(actors)
        )

    # Check for aggregated metrics first (from release-level RO-Crate)
    dataset_count = root_data.get("evi:datasetCount")
    computation_count = root_data.get("evi:computationCount")
    software_count = root_data.get("evi:softwareCount")

    if dataset_count is not None:
        # Use pre-aggregated values from release
        datasets_count = dataset_count
        transformations_count = computation_count
        software_count = software_count
    else:
        # Fall back to counting in metadata_graph (for backwards compatibility)
        datasets_count = 0
        transformations_count = 0
        software_count = 0

        for entity in metadata_graph:
            entity_type = _get_type(entity)

            if "Dataset" in entity_type:
                datasets_count += 1

            if "Computation" in entity_type or "Experiment" in entity_type:
                transformations_count += 1

            if "Software" in entity_type:
                software_count += 1
    
    if datasets_count > 0:
        provenance.transparent = SubCriterionScore(
            has_content=True,
            details=f"{datasets_count} dataset(s) documented"
        )
    
    if transformations_count > 0:
        provenance.traceable = SubCriterionScore(
            has_content=True,
            details=f"{transformations_count} computation/experiment steps documented"
        )
    
    if software_count > 0:
        provenance.interpretable = SubCriterionScore(
            has_content=True,
            details=f"{software_count} software instances documented"
        )

def _score_characterization(characterization: CharacterizationScore, root_data: Dict[str, Any], metadata_graph: List[Dict]):
    """Score Characterization criteria."""
    bias = root_data.get("rai:dataBiases", "")
    if bias and str(bias).strip():
        characterization.potential_sources_of_bias = SubCriterionScore(
            has_content=True,
            details=str(bias)[:200] + ("..." if len(str(bias)) > 200 else "")
        )
        
    missDataDoc = root_data.get("rai:dataCollectionMissingData", "")
    if missDataDoc and str(missDataDoc).strip():
        characterization.data_quality = SubCriterionScore(
            has_content=True,
            details=str(missDataDoc)[:200] + ("..." if len(str(missDataDoc)) > 200 else "")
        )

    schema_count = root_data.get("evi:schemaCount")

    if schema_count is not None:
       pass
    else:
        # Fall back to counting in metadata_graph (for backwards compatibility)
        schema_count = 0

        for entity in metadata_graph:
            entity_type = _get_type(entity)

            if "Schema" in entity_type:
                schema_count += 1
    
    if schema_count > 0:
        characterization.standards = SubCriterionScore(
            has_content=True,
            details=f"{schema_count} schema(s) documented"
        )

    # Check for aggregated metrics first
    total_size_bytes = root_data.get("evi:totalContentSizeBytes")
    stats_count_agg = root_data.get("evi:entitiesWithSummaryStats")

    if total_size_bytes is not None:
        # Use pre-aggregated statistics
        total_size = total_size_bytes
        stats_count = stats_count_agg
    else:
        # Fall back to iterating metadata_graph
        total_size = 0
        stats_count = 0

        for entity in metadata_graph:
            entity_type = _get_type(entity)

            if "Dataset" in entity_type or "ROCrate" in entity_type:
                size = entity.get("contentSize", "")
                if size:
                    try:
                        if isinstance(size, str):
                            if "TB" in size:
                                total_size += float(size.replace("TB", "").strip()) * 1e12
                            elif "GB" in size:
                                total_size += float(size.replace("GB", "").strip()) * 1e9
                            elif "MB" in size:
                                total_size += float(size.replace("MB", "").strip()) * 1e6
                    except:
                        pass

                if entity.get("hasSummaryStatistics"):
                    stats_count += 1
    
    details = []
    if total_size > 0:
        if total_size >= 1e12:
            details.append(f"Total size: {total_size/1e12:.1f} TB")
        elif total_size >= 1e9:
            details.append(f"Total size: {total_size/1e9:.1f} GB")
        else:
            details.append(f"Total size: {total_size/1e6:.1f} MB")
    
    if stats_count > 0:
        details.append(f"Summary statistics available for {stats_count} dataset(s)")
    
    if details:
        characterization.statistics = SubCriterionScore(
            has_content=True,
            details=", ".join(details)
        )

def _score_pre_model(pre_model: PreModelExplainabilityScore, root_data: Dict[str, Any], metadata_graph: List[Dict]):
    """Score Pre-Model Explainability criteria."""
    use_cases = root_data.get("rai:dataUseCases", "")
    limitations = root_data.get("rai:dataLimitations", "")
    
    details = []
    if use_cases and str(use_cases).strip():
        details.append(f"Use cases: {use_cases}")
    if limitations and str(limitations).strip():
        details.append(f"Limitations: {limitations}")

    if details:
        pre_model.fit_for_purpose = SubCriterionScore(
            has_content=True,
            details=", ".join(details)
        )

    # Check for aggregated metrics first
    total_entities = root_data.get("evi:totalEntities")
    entities_with_checksums = root_data.get("evi:entitiesWithChecksums")

    if total_entities is not None:
        # Use pre-aggregated checksum data
        total = total_entities
        with_checksum = entities_with_checksums
    else:
        # Fall back to counting in metadata_graph
        total = 0
        with_checksum = 0

        for entity in metadata_graph:
            entity_type = _get_type(entity)

            if "Dataset" in entity_type or "Software" in entity_type or "ROCrate" in entity_type:
                total += 1
                if entity.get("md5") or entity.get("MD5"):
                    with_checksum += 1
    
    if total > 0 and with_checksum > 0:
        percentage = (with_checksum / total) * 100
        pre_model.verifiable = SubCriterionScore(
            has_content=True,
            details=f"{percentage:.0f}% of files have checksums ({with_checksum}/{total})"
        )
def _score_ethics(ethics: EthicsScore, root_data: Dict[str, Any]):
    """Score Ethics criteria."""
    details = []
    collection = root_data.get("rai:dataCollection", "")
    if collection and str(collection).strip():
        details.append(f"Data collection: {collection}")
    
    addl_props = root_data.get("additionalProperty", [])
    if isinstance(addl_props, list):
        for prop in addl_props:
            if isinstance(prop, dict) and prop.get("name") == "Human Subject":
                hs_val = prop.get("value")
                if hs_val:
                    details.append(f"Human subject info: {hs_val}")
                    break
    
    if details:
        ethics.ethically_acquired = SubCriterionScore(
            has_content=True,
            details=", ".join(details)
        )
    
    details = []
    ethical_review = root_data.get("ethicalReview", "")
    if ethical_review and str(ethical_review).strip():
        details.append(f"Ethical review: {ethical_review}")
    
    if isinstance(addl_props, list):
        for prop in addl_props:
            if isinstance(prop, dict) and prop.get("name") == "Data Governance Committee":
                gov_val = prop.get("value")
                if gov_val:
                    details.append(f"Governance: {gov_val}")
                    break
    
    if details:
        ethics.ethically_managed = SubCriterionScore(
            has_content=True,
            details=", ".join(details)
        )
    
    details = []
    license_val = root_data.get("license", "")
    if license_val:
        details.append(f"License: {license_val}")
    
    psi = root_data.get("rai:personalSensitiveInformation", "")
    if psi and str(psi).strip():
        details.append(f"Sensitive info: {psi}")
    
    if isinstance(addl_props, list):
        for prop in addl_props:
            if isinstance(prop, dict) and prop.get("name") == "Prohibited Uses":
                pu_val = prop.get("value")
                if pu_val:
                    details.append(f"Prohibited uses: {pu_val}")
                    break
    
    if details:
        ethics.ethically_disseminated = SubCriterionScore(
            has_content=True,
            details=", ".join(details)
        )
    
    conf = root_data.get("confidentialityLevel", "")
    if conf and str(conf).strip():
        ethics.secure = SubCriterionScore(
            has_content=True,
            details=f"Confidentiality level: {conf}"
        )
def _score_sustainability(sustainability: SustainabilityScore, root_data: Dict[str, Any]):
    """Score Sustainability criteria."""
    id_val = root_data.get("@id", "")
    doi = root_data.get("identifier", "")
    
    if doi and str(doi).strip():
        sustainability.persistent = SubCriterionScore(
            has_content=True,
            details=f"Dataset has DOI: {doi}"
        )
    elif id_val and str(id_val).strip():
        sustainability.persistent = SubCriterionScore(
            has_content=True,
            details=f"Dataset has persistent identifier: {id_val}"
        )
    
    maint = root_data.get("rai:dataReleaseMaintenancePlan", "")
    if maint and str(maint).strip():
        sustainability.domain_appropriate = SubCriterionScore(
            has_content=True,
            details="Maintenance plan: " + maint
        )
    
    addl_props = root_data.get("additionalProperty", [])
    if isinstance(addl_props, list):
        for prop in addl_props:
            if isinstance(prop, dict) and prop.get("name") == "Data Governance Committee":
                gov_val = prop.get("value")
                if gov_val:
                    sustainability.well_governed = SubCriterionScore(
                        has_content=True,
                        details=f"Governance committee: {gov_val}"
                    )
                    break

def _score_computability(computability: ComputabilityScore, root_data: Dict[str, Any], metadata_graph: List[Dict]):
    """Score Computability criteria."""
    # Check for aggregated metrics first
    formats_agg = root_data.get("evi:formats")

    if formats_agg is not None:
        # Use pre-aggregated formats
        formats = set(formats_agg)
    else:
        # Fall back to collecting from metadata_graph
        formats = set()

        for entity in metadata_graph:
            entity_type = _get_type(entity)

            if "Dataset" in entity_type or "Software" in entity_type:
                fmt = _get_format(entity)
                if fmt:
                    formats.add(str(fmt))
    
    if formats:
        fmt_list = sorted(list(formats))[:5]
        suffix = "..." if len(formats) > 5 else ""
        computability.standardized = SubCriterionScore(
            has_content=True,
            details=f"Formats: {', '.join(fmt_list)}{suffix}"
        )
        
    if root_data.get("publisher"):
        computability.computationally_accessible = SubCriterionScore(
            has_content=True,
            details=f"Publisher: {root_data.get('publisher')}"
        )

def _build_ai_ready_score(value: Any, *, converter_instance) -> AIReadyScore:
    """Builder function for use with ROCToTargetConverter."""
    crate = converter_instance.source_crate
    metadata_graph = []
    
    for entity in crate.metadataGraph:
        entity_dict = entity.model_dump(by_alias=True)
        metadata_graph.append(entity_dict)
    
    for entity in crate.metadataGraph:
        if hasattr(entity, 'ro-crate-metadata'):
            metadata_path = Path(getattr(entity, 'ro-crate-metadata'))
            try:
                with metadata_path.open("r") as f:
                    sub_crate_dict = json.load(f)
                sub_rocrate = ROCrateV1_2.model_validate(sub_crate_dict)
                
                for sub_item in sub_rocrate.metadataGraph:
                    sub_dict = sub_item.model_dump(by_alias=True)
                    metadata_graph.append(sub_dict)
            except:
                pass
    
    root_data = None
    for entity_dict in metadata_graph:
        if entity_dict.get("@id") == "ro-crate-metadata.json":
            about_ref = entity_dict.get("about", {})
            root_id = about_ref.get("@id") if isinstance(about_ref, dict) else about_ref
            if root_id:
                for e in metadata_graph:
                    if e.get("@id") == root_id:
                        root_data = e
                        break
                break
    
    if not root_data:
        raise ValueError("Root entity not found in RO-Crate metadata graph.")
    
    score = AIReadyScore()
    _score_fairness(score.fairness, root_data)
    _score_provenance(score.provenance, root_data, metadata_graph)
    _score_characterization(score.characterization, root_data, metadata_graph)
    _score_pre_model(score.pre_model_explainability, root_data, metadata_graph)
    _score_ethics(score.ethics, root_data)
    _score_sustainability(score.sustainability, root_data)
    _score_computability(score.computability, root_data, metadata_graph)
    
    return score

AIREADY_MAPPING_CONFIGURATION = {
    "entity_map": {
        ("ROCrateMetadataElem", "ROOT"): {
            "target_class": AIReadyScore,
            "mapping_def": {},
            "builder_func": _build_ai_ready_score
        },
    },
    "sub_mappings": {},
    "assembly_instructions": [],
}