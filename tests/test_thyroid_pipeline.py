import json
from pathlib import Path

from prognostico.llm import OllamaClient
from prognostico.models import CounterfactualTree, Evidence, FailureOutcome, FailureTreeNode, MedicalRecord, TreatmentCandidate
from prognostico.record import MedicalRecordValidator
from prognostico.state import PatientStateBuilder
from prognostico.thyroid_pipeline import CounterfactualEngine, FailureDraft, ThyroidPrognosisPipeline, is_redundant_hypothesis, reasoning_context, resolve_patient_facts, summarize_reasoning


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


def test_state_exposes_cancer_fields_and_historical_treatments_as_citable_facts():
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(load_record()))
    facts = {item.fact_id for item in state.active_problems}

    assert "cancer_iodine_avidity" in facts
    assert "molecular_profile:BRAF_V600E" in facts
    assert resolve_patient_facts(state, ["prior_treatment:PT-002"])[0].status == "historical"
    assert "prior_treatment:PT-002" in {item["fact_id"] for item in reasoning_context(state)["available_patient_facts"]}


def test_validator_preserves_source_data_warnings():
    record = load_record().model_copy(update={"data_warnings": ["fonte estruturada incompleta"]})

    validation = MedicalRecordValidator().validate(record)

    assert "fonte estruturada incompleta" in validation.warnings


def test_validator_excludes_future_events_and_flags_invalid_medication_chronology():
    raw = load_record().model_dump()
    raw["lab_results"].append({"collected_at": "2026-03-02", "test_name": "calcium", "value": "7.5", "interpretation": "low"})
    raw["medications"].append({"name": "test medication", "status": "completed", "started_at": "2026-03-02", "ended_at": "2026-03-01"})

    validation = MedicalRecordValidator().validate(MedicalRecord.model_validate(raw))

    assert all(item.collected_at <= "2026-03-01" for item in validation.normalized_record.lab_results)
    assert any("posterior(es) a record_date" in item for item in validation.warnings)
    assert "medicação test medication termina antes de iniciar" in validation.temporal_conflicts


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

    assert facts["cancer_documented"].status == "active"
    assert facts["abnormal_lab_summary:calcium"].evidence[-1].finding == "calcium=7.6 mg/dL"
    assert facts["vital:heart rate:2026-03-01"].status == "active"
    assert facts["medication:levothyroxine:unknown"].status == "active"
    assert not any(item.fact_id.startswith("medication:calcium carbonate") and item.status == "active" for item in state.active_problems)
    assert reasoning_context(state)["medication_history"] == [
        {"name": "levothyroxine", "status": "active", "dose": "100 mcg", "route": None},
        {"name": "calcium carbonate", "status": "completed", "dose": None, "route": None},
    ]


def test_pipeline_default_counterfactual_depth_is_five():
    pipeline = ThyroidPrognosisPipeline(OllamaClient("http://localhost:11434", "test-model"), model_name="test-model")

    assert pipeline.failure_engine.max_depth == 5


def test_counterfactual_validation_links_hypothesis_to_fact_ids():
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(load_record()))
    engine = CounterfactualEngine(None, None)
    treatment = TreatmentCandidate(
        treatment_id="TX-1",
        name="estratégia analítica",
        treatment_class="systemic_therapy",
        therapeutic_goal="disease_control",
        reason_for_consideration=["teste"],
        patient_evidence=[],
        patient_fact_ids=["cancer_documented"],
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

    node = engine._validate_and_prune(state, treatment, outcome, None, 1, draft, guideline_evidence=[Evidence(finding="Trecho de diretriz", source="TEST:p1")])

    assert node.status == "supported"
    assert node.patient_evidence[0].finding == "hipertensão arterial"


def test_counterfactual_validation_keeps_valid_fact_ids_when_others_are_unknown():
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(load_record()))
    engine = CounterfactualEngine(None, None)
    treatment = TreatmentCandidate(treatment_id="TX-1", name="estratégia analítica", treatment_class="systemic_therapy", therapeutic_goal="disease_control", reason_for_consideration=["teste"], patient_evidence=[], patient_fact_ids=["cancer_documented"])
    outcome = FailureOutcome(outcome_id="TX-1:toxicity", label="toxicity", description="teste")
    draft = FailureDraft(hypothesis="Hipótese com uma fonte inválida", mechanism="Mecanismo de teste", causal_chain=["hipertensão", "exposição", "toxicidade"], required_patient_condition="hipertensão", patient_fact_ids=["comorbidity:hipertensão arterial", "lab:inexistente"], clinical_plausibility=0.8, temporal_plausibility=0.8, patient_specificity=0.8)

    node = engine._validate_and_prune(state, treatment, outcome, None, 1, draft, guideline_evidence=[Evidence(finding="Trecho de diretriz", source="TEST:p1")])

    assert node.status == "unresolved"
    assert node.missing_information == ["unknown_patient_fact_id:lab:inexistente"]


