TREATMENT_CLINICAL_GUIDANCE_PROMPT = """
Orientação clínica interna para geração de estratégias em câncer de tireoide:
- Trate somente o PatientState como fonte de fatos sobre o paciente.
- Use conhecimento clínico apenas para organizar possibilidades analíticas; nunca o apresente
  como guideline, artigo, fonte externa ou evidência do paciente.
- Diferencie estratégias diagnósticas, de reavaliação e terapêuticas sem recomendar uma conduta.
- Dados ausentes reduzem a certeza e devem permanecer explícitos; nunca os trate como normais.
"""


FAILURE_CLINICAL_GUIDANCE_PROMPT = """
Orientação clínica interna para hipóteses contrafactuais de falha:
- Trate somente fatos ativos do PatientState como evidência do paciente.
- Uma hipótese deve conectar uma condição documentada, a interação com o tratamento, uma
  alteração fisiológica ou operacional e o desfecho contrafactual.
- Não converta associação em causalidade e não use eventos posteriores como causa da exposição.
- Lacunas devem ser declaradas como incerteza; não invente resultados, contraindicações ou fatos.
- Conhecimento clínico serve apenas para formular mecanismos e não pode ser citado como fonte externa.
"""


IMPACT_CLINICAL_GUIDANCE_PROMPT = """
Orientação clínica interna para impactos do tratamento:
- Separe consequências esperadas de mecanismos de falha terapêutica.
- Marque um impacto como específico ao paciente somente quando ele estiver vinculado a um fato do
  PatientState; caso contrário, trate-o como possibilidade geral.
- Não apresente conhecimento clínico interno como fonte externa, guideline ou evidência do paciente.
"""
