from __future__ import annotations

from dataclasses import dataclass

from .models import PatientState, TreatmentCandidate


@dataclass(frozen=True)
class TreatmentDefinition:
    treatment_id: str
    name: str
    treatment_class: str
    therapeutic_goal: str
    eligible_histologies: tuple[str, ...]
    required_features: tuple[str, ...]
    contraindications: tuple[str, ...]
    recommendation_ids: tuple[str, ...]
    query: str
    components: tuple[str, ...] = ()
    sequence: tuple[str, ...] = ()
    monitoring: tuple[str, ...] = ()
    potential_adverse_events: tuple[str, ...] = ()
    guideline_version: str = "local-guidelines-2026"
    references: tuple[str, ...] = ()


CATALOG = (
    TreatmentDefinition("DTC_ACTIVE_SURVEILLANCE", "Vigilância ativa", "monitoring", "monitoramento estruturado de doença selecionada", ("differentiated",), ("t1a", "cN0", "cM0"), (), ("ATA_DTC_R11",), "ATA active surveillance cT1a N0 M0 papillary thyroid cancer", ("imagem seriada", "avaliação clínica"), (), ("imagem", "crescimento tumoral"), ("ansiedade", "progressão durante observação"), references=("ATA_DTC_2025",)),
    TreatmentDefinition("DTC_LOBECTOMY", "Lobectomia", "surgery", "controle locorregional inicial", ("differentiated",), ("resectable",), (), ("ATA_DTC_R15",), "ATA lobectomy differentiated thyroid cancer low risk", ("cirurgia unilateral",), (), ("função vocal", "função tireoidiana"), ("lesão nervosa", "hipotireoidismo"), references=("ATA_DTC_2025",)),
    TreatmentDefinition("DTC_TOTAL_THYROIDECTOMY", "Tireoidectomia total", "surgery", "controle locorregional e preparo para seguimento/RAI quando indicado", ("differentiated",), ("advanced_local_or_nodal_or_metastatic",), (), ("ATA_DTC_R15",), "ATA total thyroidectomy advanced differentiated thyroid cancer", ("cirurgia", "avaliação linfonodal quando indicada"), (), ("cálcio", "função vocal", "reposição hormonal"), ("hipocalcemia", "lesão nervosa"), references=("ATA_DTC_2025",)),
    TreatmentDefinition("DTC_RADIOIODINE", "Radioiodoterapia", "radioiodine", "ablação, terapia adjuvante ou tratamento de doença iodo-ávida", ("differentiated",), ("post_thyroidectomy",), ("anaplastic", "medullary"), ("ATA_DTC_R32",), "ATA radioactive iodine differentiated thyroid cancer recurrence risk", ("I-131",), ("após tireoidectomia quando indicado",), ("tireoglobulina", "função salivar"), ("sialadenite", "xerostomia"), references=("ATA_DTC_2025",)),
    TreatmentDefinition("DTC_EBRT", "Radioterapia externa selecionada", "radiotherapy", "controle locorregional em circunstâncias selecionadas", ("differentiated",), ("advanced_local_or_nodal_or_metastatic",), (), ("ATA_DTC_R64",), "external beam radiotherapy differentiated thyroid cancer locoregional", ("planejamento radioterápico",), (), ("toxicidade cervical",), ("disfagia", "dermatite", "fibrose"), references=("ATA_DTC_2025",)),
    TreatmentDefinition("DTC_RAIRD_MKI", "Inibidor multiquinase para doença refratária ao radioiodo", "systemic_therapy", "controle de doença progressiva refratária ao radioiodo", ("differentiated",), ("radioiodine_refractory", "progressive"), ("uncontrolled_hypertension",), ("ATA_DTC_R62", "ASCO_2026_1_1"), "radioiodine refractory differentiated thyroid cancer lenvatinib sorafenib hypertension", ("terapia sistêmica",), (), ("pressão arterial", "função renal", "toxicidade"), ("hipertensão", "fadiga", "diarreia"), references=("ATA_DTC_2025", "ASCO_SYSTEMIC_2026")),
    TreatmentDefinition("ATC_TARGETED_THERAPY", "Terapia-alvo para doença anaplásica com alteração acionável", "targeted_therapy", "controle sistêmico conforme perfil molecular", ("anaplastic",), ("progressive",), (), ("ATA_ATC_R20",), "anaplastic thyroid cancer molecular targeted therapy BRAF", ("perfil molecular", "terapia-alvo"), (), ("toxicidade específica",), ("toxicidade sistêmica",), references=("ATA_ATC_2021", "ASCO_SYSTEMIC_2026")),
    TreatmentDefinition("ATC_CHEMORADIOTHERAPY", "Quimiorradioterapia para doença anaplásica selecionada", "chemoradiotherapy", "controle locorregional e sistêmico em doença anaplásica selecionada", ("anaplastic",), ("advanced_local_or_nodal_or_metastatic",), (), ("ATA_ATC_R30",), "anaplastic thyroid cancer chemoradiotherapy", ("quimioterapia", "radioterapia"), (), ("hemograma", "função renal", "toxicidade"), ("mielossupressão", "mucosite"), references=("ATA_ATC_2021",)),
    TreatmentDefinition("SUPPORTIVE_CARE", "Cuidados de suporte e controle de sintomas", "supportive_care", "alívio de sintomas e preservação de qualidade de vida", ("differentiated", "anaplastic", "medullary", "poorly_differentiated"), (), (), ("ATA_DTC_R82",), "thyroid cancer supportive care quality of life", ("controle de sintomas", "apoio psicossocial"), (), ("sintomas", "necessidades de suporte"), (), references=("ATA_DTC_2025", "ATA_ATC_2021", "ASCO_SYSTEMIC_2026")),
)


