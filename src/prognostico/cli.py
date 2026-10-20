from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import get_config
from .llm import LlamaCppClient, OllamaClient
from .models import AnalysisReport, MedicalRecord
from .thyroid_pipeline import ThyroidPrognosisPipeline


def render_markdown(report: AnalysisReport) -> str:
    translations = {
        "candidate": "candidato",
        "not_applicable": "não aplicável",
        "insufficient_information": "informação insuficiente",
        "remains_plausible": "permanece plausível",
        "high_risk": "alto risco",
        "contraindication_identified": "contraindicação identificada",
        "unknown": "desconhecido",
        "diagnostic": "diagnóstico",
        "oncologic": "oncológico",
        "functional": "funcional",
        "endocrine": "endócrino",
        "cardiovascular": "cardiovascular",
        "renal": "renal",
        "hepatic": "hepático",
        "hematologic": "hematológico",
        "neurologic": "neurológico",
        "reproductive": "reprodutivo",
        "psychological": "psicológico",
        "nutritional": "nutricional",
        "quality_of_life": "qualidade de vida",
        "hospitalization": "hospitalização",
        "monitoring": "monitoramento",
        "medication": "medicamento",
        "short_term": "curto prazo",
        "medium_term": "médio prazo",
        "long_term": "longo prazo",
        "permanent": "permanente",
        "reversible": "reversível",
        "irreversible": "irreversível",
        "low": "baixo",
        "moderate": "moderado",
        "high": "alto",
        "plausible": "plausível",
        "limited": "limitado",
        "supported": "sustentado",
        "pruned": "podado",
        "unresolved": "não resolvido",
        "12 months": "12 meses",
    }

    def display(value: str | None) -> str:
        return translations.get(value or "", value or "não informado")

    mimic_labels = {
        "unknown; ICD-9 193 malignant neoplasm of thyroid gland": "desconhecido; CID-9 193 neoplasia maligna da glândula tireoide",
        "Complete thyroidectomy": "Tireoidectomia total",
        "Parathyroid tissue reimplantation": "Reimplante de tecido paratireoidiano",
        "Other incision with drainage of skin and subcutaneous tissue": "Outra incisão com drenagem de pele e tecido subcutâneo",
        "Coronary atherosclerosis of native coronary artery": "Aterosclerose coronariana de artéria nativa",
        "Other and unspecified angina pectoris": "Outra angina pectoris e angina pectoris não especificada",
        "Unspecified essential hypertension": "Hipertensão essencial não especificada",
        "Old myocardial infarction": "Infarto antigo do miocárdio",
        "Raynaud's syndrome": "Síndrome de Raynaud",
        "Occlusion and stenosis of carotid artery without mention of cerebral infarction": "Oclusão e estenose da artéria carótida sem menção de infarto cerebral",
        "Thyroid Stimulating Hormone": "Hormônio estimulante da tireoide",
        "Hematocrit": "Hematócrito",
        "Hemoglobin": "Hemoglobina",
        "Red Blood Cells": "Hemácias",
        "Calcium, Total": "Cálcio total",
        "Glucose": "Glicose",
    }

    def translate_mimic_label(text: str) -> str:
        for source, translation in mimic_labels.items():
            text = text.replace(source, translation)
        return text

    def evidence_text(items) -> str:
        return "; ".join(f"[{item.source or 'fonte não identificada'}] {translate_mimic_label(item.finding)}" for item in items) or "não registrada"

    state = report.patient_state
    cancer = state.cancer
    patient = state.patient
    lines = [
        "# Clinical Decision Memo",
        "",
        f"Caso: `{report.case_id}`",
        "",
        "> Relatório estruturado de apoio à análise terapêutica. Não é prescrição, decisão autônoma ou garantia de eficácia.",
        "",
        "## Metadados da Execução",
        f"- Modelo: `{report.model}`",
        f"- Orientação interna: `{report.reasoning_guidance_version}`",
        f"- Gerado em: `{report.timestamp}`",
        "",
        "## Estado Clínico e Oncológico",
        f"- Histologia: `{translate_mimic_label(cancer.histology)}`",
        f"- Diferenciação: `{cancer.differentiation or 'desconhecida'}`",
        f"- Estágio TNM: `{cancer.tnm_stage or 'desconhecido'}`",
        f"- Risco de recorrência: `{cancer.recurrence_risk or 'desconhecido'}`",
        f"- Doença metastática: `{'sim' if cancer.metastatic is True else 'não' if cancer.metastatic is False else 'desconhecida'}`; sítios: {', '.join(cancer.metastatic_sites) or 'não informado'}",
        f"- Radioiodo-avididade: `{cancer.iodine_avidity or 'desconhecida'}`",
        f"- Estado de progressão: `{cancer.progression_status or 'desconhecido'}`",
        f"- Perfil molecular: {', '.join(f'{key}={value}' for key, value in cancer.molecular_profile.items()) or 'não informado'}",
        f"- Idade: `{patient.age_years if patient.age_years is not None else 'desconhecida'}`; ECOG/estado funcional: `{patient.performance_status or patient.functional_status or 'desconhecido'}`",
        "",
        "## Fatos Ativos e Proveniência",
    ]
    lines.extend([f"- {translate_mimic_label(fact.statement)}. Fontes: {', '.join(fact.source_ids)}. Evidência: {evidence_text(fact.evidence)}" for fact in state.active_problems if fact.status == "active"] or ["- Nenhum fato ativo estruturado."])
    lines.extend(["", "## Histórico Terapêutico"])
    lines.extend([f"- {translate_mimic_label(item.name)}: resposta `{display(item.response)}`; período `{item.started_at or 'desconhecido'} → {item.ended_at or 'em andamento/desconhecido'}`; toxicidades: {', '.join(item.toxicities) or 'não registradas'}" for item in state.previous_treatments] or ["- Não informado."])
    lines.extend(["", "## Lacunas e Alertas do Prontuário"])
    lines.extend([f"- Dado ausente: `{item}`" for item in state.missing_information] or ["- Nenhuma lacuna estrutural identificada pelo validador."])
    lines.extend([f"- Alerta de validação: {item}" for item in state.data_warnings])
    lines.extend(["", "## Estratégias Geradas e Elegibilidade"])
    for item in report.generated_treatments:
        lines.extend([f"### {item.name}", f"- Status inicial: `{display(item.status)}`", f"- Classe: `{display(item.treatment_class)}`; objetivo: `{item.therapeutic_goal}`", f"- Motivos: {'; '.join(item.reason_for_consideration) or 'não informado'}", f"- Evidência do paciente: {evidence_text(item.patient_evidence)}", f"- Contraindicações detectadas: {', '.join(item.contraindications_detected) or 'nenhuma registrada'}", f"- Fontes externas recuperadas: {', '.join(item.evidence_source_ids) or 'nenhuma registrada'}", ""])
    lines.append("## Análise Contrafactual por Tratamento Candidato")
    for analysis in report.candidate_treatments:
        lines.extend(["", f"### {analysis.treatment.name}", f"- Status após análise: `{display(analysis.candidate_status)}`", f"- Profundidade máxima da árvore: `{analysis.failure_tree.max_depth}`"])
        for outcome in analysis.failure_tree.outcomes:
            lines.append(f"#### Desfecho contrafactual: {outcome.description}")
            nodes = [node for node in analysis.failure_tree.nodes if node.outcome_id == outcome.outcome_id]
            if not nodes:
                lines.append("- Nenhuma hipótese gerada.")
            for node in nodes:
                lines.extend([f"- Hipótese: {node.hypothesis}", f"- Estado: `{display(node.status)}`{f'; poda: `{node.pruning_code}`' if node.pruning_code else ''}", f"- Mecanismo: {node.mechanism}", f"- Cadeia causal: {' → '.join(node.causal_chain) or 'não explicitada'}", f"- Condição necessária: `{node.required_patient_condition or 'não especificada'}`", f"- Evidência do prontuário: {evidence_text(node.patient_evidence)}", f"- Evidência externa: {evidence_text(node.external_evidence)}", f"- Evidência contraditória: {evidence_text(node.contradictory_evidence)}", f"- Plausibilidade clínica/temporal/especificidade: `{node.clinical_plausibility:.2f}` / `{node.temporal_plausibility:.2f}` / `{node.patient_specificity:.2f}`"])
                lines.extend([f"- Informação ausente: `{item}`" for item in node.missing_information])
        lines.append("#### Impactos mesmo com controle oncológico")
        lines.extend([f"- {item.impact.rstrip('.')}. Domínio: `{display(item.domain)}`; tempo: `{display(item.timing)}`; reversibilidade: `{display(item.reversibility)}`; gravidade: `{display(item.severity)}`; específico ao paciente: `{'sim' if item.patient_specific else 'não'}`; evidência: {evidence_text(item.evidence)}" for item in analysis.impacts] or ["- Não descritos."])
        lines.extend(["#### Prognóstico Qualitativo", f"- Horizonte: `{analysis.forecast.horizon}`", f"- Controle da doença: `{display(analysis.forecast.disease_control)}`", f"- Risco de desfecho adverso: `{display(analysis.forecast.adverse_outcome_risk)}`", f"- Confiança no raciocínio: `{display(analysis.forecast.confidence_in_reasoning)}`", f"- Fundamentação: {'; '.join(analysis.forecast.rationale) or 'não disponível'}", f"- Informações adicionais úteis: {', '.join(analysis.missing_information) or 'nenhuma identificada'}", f"- Incertezas: {'; '.join(analysis.uncertainties) or 'nenhuma adicional'}"])
    lines.extend(["", "## Limitações Metodológicas", "- A ausência de mecanismo de falha sustentado não comprova eficácia ou segurança.", "- O prognóstico é qualitativo; probabilidades numéricas exigem validação e calibração externas.", "- A orientação clínica dos agentes é interna aos prompts e não substitui diretrizes ou avaliação por especialista."])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP de prognóstico para câncer de tireoide")
    parser.add_argument("input", type=Path, help="prontuário JSON estruturado")
    parser.add_argument("--out", type=Path, default=Path("outputs/thyroid_report.json"))
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--provider", choices=["ollama", "llama-cpp"], default="ollama")
    parser.add_argument("--base-url", help="URL do servidor do provedor")
    parser.add_argument("--model", help="Identificador do modelo no provedor")
    args = parser.parse_args()
    config = get_config()
    base_url = args.base_url or config.ollama_base_url
    model = args.model or config.model
    client_class = LlamaCppClient if args.provider == "llama-cpp" else OllamaClient
    client = client_class(base_url, model, config.temperature, config.request_timeout_seconds, config.max_output_tokens)
    record = MedicalRecord.model_validate(json.loads(args.input.read_text()))
    report = ThyroidPrognosisPipeline(client, model_name=model, max_depth=args.max_depth).run(record)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.out.with_name(f"{args.out.stem}_{timestamp}{args.out.suffix}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))
    output_path.with_suffix(".md").write_text(render_markdown(report))


if __name__ == "__main__":
    main()
