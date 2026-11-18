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
from .knowledge_graph import ClinicalKnowledgeGraphBuilder
from .models import (AnalysisReport, CausalReasoningSummary, CausalThoughtNode, CausalThoughtTree, CounterfactualTree, EligibilityAssessment, Evidence, FailureOutcome, FailureTreeNode, MedicalRecord, OutcomeScenario, OutcomeTree, PatientState, QualitativeForecast, TreatmentAnalysis, TreatmentCandidate, TreatmentContext, TreatmentImpact)
from .prompts import CAUSAL_CONDITION_PROMPT, CAUSAL_OUTCOME_PROMPT, FAILURE_OUTCOME_PROMPT, FAILURE_PROMPT, IMPACT_PROMPT, MANIFESTATION_PROMPT, OUTCOME_PROMPT, TREATMENT_PROMPT
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


class CausalConditionDraft(BaseModel):
    statement: str = Field(max_length=280)
    mechanism: str | None = Field(default=None, max_length=220)
    patient_fact_ids: list[str] = Field(min_length=1)
    clinical_plausibility: float = Field(ge=0, le=1)
    temporal_plausibility: float = Field(ge=0, le=1)


class CausalConditionList(BaseModel):
    conditions: list[CausalConditionDraft] = Field(min_length=1, max_length=2)


class ManifestationDraft(CausalConditionDraft):
    condition_id: str


class ManifestationList(BaseModel):
    manifestations: list[ManifestationDraft] = Field(min_length=1, max_length=4)


class CausalOutcomeDraft(CausalConditionDraft):
    manifestation_id: str
    outcome_label: Literal["oncologic_failure", "toxicity", "intolerance", "interruption", "progression", "hospitalization", "functional_decline", "mortality"]


class CausalOutcomeList(BaseModel):
    outcomes: list[CausalOutcomeDraft] = Field(min_length=1, max_length=4)


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


def normalize_treatment_context(state: PatientState, treatment: TreatmentCandidate) -> TreatmentContext:
    modalities = {
        "radiotherapy": "external_beam_radiotherapy",
        "radioiodine": "radioiodine",
        "surgery": "surgery",
        "systemic_therapy": "systemic_therapy",
        "targeted_therapy": "targeted_therapy",
        "chemoradiotherapy": "chemoradiotherapy",
        "supportive_care": "supportive_care",
        "monitoring": "monitoring",
    }
    modality = modalities.get(treatment.treatment_class, "unknown")
    untreated = [f"metastatic_site:{site}" for site in state.cancer.metastatic_sites]
    missing: list[str] = []
    if modality == "external_beam_radiotherapy":
        missing.extend(["intent", "target_sites", "radiation_field_sites", "treated_lesion_ids"])
    completeness = "complete" if not missing else "unknown" if len(missing) == 4 else "partial"
    return TreatmentContext(
        treatment_id=treatment.treatment_id,
        modality=modality,
        intent=treatment.therapeutic_goal or "unknown",
        untreated_known_lesion_ids=untreated,
        context_completeness=completeness,
        missing_information=missing,
    )


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

    def run(self, state: PatientState, treatment: TreatmentCandidate, treatment_context: TreatmentContext, outcome: FailureOutcome, parent: FailureTreeNode | None, depth: int, explored_hypotheses: list[str]) -> tuple[list[FailureDraft], dict, list[Evidence]]:
        citations = self.retriever.retrieve(f"{treatment.guideline_query} {outcome.description}", scope=histology_scope(state), limit=3)
        context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "treatment_context": treatment_context.model_dump(), "outcome": outcome.model_dump(), "parent": parent.model_dump() if parent else None, "explored_hypotheses": explored_hypotheses, "guideline_evidence": [item.model_dump() for item in citations], "depth": depth, "iteration_instruction": "Formule causas-raiz distintas para o desfecho." if parent is None else "Avance uma etapa causal anterior, concreta e distinta ao mecanismo do nó-pai; não repita, resuma ou reformule a hipótese do pai."}
        result = self.client.chat_json(f"{FAILURE_CLINICAL_GUIDANCE_PROMPT}\n{FAILURE_PROMPT}", build_message("thyroid_failure_generation", context), schema=FailureDraftList)
        return FailureDraftList.model_validate(result).hypotheses, context, citations


