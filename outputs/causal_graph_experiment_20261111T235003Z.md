# Clinical Decision Memo

Caso: `THYROID-POC-001`

> Relatório estruturado de apoio à análise terapêutica. Não é prescrição, decisão autônoma ou garantia de eficácia.

## Metadados da Execução
- Modelo: `qwen3.5:9b`
- Orientação interna: `thyroid-causal-graph-v2`
- Catálogo terapêutico: `thyroid-catalog-2026-1`
- Base de diretrizes: `BR_SBOC_CDT_ANAP_2026:2026+BR_SBOC_MED_2026:2026+BR_MS_PCDT_CDT_2026:2026`
- Gerado em: `2026-11-11T23:50:03.357566+00:00`

## Estado Clínico e Oncológico
- Histologia: `papillary_thyroid_carcinoma`
- Diferenciação: `differentiated`
- Estágio TNM: `pT3b pN1b M1`
- Risco de recorrência: `high`
- Doença metastática: `sim`; sítios: lungs
- Radioiodo-avididade: `absent_in_pulmonary_lesions`
- Estado de progressão: `radiological_progression`
- Perfil molecular: BRAF_V600E=positive
- Idade: `62`; ECOG/estado funcional: `ECOG 1`

## Fatos Ativos e Proveniência
- Câncer de tireoide documentado: papillary_thyroid_carcinoma. Fontes: cancer.histology. Evidência: [cancer.histology] papillary_thyroid_carcinoma
- Estadiamento TNM documentado: pT3b pN1b M1. Fontes: cancer.tnm_stage. Evidência: [cancer.tnm_stage] pT3b pN1b M1
- Risco de recorrência: high. Fontes: cancer.recurrence_risk. Evidência: [cancer.recurrence_risk] high
- Iodo-avididade: absent_in_pulmonary_lesions. Fontes: cancer.iodine_avidity. Evidência: [cancer.iodine_avidity] absent_in_pulmonary_lesions
- Perfil molecular BRAF_V600E: positive. Fontes: cancer.molecular_profile:BRAF_V600E. Evidência: [cancer.molecular_profile:BRAF_V600E] BRAF_V600E=positive
- Estado de progressão: radiological_progression. Fontes: cancer. Evidência: [cancer] radiological_progression
- Doença metastática em: lungs. Fontes: cancer. Evidência: [cancer] metastatic disease
- Comorbidade ativa: hipertensão arterial. Fontes: comorbidity:hipertensão arterial. Evidência: [medical_record] hipertensão arterial
- Comorbidades ativas documentadas: hipertensão arterial. Fontes: comorbidity:hipertensão arterial. Evidência: [medical_record] hipertensão arterial
- Anormalidade laboratorial documentada em TSH: 1 resultado(s); mais recente 0.12 mUI/L em 2026-02-25 (low).. Fontes: lab:TSH:2026-02-25. Evidência: [lab:2026-02-25] TSH=0.12 mUI/L
- Sinal vital documentado: pressão arterial sistólica=128.0 mmHg em 2026-03-01. Fontes: vital:pressão arterial sistólica:2026-03-01. Evidência: [vital:2026-03-01] pressão arterial sistólica=128.0 mmHg
- Medicação active: levotiroxina. Fontes: medication:levotiroxina. Evidência: [medical_record] levotiroxina
- Medicação active: losartana. Fontes: medication:losartana. Evidência: [medical_record] losartana

## Grafo de Conhecimento do Prontuário
- Raiz: `diagnosis:thyroid_cancer`; nós: `21`; relações: `25`.
- `diagnosis:thyroid_cancer` (diagnosis): Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma. Fontes: cancer.histology
- `cancer:differentiation` (cancer_feature): differentiation: differentiated. Fontes: cancer.differentiation
- `cancer:tnm_stage` (cancer_feature): tnm_stage: pT3b pN1b M1. Fontes: cancer.tnm_stage
- `cancer:recurrence_risk` (cancer_feature): recurrence_risk: high. Fontes: cancer.recurrence_risk
- `cancer:metastatic` (cancer_feature): metastatic: True. Fontes: cancer.metastatic
- `cancer:metastatic_sites` (cancer_feature): metastatic_sites: lungs. Fontes: cancer.metastatic_sites
- `cancer:iodine_avidity` (cancer_feature): iodine_avidity: absent_in_pulmonary_lesions. Fontes: cancer.iodine_avidity
- `cancer:progression_status` (cancer_feature): progression_status: radiological_progression. Fontes: cancer.progression_status
- `cancer:molecular_profile` (cancer_feature): molecular_profile: BRAF_V600E=positive. Fontes: cancer.molecular_profile
- `comorbidity:hipertensão arterial` (clinical_fact): Comorbidade active: hipertensão arterial. Fontes: comorbidity:hipertensão arterial
- `lab:creatinina:2026-02-25` (laboratory): creatinina=0.9 mg/dL (normal). Fontes: lab:creatinina:2026-02-25
- `lab:TSH:2026-02-25` (laboratory): TSH=0.12 mUI/L (low). Fontes: lab:TSH:2026-02-25
- `vital:pressão arterial sistólica:2026-03-01` (vital_sign): pressão arterial sistólica=128.0 mmHg. Fontes: vital:pressão arterial sistólica:2026-03-01
- `medication:levotiroxina:unknown` (medication): Medicação active: levotiroxina. Fontes: medication:levotiroxina
- `medication:losartana:unknown` (medication): Medicação active: losartana. Fontes: medication:losartana
- `prior_treatment:PT-001` (prior_treatment): Tratamento prévio tireoidectomia total: stable. Fontes: PT-001
- `prior_treatment:PT-002` (prior_treatment): Tratamento prévio terapia com radioiodo: progression. Fontes: PT-002
- `imaging:CT-2025` (imaging): maior nódulo pulmonar com 9 mm. Fontes: imaging:CT-2025
- `imaging:CT-2026` (imaging): progressão radiológica. Fontes: imaging:CT-2026
- `note:0` (clinical_note): Doença pulmonar progressiva após radioiodo; revisar opções sistêmicas e risco cardiovascular.. Fontes: note:0
- `preference:0` (preference): Preferência registrada por discutir preservação de qualidade de vida.. Fontes: preference:0

