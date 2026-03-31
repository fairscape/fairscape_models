# tests/test_annotated.py

import pytest
from fairscape_models.annotated_computation import AnnotatedComputation, CodeAnalysis, DatasetSummary
from fairscape_models.annotated_evidence_graph import AnnotatedEvidenceGraph


def _make_annotated_computation(**overrides):
    base = {
        "@id": "ark:59852/annotation-001",
        "name": "Annotation of step 1",
        "author": "claude-opus-4",
        "description": "LLM annotation of computation step 1",
        "evi:annotates": {"@id": "ark:59852/computation-001"},
        "evi:stepSummary": "This step loads raw data and normalises it.",
        "evi:llmModel": "claude-opus-4",
        "dateCreated": "2026-03-18",
    }
    base.update(overrides)
    return AnnotatedComputation.model_validate(base)


def _make_annotated_evidence_graph(**overrides):
    base = {
        "@id": "ark:59852/aeg-001",
        "name": "Annotated Evidence Graph",
        "author": "claude-opus-4",
        "description": "Full annotated evidence graph for the crate",
        "evi:annotates": {"@id": "ark:59852/rocrate-001"},
        "@graph": {
            "ark:59852/computation-001": {"@id": "ark:59852/computation-001", "@type": "Computation"},
        },
        "evi:executiveSummary": "Pipeline processes raw data into embeddings.",
        "evi:narrativeSummary": "The pipeline consists of three steps.",
        "evi:llmModel": "claude-opus-4",
        "dateCreated": "2026-03-18",
    }
    base.update(overrides)
    return AnnotatedEvidenceGraph.model_validate(base)


class TestAnnotatedComputation:

    def test_prov_fields_auto_populated(self):
        ac = _make_annotated_computation()
        # wasDerivedFrom should point to the annotated computation
        assert len(ac.wasDerivedFrom) == 1
        assert ac.wasDerivedFrom[0].guid == "ark:59852/computation-001"
        # wasAttributedTo should point to the LLM model
        assert ac.wasAttributedTo == ["claude-opus-4"]

    def test_minimal_fields(self):
        ac = _make_annotated_computation()
        assert ac.name == "Annotation of step 1"
        assert ac.stepSummary == "This step loads raw data and normalises it."
        assert ac.llmModel == "claude-opus-4"
        assert ac.annotates.guid == "ark:59852/computation-001"

    def test_with_code_analysis(self):
        ac = _make_annotated_computation(**{
            "evi:codeAnalysis": [
                {
                    "software": {"@id": "ark:59852/software-001"},
                    "summary": "Reads CSV files and applies z-score normalisation.",
                    "keyFunctions": ["pandas.read_csv", "scipy.stats.zscore"],
                    "concerns": ["No null-value handling"],
                }
            ],
        })
        assert len(ac.codeAnalysis) == 1
        assert isinstance(ac.codeAnalysis[0], CodeAnalysis)
        assert ac.codeAnalysis[0].software.guid == "ark:59852/software-001"
        assert "pandas.read_csv" in ac.codeAnalysis[0].keyFunctions

    def test_with_dataset_summaries(self):
        ac = _make_annotated_computation(**{
            "evi:inputSummaries": [
                {
                    "dataset": {"@id": "ark:59852/dataset-001"},
                    "name": "Raw data",
                    "role": "input",
                    "description": "Raw measurements",
                }
            ],
            "evi:outputSummaries": [
                {
                    "dataset": {"@id": "ark:59852/dataset-002"},
                    "role": "output",
                }
            ],
        })
        assert len(ac.inputSummaries) == 1
        assert isinstance(ac.inputSummaries[0], DatasetSummary)
        assert ac.inputSummaries[0].dataset.guid == "ark:59852/dataset-001"
        assert len(ac.outputSummaries) == 1
        assert ac.outputSummaries[0].dataset.guid == "ark:59852/dataset-002"

    def test_serialization_roundtrip(self):
        ac = _make_annotated_computation()
        dumped = ac.model_dump(by_alias=True)
        assert dumped["evi:stepSummary"] == "This step loads raw data and normalises it."
        assert dumped["evi:annotates"]["@id"] == "ark:59852/computation-001"
        assert dumped["evi:llmModel"] == "claude-opus-4"
        restored = AnnotatedComputation.model_validate(dumped)
        assert restored.stepSummary == ac.stepSummary


class TestAnnotatedEvidenceGraph:

    def test_prov_fields_auto_populated(self):
        aeg = _make_annotated_evidence_graph()
        # wasDerivedFrom should point to the annotated crate
        assert len(aeg.wasDerivedFrom) == 1
        assert aeg.wasDerivedFrom[0].guid == "ark:59852/rocrate-001"
        # wasAttributedTo should point to the LLM model
        assert aeg.wasAttributedTo == ["claude-opus-4"]

    def test_minimal_fields(self):
        aeg = _make_annotated_evidence_graph()
        assert aeg.executiveSummary == "Pipeline processes raw data into embeddings."
        assert aeg.narrativeSummary == "The pipeline consists of three steps."
        assert aeg.annotates.guid == "ark:59852/rocrate-001"
        assert "ark:59852/computation-001" in aeg.graph

    def test_with_optional_fields(self):
        aeg = _make_annotated_evidence_graph(**{
            "evi:keyFindings": ["Finding 1", "Finding 2"],
            "evi:concerns": ["Missing validation step"],
            "evi:llmTemperature": 0.7,
            "evi:interpreterVersion": "1.2.0",
            "evi:stepAnnotations": [{"@id": "ark:59852/annotation-001"}],
        })
        assert aeg.keyFindings == ["Finding 1", "Finding 2"]
        assert aeg.concerns == ["Missing validation step"]
        assert aeg.llmTemperature == 0.7
        assert aeg.interpreterVersion == "1.2.0"
        assert len(aeg.stepAnnotations) == 1
        assert aeg.stepAnnotations[0].guid == "ark:59852/annotation-001"

    def test_serialization_roundtrip(self):
        aeg = _make_annotated_evidence_graph()
        dumped = aeg.model_dump(by_alias=True)
        assert dumped["evi:executiveSummary"] == "Pipeline processes raw data into embeddings."
        assert dumped["evi:annotates"]["@id"] == "ark:59852/rocrate-001"
        restored = AnnotatedEvidenceGraph.model_validate(dumped)
        assert restored.executiveSummary == aeg.executiveSummary