class FailureOutcomeGenerator:
    def __init__(self, client: LLMClient, retriever: GuidelineRetriever) -> None:
        self.client = client
        self.retriever = retriever

    def run(self, state: PatientState, treatment: TreatmentCandidate, treatment_context: TreatmentContext) -> tuple[list[FailureOutcome], dict, list[Evidence]]:
        citations = self.retriever.retrieve(treatment.guideline_query or f"thyroid cancer {treatment.name}", scope=histology_scope(state), limit=3)
        context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "treatment_context": treatment_context.model_dump(), "guideline_evidence": [item.model_dump() for item in citations]}
        result = self.client.chat_json(f"{OUTCOME_CLINICAL_GUIDANCE_PROMPT}\n{FAILURE_OUTCOME_PROMPT}", build_message("thyroid_failure_outcome_generation", context), schema=OutcomeDraftList)
        drafts = OutcomeDraftList.model_validate(result).outcomes
        distinct_drafts = []
        seen_labels: set[str] = set()
        for draft in drafts:
            if draft.label in seen_labels:
                continue
            seen_labels.add(draft.label)
            distinct_drafts.append(draft)
        outcomes = []
        for index, draft in enumerate(distinct_drafts, start=1):
            outcome_type = "treatment_toxicity" if draft.label == "toxicity" else "treatment_interruption" if draft.label in {"intolerance", "interruption"} else "distant_progression" if draft.label == "progression" and state.cancer.metastatic else "unknown_or_unclassified"
            relationship = "outside_direct_locoregional_target" if outcome_type == "distant_progression" and treatment_context.modality == "external_beam_radiotherapy" else "unknown"
            failure = False if relationship == "outside_direct_locoregional_target" else None
            outcomes.append(FailureOutcome(outcome_id=f"{treatment.treatment_id}:{index}:{draft.label}", label=draft.label, description=draft.description, outcome_type=outcome_type, anatomic_sites=state.cancer.metastatic_sites if outcome_type == "distant_progression" else [], relationship_to_treatment_goal=relationship, is_treatment_failure=failure))
        return outcomes, context, citations


class OutcomeTreeGenerator:
    def __init__(self, client: LLMClient, retriever: GuidelineRetriever) -> None:
        self.client = client
        self.retriever = retriever

    def run(self, state: PatientState, treatment: TreatmentCandidate, treatment_context: TreatmentContext) -> OutcomeTree:
        citations = self.retriever.retrieve(treatment.guideline_query or f"thyroid cancer {treatment.name}", scope=histology_scope(state), limit=3)
        context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "treatment_context": treatment_context.model_dump(), "guideline_evidence": [item.model_dump() for item in citations]}
        result = self.client.chat_json(f"{OUTCOME_CLINICAL_GUIDANCE_PROMPT}\n{OUTCOME_PROMPT}", build_message("thyroid_outcome_tree_generation", context), schema=OutcomeScenarioDraftList)
        outcomes = [OutcomeScenario(outcome_id=f"{treatment.treatment_id}:outcome:{index}:{draft.label}", **draft.model_dump()) for index, draft in enumerate(OutcomeScenarioDraftList.model_validate(result).outcomes, start=1)]
        return OutcomeTree(treatment_id=treatment.treatment_id, root_description=f"Estratégia aplicada ao estado clínico inicial: {treatment.name}", outcomes=outcomes, evidence=citations, generation_context=context)


