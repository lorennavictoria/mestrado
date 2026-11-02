from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import re
import unicodedata
from uuid import uuid4

from pydantic import BaseModel, Field

from .clinical_guidance_prompts import FAILURE_CLINICAL_GUIDANCE_PROMPT, IMPACT_CLINICAL_GUIDANCE_PROMPT, OUTCOME_CLINICAL_GUIDANCE_PROMPT, TREATMENT_CLINICAL_GUIDANCE_PROMPT
from .eligibility import ClinicalEligibilityAgent
from .guidelines import GuidelineRetriever
from .llm import LLMClient, build_message
from .models import (AnalysisReport, CausalReasoningSummary, CounterfactualTree, EligibilityAssessment, Evidence, FailureOutcome, FailureTreeNode, MedicalRecord, OutcomeScenario, OutcomeTree, PatientState, QualitativeForecast, TreatmentAnalysis, TreatmentCandidate, TreatmentImpact)
from .prompts import FAILURE_OUTCOME_PROMPT, FAILURE_PROMPT, IMPACT_PROMPT, OUTCOME_PROMPT, TREATMENT_PROMPT
from .record import MedicalRecordValidator
from .state import PatientStateBuilder
from .treatment_catalog import catalog_version, evaluate_catalog, histology_scope


class TreatmentDraft(TreatmentCandidate):
    patient_fact_ids: list[str] = Field(min_length=1)


class CandidateList(BaseModel):
    treatments: list[TreatmentDraft]


class FailureDraft(BaseModel):
    hypothesis: str = Field(max_length=280)
    mechanism: str = Field(max_length=220)
    causal_chain: list[str] = Field(min_length=3, max_length=4)
    required_patient_condition: str = Field(max_length=180)
    patient_fact_ids: list[str] = Field(min_length=1)
    clinical_plausibility: float = Field(ge=0, le=1, description="Decimal score from 0.0 to 1.0")
    temporal_plausibility: float = Field(ge=0, le=1, description="Decimal score from 0.0 to 1.0")
    patient_specificity: float = Field(ge=0, le=1, description="Decimal score from 0.0 to 1.0")


class FailureDraftList(BaseModel):
    hypotheses: list[FailureDraft] = Field(max_length=2)


class OutcomeDraft(BaseModel):
    label: Literal["oncologic_failure", "toxicity", "intolerance", "interruption", "progression", "hospitalization", "functional_decline", "mortality"]
    description: str


class OutcomeDraftList(BaseModel):
    outcomes: list[OutcomeDraft] = Field(min_length=1, max_length=3)


class OutcomeScenarioDraft(BaseModel):
    label: Literal["response_control", "persistence", "recurrence_progression", "toxicity", "quality_of_life", "subsequent_therapy", "mortality"]
    description: str
    mechanism: str | None = None
    modifiers: list[str] = Field(default_factory=list)


class OutcomeScenarioDraftList(BaseModel):
    outcomes: list[OutcomeScenarioDraft] = Field(min_length=2, max_length=7)


class ImpactList(BaseModel):
    impacts: list[TreatmentImpact] = Field(max_length=3)


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
        "available_patient_facts": [
            {"fact_id": fact.fact_id, "statement": fact.statement, "status": fact.status, "sources": fact.source_ids}
            for fact in state.active_problems
            if fact.status in {"active", "historical"}
        ],
        "previous_treatments": [item.model_dump(exclude_none=True) for item in state.previous_treatments],
        "medication_history": list(medications.values()),
        "missing_information": state.missing_information,
        "data_warnings": state.data_warnings,
    }


def resolve_patient_facts(state: PatientState, fact_ids: list[str]) -> list:
    available_facts = {fact.fact_id: fact for fact in state.active_problems if fact.status in {"active", "historical"}}
    return [available_facts[fact_id] for fact_id in fact_ids if fact_id in available_facts]


