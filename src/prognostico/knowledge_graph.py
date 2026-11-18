from __future__ import annotations

from .models import ClinicalKnowledgeGraph, Evidence, KnowledgeGraphEdge, KnowledgeGraphNode, RecordValidation


class ClinicalKnowledgeGraphBuilder:
    """Converte o prontuário validado em fatos navegáveis, sem inferir causalidade."""

    def build(self, validation: RecordValidation) -> ClinicalKnowledgeGraph:
        record = validation.normalized_record
        root_id = "diagnosis:thyroid_cancer"
        nodes = [KnowledgeGraphNode(
            node_id=root_id,
            label=f"Diagnóstico confirmado de câncer de tireoide: {record.cancer.histology}",
            node_type="diagnosis",
            source_ids=["cancer.histology"],
            evidence=[Evidence(finding=record.cancer.histology, source="cancer.histology")],
        )]
        edges: list[KnowledgeGraphEdge] = []

        def add(node: KnowledgeGraphNode, relation: str) -> None:
            nodes.append(node)
            edges.append(KnowledgeGraphEdge(source_id=root_id, target_id=node.node_id, relation=relation))

        for name, value in record.cancer.model_dump(exclude_none=True).items():
            if name == "histology" or value in ([], {}):
                continue
            rendered = ", ".join(value) if isinstance(value, list) else ", ".join(f"{key}={item}" for key, item in value.items()) if isinstance(value, dict) else str(value)
            add(KnowledgeGraphNode(node_id=f"cancer:{name}", label=f"{name}: {rendered}", node_type="cancer_feature", source_ids=[f"cancer.{name}"], evidence=[Evidence(finding=rendered, source=f"cancer.{name}")]), "has_feature")
        for item in record.comorbidities:
            add(KnowledgeGraphNode(node_id=f"comorbidity:{item.condition}", label=f"Comorbidade {item.status}: {item.condition}", node_type="clinical_fact", source_ids=[f"comorbidity:{item.condition}"], evidence=[Evidence(finding=item.condition, source="medical_record")], observed_at=item.diagnosed_at), "has_condition")
        for item in record.lab_results:
            add(KnowledgeGraphNode(node_id=f"lab:{item.test_name}:{item.collected_at}", label=f"{item.test_name}={item.value} {item.unit or ''} ({item.interpretation})", node_type="laboratory", source_ids=[f"lab:{item.test_name}:{item.collected_at}"], evidence=[Evidence(finding=f"{item.test_name}={item.value} {item.unit or ''}", source=f"lab:{item.collected_at}")], observed_at=item.collected_at), "has_measurement")
        for item in record.vital_signs:
            add(KnowledgeGraphNode(node_id=f"vital:{item.name}:{item.measured_at}", label=f"{item.name}={item.value} {item.unit}", node_type="vital_sign", source_ids=[f"vital:{item.name}:{item.measured_at}"], evidence=[Evidence(finding=f"{item.name}={item.value} {item.unit}", source=f"vital:{item.measured_at}")], observed_at=item.measured_at), "has_measurement")
        for item in record.medications:
            add(KnowledgeGraphNode(node_id=f"medication:{item.name}:{item.started_at or 'unknown'}", label=f"Medicação {item.status}: {item.name}", node_type="medication", source_ids=[f"medication:{item.name}"], evidence=[Evidence(finding=item.name, source="medical_record")], observed_at=item.started_at), "receives")
        for item in record.prior_treatments:
            add(KnowledgeGraphNode(node_id=f"prior_treatment:{item.treatment_id}", label=f"Tratamento prévio {item.name}: {item.response}", node_type="prior_treatment", source_ids=[item.treatment_id], evidence=[Evidence(finding=item.response, source=item.treatment_id)], observed_at=item.started_at), "previously_received")
        for item in record.imaging_studies:
            add(KnowledgeGraphNode(node_id=f"imaging:{item.study_id}", label=item.impression or item.finding, node_type="imaging", source_ids=[f"imaging:{item.study_id}"], evidence=[Evidence(finding=item.finding, source=f"imaging:{item.study_id}")], observed_at=item.performed_at), "has_imaging")
        for index, item in enumerate(record.clinical_notes):
            add(KnowledgeGraphNode(node_id=f"note:{index}", label=item.text, node_type="clinical_note", source_ids=[f"note:{index}"], evidence=[Evidence(finding=item.text, source=f"note:{index}")], observed_at=item.recorded_at), "has_note")
        for index, item in enumerate(record.preferences):
            add(KnowledgeGraphNode(node_id=f"preference:{index}", label=item, node_type="preference", source_ids=[f"preference:{index}"], evidence=[Evidence(finding=item, source=f"preference:{index}")]), "has_preference")

        dated = sorted((node for node in nodes if node.observed_at), key=lambda node: node.observed_at or "")
        edges.extend(KnowledgeGraphEdge(source_id=previous.node_id, target_id=current.node_id, relation="precedes") for previous, current in zip(dated, dated[1:]) if previous.observed_at != current.observed_at)
        return ClinicalKnowledgeGraph(case_id=record.case_id, root_id=root_id, nodes=nodes, edges=edges)
