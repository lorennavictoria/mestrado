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
        normalized = record.model_copy(deep=True)
        if _valid_date(record.record_date):
            reference_date = date.fromisoformat(record.record_date)
            future_labs = [lab for lab in normalized.lab_results if _valid_date(lab.collected_at) and date.fromisoformat(lab.collected_at) > reference_date]
            future_imaging = [study for study in normalized.imaging_studies if _valid_date(study.performed_at) and date.fromisoformat(study.performed_at) > reference_date]
            if future_labs:
                warnings.append(f"{len(future_labs)} resultado(s) laboratorial(is) posterior(es) a record_date foram excluídos da análise.")
                normalized.lab_results = [lab for lab in normalized.lab_results if lab not in future_labs]
            if future_imaging:
                warnings.append(f"{len(future_imaging)} estudo(s) de imagem posterior(es) a record_date foram excluídos da análise.")
                normalized.imaging_studies = [study for study in normalized.imaging_studies if study not in future_imaging]
        for medication in normalized.medications:
            if medication.started_at and medication.ended_at and medication.ended_at < medication.started_at:
                conflicts.append(f"medicação {medication.name} termina antes de iniciar")
        if not normalized.patient.performance_status:
            missing.append("performance_status")
        if not normalized.cancer.tnm_stage:
            missing.append("tnm_stage")
        if not normalized.lab_results:
            missing.append("recent_laboratory_results")
        normalized.lab_results.sort(key=lambda item: item.collected_at)
        normalized.imaging_studies.sort(key=lambda item: item.performed_at)
        return RecordValidation(normalized_record=normalized, warnings=warnings, missing_information=missing, temporal_conflicts=conflicts)
