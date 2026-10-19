from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    finding: str
    source: str | None = None


class PatientCharacteristics(BaseModel):
    age_years: int | None = Field(default=None, ge=0, le=130)
    sex_at_birth: str | None = None
    gender_identity: str | None = None
    weight_kg: float | None = Field(default=None, gt=0)
    height_cm: float | None = Field(default=None, gt=0)
    performance_status: str | None = None
    frailty_assessment: str | None = None
    functional_status: str | None = None
    pregnancy_status: str | None = None
    allergies: list[str] = Field(default_factory=list)


class Encounter(BaseModel):
    encounter_id: str
    started_at: str
    ended_at: str | None = None
    encounter_type: str
    care_setting: str | None = None
    reason: str | None = None


class Comorbidity(BaseModel):
    condition: str
    status: Literal["active", "resolved", "history", "unknown"] = "unknown"
    diagnosed_at: str | None = None
    severity: str | None = None
    notes: str | None = None


class VitalSign(BaseModel):
    measured_at: str
    name: str
    value: float
    unit: str
    reference_range: str | None = None


class LabResult(BaseModel):
    collected_at: str
    test_name: str
    value: str
    unit: str | None = None
    reference_range: str | None = None
    interpretation: Literal["low", "normal", "high", "abnormal", "unknown"] = "unknown"


class Medication(BaseModel):
    name: str
    status: Literal["active", "held", "completed", "discontinued", "unknown"] = "unknown"
    dose: str | None = None
    route: str | None = None
    frequency: str | None = None
    indication: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


class Procedure(BaseModel):
    performed_at: str
    name: str
    outcome: str | None = None
    complications: list[str] = Field(default_factory=list)


class ClinicalNote(BaseModel):
    recorded_at: str
    category: str
    text: str
    author_role: str | None = None


class SocialHistory(BaseModel):
    smoking_status: str | None = None
    alcohol_use: str | None = None
    substance_use: str | None = None
    living_situation: str | None = None
    support_network: str | None = None
    barriers_to_care: list[str] = Field(default_factory=list)