class ClinicalCritic:
    """Classifies support without treating a model score as clinical refutation."""

    def evaluate(self, state: PatientState, treatment_context: TreatmentContext, outcome: FailureOutcome, draft: FailureDraft, selected_facts: list, unknown_fact_ids: list[str], guideline_evidence: list[Evidence]) -> tuple[str, str | None, list[str], str, str]:
        hypothesis = f"{draft.hypothesis} {draft.mechanism}".casefold()
        if treatment_context.modality == "external_beam_radiotherapy" and treatment_context.context_completeness != "complete":
            return "unresolved", "UNRESOLVED_MISSING_DATA", treatment_context.missing_information, "Campo, alvo e intenção da EBRT não estão documentados; não é possível atribuir progressão a falha ou resistência da radioterapia.", "uncertain"
        if treatment_context.modality == "external_beam_radiotherapy" and outcome.relationship_to_treatment_goal == "outside_direct_locoregional_target" and any(term in hypothesis for term in ("radioresist", "reparo de dna", "resistência à radioterapia", "resistencia a radioterapia")):
            return "unresolved", "UNRESOLVED_INSUFFICIENT_SUPPORT", ["treated_lesion_ids", "radiation_field_sites"], "Mecanismo de resistência à EBRT não explica progressão distante fora do campo sem evidência de lesão efetivamente irradiada.", "relocate"
        if treatment_context.modality == "external_beam_radiotherapy" and "seleção clonal" in hypothesis:
            return "unresolved", "UNRESOLVED_INSUFFICIENT_SUPPORT", ["serial_molecular_evidence"], "Progressão após I-131 não demonstra seleção clonal induzida nem resistência à EBRT.", "revise"
        if not selected_facts:
            return "pruned", "PRUNED_ABSENT_CONDITION", [], "A condição necessária não está documentada no estado ativo.", "prune"
        if unknown_fact_ids:
            return "unresolved", "UNRESOLVED_MISSING_DATA", [f"unknown_patient_fact_id:{fact_id}" for fact_id in unknown_fact_ids], "A hipótese referencia fatos que não existem no prontuário ativo.", "uncertain"
        if not guideline_evidence:
            return "unresolved", "UNRESOLVED_MISSING_DATA", ["guideline_evidence"], "Não foi recuperada evidência externa para avaliar o mecanismo.", "uncertain"
        if len(draft.causal_chain) < 3 or min(draft.clinical_plausibility, draft.temporal_plausibility, draft.patient_specificity) < 0.6:
            return "unresolved", "UNRESOLVED_INSUFFICIENT_SUPPORT", [], "A hipótese exige revisão: a cadeia causal ou o suporte específico ainda é insuficiente para sustentação.", "revise"
        return "supported", None, [], "Hipótese ligada a fatos ativos e a evidência externa recuperada; permanece contrafactual.", "keep"


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

    def build(self, state: PatientState, treatment: TreatmentCandidate, treatment_context: TreatmentContext) -> CounterfactualTree:
        outcomes, outcome_generation_context, outcome_evidence = self.outcome_generator.run(state, treatment, treatment_context)
        nodes: list[FailureTreeNode] = []
        frontier: list[tuple[FailureOutcome, FailureTreeNode | None]] = [(outcome, None) for outcome in outcomes]
        seen: set[tuple[str, str]] = set()
        for depth in range(1, self.max_depth + 1):
            next_frontier: list[tuple[FailureOutcome, FailureTreeNode]] = []
            for outcome, parent in frontier:
                existing_for_outcome = [node for node in nodes if node.outcome_id == outcome.outcome_id]
                explored_hypotheses = [node.hypothesis for node in existing_for_outcome]
                drafts, generation_context, guideline_evidence = self.generator.run(state, treatment, treatment_context, outcome, parent, depth, explored_hypotheses)
                drafts = sorted(drafts, key=lambda item: item.clinical_plausibility + item.temporal_plausibility + item.patient_specificity, reverse=True)[: self.beam_width]
                for draft in drafts:
                    key = (outcome.outcome_id, draft.hypothesis.casefold())
                    if key in seen or is_redundant_hypothesis(draft, existing_for_outcome):
                        continue
                    seen.add(key)
                    node = self._validate_and_prune(state, treatment, treatment_context, outcome, parent, depth, draft, generation_context, guideline_evidence)
                    nodes.append(node)
                    existing_for_outcome.append(node)
                    if node.status == "supported" and depth < self.max_depth:
                        next_frontier.append((outcome, node))
            frontier = next_frontier
            if not frontier:
                break
        return CounterfactualTree(treatment_id=treatment.treatment_id, outcomes=outcomes, nodes=nodes, max_depth=self.max_depth, outcome_generation_context=outcome_generation_context, outcome_generation_trace={"outcome_ids": [outcome.outcome_id for outcome in outcomes], "outcome_count": len(outcomes), "evidence_sources": [item.source for item in outcome_evidence]})

    def _validate_and_prune(self, state: PatientState, treatment: TreatmentCandidate, treatment_context: TreatmentContext | None, outcome: FailureOutcome, parent: FailureTreeNode | None, depth: int, draft: FailureDraft, generation_context: dict | None = None, guideline_evidence: list[Evidence] | None = None) -> FailureTreeNode:
        active_facts = {fact.fact_id: fact for fact in state.active_problems if fact.status in {"active", "historical"}}
        selected_facts = resolve_patient_facts(state, draft.patient_fact_ids)
        patient_evidence = [evidence for fact in selected_facts for evidence in fact.evidence]
        unknown_fact_ids = sorted(set(draft.patient_fact_ids) - set(active_facts))
        context = treatment_context or normalize_treatment_context(state, treatment)
        status, code, missing, critique, decision = self.critic.evaluate(state, context, outcome, draft, selected_facts, unknown_fact_ids, guideline_evidence or [])
        validation_trace = {
            "requested_patient_fact_ids": draft.patient_fact_ids,
            "resolved_patient_fact_ids": [fact.fact_id for fact in selected_facts],
            "unknown_patient_fact_ids": unknown_fact_ids,
            "causal_chain_length": len(draft.causal_chain),
            "minimum_patient_specificity": self.minimum_plausibility,
            "status": status,
            "pruning_code": code,
        }
        return FailureTreeNode(node_id=str(uuid4()), parent_id=parent.node_id if parent else None, depth=depth, outcome_id=outcome.outcome_id, hypothesis=draft.hypothesis, mechanism=draft.mechanism, causal_chain=draft.causal_chain, required_patient_condition=draft.required_patient_condition, patient_evidence=patient_evidence, external_evidence=guideline_evidence or [], missing_information=missing, generation_context=generation_context or {}, validation_trace=validation_trace, clinical_plausibility=draft.clinical_plausibility, temporal_plausibility=draft.temporal_plausibility, patient_specificity=draft.patient_specificity, status=status, pruning_code=code, critique=critique, critic_decision=decision, inference_level="supported_inference" if status == "supported" else "speculative")


