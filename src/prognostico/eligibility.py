from __future__ import annotations

from .guidelines import GuidelineRetriever
from .models import EligibilityAssessment, PatientState, TreatmentCandidate
from .treatment_catalog import histology_scope


class ClinicalEligibilityAgent:
    """Applies deterministic candidate status before tree expansion."""

    def __init__(self, retriever: GuidelineRetriever) -> None:
        self.retriever = retriever

    def assess(self, state: PatientState, treatment: TreatmentCandidate) -> EligibilityAssessment:
        citations = self.retriever.retrieve(treatment.guideline_query or f"thyroid cancer {treatment.name}", scope=histology_scope(state), limit=3)
        if treatment.status == "not_applicable":
            return EligibilityAssessment(status="ineligible", reasons=treatment.reason_for_consideration, citations=citations)
        if treatment.status == "insufficient_information":
            return EligibilityAssessment(
                status="indeterminate",
                reasons=treatment.reason_for_consideration,
                missing_requirements=treatment.eligibility_missing,
                citations=citations,
            )
        return EligibilityAssessment(status="eligible", reasons=treatment.reason_for_consideration, citations=citations)