def histology_scope(state: PatientState) -> str | None:
    text = state.cancer.histology.casefold()
    if any(value in text for value in ("papillary", "follicular", "differentiated", "oncocytic")):
        return "differentiated"
    if "anaplastic" in text:
        return "anaplastic"
    if "medullary" in text:
        return "medullary"
    return None


def _feature_status(state: PatientState, feature: str) -> bool | None:
    stage = (state.cancer.tnm_stage or "").casefold().replace(" ", "")
    progression = (state.cancer.progression_status or "").casefold()
    iodine = (state.cancer.iodine_avidity or "").casefold()
    prior_names = " ".join(item.name.casefold() for item in state.previous_treatments)

    if feature == "t1a":
        return True if "t1a" in stage else False if stage else None
    if feature == "cN0":
        return True if "cn0" in stage else False if "n" in stage else None
    if feature == "cM0":
        if state.cancer.metastatic is not None:
            return not state.cancer.metastatic
        return True if "cm0" in stage else False if "m1" in stage else None
    if feature == "resectable":
        return None
    if feature == "advanced_local_or_nodal_or_metastatic":
        if state.cancer.metastatic is True:
            return True
        return True if any(value in stage for value in ("t3", "t4", "n1", "m1")) else False if stage else None
    if feature == "post_thyroidectomy":
        return True if any(name in prior_names for name in ("thyroidectomy", "tireoidectomia")) else None
    if feature == "radioiodine_refractory":
        return True if "refractory" in iodine else None
    if feature == "progressive":
        return True if "progress" in progression else None
    raise ValueError(f"Critério de catálogo desconhecido: {feature}")


def _detected_contraindications(state: PatientState, definition: TreatmentDefinition) -> list[str]:
    active_text = " ".join(fact.statement.casefold() for fact in state.active_problems if fact.status == "active")
    return [item for item in definition.contraindications if item.replace("_", " ") in active_text]


def evaluate_catalog(state: PatientState) -> list[TreatmentCandidate]:
    scope = histology_scope(state)
    prior_names = " ".join(item.name.casefold() for item in state.previous_treatments)
    iodine = (state.cancer.iodine_avidity or "").casefold()
    candidates: list[TreatmentCandidate] = []
    for definition in CATALOG:
        contraindications = _detected_contraindications(state, definition)
        if scope and scope not in definition.eligible_histologies:
            status, reasons = "not_applicable", ["Histologia incompatível com a estratégia do catálogo."]
            missing = []
        elif definition.treatment_id == "DTC_RADIOIODINE" and scope in {"anaplastic", "medullary"}:
            status, reasons = "not_applicable", ["Radioiodo dirigido ao tumor não é aplicável para esta histologia."]
            missing = []
        elif definition.treatment_id in {"DTC_LOBECTOMY", "DTC_TOTAL_THYROIDECTOMY"} and any(name in prior_names for name in ("thyroidectomy", "tireoidectomia")):
            status, reasons = "not_applicable", ["Cirurgia tireoidiana definitiva já documentada no histórico terapêutico."]
            missing = []
        elif definition.treatment_id == "DTC_RADIOIODINE" and any(value in iodine for value in ("refractory", "absent")):
            status, reasons = "not_applicable", ["Doença refratária ao radioiodo documentada; nova radioiodoterapia dirigida ao tumor não é aplicável no catálogo."]
            missing = []
        elif contraindications:
            status, reasons = "not_applicable", ["Contraindicações documentadas: " + ", ".join(contraindications)]
            missing = []
        else:
            feature_statuses = {feature: _feature_status(state, feature) for feature in definition.required_features}
            excluded = [feature for feature, present in feature_statuses.items() if present is False]
            missing = [feature for feature, present in feature_statuses.items() if present is None]
            if excluded:
                status, reasons = "not_applicable", ["Critérios clínicos não atendidos: " + ", ".join(excluded)]
                missing = []
            elif scope and not missing:
                status, reasons = "candidate", ["Critérios do catálogo presentes no prontuário."]
            else:
                status, reasons = "insufficient_information", ["Dados necessários para elegibilidade: " + ", ".join(missing or ["histologia confirmada"])]
        candidates.append(TreatmentCandidate(
            treatment_id=definition.treatment_id,
            name=definition.name,
            treatment_class=definition.treatment_class,
            therapeutic_goal=definition.therapeutic_goal,
            components=list(definition.components),
            sequence=list(definition.sequence),
            monitoring=list(definition.monitoring),
            potential_adverse_events=list(definition.potential_adverse_events),
            guideline_version=definition.guideline_version,
            references=list(definition.references),
            guideline_query=definition.query,
            reason_for_consideration=reasons,
            patient_evidence=[],
            patient_fact_ids=["cancer_documented"],
            contraindications_detected=contraindications,
            eligibility_missing=missing,
            evidence_source_ids=list(definition.recommendation_ids),
            status=status,
        ))
    return candidates


def catalog_version() -> str:
    return "thyroid-catalog-2026-1"