def summarize_reasoning(tree: CounterfactualTree) -> list[CausalReasoningSummary]:
    summaries: list[CausalReasoningSummary] = []
    for outcome in tree.outcomes:
        paths: list[list[str]] = []
        for node in tree.nodes:
            if node.outcome_id != outcome.outcome_id or node.status != "supported" or node.causal_chain in paths:
                continue
            paths.append(node.causal_chain)
        unresolved = [node for node in tree.nodes if node.outcome_id == outcome.outcome_id and node.status == "unresolved"]
        narratives = ["; ".join(f"Se {cause}, então {effect}" for cause, effect in zip(path, path[1:])) + "." for path in paths]
        limitations = ["Há hipóteses não resolvidas para este desfecho; elas não foram usadas na síntese."] if unresolved else []
        summaries.append(CausalReasoningSummary(outcome_id=outcome.outcome_id, outcome_description=outcome.description, supported_paths=paths, narrative=narratives, limitations=limitations))
    return summaries


_CAUSAL_STOPWORDS = frozenset({"a", "ao", "aos", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "entre", "na", "nas", "no", "nos", "o", "os", "ou", "para", "por", "que", "se", "uma", "um"})


def _causal_terms(*parts: str | list[str]) -> set[str]:
    text = " ".join(" ".join(part) if isinstance(part, list) else part for part in parts).casefold()
    text = "".join(char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn")
    return {token for token in re.findall(r"[a-z0-9_]{3,}", text) if token not in _CAUSAL_STOPWORDS}


def is_redundant_hypothesis(draft: FailureDraft, existing: list[FailureDraft | FailureTreeNode]) -> bool:
    candidate = _causal_terms(draft.hypothesis, draft.mechanism, draft.causal_chain)
    if not candidate:
        return False
    for item in existing:
        compared = _causal_terms(item.hypothesis, item.mechanism, item.causal_chain)
        if not compared:
            continue
        intersection = len(candidate & compared)
        if intersection / min(len(candidate), len(compared)) >= 0.75:
            return True
        if intersection / len(candidate | compared) >= 0.65:
            return True
    return False


class TreatmentGenerator:
    def __init__(self, retriever: GuidelineRetriever) -> None:
        self.retriever = retriever

    def run(self, state: PatientState) -> list[TreatmentCandidate]:
        candidates: list[TreatmentCandidate] = []
        for candidate in evaluate_catalog(state):
            facts = resolve_patient_facts(state, candidate.patient_fact_ids)
            citations = self.retriever.retrieve(candidate.guideline_query or f"thyroid cancer {candidate.name}", scope=histology_scope(state), limit=2)
            candidates.append(candidate.model_copy(update={
                "status": candidate.status if facts else "insufficient_information",
                "patient_evidence": [evidence for fact in facts for evidence in fact.evidence],
                "evidence_source_ids": [citation.source or "" for citation in citations],
            }))
        return candidates


class FailureHypothesisGenerator:
    def __init__(self, client: LLMClient, retriever: GuidelineRetriever) -> None:
        self.client = client
        self.retriever = retriever

    def run(self, state: PatientState, treatment: TreatmentCandidate, outcome: FailureOutcome, parent: FailureTreeNode | None, depth: int, explored_hypotheses: list[str]) -> tuple[list[FailureDraft], dict, list[Evidence]]:
        citations = self.retriever.retrieve(f"{treatment.guideline_query} {outcome.description}", scope=histology_scope(state), limit=3)
        context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "outcome": outcome.model_dump(), "parent": parent.model_dump() if parent else None, "explored_hypotheses": explored_hypotheses, "guideline_evidence": [item.model_dump() for item in citations], "depth": depth, "iteration_instruction": "Formule causas-raiz distintas para o desfecho." if parent is None else "Avance uma etapa causal anterior, concreta e distinta ao mecanismo do nó-pai; não repita, resuma ou reformule a hipótese do pai."}
        result = self.client.chat_json(f"{FAILURE_CLINICAL_GUIDANCE_PROMPT}\n{FAILURE_PROMPT}", build_message("thyroid_failure_generation", context), schema=FailureDraftList)
        return FailureDraftList.model_validate(result).hypotheses, context, citations