## Histórico Terapêutico
- tireoidectomia total: resposta `stable`; período `2023-02-01 → 2023-02-01`; toxicidades: não registradas
- terapia com radioiodo: resposta `progression`; período `2023-05-01 → 2023-05-10`; toxicidades: não registradas

## Lacunas e Alertas do Prontuário
- Nenhuma lacuna estrutural identificada pelo validador.

## Estratégias Geradas e Elegibilidade
### Vigilância ativa
- Status inicial: `não aplicável`
- Classe: `monitoramento`; objetivo: `monitoramento estruturado de doença selecionada`
- Motivos: Critérios clínicos não atendidos: t1a, cN0, cM0
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_MS_PCDT_CDT_2026:2026:p38:BR_MS_PCDT_CDT_2026:p38:c2, BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c2

### Lobectomia
- Status inicial: `não aplicável`
- Classe: `surgery`; objetivo: `controle locorregional inicial`
- Motivos: Cirurgia tireoidiana definitiva já documentada no histórico terapêutico.
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_MS_PCDT_CDT_2026:2026:p38:BR_MS_PCDT_CDT_2026:p38:c2, BR_MS_PCDT_CDT_2026:2026:p41:BR_MS_PCDT_CDT_2026:p41:c1

### Tireoidectomia total
- Status inicial: `não aplicável`
- Classe: `surgery`; objetivo: `controle locorregional e preparo para seguimento/RAI quando indicado`
- Motivos: Cirurgia tireoidiana definitiva já documentada no histórico terapêutico.
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_MS_PCDT_CDT_2026:2026:p38:BR_MS_PCDT_CDT_2026:p38:c2, BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c3

### Radioiodoterapia
- Status inicial: `não aplicável`
- Classe: `radioiodine`; objetivo: `ablação, terapia adjuvante ou tratamento de doença iodo-ávida`
- Motivos: Doença refratária ao radioiodo documentada; nova radioiodoterapia dirigida ao tumor não é aplicável no catálogo.
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_MS_PCDT_CDT_2026:2026:p38:BR_MS_PCDT_CDT_2026:p38:c2, BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c3

### Radioterapia externa selecionada
- Status inicial: `candidato`
- Classe: `radiotherapy`; objetivo: `controle locorregional em circunstâncias selecionadas`
- Motivos: Critérios do catálogo presentes no prontuário.
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_MS_PCDT_CDT_2026:2026:p34:BR_MS_PCDT_CDT_2026:p34:c3, BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c1

### Inibidor multiquinase para doença refratária ao radioiodo
- Status inicial: `informação insuficiente`
- Classe: `systemic_therapy`; objetivo: `controle de doença progressiva refratária ao radioiodo`
- Motivos: Dados necessários para elegibilidade: radioiodine_refractory
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: radioiodine_refractory
- Fontes externas recuperadas: BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c3, BR_SBOC_CDT_ANAP_2026:2026:p13:BR_SBOC_CDT_ANAP_2026:p13:c2

### Terapia-alvo para doença anaplásica com alteração acionável
- Status inicial: `não aplicável`
- Classe: `targeted_therapy`; objetivo: `controle sistêmico conforme perfil molecular`
- Motivos: Histologia incompatível com a estratégia do catálogo.
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_SBOC_CDT_ANAP_2026:2026:p13:BR_SBOC_CDT_ANAP_2026:p13:c1, BR_SBOC_CDT_ANAP_2026:2026:p14:BR_SBOC_CDT_ANAP_2026:p14:c1

### Quimiorradioterapia para doença anaplásica selecionada
- Status inicial: `não aplicável`
- Classe: `chemoradiotherapy`; objetivo: `controle locorregional e sistêmico em doença anaplásica selecionada`
- Motivos: Histologia incompatível com a estratégia do catálogo.
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_SBOC_CDT_ANAP_2026:2026:p13:BR_SBOC_CDT_ANAP_2026:p13:c1, BR_SBOC_CDT_ANAP_2026:2026:p14:BR_SBOC_CDT_ANAP_2026:p14:c1

### Cuidados de suporte e controle de sintomas
- Status inicial: `candidato`
- Classe: `supportive_care`; objetivo: `alívio de sintomas e preservação de qualidade de vida`
- Motivos: Critérios do catálogo presentes no prontuário.
- Evidência do paciente: [cancer.histology] papillary_thyroid_carcinoma
- Contraindicações detectadas: nenhuma registrada
- Critérios ausentes: nenhum
- Fontes externas recuperadas: BR_MS_PCDT_CDT_2026:2026:p34:BR_MS_PCDT_CDT_2026:p34:c3, BR_MS_PCDT_CDT_2026:2026:p38:BR_MS_PCDT_CDT_2026:p38:c1

## Análise Contrafactual por Tratamento Candidato