class CausalThoughtEngine:
    """Expande diagnóstico -> condição -> manifestação -> desfecho, nessa ordem estrita."""

    def __init__(self, client: LLMClient, retriever: GuidelineRetriever) -> None:
        self.client = client
        self.retriever = retriever

    def build(self, state: PatientState, treatment: TreatmentCandidate) -> CausalThoughtTree:
        root = CausalThoughtNode(
            node_id=f"{treatment.treatment_id}:diagnosis",
            depth=0,
            stage="diagnosis",
            statement=f"Diagnóstico confirmado de câncer de tireoide: {state.cancer.histology}",
            patient_fact_ids=["cancer_documented"],
            patient_evidence=resolve_patient_facts(state, ["cancer_documented"])[0].evidence,
            status="documented",
        )
        citations = self.retriever.retrieve(treatment.guideline_query or treatment.name, scope=histology_scope(state), limit=3)
        base_context = {"patient_state": reasoning_context(state), "treatment": treatment.model_dump(), "guideline_evidence": [item.model_dump() for item in citations]}
        conditions = CausalConditionList.model_validate(self.client.chat_json(CAUSAL_CONDITION_PROMPT, build_message("causal_conditions", base_context), schema=CausalConditionList)).conditions
        nodes = [root]
        condition_ids: set[str] = set()
        for index, draft in enumerate(conditions, start=1):
            node = self._node(f"{treatment.treatment_id}:condition:{index}", root.node_id, 1, "counterfactual_condition", draft, citations, state)
            nodes.append(node)
            if node.status == "supported":
                condition_ids.add(node.node_id)
        if not condition_ids:
            return CausalThoughtTree(treatment_id=treatment.treatment_id, root_id=root.node_id, nodes=nodes)

        manifestation_context = base_context | {"conditions": [node.model_dump() for node in nodes if node.node_id in condition_ids]}
        manifestations = ManifestationList.model_validate(self.client.chat_json(MANIFESTATION_PROMPT, build_message("causal_manifestations", manifestation_context), schema=ManifestationList)).manifestations
        manifestation_ids: set[str] = set()
        for index, draft in enumerate(manifestations, start=1):
            parent_id = draft.condition_id
            if parent_id not in condition_ids:
                continue
            node = self._node(f"{treatment.treatment_id}:manifestation:{index}", parent_id, 2, "manifestation", draft, citations, state)
            nodes.append(node)
            if node.status == "supported":
                manifestation_ids.add(node.node_id)
        if not manifestation_ids:
            return CausalThoughtTree(treatment_id=treatment.treatment_id, root_id=root.node_id, nodes=nodes)

        outcome_context = base_context | {"manifestations": [node.model_dump() for node in nodes if node.node_id in manifestation_ids]}
        outcomes = CausalOutcomeList.model_validate(self.client.chat_json(CAUSAL_OUTCOME_PROMPT, build_message("causal_outcomes", outcome_context), schema=CausalOutcomeList)).outcomes
        for index, draft in enumerate(outcomes, start=1):
            if draft.manifestation_id not in manifestation_ids:
                continue
            nodes.append(self._node(f"{treatment.treatment_id}:outcome:{index}", draft.manifestation_id, 3, "outcome", draft, citations, state, outcome_label=draft.outcome_label))
        return CausalThoughtTree(treatment_id=treatment.treatment_id, root_id=root.node_id, nodes=nodes)

    @staticmethod
    def _node(node_id: str, parent_id: str, depth: int, stage: str, draft: CausalConditionDraft, citations: list[Evidence], state: PatientState, outcome_label: str | None = None) -> CausalThoughtNode:
        facts = resolve_patient_facts(state, draft.patient_fact_ids)
        unknown = sorted(set(draft.patient_fact_ids) - {fact.fact_id for fact in state.active_problems})
        supported = bool(facts) and not unknown and bool(citations) and min(draft.clinical_plausibility, draft.temporal_plausibility) >= 0.6
        return CausalThoughtNode(
            node_id=node_id, parent_id=parent_id, depth=depth, stage=stage, statement=draft.statement,
            mechanism=draft.mechanism, patient_fact_ids=draft.patient_fact_ids,
            patient_evidence=[evidence for fact in facts for evidence in fact.evidence], external_evidence=citations,
            clinical_plausibility=draft.clinical_plausibility, temporal_plausibility=draft.temporal_plausibility,
            status="supported" if supported else "unresolved", missing_information=[f"unknown_patient_fact_id:{item}" for item in unknown],
            critique="Nó sustentado por fatos do prontuário e diretriz recuperada." if supported else "Nó não avança sem fatos válidos, suporte externo e plausibilidade suficiente.",
            outcome_label=outcome_label,
        )