class FailureOutcomeGenerator:
    def __init__(self, client: LLMClient, retriever: GuidelineRetriever) -> None:
        self.client = client
        self.retriever = retriever

    def run(self, state: PatientState, treatment: TreatmentCandidate) -> tuple[list[FailureOutcome], dict, list[Evidence]]:
        citations = self.retriever.retrieve(treatment.guideline_query or f"thyroid cancer {treatment.name}", scope=histology_scope(state), limit=3)
        context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "guideline_evidence": [item.model_dump() for item in citations]}
        result = self.client.chat_json(f"{OUTCOME_CLINICAL_GUIDANCE_PROMPT}\n{FAILURE_OUTCOME_PROMPT}", build_message("thyroid_failure_outcome_generation", context), schema=OutcomeDraftList)
        drafts = OutcomeDraftList.model_validate(result).outcomes
        distinct_drafts = []
        seen_labels: set[str] = set()
        for draft in drafts:
            if draft.label in seen_labels:
                continue
            seen_labels.add(draft.label)
            distinct_drafts.append(draft)
        outcomes = [FailureOutcome(outcome_id=f"{treatment.treatment_id}:{index}:{draft.label}", label=draft.label, description=draft.description) for index, draft in enumerate(distinct_drafts, start=1)]
        return outcomes, context, citations


class OutcomeTreeGenerator:
    def __init__(self, client: LLMClient, retriever: GuidelineRetriever) -> None:
        self.client = client
        self.retriever = retriever

    def run(self, state: PatientState, treatment: TreatmentCandidate) -> OutcomeTree:
        citations = self.retriever.retrieve(treatment.guideline_query or f"thyroid cancer {treatment.name}", scope=histology_scope(state), limit=3)
        context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "guideline_evidence": [item.model_dump() for item in citations]}
        result = self.client.chat_json(f"{OUTCOME_CLINICAL_GUIDANCE_PROMPT}\n{OUTCOME_PROMPT}", build_message("thyroid_outcome_tree_generation", context), schema=OutcomeScenarioDraftList)
        outcomes = [OutcomeScenario(outcome_id=f"{treatment.treatment_id}:outcome:{index}:{draft.label}", **draft.model_dump()) for index, draft in enumerate(OutcomeScenarioDraftList.model_validate(result).outcomes, start=1)]
        return OutcomeTree(treatment_id=treatment.treatment_id, root_description=f"Estratégia aplicada ao estado clínico inicial: {treatment.name}", outcomes=outcomes, evidence=citations, generation_context=context)


class ClinicalCritic:
    """Classifies support without treating a model score as clinical refutation."""

    def evaluate(self, state: PatientState, draft: FailureDraft, selected_facts: list, unknown_fact_ids: list[str], guideline_evidence: list[Evidence]) -> tuple[str, str | None, list[str], str]:
        if not selected_facts:
            return "pruned", "PRUNED_ABSENT_CONDITION", [], "A condição necessária não está documentada no estado ativo."
        if unknown_fact_ids:
            return "unresolved", "UNRESOLVED_MISSING_DATA", [f"unknown_patient_fact_id:{fact_id}" for fact_id in unknown_fact_ids], "A hipótese referencia fatos que não existem no prontuário ativo."
        if not guideline_evidence:
            return "unresolved", "UNRESOLVED_MISSING_DATA", ["guideline_evidence"], "Não foi recuperada evidência externa para avaliar o mecanismo."
        if len(draft.causal_chain) < 3 or min(draft.clinical_plausibility, draft.temporal_plausibility, draft.patient_specificity) < 0.6:
            return "unresolved", "UNRESOLVED_INSUFFICIENT_SUPPORT", [], "A hipótese exige revisão: a cadeia causal ou o suporte específico ainda é insuficiente para sustentação."
        return "supported", None, [], "Hipótese ligada a fatos ativos e a evidência externa recuperada; permanece contrafactual."


class ImpactAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def run(self, state: PatientState, treatment: TreatmentCandidate) -> list[TreatmentImpact]:
        result = self.client.chat_json(f"{IMPACT_CLINICAL_GUIDANCE_PROMPT}\n{IMPACT_PROMPT}", build_message("thyroid_impact_analysis", {"patient_state": reasoning_context(state), "treatment": treatment.model_dump()}), schema=ImpactList)
        impacts: list[TreatmentImpact] = []
        for impact in ImpactList.model_validate(result).impacts:
            facts = resolve_patient_facts(state, impact.patient_fact_ids)
            impacts.append(impact.model_copy(update={
                "patient_specific": impact.patient_specific and bool(facts),
                "evidence": [evidence for fact in facts for evidence in fact.evidence],
            }))
        return impacts