### Radioterapia externa selecionada
- Status após análise: `permanece plausível`
- Contexto terapêutico: modalidade `external_beam_radiotherapy`; intenção `controle locorregional em circunstâncias selecionadas`; completude `unknown`
- Alvos/campo tratados: desconhecidos
- Lesões conhecidas não tratadas diretamente: metastatic_site:lungs
- Lacunas do contexto: intent, target_sites, radiation_field_sites, treated_lesion_ids
- Elegibilidade: `eligible`; motivos: Critérios do catálogo presentes no prontuário.
- Critérios pendentes: 
- Diretrizes de elegibilidade: [BR_MS_PCDT_CDT_2026:2026:p34:BR_MS_PCDT_CDT_2026:p34:c3] https://www.gov.br/inca/pt- br/assuntos/cancer/tipos/tireoide#:~:text=Os%20carcinomas%20diferenciados%20s%C3%A3o%20os,tamb%C3%A9 m%20cerca%20de%2010%25). 2022. Câncer de tireoide. 13. Rosário PW, Ward LS, Carvalho GA, Graf H, Maciel RMB, Maciel LMZ, et al. Thyroid nodules and differentiated thyroid cancer: update on the Brazilian consensus. Arquivos Brasileiros de Endocrinologia & Metabologia. 2013 Jun;57(4):240–64. doi:10.1590/S0004-27302013000400002 14. Luster M, Aktolun C, Amendoeira I, Barczyński M, Bible KC, Duntas LH, et al. European Perspective on 2015 American Thyroid Association Management Guidelines for Adult Patients with Thyroid Nodules and Differentiated Thyroid Cancer: Proceedings of an Interactive International Symposium. Thyroid. 2019 Jan;29(1) :7–26. doi:10.1089/thy.2017.0129 15. Schmidbauer B, Menhart K, Hellwig D, Grosse J. Differentiated thyroid cancer —treatment: state of the art. Int J Mol Sci. 2017;18(6):1292. 16. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta -analysis. Head and Neck. 2020. doi:10.1002/hed.26133; [BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c1] 122. Perros P, Boelaert K, Colley S, Evans C, Evans RM, Gerrard BA G, et al. Guidelines for the management of thyroid cancer. Clin Endocrinol (Oxf). 2014 Jul 3;81(s1):1 –122. doi:10.1111/cen.12515 123. Megwalu UC, Orloff LA, Ma Y. Adjuvant external beam radiotherapy for locally invasive papillary thyroid cancer. Head Neck. 2019 Jun 8;41(6):1719–24. doi:10.1002/hed.25639 124. Mangoni M, Gobitti C, Autorino R, Cerizza L, Furlan C, Mazzarotto R, et al. External Beam Radiotherapy in Thyroid Carcinoma: Clinical Review and Recommendations of the AIRO “Radioterapia Metabolica” Group. Tumori Journal. 2017 Mar 9;103(2):114–23. doi:10.5301/tj.5000532 125. Fussey JM, Crunkhorn R, Tedla M, We ickert MO, Mehanna H. External beam radiotherapy in differentiated thyroid carcinoma: A systematic review. Head Neck. 2016 Apr 3;38(S1). doi:10.1002/hed.24218 126. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta‐analysis. Head Neck. 2020 Aug 4;42(8):2181–93. doi:10.1002/hed.26133 127. Sit D, Koh WX, Shokoohi A, Raycraft T, Vu M, Hamm J, et al.; [BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c2] External Beam Radiation Therapy in pT4 Well-Differentiated Thyroid Cancer: A Population-Based Study of 405 Patients. International Journal of Radiation Oncology*Biology*Physics. 2021 Oct;111(2):468–78. doi:10.1016/j.ijrobp.2021.05.006 128. Makita K, Hamamoto Y, Tsuruoka S, Takata N, Urashima Y, Miyagawa M, et al. Treatment intensity and control rates in combining external -beam radiotherapy and radioactive iodine therapy for metastatic or recurrent differentiated thyroid cancer. Int J Clin Oncol. 2020 Apr 2;25(4):691–7. doi:10.1007/s10147-019-01591-y 129. Weitzman SP, Sherman SI. Novel Drug Treatments of Progressive Radioiodine -Refractory Differentiated Thyroid Cancer. Endocrinol Metab Clin North Am. 2019 Mar;48(1):253 –68. doi:10.1016/j.ecl.2018.10.009 130. Durante C, Haddy N, Baudi n E, Leboulleux S, Hartl D, Travagli JP, et al. Long -Term Outcome of 444 Patients with Distant Metastases from Papillary and Follicular Thyroid Carcinoma: Benefits and Limits of Radioiodine Therapy. J Clin Endocrinol Metab. 2006 Aug 1;91(8):2892 –9. doi:10.1210/jc.2005-2838 131. Enokida T, Tahara M. Management of VEGFR -Targeted TKI for thyroid Cancer. Cancers (Basel). 2021;13(21):5536. 132. Brasil.
- Raiz da árvore de desfechos: Folhas derivadas após diagnóstico, condições contrafactuais e manifestações clínicas.
- Diretrizes da árvore de desfechos: não registrada
- Profundidade máxima da árvore de falhas: `3`
#### Cenários de Desfecho
- `recurrence_progression`: Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo.. Mecanismo: não especificado; modificadores: não especificados
- `toxicity`: Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia.. Mecanismo: não especificado; modificadores: não especificados
#### Árvore Causal Gerada
- Profundidade `0` / `diagnosis`: Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma. Estado: `documented`; pai: `nenhum`; fatos: cancer_documented.
- Profundidade `1` / `counterfactual_condition`: O paciente inicia o tratamento com radioterapia externa (DTC_EBRT) para controle locorregional.. Estado: `sustentado`; pai: `DTC_EBRT:diagnosis`; fatos: cancer_documented, prior_treatment:PT-002.
- Profundidade `1` / `counterfactual_condition`: O paciente apresenta resposta radiológica parcial ou estável à radioterapia externa.. Estado: `sustentado`; pai: `DTC_EBRT:diagnosis`; fatos: cancer_progression, metastatic_disease.
- Profundidade `2` / `manifestation`: Dor ou desconforto na região cervical devido ao aumento de volume tumoral local.. Estado: `sustentado`; pai: `DTC_EBRT:condition:1`; fatos: cancer_documented, metastatic_disease.
- Profundidade `2` / `manifestation`: Disfagia (dificuldade para deglutição) decorrente da compressão esofagiana pela massa tumoral.. Estado: `sustentado`; pai: `DTC_EBRT:condition:2`; fatos: cancer_documented, metastatic_disease.
- Profundidade `3` / `outcome`: Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo.. Estado: `sustentado`; pai: `DTC_EBRT:manifestation:1`; fatos: cancer_documented, metastatic_disease, cancer_iodine_avidity, prior_treatment:PT-002.
- Profundidade `3` / `outcome`: Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia.. Estado: `sustentado`; pai: `DTC_EBRT:manifestation:2`; fatos: cancer_documented, metastatic_disease.
#### Desfecho contrafactual: Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo.
- Hipótese: Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo.
- Estado: `sustentado`; decisão crítica: `keep`
- Mecanismo: Cadeia causal derivada
- Cadeia causal: Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma → O paciente inicia o tratamento com radioterapia externa (DTC_EBRT) para controle locorregional. → Dor ou desconforto na região cervical devido ao aumento de volume tumoral local. → Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo.
- Condição necessária: `não especificada`
- Evidência do prontuário: [cancer.histology] papillary_thyroid_carcinoma; [cancer] metastatic disease; [cancer.iodine_avidity] absent_in_pulmonary_lesions; [PT-002] progression
- Evidência externa: [BR_MS_PCDT_CDT_2026:2026:p34:BR_MS_PCDT_CDT_2026:p34:c3] https://www.gov.br/inca/pt- br/assuntos/cancer/tipos/tireoide#:~:text=Os%20carcinomas%20diferenciados%20s%C3%A3o%20os,tamb%C3%A9 m%20cerca%20de%2010%25). 2022. Câncer de tireoide. 13. Rosário PW, Ward LS, Carvalho GA, Graf H, Maciel RMB, Maciel LMZ, et al. Thyroid nodules and differentiated thyroid cancer: update on the Brazilian consensus. Arquivos Brasileiros de Endocrinologia & Metabologia. 2013 Jun;57(4):240–64. doi:10.1590/S0004-27302013000400002 14. Luster M, Aktolun C, Amendoeira I, Barczyński M, Bible KC, Duntas LH, et al. European Perspective on 2015 American Thyroid Association Management Guidelines for Adult Patients with Thyroid Nodules and Differentiated Thyroid Cancer: Proceedings of an Interactive International Symposium. Thyroid. 2019 Jan;29(1) :7–26. doi:10.1089/thy.2017.0129 15. Schmidbauer B, Menhart K, Hellwig D, Grosse J. Differentiated thyroid cancer —treatment: state of the art. Int J Mol Sci. 2017;18(6):1292. 16. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta -analysis. Head and Neck. 2020. doi:10.1002/hed.26133; [BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c1] 122. Perros P, Boelaert K, Colley S, Evans C, Evans RM, Gerrard BA G, et al. Guidelines for the management of thyroid cancer. Clin Endocrinol (Oxf). 2014 Jul 3;81(s1):1 –122. doi:10.1111/cen.12515 123. Megwalu UC, Orloff LA, Ma Y. Adjuvant external beam radiotherapy for locally invasive papillary thyroid cancer. Head Neck. 2019 Jun 8;41(6):1719–24. doi:10.1002/hed.25639 124. Mangoni M, Gobitti C, Autorino R, Cerizza L, Furlan C, Mazzarotto R, et al. External Beam Radiotherapy in Thyroid Carcinoma: Clinical Review and Recommendations of the AIRO “Radioterapia Metabolica” Group. Tumori Journal. 2017 Mar 9;103(2):114–23. doi:10.5301/tj.5000532 125. Fussey JM, Crunkhorn R, Tedla M, We ickert MO, Mehanna H. External beam radiotherapy in differentiated thyroid carcinoma: A systematic review. Head Neck. 2016 Apr 3;38(S1). doi:10.1002/hed.24218 126. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta‐analysis. Head Neck. 2020 Aug 4;42(8):2181–93. doi:10.1002/hed.26133 127. Sit D, Koh WX, Shokoohi A, Raycraft T, Vu M, Hamm J, et al.; [BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c2] External Beam Radiation Therapy in pT4 Well-Differentiated Thyroid Cancer: A Population-Based Study of 405 Patients. International Journal of Radiation Oncology*Biology*Physics. 2021 Oct;111(2):468–78. doi:10.1016/j.ijrobp.2021.05.006 128. Makita K, Hamamoto Y, Tsuruoka S, Takata N, Urashima Y, Miyagawa M, et al. Treatment intensity and control rates in combining external -beam radiotherapy and radioactive iodine therapy for metastatic or recurrent differentiated thyroid cancer. Int J Clin Oncol. 2020 Apr 2;25(4):691–7. doi:10.1007/s10147-019-01591-y 129. Weitzman SP, Sherman SI. Novel Drug Treatments of Progressive Radioiodine -Refractory Differentiated Thyroid Cancer. Endocrinol Metab Clin North Am. 2019 Mar;48(1):253 –68. doi:10.1016/j.ecl.2018.10.009 130. Durante C, Haddy N, Baudi n E, Leboulleux S, Hartl D, Travagli JP, et al. Long -Term Outcome of 444 Patients with Distant Metastases from Papillary and Follicular Thyroid Carcinoma: Benefits and Limits of Radioiodine Therapy. J Clin Endocrinol Metab. 2006 Aug 1;91(8):2892 –9. doi:10.1210/jc.2005-2838 131. Enokida T, Tahara M. Management of VEGFR -Targeted TKI for thyroid Cancer. Cancers (Basel). 2021;13(21):5536. 132. Brasil.
- Evidência contraditória: não registrada
- Plausibilidade clínica/temporal/especificidade: `0.85` / `1.00` / `0.85`
#### Desfecho contrafactual: Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia.
- Hipótese: Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia.
- Estado: `sustentado`; decisão crítica: `keep`
- Mecanismo: Cadeia causal derivada
- Cadeia causal: Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma → O paciente apresenta resposta radiológica parcial ou estável à radioterapia externa. → Disfagia (dificuldade para deglutição) decorrente da compressão esofagiana pela massa tumoral. → Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia.
- Condição necessária: `não especificada`
- Evidência do prontuário: [cancer.histology] papillary_thyroid_carcinoma; [cancer] metastatic disease
- Evidência externa: [BR_MS_PCDT_CDT_2026:2026:p34:BR_MS_PCDT_CDT_2026:p34:c3] https://www.gov.br/inca/pt- br/assuntos/cancer/tipos/tireoide#:~:text=Os%20carcinomas%20diferenciados%20s%C3%A3o%20os,tamb%C3%A9 m%20cerca%20de%2010%25). 2022. Câncer de tireoide. 13. Rosário PW, Ward LS, Carvalho GA, Graf H, Maciel RMB, Maciel LMZ, et al. Thyroid nodules and differentiated thyroid cancer: update on the Brazilian consensus. Arquivos Brasileiros de Endocrinologia & Metabologia. 2013 Jun;57(4):240–64. doi:10.1590/S0004-27302013000400002 14. Luster M, Aktolun C, Amendoeira I, Barczyński M, Bible KC, Duntas LH, et al. European Perspective on 2015 American Thyroid Association Management Guidelines for Adult Patients with Thyroid Nodules and Differentiated Thyroid Cancer: Proceedings of an Interactive International Symposium. Thyroid. 2019 Jan;29(1) :7–26. doi:10.1089/thy.2017.0129 15. Schmidbauer B, Menhart K, Hellwig D, Grosse J. Differentiated thyroid cancer —treatment: state of the art. Int J Mol Sci. 2017;18(6):1292. 16. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta -analysis. Head and Neck. 2020. doi:10.1002/hed.26133; [BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c1] 122. Perros P, Boelaert K, Colley S, Evans C, Evans RM, Gerrard BA G, et al. Guidelines for the management of thyroid cancer. Clin Endocrinol (Oxf). 2014 Jul 3;81(s1):1 –122. doi:10.1111/cen.12515 123. Megwalu UC, Orloff LA, Ma Y. Adjuvant external beam radiotherapy for locally invasive papillary thyroid cancer. Head Neck. 2019 Jun 8;41(6):1719–24. doi:10.1002/hed.25639 124. Mangoni M, Gobitti C, Autorino R, Cerizza L, Furlan C, Mazzarotto R, et al. External Beam Radiotherapy in Thyroid Carcinoma: Clinical Review and Recommendations of the AIRO “Radioterapia Metabolica” Group. Tumori Journal. 2017 Mar 9;103(2):114–23. doi:10.5301/tj.5000532 125. Fussey JM, Crunkhorn R, Tedla M, We ickert MO, Mehanna H. External beam radiotherapy in differentiated thyroid carcinoma: A systematic review. Head Neck. 2016 Apr 3;38(S1). doi:10.1002/hed.24218 126. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta‐analysis. Head Neck. 2020 Aug 4;42(8):2181–93. doi:10.1002/hed.26133 127. Sit D, Koh WX, Shokoohi A, Raycraft T, Vu M, Hamm J, et al.; [BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c2] External Beam Radiation Therapy in pT4 Well-Differentiated Thyroid Cancer: A Population-Based Study of 405 Patients. International Journal of Radiation Oncology*Biology*Physics. 2021 Oct;111(2):468–78. doi:10.1016/j.ijrobp.2021.05.006 128. Makita K, Hamamoto Y, Tsuruoka S, Takata N, Urashima Y, Miyagawa M, et al. Treatment intensity and control rates in combining external -beam radiotherapy and radioactive iodine therapy for metastatic or recurrent differentiated thyroid cancer. Int J Clin Oncol. 2020 Apr 2;25(4):691–7. doi:10.1007/s10147-019-01591-y 129. Weitzman SP, Sherman SI. Novel Drug Treatments of Progressive Radioiodine -Refractory Differentiated Thyroid Cancer. Endocrinol Metab Clin North Am. 2019 Mar;48(1):253 –68. doi:10.1016/j.ecl.2018.10.009 130. Durante C, Haddy N, Baudi n E, Leboulleux S, Hartl D, Travagli JP, et al. Long -Term Outcome of 444 Patients with Distant Metastases from Papillary and Follicular Thyroid Carcinoma: Benefits and Limits of Radioiodine Therapy. J Clin Endocrinol Metab. 2006 Aug 1;91(8):2892 –9. doi:10.1210/jc.2005-2838 131. Enokida T, Tahara M. Management of VEGFR -Targeted TKI for thyroid Cancer. Cancers (Basel). 2021;13(21):5536. 132. Brasil.
- Evidência contraditória: não registrada
- Plausibilidade clínica/temporal/especificidade: `0.85` / `1.00` / `0.85`
#### Síntese das Cadeias Causais Sustentadas
- Desfecho: Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo.
  - Se Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma, então O paciente inicia o tratamento com radioterapia externa (DTC_EBRT) para controle locorregional.; Se O paciente inicia o tratamento com radioterapia externa (DTC_EBRT) para controle locorregional., então Dor ou desconforto na região cervical devido ao aumento de volume tumoral local.; Se Dor ou desconforto na região cervical devido ao aumento de volume tumoral local., então Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo..
