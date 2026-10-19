from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import get_config
from .knowledge import ClinicalKnowledgeBase
from .llm import OllamaClient
from .models import AnalysisReport, MedicalRecord
from .thyroid_pipeline import ThyroidPrognosisPipeline


def render_markdown(report: AnalysisReport) -> str:
    def evidence_text(items) -> str:
        return "; ".join(f"[{item.source or 'fonte não identificada'}] {item.finding}" for item in items) or "não registrada"

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
        f"- Base de conhecimento: `{report.knowledge_base_version}`",
        f"- Gerado em: `{report.timestamp}`",
        "",
        "## Estado Clínico e Oncológico",
        f"- Histologia: `{cancer.histology}`",
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
    lines.extend([f"- {fact.statement}. Fontes: {', '.join(fact.source_ids)}. Evidência: {evidence_text(fact.evidence)}" for fact in state.active_problems if fact.status == "active"] or ["- Nenhum fato ativo estruturado."])
    lines.extend(["", "## Histórico Terapêutico"])
    lines.extend([f"- {item.name}: resposta `{item.response}`; período `{item.started_at or 'desconhecido'} → {item.ended_at or 'em andamento/desconhecido'}`; toxicidades: {', '.join(item.toxicities) or 'não registradas'}" for item in state.previous_treatments] or ["- Não informado."])
    lines.extend(["", "## Lacunas e Alertas do Prontuário"])
    lines.extend([f"- Dado ausente: `{item}`" for item in state.missing_information] or ["- Nenhuma lacuna estrutural identificada pelo validador."])
    lines.extend([f"- Alerta de validação: {item}" for item in state.data_warnings])
    lines.extend(["", "## Estratégias Geradas e Elegibilidade"])
    for item in report.generated_treatments:
        lines.extend([f"### {item.name}", f"- Status inicial: `{item.status}`", f"- Classe: `{item.treatment_class}`; objetivo: `{item.therapeutic_goal}`", f"- Motivos: {'; '.join(item.reason_for_consideration) or 'não informado'}", f"- Evidência do paciente: {evidence_text(item.patient_evidence)}", f"- Contraindicações detectadas: {', '.join(item.contraindications_detected) or 'nenhuma registrada'}", f"- Fontes externas recuperadas: {', '.join(item.evidence_source_ids) or 'nenhuma registrada'}", ""])
    lines.append("## Análise Contrafactual por Tratamento Candidato")
    for analysis in report.candidate_treatments:
        lines.extend(["", f"### {analysis.treatment.name}", f"- Status após análise: `{analysis.candidate_status}`", f"- Profundidade máxima da árvore: `{analysis.failure_tree.max_depth}`"])
        for outcome in analysis.failure_tree.outcomes:
            lines.append(f"#### Desfecho contrafactual: {outcome.description}")
            nodes = [node for node in analysis.failure_tree.nodes if node.outcome_id == outcome.outcome_id]
            if not nodes:
                lines.append("- Nenhuma hipótese gerada.")
            for node in nodes:
                lines.extend([f"- Hipótese: {node.hypothesis}", f"- Estado: `{node.status}`{f'; poda: `{node.pruning_code}`' if node.pruning_code else ''}", f"- Mecanismo: {node.mechanism}", f"- Cadeia causal: {' → '.join(node.causal_chain) or 'não explicitada'}", f"- Condição necessária: `{node.required_patient_condition or 'não especificada'}`", f"- Evidência do prontuário: {evidence_text(node.patient_evidence)}", f"- Evidência externa: {evidence_text(node.external_evidence)}", f"- Evidência contraditória: {evidence_text(node.contradictory_evidence)}", f"- Plausibilidade clínica/temporal/especificidade: `{node.clinical_plausibility:.2f}` / `{node.temporal_plausibility:.2f}` / `{node.patient_specificity:.2f}`"])
                lines.extend([f"- Informação ausente: `{item}`" for item in node.missing_information])
        lines.append("#### Impactos mesmo com controle oncológico")
        lines.extend([f"- {item.impact.rstrip('.')}. Domínio: `{item.domain}`; tempo: `{item.timing}`; reversibilidade: `{item.reversibility}`; gravidade: `{item.severity}`; específico ao paciente: `{'sim' if item.patient_specific else 'não'}`; evidência: {evidence_text(item.evidence)}" for item in analysis.impacts] or ["- Não descritos."])
        lines.extend(["#### Prognóstico Qualitativo", f"- Horizonte: `{analysis.forecast.horizon}`", f"- Controle da doença: `{analysis.forecast.disease_control}`", f"- Risco de desfecho adverso: `{analysis.forecast.adverse_outcome_risk}`", f"- Confiança no raciocínio: `{analysis.forecast.confidence_in_reasoning}`", f"- Fundamentação: {'; '.join(analysis.forecast.rationale) or 'não disponível'}", f"- Informações adicionais úteis: {', '.join(analysis.missing_information) or 'nenhuma identificada'}", f"- Incertezas: {'; '.join(analysis.uncertainties) or 'nenhuma adicional'}"])
    lines.extend(["", "## Limitações Metodológicas", "- A ausência de mecanismo de falha sustentado não comprova eficácia ou segurança.", "- O prognóstico é qualitativo; probabilidades numéricas exigem validação e calibração externas.", "- A base documental do MVP é demonstrativa e não substitui guidelines ou avaliação por especialista."])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP de prognóstico para câncer de tireoide")
    parser.add_argument("input", type=Path, help="prontuário JSON estruturado")
    parser.add_argument("--out", type=Path, default=Path("outputs/thyroid_report.json"))
    parser.add_argument("--knowledge", type=Path, default=Path("data/guidelines/thyroid_poc.json"))
    parser.add_argument("--max-depth", type=int, default=3)
    args = parser.parse_args()
    config = get_config()
    client = OllamaClient(config.ollama_base_url, config.model, config.temperature, config.request_timeout_seconds, config.max_output_tokens)
    record = MedicalRecord.model_validate(json.loads(args.input.read_text()))
    knowledge_base = ClinicalKnowledgeBase(json.loads(args.knowledge.read_text()))
    report = ThyroidPrognosisPipeline(client, knowledge_base, model_name=config.model, max_depth=args.max_depth).run(record)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))
    args.out.with_suffix(".md").write_text(render_markdown(report))


if __name__ == "__main__":
    main()