class CounterfactualEngine:
    def __init__(self, generator: FailureHypothesisGenerator, outcome_generator: FailureOutcomeGenerator, *, critic: ClinicalCritic | None = None, max_depth: int = 3, beam_width: int = 3, minimum_plausibility: float = 0.6) -> None:
        self.generator = generator
        self.outcome_generator = outcome_generator
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.minimum_plausibility = minimum_plausibility
        self.critic = critic or ClinicalCritic()

    def build(self, state: PatientState, treatment: TreatmentCandidate) -> CounterfactualTree:
        outcomes, outcome_generation_context, outcome_evidence = self.outcome_generator.run(state, treatment)
        nodes: list[FailureTreeNode] = []
        frontier: list[tuple[FailureOutcome, FailureTreeNode | None]] = [(outcome, None) for outcome in outcomes]
        seen: set[tuple[str, str]] = set()
        for depth in range(1, self.max_depth + 1):
            next_frontier: list[tuple[FailureOutcome, FailureTreeNode]] = []
            for outcome, parent in frontier:
                existing_for_outcome = [node for node in nodes if node.outcome_id == outcome.outcome_id]
                explored_hypotheses = [node.hypothesis for node in existing_for_outcome]
                drafts, generation_context, guideline_evidence = self.generator.run(state, treatment, outcome, parent, depth, explored_hypotheses)
                drafts = sorted(drafts, key=lambda item: item.clinical_plausibility + item.temporal_plausibility + item.patient_specificity, reverse=True)[: self.beam_width]
                for draft in drafts:
                    key = (outcome.outcome_id, draft.hypothesis.casefold())
                    if key in seen or is_redundant_hypothesis(draft, existing_for_outcome):
                        continue
                    seen.add(key)
                    node = self._validate_and_prune(state, treatment, outcome, parent, depth, draft, generation_context, guideline_evidence)
                    nodes.append(node)
                    existing_for_outcome.append(node)
                    if node.status == "supported" and depth < self.max_depth:
                        next_frontier.append((outcome, node))
            frontier = next_frontier
            if not frontier:
                break
        return CounterfactualTree(treatment_id=treatment.treatment_id, outcomes=outcomes, nodes=nodes, max_depth=self.max_depth, outcome_generation_context=outcome_generation_context, outcome_generation_trace={"outcome_ids": [outcome.outcome_id for outcome in outcomes], "outcome_count": len(outcomes), "evidence_sources": [item.source for item in outcome_evidence]})

    def _validate_and_prune(self, state: PatientState, treatment: TreatmentCandidate, outcome: FailureOutcome, parent: FailureTreeNode | None, depth: int, draft: FailureDraft, generation_context: dict | None = None, guideline_evidence: list[Evidence] | None = None) -> FailureTreeNode:
        active_facts = {fact.fact_id: fact for fact in state.active_problems if fact.status in {"active", "historical"}}
        selected_facts = resolve_patient_facts(state, draft.patient_fact_ids)
        patient_evidence = [evidence for fact in selected_facts for evidence in fact.evidence]
        unknown_fact_ids = sorted(set(draft.patient_fact_ids) - set(active_facts))
        status, code, missing, critique = self.critic.evaluate(state, draft, selected_facts, unknown_fact_ids, guideline_evidence or [])
        validation_trace = {
            "requested_patient_fact_ids": draft.patient_fact_ids,
            "resolved_patient_fact_ids": [fact.fact_id for fact in selected_facts],
            "unknown_patient_fact_ids": unknown_fact_ids,
            "causal_chain_length": len(draft.causal_chain),
            "minimum_patient_specificity": self.minimum_plausibility,
            "status": status,
            "pruning_code": code,
        }
        return FailureTreeNode(node_id=str(uuid4()), parent_id=parent.node_id if parent else None, depth=depth, outcome_id=outcome.outcome_id, hypothesis=draft.hypothesis, mechanism=draft.mechanism, causal_chain=draft.causal_chain, required_patient_condition=draft.required_patient_condition, patient_evidence=patient_evidence, external_evidence=guideline_evidence or [], missing_information=missing, generation_context=generation_context or {}, validation_trace=validation_trace, clinical_plausibility=draft.clinical_plausibility, temporal_plausibility=draft.temporal_plausibility, patient_specificity=draft.patient_specificity, status=status, pruning_code=code, critique=critique)