- Desfecho: Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia.
  - Se Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma, então O paciente apresenta resposta radiológica parcial ou estável à radioterapia externa.; Se O paciente apresenta resposta radiológica parcial ou estável à radioterapia externa., então Disfagia (dificuldade para deglutição) decorrente da compressão esofagiana pela massa tumoral.; Se Disfagia (dificuldade para deglutição) decorrente da compressão esofagiana pela massa tumoral., então Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia..
#### Impactos mesmo com controle oncológico
- Risco aumentado de disfagia e dermatite cervical devido à irradiação direta da região, exacerbado pela presença de lesões metastáticas pulmonares que podem limitar a dose terapêutica local. Domínio: `qualidade de vida`; tempo: `permanente`; reversibilidade: `irreversível`; gravidade: `moderado`; específico ao paciente: `sim`; evidência: [cancer.histology] papillary_thyroid_carcinoma; [cancer] metastatic disease; [PT-002] progression
- Possibilidade de fibrose cervical tardia resultante da radioterapia externa, potencialmente comprometendo a função respiratória ou deglutição a longo prazo. Domínio: `funcional`; tempo: `longo prazo`; reversibilidade: `irreversível`; gravidade: `moderado`; específico ao paciente: `não`; evidência: não registrada
- Necessidade de monitoramento rigoroso de toxicidade cervical devido ao histórico de progressão após radioiodo e presença de comorbidade hipertensiva que pode influenciar a resposta vascular local. Domínio: `monitoramento`; tempo: `permanente`; reversibilidade: `desconhecido`; gravidade: `moderado`; específico ao paciente: `sim`; evidência: [cancer] radiological_progression; [medical_record] hipertensão arterial
#### Prognóstico Qualitativo
- Horizonte: `12 months`
- Controle da doença: `desconhecido`
- Risco de desfecho adverso: `desconhecido`
- Confiança no raciocínio: `moderado`
- Fundamentação: Possibilidade de controle locorregional da doença com radioterapia externa, mas persistência ou progressão das metástases pulmonares devido à ausência de avididade ao iodo.; Possibilidade de desenvolvimento de disfagia e outras toxicidades agudas na região cervical devido à compressão esofagiana pela massa tumoral ou efeitos diretos da radioterapia.
- Informações adicionais úteis: intent, target_sites, radiation_field_sites, treated_lesion_ids
- Incertezas: nenhuma adicional

