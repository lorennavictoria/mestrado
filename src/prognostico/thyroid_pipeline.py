from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from .knowledge import ClinicalKnowledgeBase
from .llm import LLMClient, build_message
from .models import (AnalysisReport, CounterfactualTree, Evidence, FailureOutcome, FailureTreeNode, MedicalRecord, PatientState, QualitativeForecast, TreatmentAnalysis, TreatmentCandidate, TreatmentImpact)
from .prompts import FAILURE_PROMPT, IMPACT_PROMPT, TREATMENT_PROMPT
from .record import MedicalRecordValidator
from .state import PatientStateBuilder


class CandidateList(BaseModel):
    treatments: list[TreatmentCandidate]


class FailureDraft(BaseModel):
    hypothesis: str
    mechanism: str
    causal_chain: list[str] = Field(default_factory=list)
    required_patient_condition: str | None = None
    patient_fact_ids: list[str] = Field(default_factory=list)
    clinical_plausibility: float = Field(ge=0, le=1, description="Decimal score from 0.0 to 1.0")
    temporal_plausibility: float = Field(ge=0, le=1, description="Decimal score from 0.0 to 1.0")
    patient_specificity: float = Field(ge=0, le=1, description="Decimal score from 0.0 to 1.0")


class FailureDraftList(BaseModel):
    hypotheses: list[FailureDraft]


class ImpactList(BaseModel):
    impacts: list[TreatmentImpact]


def reasoning_context(state: PatientState) -> dict:
    """Keep model context factual and bounded without changing the audited state."""
    medications = {}
    for medication in state.medications:
        key = (medication.name.casefold(), medication.status, medication.route)
        medications.setdefault(key, {"name": medication.name, "status": medication.status, "dose": medication.dose, "route": medication.route})
    return {
        "case_id": state.case_id,
        "cancer": state.cancer.model_dump(exclude_none=True),
        "patient": state.patient.model_dump(exclude_none=True),
        "active_problems": [
            {"fact_id": fact.fact_id, "statement": fact.statement, "sources": fact.source_ids}
            for fact in state.active_problems
            if fact.status == "active"
        ],
        "previous_treatments": [item.model_dump(exclude_none=True) for item in state.previous_treatments],
        "medication_history": list(medications.values()),
        "missing_information": state.missing_information,
        "data_warnings": state.data_warnings,
    }


class TreatmentGenerator:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def run(self, state: PatientState, evidence: list[Evidence]) -> list[TreatmentCandidate]:
        result = self.client.chat_json(TREATMENT_PROMPT, build_message("thyroid_treatment_generation", {"patient_state": reasoning_context(state), "external_evidence": [item.model_dump() for item in evidence]}), schema=CandidateList)
        return CandidateList.model_validate(result).treatments


class FailureHypothesisGenerator:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def run(self, state: PatientState, treatment: TreatmentCandidate, outcome: FailureOutcome, parent: FailureTreeNode | None, depth: int, evidence: list[Evidence]) -> list[FailureDraft]:
        context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "outcome": outcome.model_dump(), "parent": parent.model_dump() if parent else None, "depth": depth, "external_evidence": [item.model_dump() for item in evidence]}
        result = self.client.chat_json(FAILURE_PROMPT, build_message("thyroid_failure_generation", context), schema=FailureDraftList)
        return FailureDraftList.model_validate(result).hypotheses


class ImpactAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def run(self, state: PatientState, treatment: TreatmentCandidate, evidence: list[Evidence]) -> list[TreatmentImpact]:
        result = self.client.chat_json(IMPACT_PROMPT, build_message("thyroid_impact_analysis", {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "external_evidence": [item.model_dump() for item in evidence]}), schema=ImpactList)
        return ImpactList.model_validate(result).impacts


