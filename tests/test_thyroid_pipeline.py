import json
from pathlib import Path

from prognostico.llm import OllamaClient
from prognostico.models import FailureOutcome, MedicalRecord, TreatmentCandidate
from prognostico.record import MedicalRecordValidator
from prognostico.state import PatientStateBuilder
from prognostico.thyroid_pipeline import CounterfactualEngine, FailureDraft, ThyroidPrognosisPipeline, reasoning_context


ROOT = Path(__file__).parents[1]


def load_record() -> MedicalRecord:
    return MedicalRecord.model_validate(json.loads((ROOT / "examples" / "caso_prognostico.json").read_text()))


def test_validator_preserves_chronological_laboratory_values_and_missing_data():
    record = load_record()
    validation = MedicalRecordValidator().validate(record)

    assert [item.test_name for item in validation.normalized_record.lab_results] == ["creatinina", "TSH"]
    assert not validation.temporal_conflicts


def test_patient_state_keeps_provenance_for_active_problems():
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(load_record()))

    progression = next(item for item in state.active_problems if item.fact_id == "cancer_progression")
    hypertension = next(item for item in state.active_problems if item.fact_id == "comorbidity:hipertensão arterial")
    assert progression.evidence[0].source == "cancer"
    assert hypertension.status == "active"


def test_validator_preserves_source_data_warnings():
    record = load_record().model_copy(update={"data_warnings": ["fonte estruturada incompleta"]})

    validation = MedicalRecordValidator().validate(record)

    assert "fonte estruturada incompleta" in validation.warnings


def test_state_enriches_only_available_structured_data():
    raw = load_record().model_dump()
    raw["lab_results"] = [
        {"collected_at": "2026-02-24", "test_name": "calcium", "value": "7.8", "unit": "mg/dL", "interpretation": "low"},
        {"collected_at": "2026-02-25", "test_name": "calcium", "value": "7.6", "unit": "mg/dL", "interpretation": "low"},
    ]
    raw["vital_signs"] = [{"measured_at": "2026-03-01", "name": "heart rate", "value": 82, "unit": "bpm"}]
    raw["medications"] = [
        {"name": "levothyroxine", "status": "active", "dose": "100 mcg"},
        {"name": "calcium carbonate", "status": "completed"},
    ]

    state = PatientStateBuilder().build(MedicalRecordValidator().validate(MedicalRecord.model_validate(raw)))
    facts = {item.fact_id: item for item in state.active_problems}

    assert facts["abnormal_lab_summary:calcium"].evidence[-1].finding == "calcium=7.6 mg/dL"
    assert facts["vital:heart rate:2026-03-01"].status == "active"
    assert facts["medication:levothyroxine:unknown"].status == "active"
    assert not any(item.fact_id.startswith("medication:calcium carbonate") and item.status == "active" for item in state.active_problems)
    assert reasoning_context(state)["medication_history"] == [
        {"name": "levothyroxine", "status": "active", "dose": "100 mcg", "route": None},
        {"name": "calcium carbonate", "status": "completed", "dose": None, "route": None},
    ]


def test_pipeline_default_counterfactual_depth_is_three():
    pipeline = ThyroidPrognosisPipeline(OllamaClient("http://localhost:11434", "test-model"), model_name="test-model")

    assert pipeline.failure_engine.max_depth == 3


def test_counterfactual_validation_links_hypothesis_to_fact_ids():
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(load_record()))
    engine = CounterfactualEngine(None)
    treatment = TreatmentCandidate(
        treatment_id="TX-1",
        name="estratégia analítica",
        treatment_class="systemic_therapy",
        therapeutic_goal="disease_control",
        reason_for_consideration=["teste"],
        patient_evidence=[],
    )
    outcome = FailureOutcome(outcome_id="TX-1:toxicity", label="toxicity", description="teste")
    draft = FailureDraft(
        hypothesis="Hipótese com evidência identificada",
        mechanism="Mecanismo de teste",
        causal_chain=["hipertensão", "exposição", "toxicidade"],
        required_patient_condition="hipertensão",
        patient_fact_ids=["comorbidity:hipertensão arterial"],
        clinical_plausibility=0.8,
        temporal_plausibility=0.8,
        patient_specificity=0.8,
    )

    node = engine._validate_and_prune(state, treatment, outcome, None, 1, draft)

    assert node.status == "supported"
    assert node.patient_evidence[0].finding == "hipertensão arterial"


def test_counterfactual_validation_keeps_valid_fact_ids_when_others_are_unknown():
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(load_record()))
    engine = CounterfactualEngine(None)
    treatment = TreatmentCandidate(treatment_id="TX-1", name="estratégia analítica", treatment_class="systemic_therapy", therapeutic_goal="disease_control", reason_for_consideration=["teste"], patient_evidence=[])
    outcome = FailureOutcome(outcome_id="TX-1:toxicity", label="toxicity", description="teste")
    draft = FailureDraft(hypothesis="Hipótese com uma fonte inválida", mechanism="Mecanismo de teste", causal_chain=["hipertensão", "exposição", "toxicidade"], patient_fact_ids=["comorbidity:hipertensão arterial", "lab:inexistente"], clinical_plausibility=0.8, temporal_plausibility=0.8, patient_specificity=0.8)

    node = engine._validate_and_prune(state, treatment, outcome, None, 1, draft)

    assert node.status == "supported"
    assert node.missing_information == ["unknown_patient_fact_id:lab:inexistente"]