class ClinicalCase(BaseModel):
    """Fatos clínicos consolidados; agentes nunca devem alterar este objeto."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    diagnosis: str
    stage: str | None = None
    tumor: dict[str, str] = Field(default_factory=dict)
    patient: PatientCharacteristics = Field(default_factory=PatientCharacteristics)
    encounters: list[Encounter] = Field(default_factory=list)
    comorbidities: list[Comorbidity] = Field(default_factory=list)
    vital_signs: list[VitalSign] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    procedures: list[Procedure] = Field(default_factory=list)
    clinical_notes: list[ClinicalNote] = Field(default_factory=list)
    social_history: SocialHistory = Field(default_factory=SocialHistory)
    biomarkers: dict[str, str] = Field(default_factory=dict)
    clinical_constraints: list[str] = Field(default_factory=list)
    relevant_features: list[str] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)


class Treatment(BaseModel):
    id: str
    name: str
    rationale: str | None = None
    supporting_evidence: list[Evidence] = Field(default_factory=list)


class TreatmentApplicability(BaseModel):
    treatment_id: str
    status: Literal["applicable", "uncertain", "not_applicable"]
    rationale: str
    contraindications: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class TreatmentConsequences(BaseModel):
    treatment_id: str
    therapeutic_goal: list[str] = Field(default_factory=list)
    expected_effects: list[str] = Field(default_factory=list)
    anatomical_consequences: list[str] = Field(default_factory=list)
    functional_consequences: list[str] = Field(default_factory=list)
    short_term_burden: list[str] = Field(default_factory=list)
    long_term_burden: list[str] = Field(default_factory=list)
    quality_of_life_impacts: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class FailureMode(BaseModel):
    failure: str
    mechanism: str
    causal_pathway: list[str] = Field(default_factory=list)
    worst_case_outcome: Literal["none", "serious_harm", "death"] = "none"
    patient_specific_evidence: list[Evidence] = Field(default_factory=list)
    supporting_evidence: list[Evidence] = Field(default_factory=list)
    possible_consequences: list[str] = Field(default_factory=list)
    possible_state_changes: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    hypothesis: Literal[True] = True
    requires_human_review: Literal[True] = True


class Premortem(BaseModel):
    treatment_id: str
    failure_modes: list[FailureMode] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Vulnerability(BaseModel):
    description: str
    scope: Literal["specific", "shared"]
    potentially_relevant_to: list[str] = Field(default_factory=list)
    reason: str
    evidence: list[Evidence] = Field(default_factory=list)
    origin_treatment_id: str
    reasoning_type: Literal["fact", "hypothesis", "inference"] = "hypothesis"


class SharedMemory(BaseModel):
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)

    def add(self, vulnerabilities: list[Vulnerability]) -> None:
        self.vulnerabilities.extend(item for item in vulnerabilities if item.scope == "shared")


class TreatmentProfile(BaseModel):
    treatment: Treatment
    consequences: TreatmentConsequences
    premortem: Premortem
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    memory_seen: list[Vulnerability] = Field(default_factory=list)


class RunResult(BaseModel):
    run_id: int
    order: list[str]
    treatment_profiles: list[TreatmentProfile]
    final_memory: SharedMemory


class FindingOccurrence(BaseModel):
    description: str
    treatment_ids: list[str]
    run_ids: list[int]


class AggregatedResult(BaseModel):
    stable_findings: list[FindingOccurrence] = Field(default_factory=list)
    order_sensitive_findings: list[FindingOccurrence] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    treatment_profiles: dict[str, list[TreatmentProfile]] = Field(default_factory=dict)


# Contratos do MVP para câncer de tireoide. Os modelos anteriores permanecem apenas
# para compatibilidade interna durante a migração; o novo pipeline usa os modelos abaixo.
class ThyroidCancer(BaseModel):
    histology: str
    differentiation: str | None = None
    tnm_stage: str | None = None
    recurrence_risk: str | None = None
    metastatic: bool | None = None
    metastatic_sites: list[str] = Field(default_factory=list)
    iodine_avidity: str | None = None
    progression_status: str | None = None
    molecular_profile: dict[str, str] = Field(default_factory=dict)


class ImagingStudy(BaseModel):
    study_id: str
    performed_at: str
    modality: str
    finding: str
    impression: str | None = None


class PriorTreatment(BaseModel):
    treatment_id: str
    name: str
    started_at: str | None = None
    ended_at: str | None = None
    response: Literal["response", "stable", "progression", "intolerant", "unknown"] = "unknown"
    toxicities: list[str] = Field(default_factory=list)


class MedicalRecord(BaseModel):
    """Prontuário fonte; valores objetivos e sua cronologia não são descartados."""

    case_id: str
    record_date: str
    cancer: ThyroidCancer
    patient: PatientCharacteristics
    comorbidities: list[Comorbidity] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    vital_signs: list[VitalSign] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    prior_treatments: list[PriorTreatment] = Field(default_factory=list)
    imaging_studies: list[ImagingStudy] = Field(default_factory=list)
    clinical_notes: list[ClinicalNote] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)


class RecordValidation(BaseModel):
    normalized_record: MedicalRecord
    warnings: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    temporal_conflicts: list[str] = Field(default_factory=list)


class ProvenancedFact(BaseModel):
    fact_id: str
    statement: str
    source_ids: list[str]
    evidence: list[Evidence] = Field(default_factory=list)
    status: Literal["active", "resolved", "historical", "unknown"] = "unknown"


class PatientState(BaseModel):
    case_id: str
    cancer: ThyroidCancer
    patient: PatientCharacteristics
    active_problems: list[ProvenancedFact] = Field(default_factory=list)
    previous_treatments: list[PriorTreatment] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)


class TreatmentCandidate(BaseModel):
    treatment_id: str
    name: str
    treatment_class: str
    therapeutic_goal: str
    reason_for_consideration: list[str]
    patient_evidence: list[Evidence]
    contraindications_detected: list[str] = Field(default_factory=list)
    evidence_source_ids: list[str] = Field(default_factory=list)
    status: Literal["candidate", "not_applicable", "insufficient_information"] = "candidate"


class FailureOutcome(BaseModel):
    outcome_id: str
    label: Literal["oncologic_failure", "toxicity", "intolerance", "interruption", "progression", "hospitalization", "functional_decline", "mortality"]
    description: str


class NodeEvidenceValidation(BaseModel):
    supported: bool
    supporting_evidence: list[Evidence] = Field(default_factory=list)
    contradictory_evidence: list[Evidence] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class FailureTreeNode(BaseModel):
    node_id: str
    parent_id: str | None = None
    depth: int = Field(ge=0)
    outcome_id: str
    hypothesis: str
    mechanism: str
    causal_chain: list[str] = Field(default_factory=list)
    required_patient_condition: str | None = None
    patient_evidence: list[Evidence] = Field(default_factory=list)
    external_evidence: list[Evidence] = Field(default_factory=list)
    contradictory_evidence: list[Evidence] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    clinical_plausibility: float = Field(ge=0, le=1)
    temporal_plausibility: float = Field(ge=0, le=1)
    patient_specificity: float = Field(ge=0, le=1)
    status: Literal["active", "supported", "pruned", "unresolved"] = "active"
    pruning_code: Literal["PRUNED_CONTRADICTION", "PRUNED_ABSENT_CONDITION", "PRUNED_UNSUPPORTED_MECHANISM", "PRUNED_TEMPORAL", "PRUNED_NON_SPECIFIC", "UNRESOLVED_MISSING_DATA"] | None = None


class CounterfactualTree(BaseModel):
    treatment_id: str
    outcomes: list[FailureOutcome]
    nodes: list[FailureTreeNode]
    max_depth: int


class TreatmentImpact(BaseModel):
    impact: str
    domain: Literal["oncologic", "functional", "endocrine", "cardiovascular", "renal", "hepatic", "hematologic", "neurologic", "reproductive", "psychological", "nutritional", "quality_of_life", "hospitalization", "monitoring", "medication"]
    timing: Literal["short_term", "medium_term", "long_term", "permanent"]
    reversibility: Literal["reversible", "irreversible", "unknown"]
    severity: Literal["low", "moderate", "high", "unknown"]
    patient_specific: bool
    evidence: list[Evidence] = Field(default_factory=list)


class QualitativeForecast(BaseModel):
    horizon: str
    disease_control: Literal["unknown", "limited", "plausible"] = "unknown"
    adverse_outcome_risk: Literal["unknown", "low", "moderate", "high"] = "unknown"
    confidence_in_reasoning: Literal["low", "moderate", "high"] = "low"
    rationale: list[str] = Field(default_factory=list)


class TreatmentAnalysis(BaseModel):
    treatment: TreatmentCandidate
    candidate_status: Literal["remains_plausible", "high_risk", "contraindication_identified", "insufficient_information", "not_applicable"]
    failure_tree: CounterfactualTree
    impacts: list[TreatmentImpact] = Field(default_factory=list)
    forecast: QualitativeForecast
    missing_information: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    case_id: str
    patient_state: PatientState
    generated_treatments: list[TreatmentCandidate]
    candidate_treatments: list[TreatmentAnalysis]
    knowledge_base_version: str
    model: str
    timestamp: str