def derive_legacy_trees(tree: CausalThoughtTree) -> tuple[CounterfactualTree, OutcomeTree]:
    """Mantém o contrato do relatório, mas deriva as folhas após a cadeia causal completa."""
    by_id = {node.node_id: node for node in tree.nodes}
    leaves = [node for node in tree.nodes if node.stage == "outcome" and node.status == "supported" and node.outcome_label]
    outcomes: list[FailureOutcome] = []
    failure_nodes: list[FailureTreeNode] = []
    scenarios: list[OutcomeScenario] = []
    scenario_labels = {"oncologic_failure": "recurrence_progression", "progression": "recurrence_progression", "toxicity": "toxicity", "intolerance": "quality_of_life", "interruption": "subsequent_therapy", "hospitalization": "quality_of_life", "functional_decline": "quality_of_life", "mortality": "mortality"}
    for index, leaf in enumerate(leaves, start=1):
        outcome_id = f"{tree.treatment_id}:derived:{index}"
        outcomes.append(FailureOutcome(outcome_id=outcome_id, label=leaf.outcome_label, description=leaf.statement))
        path: list[CausalThoughtNode] = []
        current: CausalThoughtNode | None = leaf
        while current:
            path.append(current)
            current = by_id.get(current.parent_id or "")
        path.reverse()
        failure_nodes.append(FailureTreeNode(node_id=leaf.node_id, depth=leaf.depth, outcome_id=outcome_id, hypothesis=leaf.statement, mechanism=leaf.mechanism or "Cadeia causal derivada", causal_chain=[node.statement for node in path], patient_evidence=leaf.patient_evidence, external_evidence=leaf.external_evidence, clinical_plausibility=leaf.clinical_plausibility, temporal_plausibility=leaf.temporal_plausibility, patient_specificity=leaf.clinical_plausibility, status="supported", critic_decision="keep", inference_level="supported_inference"))
        scenarios.append(OutcomeScenario(outcome_id=outcome_id, label=scenario_labels[leaf.outcome_label], description=leaf.statement, mechanism=leaf.mechanism))
    return CounterfactualTree(treatment_id=tree.treatment_id, outcomes=outcomes, nodes=failure_nodes, max_depth=tree.max_depth), OutcomeTree(treatment_id=tree.treatment_id, root_description="Folhas derivadas após diagnóstico, condições contrafactuais e manifestações clínicas.", outcomes=scenarios)


