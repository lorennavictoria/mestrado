from __future__ import annotations

from .models import Evidence, PatientState, TreatmentCandidate


class ClinicalKnowledgeBase:
    
    version = "thyroid-poc-1"

    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def retrieve(self, state: PatientState, treatment: TreatmentCandidate | None = None) -> list[Evidence]:
        query = " ".join([state.cancer.histology, state.cancer.progression_status or "", treatment.name if treatment else ""]).casefold().replace("_", " ")
        results: list[Evidence] = []
        for document in self.documents:
            text = " ".join(document.get("keywords", [])).casefold()
            if any(token in text for token in query.split() if len(token) > 3):
                results.append(Evidence(finding=document["summary"], source=document["document_id"]))
        return results
