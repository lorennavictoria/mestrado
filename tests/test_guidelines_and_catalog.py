from pathlib import Path

from prognostico.guidelines import GuidelineRetriever
from prognostico.eligibility import ClinicalEligibilityAgent
from prognostico.models import MedicalRecord
from prognostico.record import MedicalRecordValidator
from prognostico.state import PatientStateBuilder
from prognostico.treatment_catalog import evaluate_catalog

from test_thyroid_pipeline import load_record


ROOT = Path(__file__).parents[1]


def test_guideline_retriever_returns_citable_local_passages():
    retriever = GuidelineRetriever(ROOT / "guidelines" / "processed" / "index.json")

    passages = retriever.retrieve("radioiodine differentiated thyroid cancer", scope="differentiated")

    assert passages
    assert passages[0].source and ":p" in passages[0].source
    assert passages[0].document_id
    assert passages[0].guideline_version
    assert passages[0].page


def test_guideline_retriever_honors_histology_scope():
    retriever = GuidelineRetriever(ROOT / "guidelines" / "processed" / "index.json")

    passages = retriever.retrieve("anaplastic thyroid cancer", scope="anaplastic")

    assert passages
    assert all("anaplastic" in item.scope for item in passages)


def test_catalog_marks_missing_criteria_as_indeterminate():
    raw = load_record().model_dump()
    raw["prior_treatments"] = []
    raw["cancer"]["iodine_avidity"] = None
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(MedicalRecord.model_validate(raw)))

    candidates = evaluate_catalog(state)
    radioiodine = next(item for item in candidates if item.treatment_id == "DTC_RADIOIODINE")

    assert radioiodine.status == "insufficient_information"
    assert radioiodine.patient_fact_ids == ["cancer_documented"]
    assert radioiodine.eligibility_missing == ["post_thyroidectomy"]
    assert radioiodine.components == ["I-131"]
    assert radioiodine.references == ["ATA_DTC_2025"]


def test_eligibility_agent_preserves_catalog_missing_requirement():
    raw = load_record().model_dump()
    raw["prior_treatments"] = []
    raw["cancer"]["iodine_avidity"] = None
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(MedicalRecord.model_validate(raw)))
    radioiodine = next(item for item in evaluate_catalog(state) if item.treatment_id == "DTC_RADIOIODINE")

    assessment = ClinicalEligibilityAgent(GuidelineRetriever(ROOT / "guidelines" / "processed" / "index.json")).assess(state, radioiodine)

    assert assessment.status == "indeterminate"
    assert assessment.missing_requirements == ["post_thyroidectomy"]
    assert assessment.citations