class ThyroidPrognosisPipeline:
    def __init__(self, client: LLMClient, *, model_name: str, max_depth: int = 5, guideline_index: Path | None = None) -> None:
        self.validator = MedicalRecordValidator()
        self.state_builder = PatientStateBuilder()
        self.graph_builder = ClinicalKnowledgeGraphBuilder()
        default_index = Path(__file__).resolve().parents[2] / "guidelines" / "br" / "processed" / "index.json"
        self.retriever = GuidelineRetriever(guideline_index or default_index)
        self.generator = TreatmentGenerator(self.retriever)
        self.eligibility_agent = ClinicalEligibilityAgent(self.retriever)
        self.failure_engine = CounterfactualEngine(FailureHypothesisGenerator(client, self.retriever), FailureOutcomeGenerator(client, self.retriever), max_depth=max_depth)
        self.causal_engine = CausalThoughtEngine(client, self.retriever)
        self.impact_agent = ImpactAgent(client)
        self.model_name = model_name

    def run(self, record: MedicalRecord) -> AnalysisReport:
        run_id = str(uuid4())
        validation = self.validator.validate(record)
        state = self.state_builder.build(validation)
        knowledge_graph = self.graph_builder.build(validation)
        candidates = self.generator.run(state)
        analyses: list[TreatmentAnalysis] = []
        for treatment in candidates:
            eligibility = self.eligibility_agent.assess(state, treatment)
            if eligibility.status == "ineligible":
                continue
            treatment_context = normalize_treatment_context(state, treatment)
            causal_tree = self.causal_engine.build(state, treatment)
            tree, outcome_tree = derive_legacy_trees(causal_tree)
            impacts = self.impact_agent.run(state, treatment)
            supported = [node for node in tree.nodes if node.status == "supported"]
            unresolved = [node for node in tree.nodes if node.status == "unresolved"]
            all_pruned = bool(tree.nodes) and all(node.status == "pruned" for node in tree.nodes)
            candidate_status = "insufficient_information" if eligibility.status == "indeterminate" else "high_risk" if any(node.outcome_id.endswith("toxicity") for node in supported) else "remains_plausible" if supported or all_pruned else "insufficient_information"
            forecast = QualitativeForecast(horizon="12 months", disease_control="unknown", adverse_outcome_risk="high" if any(node.outcome_id.endswith("toxicity") for node in supported) else "unknown", confidence_in_reasoning="moderate" if supported and eligibility.status == "eligible" else "low", rationale=[node.hypothesis for node in supported])
            uncertainties = ["Nenhum mecanismo causal específico ao paciente foi sustentado; isso não demonstra segurança ou eficácia."] if all_pruned else ["Ausência de mecanismo suportado não demonstra eficácia."] if not supported else []
            analyses.append(TreatmentAnalysis(treatment=treatment, treatment_context=treatment_context, eligibility=eligibility, causal_tree=causal_tree, outcome_tree=outcome_tree, candidate_status=candidate_status, failure_tree=tree, impacts=impacts, forecast=forecast, reasoning_summary=summarize_reasoning(tree), missing_information=state.missing_information + treatment_context.missing_information + [item for node in unresolved for item in node.missing_information], uncertainties=uncertainties))
        return AnalysisReport(run_id=run_id, case_id=record.case_id, patient_state=state, knowledge_graph=knowledge_graph, generated_treatments=candidates, candidate_treatments=analyses, reasoning_guidance_version="thyroid-causal-graph-v2", knowledge_base_version=self.retriever.version, catalog_version=catalog_version(), execution_parameters={"causal_order": ["diagnosis", "counterfactual_condition", "manifestation", "outcome"], "max_depth": 3}, audit_events=[{"event": "record_validated", "warnings": validation.warnings, "missing_information": validation.missing_information}, {"event": "knowledge_graph_built", "node_count": len(knowledge_graph.nodes), "edge_count": len(knowledge_graph.edges)}, {"event": "catalog_evaluated", "candidate_count": len(candidates)}, {"event": "treatments_analyzed", "treatment_ids": [item.treatment.treatment_id for item in analyses]}], model=self.model_name, timestamp=datetime.now(timezone.utc).isoformat())
