from __future__ import annotations

from datetime import date

from .models import MedicalRecord, RecordValidation


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


class MedicalRecordValidator:
    """Valida cronologia e preserva as medidas originais do prontuário."""

    def validate(self, record: MedicalRecord) -> RecordValidation:
        warnings: list[str] = list(record.data_warnings)
        missing: list[str] = []
        conflicts: list[str] = []
        if not _valid_date(record.record_date):
            warnings.append("record_date não está no formato ISO YYYY-MM-DD.")
        for lab in record.lab_results:
            if not _valid_date(lab.collected_at):
                warnings.append(f"data inválida para exame {lab.test_name}: {lab.collected_at}")
        for study in record.imaging_studies:
            if not _valid_date(study.performed_at):
                warnings.append(f"data inválida para imagem {study.study_id}: {study.performed_at}")
        for treatment in record.prior_treatments:
            if treatment.started_at and treatment.ended_at and treatment.ended_at < treatment.started_at:
                conflicts.append(f"tratamento {treatment.treatment_id} termina antes de iniciar")
        if not record.patient.performance_status:
            missing.append("performance_status")
        if not record.cancer.tnm_stage:
            missing.append("tnm_stage")
        if not record.lab_results:
            missing.append("recent_laboratory_results")
        normalized = record.model_copy(deep=True)
        normalized.lab_results.sort(key=lambda item: item.collected_at)
        normalized.imaging_studies.sort(key=lambda item: item.performed_at)
        return RecordValidation(normalized_record=normalized, warnings=warnings, missing_information=missing, temporal_conflicts=conflicts)