class CounterfactualEngine:
    outcomes = [
        ("oncologic_failure", "Ausência de resposta ou progressão"),
        ("toxicity", "Toxicidade grave relacionada ao tratamento"),
        ("interruption", "Interrupção ou redução de dose"),
    ]

    def __init__(self, generator: FailureHypothesisGenerator, knowledge_base: ClinicalKnowledgeBase, *, max_depth: int = 3, beam_width: int = 3, minimum_plausibility: float = 0.6) -> None:
        self.generator = generator
        self.knowledge_base = knowledge_base
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.minimum_plausibility = minimum_plausibility

    def build(self, state: PatientState, treatment: TreatmentCandidate) -> CounterfactualTree:
        outcomes = [FailureOutcome(outcome_id=f"{treatment.treatment_id}:{label}", label=label, description=description) for label, description in self.outcomes]
        evidence = self.knowledge_base.retrieve(state, treatment)
        nodes: list[FailureTreeNode] = []
        frontier: list[tuple[FailureOutcome, FailureTreeNode | None]] = [(outcome, None) for outcome in outcomes]
        seen: set[tuple[str, str]] = set()
        for depth in range(1, self.max_depth + 1):
            next_frontier: list[tuple[FailureOutcome, FailureTreeNode]] = []
            for outcome, parent in frontier:
                drafts = self.generator.run(state, treatment, outcome, parent, depth, evidence)
                drafts = sorted(drafts, key=lambda item: item.clinical_plausibility + item.temporal_plausibility + item.patient_specificity, reverse=True)[: self.beam_width]
                for draft in drafts:
                    key = (outcome.outcome_id, draft.hypothesis.casefold())
                    if key in seen:
                        continue
                    seen.add(key)
                    node = self._validate_and_prune(state, treatment, outcome, parent, depth, draft, evidence)
                    nodes.append(node)
                    if node.status == "supported" and depth < self.max_depth:
                        next_frontier.append((outcome, node))
            frontier = next_frontier
            if not frontier:
                break
        return CounterfactualTree(treatment_id=treatment.treatment_id, outcomes=outcomes, nodes=nodes, max_depth=self.max_depth)

    def _validate_and_prune(self, state: PatientState, treatment: TreatmentCandidate, outcome: FailureOutcome, parent: FailureTreeNode | None, depth: int, draft: FailureDraft, external_evidence: list[Evidence]) -> FailureTreeNode:
        active_facts = {fact.fact_id: fact for fact in state.active_problems if fact.status == "active"}
        selected_facts = [active_facts[fact_id] for fact_id in draft.patient_fact_ids if fact_id in active_facts]
        patient_evidence = [evidence for fact in selected_facts for evidence in fact.evidence]
        unknown_fact_ids = sorted(set(draft.patient_fact_ids) - set(active_facts))
        status = "supported"
        code = None
        missing: list[str] = []
        if not draft.patient_fact_ids:
            status, code, missing = "unresolved", "UNRESOLVED_MISSING_DATA", ["patient_fact_ids"]
        elif not selected_facts:
            status, code = "pruned", "PRUNED_ABSENT_CONDITION"
        elif unknown_fact_ids:
            missing = [f"unknown_patient_fact_id:{fact_id}" for fact_id in unknown_fact_ids]
        elif len(draft.causal_chain) < 3 or draft.patient_specificity < self.minimum_plausibility:
            status, code = "pruned", "PRUNED_NON_SPECIFIC"
        elif draft.clinical_plausibility < self.minimum_plausibility or not external_evidence:
            status, code = "pruned", "PRUNED_UNSUPPORTED_MECHANISM"
        return FailureTreeNode(node_id=str(uuid4()), parent_id=parent.node_id if parent else None, depth=depth, outcome_id=outcome.outcome_id, hypothesis=draft.hypothesis, mechanism=draft.mechanism, causal_chain=draft.causal_chain, required_patient_condition=draft.required_patient_condition, patient_evidence=patient_evidence, external_evidence=external_evidence, missing_information=missing, clinical_plausibility=draft.clinical_plausibility, temporal_plausibility=draft.temporal_plausibility, patient_specificity=draft.patient_specificity, status=status, pruning_code=code)


class ThyroidPrognosisPipeline:
    def __init__(self, client: LLMClient, knowledge_base: ClinicalKnowledgeBase, *, model_name: str, max_depth: int = 3) -> None:
        self.validator = MedicalRecordValidator()
        self.state_builder = PatientStateBuilder()
        self.generator = TreatmentGenerator(client)
        self.failure_engine = CounterfactualEngine(FailureHypothesisGenerator(client), knowledge_base, max_depth=max_depth)
        self.impact_agent = ImpactAgent(client)
        self.knowledge_base = knowledge_base
        self.model_name = model_name

    def run(self, record: MedicalRecord) -> AnalysisReport:
        validation = self.validator.validate(record)
        state = self.state_builder.build(validation)
        general_evidence = self.knowledge_base.retrieve(state)
        candidates = self.generator.run(state, general_evidence)
        analyses: list[TreatmentAnalysis] = []
        for treatment in candidates:
            if treatment.status != "candidate":
                continue
            evidence = self.knowledge_base.retrieve(state, treatment)
            tree = self.failure_engine.build(state, treatment)
            impacts = self.impact_agent.run(state, treatment, evidence)
            supported = [node for node in tree.nodes if node.status == "supported"]
            unresolved = [node for node in tree.nodes if node.status == "unresolved"]
            candidate_status = "high_risk" if any(node.outcome_id.endswith("toxicity") for node in supported) else "insufficient_information" if unresolved and not supported else "remains_plausible"
            forecast = QualitativeForecast(horizon="12 months", disease_control="plausible" if candidate_status == "remains_plausible" else "unknown", adverse_outcome_risk="high" if candidate_status == "high_risk" else "unknown", confidence_in_reasoning="moderate" if supported else "low", rationale=[node.hypothesis for node in supported])
            analyses.append(TreatmentAnalysis(treatment=treatment, candidate_status=candidate_status, failure_tree=tree, impacts=impacts, forecast=forecast, missing_information=state.missing_information + [item for node in unresolved for item in node.missing_information], uncertainties=["Ausência de mecanismo suportado não demonstra eficácia."] if not supported else []))
        return AnalysisReport(case_id=record.case_id, patient_state=state, generated_treatments=candidates, candidate_treatments=analyses, knowledge_base_version=self.knowledge_base.version, model=self.model_name, timestamp=datetime.now(timezone.utc).isoformat())