### Inibidor multiquinase para doença refratária ao radioiodo
- Status após análise: `informação insuficiente`
- Contexto terapêutico: modalidade `systemic_therapy`; intenção `controle de doença progressiva refratária ao radioiodo`; completude `complete`
- Alvos/campo tratados: desconhecidos
- Lesões conhecidas não tratadas diretamente: metastatic_site:lungs
- Lacunas do contexto: nenhuma
- Elegibilidade: `indeterminate`; motivos: Dados necessários para elegibilidade: radioiodine_refractory
- Critérios pendentes: radioiodine_refractory
- Diretrizes de elegibilidade: [BR_MS_PCDT_CDT_2026:2026:p42:BR_MS_PCDT_CDT_2026:p42:c3] Ministério da Saúde. Relatório de Recomendação n° 917 - Sorafenibe e lenvatinibe para o tratamento de indivíduos com diagnóstico de carcinoma diferenciado da tireoide localmente avançado e/ou metastático, refratário ao iodo, progressivo [Internet]. 2024 [cited 2024 Nov 13]. Available from: https://www.gov.br/conitec/pt - br/midias/relatorios/2024/relatorio-de-recomendacao-no-917-sorafenibe-e-lenvatinibe 133. Fatourechi V, Hay ID, Mullan BP, Wiseman GA, Eghbali -Fatourechi GZ, Thorson LM, et al. Are Posttherapy Radioiodine Scans Informative and Do They Influence Subsequent Therapy of Patients with Differentiated Thyroid Cancer? Thyroid. 2000 Jul;10(7):573–7. doi:10.1089/thy.2000.10.573 134. Ministério da Saúde Secretaria de Atenção à Saúde. Diário Oficia l da União [Internet]. 2014. p. 35. Protocolo Clínico e Diretrizes Terapêuticas do Carcinoma Diferenciado da Tireoide. Available from: http://conitec.gov.br/images/Protocolos/PCDT_CarcinomaTireoide.pdf 135. Vaisman F, Momesso D, Bulzico DA, Pessoa CHCN, Dias F, Corbo R, et al. Spontaneous remission in thyroid cancer patients after biochemical incomplete response to initial therapy. Clin Endocrinol (Oxf). 2012 Jul;77(1):132–8.; [BR_SBOC_CDT_ANAP_2026:2026:p13:BR_SBOC_CDT_ANAP_2026:p13:c2] Schlumberger M, Tahara M, Wirth LJ, Robinson B, Brose MS, Elisei R, et al. Lenvatinib versus placebo in radioiodine-refractory thyroid cancer. N Engl J Med. 12 de fevereiro de 2015;372(7):621–30. 6. Brose MS, Robinson B, Sherman SI, Krajewska J, Lin CC, Vaisman F, et al. Cabozantinib for radioiodine-refractory differentiated thyroid cancer (COSMIC- 311): a randomised, double-blind, placebo-controlled, phase 3 trial. Lancet Oncol. agosto de 2021;22(8):1126–38. 7. Brose MS, Nutting CM, Jarzab B, Elisei R, Siena S, Bastholt L, et al. Sorafenib in radioactive iodine-refractory, locally advanced or metastatic differentiated thyroid cancer: a randomised, double-blind, phase 3 trial. Lancet. 26 de julho de 2014;384(9940):319–28. 8. Shah MH, Wei L, Wirth LJ, Daniels GA, De Souza JA, Timmers CD, et al. Results of randomized phase II trial of dabrafenib versus dabrafenib plus trame- tinib in BRAF-mutated papillary thyroid carcinoma. J Clin Oncol. 20 de maio de 2017;35(15_suppl):6022–6022. 9. Brose MS, Cabanillas ME, Cohen EEW, Wirth LJ, Riehl T, Yue H, et al.; [BR_MS_PCDT_CDT_2026:2026:p34:BR_MS_PCDT_CDT_2026:p34:c3] https://www.gov.br/inca/pt- br/assuntos/cancer/tipos/tireoide#:~:text=Os%20carcinomas%20diferenciados%20s%C3%A3o%20os,tamb%C3%A9 m%20cerca%20de%2010%25). 2022. Câncer de tireoide. 13. Rosário PW, Ward LS, Carvalho GA, Graf H, Maciel RMB, Maciel LMZ, et al. Thyroid nodules and differentiated thyroid cancer: update on the Brazilian consensus. Arquivos Brasileiros de Endocrinologia & Metabologia. 2013 Jun;57(4):240–64. doi:10.1590/S0004-27302013000400002 14. Luster M, Aktolun C, Amendoeira I, Barczyński M, Bible KC, Duntas LH, et al. European Perspective on 2015 American Thyroid Association Management Guidelines for Adult Patients with Thyroid Nodules and Differentiated Thyroid Cancer: Proceedings of an Interactive International Symposium. Thyroid. 2019 Jan;29(1) :7–26. doi:10.1089/thy.2017.0129 15. Schmidbauer B, Menhart K, Hellwig D, Grosse J. Differentiated thyroid cancer —treatment: state of the art. Int J Mol Sci. 2017;18(6):1292. 16. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta -analysis. Head and Neck. 2020. doi:10.1002/hed.26133
- Raiz da árvore de desfechos: Folhas derivadas após diagnóstico, condições contrafactuais e manifestações clínicas.
- Diretrizes da árvore de desfechos: não registrada
- Profundidade máxima da árvore de falhas: `3`
#### Cenários de Desfecho
- Nenhum cenário registrado.
#### Árvore Causal Gerada
- Profundidade `0` / `diagnosis`: Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma. Estado: `documented`; pai: `nenhum`; fatos: cancer_documented.
- Profundidade `1` / `counterfactual_condition`: Início da terapia sistêmica com inibidor multiquinase (ex: lenvatinibe ou sorafenibe) para controle de doença progressiva refratária ao radioiodo.. Estado: `sustentado`; pai: `DTC_RAIRD_MKI:diagnosis`; fatos: cancer_documented, metastatic_disease, cancer_iodine_avidity, prior_treatment:PT-002.
- Profundidade `1` / `counterfactual_condition`: Otimização da terapia hormonal substitutiva com ajuste de dose de levotiroxina visando supressão eutróide de TSH.. Estado: `sustentado`; pai: `DTC_RAIRD_MKI:diagnosis`; fatos: medication:levotiroxina:unknown, abnormal_lab_summary:tsh, cancer_documented.
- Profundidade `2` / `manifestation`: Dor torácica ou dispneia devido ao crescimento de lesões metastáticas pulmonares.. Estado: `sustentado`; pai: `DTC_RAIRD_MKI:condition:1`; fatos: metastatic_disease, cancer_progression.
- Profundidade `2` / `manifestation`: Sensação de aperto ou desconforto no pescoço devido ao aumento do volume da tireoidectomizada ou linfonodos metastáticos.. Estado: `sustentado`; pai: `DTC_RAIRD_MKI:condition:2`; fatos: metastatic_disease, cancer_tnm_stage.
- Profundidade `3` / `outcome`: Possibilidade de resposta terapêutica com inibidor multiquinase, resultando em estabilização da doença metastática pulmonar e controle dos sintomas.. Estado: `não resolvido`; pai: `DTC_RAIRD_MKI:manifestation:1`; fatos: metastatic_disease, cancer_progression, medication:levotiroxina.
- Profundidade `3` / `outcome`: Possibilidade de progressão da doença apesar do tratamento com inibidor multiquinase, levando a piora clínica e aumento das lesões metastáticas.. Estado: `não resolvido`; pai: `DTC_RAIRD_MKI:manifestation:2`; fatos: metastatic_disease, cancer_progression, medication:levotiroxina.
#### Síntese das Cadeias Causais Sustentadas
#### Impactos mesmo com controle oncológico
- Risco aumentado de hipertensão arterial devido ao uso de inibidores multiquinase, exacerbando a comorbidade ativa documentada no paciente. Domínio: `cardiovascular`; tempo: `permanente`; reversibilidade: `irreversível`; gravidade: `moderado`; específico ao paciente: `sim`; evidência: [medical_record] hipertensão arterial
- Possibilidade de fadiga e diarreia como eventos adversos comuns à classe terapêutica de inibidores multiquinase. Domínio: `qualidade de vida`; tempo: `permanente`; reversibilidade: `irreversível`; gravidade: `moderado`; específico ao paciente: `não`; evidência: não registrada
- Necessidade de monitoramento rigoroso da função renal devido ao perfil de toxicidade do tratamento sistêmico. Domínio: `renal`; tempo: `permanente`; reversibilidade: `irreversível`; gravidade: `moderado`; específico ao paciente: `não`; evidência: não registrada
#### Prognóstico Qualitativo
- Horizonte: `12 months`
- Controle da doença: `desconhecido`
- Risco de desfecho adverso: `desconhecido`
- Confiança no raciocínio: `baixo`
- Fundamentação: não disponível
- Informações adicionais úteis: nenhuma identificada
- Incertezas: Ausência de mecanismo suportado não demonstra eficácia.

