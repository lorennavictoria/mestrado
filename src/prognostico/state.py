from __future__ import annotations

from .models import Evidence, PatientState, ProvenancedFact, RecordValidation


class PatientStateBuilder:
    """Resume fatos decisórios e mantém a proveniência no prontuário de origem."""

    def build(self, validation: RecordValidation) -> PatientState:
        record = validation.normalized_record
        facts: list[ProvenancedFact] = []
        cancer = record.cancer
        if cancer.progression_status:
            facts.append(ProvenancedFact(fact_id="cancer_progression", statement=f"Estado de progressão: {cancer.progression_status}", source_ids=["cancer"], evidence=[Evidence(finding=cancer.progression_status, source="cancer")], status="active"))
        if cancer.metastatic:
            facts.append(ProvenancedFact(fact_id="metastatic_disease", statement=f"Doença metastática em: {', '.join(cancer.metastatic_sites) or 'local não especificado'}", source_ids=["cancer"], evidence=[Evidence(finding="metastatic disease", source="cancer")], status="active"))
        active_comorbidities = [item for item in record.comorbidities if item.status == "active"]
        for item in active_comorbidities:
            if item.status == "active":
                facts.append(ProvenancedFact(fact_id=f"comorbidity:{item.condition}", statement=f"Comorbidade ativa: {item.condition}", source_ids=[f"comorbidity:{item.condition}"], evidence=[Evidence(finding=item.condition, source="medical_record")], status="active"))
        if active_comorbidities:
            facts.append(ProvenancedFact(
                fact_id="active_comorbidity_summary",
                statement="Comorbidades ativas documentadas: " + "; ".join(item.condition for item in active_comorbidities),
                source_ids=[f"comorbidity:{item.condition}" for item in active_comorbidities],
                evidence=[Evidence(finding=item.condition, source="medical_record") for item in active_comorbidities],
                status="active",
            ))

        abnormal_labs: dict[str, list] = {}
        for lab in record.lab_results:
            if lab.interpretation in {"low", "high", "abnormal"}:
                abnormal_labs.setdefault(lab.test_name.casefold(), []).append(lab)
        for test_name, results in abnormal_labs.items():
            latest = results[-1]
            facts.append(ProvenancedFact(
                fact_id=f"abnormal_lab_summary:{test_name}",
                statement=f"Anormalidade laboratorial documentada em {latest.test_name}: {len(results)} resultado(s); mais recente {latest.value} {latest.unit or ''} em {latest.collected_at} ({latest.interpretation}).",
                source_ids=[f"lab:{item.test_name}:{item.collected_at}" for item in results],
                evidence=[Evidence(finding=f"{item.test_name}={item.value} {item.unit or ''}", source=f"lab:{item.collected_at}") for item in results],
                status="active",
            ))

        for vital in record.vital_signs:
            facts.append(ProvenancedFact(
                fact_id=f"vital:{vital.name}:{vital.measured_at}",
                statement=f"Sinal vital documentado: {vital.name}={vital.value} {vital.unit} em {vital.measured_at}",
                source_ids=[f"vital:{vital.name}:{vital.measured_at}"],
                evidence=[Evidence(finding=f"{vital.name}={vital.value} {vital.unit}", source=f"vital:{vital.measured_at}")],
                status="active",
            ))

        for medication in record.medications:
            if medication.status not in {"active", "held"}:
                continue
            facts.append(ProvenancedFact(
                fact_id=f"medication:{medication.name}:{medication.started_at or 'unknown'}",
                statement=f"Medicação {medication.status}: {medication.name}" + (f"; dose {medication.dose}" if medication.dose else ""),
                source_ids=[f"medication:{medication.name}"],
                evidence=[Evidence(finding=medication.name, source="medical_record")],
                status="active",
            ))
        for treatment in record.prior_treatments:
            facts.append(ProvenancedFact(fact_id=f"prior_treatment:{treatment.treatment_id}", statement=f"Tratamento prévio {treatment.name}: {treatment.response}", source_ids=[treatment.treatment_id], evidence=[Evidence(finding=treatment.response, source=treatment.treatment_id)], status="historical"))
        return PatientState(case_id=record.case_id, cancer=cancer, patient=record.patient, active_problems=facts, previous_treatments=record.prior_treatments, medications=record.medications, missing_information=validation.missing_information, data_warnings=validation.warnings + validation.temporal_conflicts)