def test_counterfactual_validation_keeps_low_score_hypothesis_indeterminate():
    state = PatientStateBuilder().build(MedicalRecordValidator().validate(load_record()))
    engine = CounterfactualEngine(None, None)
    treatment = TreatmentCandidate(treatment_id="TX-1", name="estratégia analítica", treatment_class="systemic_therapy", therapeutic_goal="disease_control", reason_for_consideration=["teste"], patient_evidence=[], patient_fact_ids=["cancer_documented"])
    outcome = FailureOutcome(outcome_id="TX-1:toxicity", label="toxicity", description="teste")
    draft = FailureDraft(hypothesis="Hipótese ainda pouco específica", mechanism="Mecanismo de teste", causal_chain=["hipertensão", "exposição", "toxicidade"], required_patient_condition="hipertensão", patient_fact_ids=["comorbidity:hipertensão arterial"], clinical_plausibility=0.5, temporal_plausibility=0.8, patient_specificity=0.8)

    node = engine._validate_and_prune(state, treatment, outcome, None, 1, draft, guideline_evidence=[Evidence(finding="Trecho de diretriz", source="TEST:p1")])

    assert node.status == "unresolved"
    assert node.pruning_code == "UNRESOLVED_INSUFFICIENT_SUPPORT"


def test_reasoning_summary_renders_supported_causal_chain():
    outcome = FailureOutcome(outcome_id="TX-1:toxicity", label="toxicity", description="Toxicidade limita a estratégia")
    node = FailureTreeNode(node_id="node-1", depth=1, outcome_id=outcome.outcome_id, hypothesis="Hipótese", mechanism="Mecanismo", causal_chain=["condição", "exposição", "toxicidade"], clinical_plausibility=0.8, temporal_plausibility=0.8, patient_specificity=0.8, status="supported")
    tree = CounterfactualTree(treatment_id="TX-1", outcomes=[outcome], nodes=[node], max_depth=5)

    summary = summarize_reasoning(tree)

    assert summary[0].supported_paths == [["condição", "exposição", "toxicidade"]]
    assert summary[0].narrative == ["Se condição, então exposição; Se exposição, então toxicidade."]


def test_semantic_deduplication_rejects_rephrased_resistance_hypothesis():
    original = FailureDraft(hypothesis="Resistência intrínseca da doença ao mecanismo de ação do DTC_RAIRD_MKI", mechanism="Resistência tumoral ao inibidor multiquinase", causal_chain=["doença refratária", "resistência intrínseca", "progressão"], required_patient_condition="doença refratária", patient_fact_ids=["cancer_documented"], clinical_plausibility=0.8, temporal_plausibility=0.8, patient_specificity=0.8)
    reformulation = FailureDraft(hypothesis="A progressão radiológica do câncer de tireoide é causada pela resistência da doença ao mecanismo de ação do DTC_RAIRD_MKI", mechanism="Resistência tumoral ao inibidor multiquinase", causal_chain=["doença refratária", "resistência ao inibidor", "progressão radiológica"], required_patient_condition="doença refratária", patient_fact_ids=["cancer_documented"], clinical_plausibility=0.8, temporal_plausibility=0.8, patient_specificity=0.8)

    assert is_redundant_hypothesis(reformulation, [original])