### Cuidados de suporte e controle de sintomas
- Status após análise: `informação insuficiente`
- Contexto terapêutico: modalidade `supportive_care`; intenção `alívio de sintomas e preservação de qualidade de vida`; completude `complete`
- Alvos/campo tratados: desconhecidos
- Lesões conhecidas não tratadas diretamente: metastatic_site:lungs
- Lacunas do contexto: nenhuma
- Elegibilidade: `eligible`; motivos: Critérios do catálogo presentes no prontuário.
- Critérios pendentes: 
- Diretrizes de elegibilidade: [BR_MS_PCDT_CDT_2026:2026:p34:BR_MS_PCDT_CDT_2026:p34:c3] https://www.gov.br/inca/pt- br/assuntos/cancer/tipos/tireoide#:~:text=Os%20carcinomas%20diferenciados%20s%C3%A3o%20os,tamb%C3%A9 m%20cerca%20de%2010%25). 2022. Câncer de tireoide. 13. Rosário PW, Ward LS, Carvalho GA, Graf H, Maciel RMB, Maciel LMZ, et al. Thyroid nodules and differentiated thyroid cancer: update on the Brazilian consensus. Arquivos Brasileiros de Endocrinologia & Metabologia. 2013 Jun;57(4):240–64. doi:10.1590/S0004-27302013000400002 14. Luster M, Aktolun C, Amendoeira I, Barczyński M, Bible KC, Duntas LH, et al. European Perspective on 2015 American Thyroid Association Management Guidelines for Adult Patients with Thyroid Nodules and Differentiated Thyroid Cancer: Proceedings of an Interactive International Symposium. Thyroid. 2019 Jan;29(1) :7–26. doi:10.1089/thy.2017.0129 15. Schmidbauer B, Menhart K, Hellwig D, Grosse J. Differentiated thyroid cancer —treatment: state of the art. Int J Mol Sci. 2017;18(6):1292. 16. Jacomina LE, Jacinto JKM, Co LBA, Yu KKL, Agas RAF, Co JL, et al. The Role of postoperative external beam radiotherapy for differentiated thyroid carcinoma: A Systematic review and meta -analysis. Head and Neck. 2020. doi:10.1002/hed.26133; [BR_MS_PCDT_CDT_2026:2026:p38:BR_MS_PCDT_CDT_2026:p38:c1] 64. Brasil. Ministério da Saúde. Instituto Nacional de Câncer - INCA. Ministério da Saúde. [Internet]. 2022 [cited 2023 Oct 12]. C âncer de tireoide. . Available from: https://www.gov.br/inca/pt - br/assuntos/cancer/tipos/tireoide 65. Brierley JD, Gospodarowicz MK, Wittekind C. TNM classification of malignant tumours. John Wiley & Sons; 2017. 66. Shaha AR. Extrathyroidal extension —what does it mean. Oral Oncol. 2017 May;68:50 –2. doi:10.1016/j.oraloncology.2017.03.008 67. Harries V, McGill M, Yuan A, Wang LY, Tuttle RM, Shaha AR, et al. Does macroscopic extrathyroidal extension to the strap muscles alone affect survival in papillary thyro id carcinoma? Surgery. 2022 May;171(5):1341–7. doi:10.1016/j.surg.2021.08.041 68. Nava CF, Zanella AB, Scheffel RS, Maia AL, Dora JM. Impact of the updated TNM staging criteria on prediction of persistent disease in a differentiated thyroid carcinoma cohort. Arch Endocrinol Metab. 2019 Feb;63(1):5–11. doi:10.20945/2359-3997000000097 69. Filetti S, Durante C, Hartl DM, Leboulleux S, Locati LD, Newbold K, et al. ESMO Clinical Practice Guideline update on the use of systemic therapy in advanced thyroid ca ncer. Annals of Oncology.; [BR_MS_PCDT_CDT_2026:2026:p38:BR_MS_PCDT_CDT_2026:p38:c2] 2022 Jul;33(7):674 – 84. doi:10.1016/j.annonc.2022.04.009 70. Pacini F, Schlumberger M, Dralle H, Elisei R, Smit JWA, Wiersinga W, et al. European consensus for the management of patients with differentiated thyroid carcinoma of the follicular epithelium. Eur J Endocrinol. 2006;154(6). doi:10.1530/eje.1.02158 71. Sociedade Brasileira de Oncologia Clínica (SBOC). Diretrizes de tratamento oncológico - Tumores de cabeça e pescoço - Tireoide:Carcinoma diferenciada e anaplásico [Internet]. 2026 [cited 2026 Jul 6]. Available from: https://sboc.org.br/wp-content/uploads/2026/04/Diretrizes-SBOC-2026-Tireoide-carcinoma-diferenciado-e- anapl%E2%94%9Cisico-v6-VERS%E2%94%9CaO-FINAL.pdf 72. Tuttle RM, Tala H, Shah J, Leboeuf R, Ghossein R, Gonen M, et al. Estimating Risk of Recurrence in Differentiated Thyroid Cancer After Total Thyroidectomy and Radioactive Iodine Remnant Ablation: Using Response to Therapy Variables to Modify the Initial Risk Estimates Predicted by the New American Thyroid Association Staging System. Thyroid. 2010 Dec;20(12):1341–9. doi:10.1089/thy.2010.0178 73. Lee YA, Lee H, Im SW, Song YS, Oh DY, Kang HJ, et al.
- Raiz da árvore de desfechos: Folhas derivadas após diagnóstico, condições contrafactuais e manifestações clínicas.
- Diretrizes da árvore de desfechos: não registrada
- Profundidade máxima da árvore de falhas: `3`
#### Cenários de Desfecho
- Nenhum cenário registrado.
#### Árvore Causal Gerada
- Profundidade `0` / `diagnosis`: Diagnóstico confirmado de câncer de tireoide: papillary_thyroid_carcinoma. Estado: `documented`; pai: `nenhum`; fatos: cancer_documented.
- Profundidade `1` / `counterfactual_condition`: O paciente apresenta progressão radiológica da doença metastática pulmonar, apesar do tratamento prévio com radioiodo.. Estado: `sustentado`; pai: `SUPPORTIVE_CARE:diagnosis`; fatos: cancer_progression, metastatic_disease, prior_treatment:PT-002.
- Profundidade `1` / `counterfactual_condition`: O perfil molecular positivo para BRAF_V600E está associado a uma trajetória de progressão mais agressiva do carcinoma diferenciado.. Estado: `sustentado`; pai: `SUPPORTIVE_CARE:diagnosis`; fatos: molecular_profile:BRAF_V600E, cancer_recurrence_risk.
- Profundidade `2` / `manifestation`: Dispneia progressiva ao esforço devido à compressão mecânica das vias aéreas superiores por metástases pulmonares volumosas.. Estado: `sustentado`; pai: `SUPPORTIVE_CARE:condition:1`; fatos: metastatic_disease, cancer_progression.
- Profundidade `2` / `manifestation`: Dor torácica pleurítica ou dor no peito devido à invasão da pleura pelas lesões metastáticas pulmonares.. Estado: `sustentado`; pai: `SUPPORTIVE_CARE:condition:1`; fatos: metastatic_disease, cancer_progression.
- Profundidade `3` / `outcome`: Piora progressiva da dispneia e dor torácica devido ao aumento volumétrico das metástases pulmonares, levando à necessidade de intervenções paliativas avançadas ou cuidados de suporte final.. Estado: `não resolvido`; pai: `SUPPORTIVE_CARE:manifestation:1`; fatos: metastatic_disease, cancer_progression, manifestation:1, manifestation:2.
- Profundidade `3` / `outcome`: Manutenção do estado de doença metastática estável com controle sintomático limitado pela progressão radiológica e ausência de avididade ao iodo.. Estado: `não resolvido`; pai: `SUPPORTIVE_CARE:manifestation:1`; fatos: metastatic_disease, cancer_progression, manifestation:1.
- Profundidade `3` / `outcome`: Desenvolvimento de complicações respiratórias graves decorrentes da compressão das vias aéreas superiores por lesões metastáticas pulmonares volumosas.. Estado: `não resolvido`; pai: `SUPPORTIVE_CARE:manifestation:1`; fatos: metastatic_disease, manifestation:1.
#### Síntese das Cadeias Causais Sustentadas
#### Impactos mesmo com controle oncológico
- Risco de progressão da doença devido à ausência de avididade ao iodo nas lesões pulmonares e histórico de progressão após terapia com radioiodo. Domínio: `oncológico`; tempo: `longo prazo`; reversibilidade: `irreversível`; gravidade: `alto`; específico ao paciente: `sim`; evidência: [cancer.iodine_avidity] absent_in_pulmonary_lesions; [cancer] metastatic disease; [PT-002] progression
- Necessidade de monitoramento rigoroso para toxicidades sistêmicas associadas a terapias alvo (ex. vemurafenibe) devido ao perfil molecular positivo para BRAF_V600E. Domínio: `oncológico`; tempo: `longo prazo`; reversibilidade: `reversível`; gravidade: `moderado`; específico ao paciente: `sim`; evidência: [cancer.molecular_profile:BRAF_V600E] BRAF_V600E=positive
- Potencial impacto na qualidade de vida devido à progressão radiológica e metástases pulmonares, exigindo suporte sintomático ativo. Domínio: `qualidade de vida`; tempo: `curto prazo`; reversibilidade: `reversível`; gravidade: `moderado`; específico ao paciente: `sim`; evidência: [cancer] radiological_progression; [cancer] metastatic disease
#### Prognóstico Qualitativo
- Horizonte: `12 months`
- Controle da doença: `desconhecido`
- Risco de desfecho adverso: `desconhecido`
- Confiança no raciocínio: `baixo`
- Fundamentação: não disponível
- Informações adicionais úteis: nenhuma identificada
- Incertezas: Ausência de mecanismo suportado não demonstra eficácia.

## Limitações Metodológicas
- A ausência de mecanismo de falha sustentado não comprova eficácia ou segurança.
- O prognóstico é qualitativo; probabilidades numéricas exigem validação e calibração externas.
- A orientação clínica dos agentes é interna aos prompts e não substitui diretrizes ou avaliação por especialista.