class ThyroidPrognosisPipeline:
    def __init__(self, client: LLMClient, *, model_name: str, max_depth: int = 5, guideline_index: Path | None = None) -> None:
        self.validator = MedicalRecordValidator()
        self.state_builder = PatientStateBuilder()
        default_index = Path(__file__).resolve().parents[2] / "guidelines" / "processed" / "index.json"
        self.retriever = GuidelineRetriever(guideline_index or default_index)
        self.generator = TreatmentGenerator(self.retriever)
        self.eligibility_agent = ClinicalEligibilityAgent(self.retriever)
        self.failure_engine = CounterfactualEngine(FailureHypothesisGenerator(client, self.retriever), FailureOutcomeGenerator(client, self.retriever), max_depth=max_depth)
        self.outcome_generator = OutcomeTreeGenerator(client, self.retriever)
        self.impact_agent = ImpactAgent(client)
        self.model_name = model_name

    def run(self, record: MedicalRecord) -> AnalysisReport:
        run_id = str(uuid4())
        validation = self.validator.validate(record)
        state = self.state_builder.build(validation)
        candidates = self.generator.run(state)
        analyses: list[TreatmentAnalysis] = []
        for treatment in candidates:
            eligibility = self.eligibility_agent.assess(state, treatment)
            if eligibility.status == "ineligible":
                continue
            tree = self.failure_engine.build(state, treatment)
            impacts = self.impact_agent.run(state, treatment)
            outcome_tree = self.outcome_generator.run(state, treatment)
            supported = [node for node in tree.nodes if node.status == "supported"]
            unresolved = [node for node in tree.nodes if node.status == "unresolved"]
            all_pruned = bool(tree.nodes) and all(node.status == "pruned" for node in tree.nodes)
            candidate_status = "insufficient_information" if eligibility.status == "indeterminate" else "high_risk" if any(node.outcome_id.endswith("toxicity") for node in supported) else "remains_plausible" if supported or all_pruned else "insufficient_information"
            forecast = QualitativeForecast(horizon="12 months", disease_control="unknown", adverse_outcome_risk="high" if any(node.outcome_id.endswith("toxicity") for node in supported) else "unknown", confidence_in_reasoning="moderate" if supported and eligibility.status == "eligible" else "low", rationale=[node.hypothesis for node in supported])
            uncertainties = ["Nenhum mecanismo causal específico ao paciente foi sustentado; isso não demonstra segurança ou eficácia."] if all_pruned else ["Ausência de mecanismo suportado não demonstra eficácia."] if not supported else []
            analyses.append(TreatmentAnalysis(treatment=treatment, eligibility=eligibility, outcome_tree=outcome_tree, candidate_status=candidate_status, failure_tree=tree, impacts=impacts, forecast=forecast, reasoning_summary=summarize_reasoning(tree), missing_information=state.missing_information + [item for node in unresolved for item in node.missing_information], uncertainties=uncertainties))
        return AnalysisReport(run_id=run_id, case_id=record.case_id, patient_state=state, generated_treatments=candidates, candidate_treatments=analyses, reasoning_guidance_version="thyroid-architecture-v1", knowledge_base_version=self.retriever.version, catalog_version=catalog_version(), execution_parameters={"max_depth": self.failure_engine.max_depth, "beam_width": self.failure_engine.beam_width, "minimum_plausibility": self.failure_engine.minimum_plausibility}, audit_events=[{"event": "record_validated", "warnings": validation.warnings, "missing_information": validation.missing_information}, {"event": "catalog_evaluated", "candidate_count": len(candidates)}, {"event": "treatments_analyzed", "treatment_ids": [item.treatment.treatment_id for item in analyses]}], model=self.model_name, timestamp=datetime.now(timezone.utc).isoformat())
