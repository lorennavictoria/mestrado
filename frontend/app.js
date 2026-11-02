const $ = (selector) => document.querySelector(selector);
let report;
let selectedNode;
let expandedNodes = new Set();

const text = (value, fallback = "nao informado") => value === null || value === undefined || value === "" ? fallback : value;
const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char]));
const evidence = (items = []) => items.length ? items.map((item) => `${item.finding}${item.source ? ` [${item.source}]` : ""}`).join("; ") : "nao registrada";

function setReport(next, name) {
  report = next; selectedNode = null; expandedNodes = new Set();
  $("#empty").hidden = true; $("#report").hidden = false;
  $("#file-name").textContent = name;
  $("#case-title").textContent = `Caso ${report.case_id || "sem identificador"}`;
  $("#model-badge").textContent = report.model || "modelo nao informado";
  renderAll();
}

function renderAll() {
  const state = report.patient_state || {}; const cancer = state.cancer || {};
  const metrics = [["Histologia",cancer.histology],["TNM",cancer.tnm_stage],["Progressao",cancer.progression_status],["Metastase",cancer.metastatic === true ? "documentada" : cancer.metastatic === false ? "nao documentada" : "desconhecida"],["Idade",state.patient && state.patient.age_years],["Modelo",report.model]];
  $("#overview-grid").innerHTML = metrics.map(([label,value]) => `<div class="metric"><small>${escape(label)}</small><strong>${escape(text(value))}</strong></div>`).join("");
  $("#fact-list").innerHTML = (state.active_problems || []).map((fact) => `<article class="fact"><strong>${escape(fact.statement)}</strong><small>${escape(evidence(fact.evidence))}</small></article>`).join("") || "<p>Nenhum fato ativo.</p>";
  const notices = [...(state.missing_information || []).map((item) => `Dado ausente: ${item}`), ...(state.data_warnings || [])];
  $("#warning-list").innerHTML = notices.map((item) => `<article class="warning">${escape(item)}</article>`).join("") || "<p>Sem alertas.</p>";
  $("#strategy-list").innerHTML = (report.generated_treatments || []).map((item) => `<article class="strategy"><h3>${escape(item.name)}</h3><small>${escape(item.status)} · ${escape(item.treatment_class)}</small><p>${escape((item.reason_for_consideration || []).join("; "))}</p><small>Evidencia do paciente: ${escape(evidence(item.patient_evidence))}</small><small>Diretrizes: ${escape((item.evidence_source_ids || []).join("; ") || "nao recuperadas")}</small><small>Lacunas de elegibilidade: ${escape((item.eligibility_missing || []).join("; ") || "nenhuma")}</small></article>`).join("") || "<p>O modelo nao gerou estrategias.</p>";
  $("#raw-json").textContent = JSON.stringify(report, null, 2);
  renderTree(); renderImpacts(); applySectionFilters();
}

function renderImpacts() {
  const analyses = report.candidate_treatments || [];
  $("#impact-list").innerHTML = analyses.map((analysis) => `<article class="impact"><strong>${escape(analysis.treatment.name)} · ${escape(analysis.candidate_status)}</strong><small>Elegibilidade: ${escape(analysis.eligibility && analysis.eligibility.status)} · Prognostico: ${escape(analysis.forecast && analysis.forecast.disease_control)} · confianca ${escape(analysis.forecast && analysis.forecast.confidence_in_reasoning)}</small><p>Cenarios de desfecho: ${escape((analysis.outcome_tree && analysis.outcome_tree.outcomes || []).map((item) => item.description).join("; ") || "nao registrados.")}</p><p>Raciocinio estruturado: ${escape((analysis.reasoning_summary || []).flatMap((item) => item.narrative || []).join("; ") || "nenhuma cadeia sustentada registrada.")}</p><p>Impactos: ${escape((analysis.impacts || []).map((item) => item.impact).join("; ") || "Nenhum impacto registrado.")}</p></article>`).join("") || "<p>Sem analises de tratamento.</p>";
}

function renderTree() {
  const analyses = report.candidate_treatments || []; const select = $("#treatment-select");
  select.innerHTML = analyses.map((item, index) => `<option value="${index}">${escape(item.treatment.name)}</option>`).join("");
  select.hidden = !analyses.length;
  select.onchange = () => { selectedNode = null; expandedNodes = new Set(); drawTree(); };
  drawTree();
}

function graphNodes(analysis) {
  const tree = analysis.failure_tree; const treatmentRoot = {node_id:`treatment:${tree.treatment_id}`, depth:-1, hypothesis:analysis.treatment.name, status:"treatment", treatment:true, treatment_data:analysis.treatment, analysis}; const initialOutcomes = tree.outcomes.map((outcome) => ({node_id:`root:${outcome.outcome_id}`, parent_id:treatmentRoot.node_id, outcome_id:outcome.outcome_id, depth:0, hypothesis:outcome.description, status:"outcome", initial:true, generation_context:tree.outcome_generation_context, validation_trace:tree.outcome_generation_trace, outcome_evidence:analysis.outcome_tree && analysis.outcome_tree.evidence})); const parentIds = new Set(tree.nodes.map((node) => node.parent_id).filter(Boolean)); const terminalOutcomes = tree.nodes.filter((node) => node.status === "supported" && !parentIds.has(node.node_id)).map((node) => { const outcome = tree.outcomes.find((item) => item.outcome_id === node.outcome_id); return {node_id:`terminal:${node.node_id}`, parent_id:node.node_id, outcome_id:node.outcome_id, depth:node.depth + 1, hypothesis:outcome ? outcome.description : "Desfecho não registrado", status:"outcome", terminal:true, generation_context:tree.outcome_generation_context, validation_trace:tree.outcome_generation_trace, outcome_evidence:analysis.outcome_tree && analysis.outcome_tree.evidence}; }); return [treatmentRoot, ...initialOutcomes, ...tree.nodes, ...terminalOutcomes];
}

function visibleGraphNodes(nodes) {
  const children = new Map(); nodes.filter((node) => !node.treatment).forEach((node) => { const parent = node.parent_id || `root:${node.outcome_id}`; children.set(parent, [...(children.get(parent) || []), node]); }); const root = nodes.find((node) => node.treatment); const visible = [root]; const queue = [root]; while (queue.length) { const node = queue.shift(); if (!expandedNodes.has(node.node_id)) continue; (children.get(node.node_id) || []).forEach((child) => { visible.push(child); queue.push(child); }); } return visible;
}

function drawTree() {
  const analysis = (report.candidate_treatments || [])[$("#treatment-select").value || 0]; const graph = $("#graph");
  if (!analysis) { graph.innerHTML = "<p>Sem arvore para exibir.</p>"; $("#node-detail").innerHTML = "<p>Sem rastreabilidade de nos.</p>"; return; }
  const all = graphNodes(analysis); const visible = visibleGraphNodes(all); const lanes = new Map(); visible.forEach((node) => { const depth = node.depth === undefined ? 0 : node.depth; lanes.set(depth, [...(lanes.get(depth) || []), node]); });
  graph.innerHTML = '<svg id="edges"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker></defs></svg>' + [...lanes.entries()].sort((a,b)=>a[0]-b[0]).map(([depth,nodes]) => `<div class="lane"><span class="lane-title">${depth === -1 ? "tratamento candidato" : depth === 0 ? "desfechos iniciais" : nodes.some((node) => node.terminal) ? "desfecho final" : `iteracao ${depth}`}</span>${nodes.map((node) => `<button class="graph-node ${node.status}" data-node="${escape(node.node_id)}"><span class="node-kicker">${escape(node.treatment ? "origem" : node.initial ? "desfecho inicial" : node.terminal ? "desfecho final" : `iteracao ${node.depth}`)}</span><b>${escape(node.hypothesis)}</b><small>${escape(node.treatment ? node.treatment_data.status : node.initial ? "cenário contrafactual" : node.terminal ? "desfecho associado ao ramo sustentado" : `${node.status}${node.pruning_code ? ` · ${node.pruning_code}` : ""}`)}</small></button>`).join("")}</div>`).join("");
  graph.querySelectorAll(".graph-node").forEach((button) => button.onclick = () => { selectedNode = visible.find((node) => node.node_id === button.dataset.node); expandedNodes.add(button.dataset.node); drawTree(); });
  selectedNode = selectedNode && visible.find((node) => node.node_id === selectedNode.node_id); requestAnimationFrame(() => drawEdges(visible)); renderNodeDetail();
}

function drawEdges(nodes) {
  const graph = $("#graph"); const svg = $("#edges"); const bounds = graph.getBoundingClientRect(); svg.setAttribute("viewBox", `0 0 ${bounds.width} ${bounds.height}`); svg.innerHTML = '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker></defs>';
  const treatmentRoot = nodes.find((node) => node.treatment); nodes.filter((node) => !node.treatment).forEach((node) => { const parent = node.parent_id || (node.outcome_id ? `root:${node.outcome_id}` : treatmentRoot && treatmentRoot.node_id); const source = parent && graph.querySelector(`[data-node="${CSS.escape(parent)}"]`); const target = graph.querySelector(`[data-node="${CSS.escape(node.node_id)}"]`); if (!source || !target) return; const a = source.getBoundingClientRect(), b = target.getBoundingClientRect(); const x1=a.right-bounds.left, y1=a.top+a.height/2-bounds.top, x2=b.left-bounds.left, y2=b.top+b.height/2-bounds.top; svg.innerHTML += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" marker-end="url(#arrow)"/>`; });
}

function renderNodeDetail() {
  const panel = $("#node-detail"); if (!selectedNode) { panel.innerHTML = "<p>Selecione uma hipotese para ver o contexto que o sistema enviou ao modelo, os fatos vinculados e a decisao de poda.</p>"; return; }
  if (selectedNode.treatment) { const treatment = selectedNode.treatment_data; const eligibility = selectedNode.analysis.eligibility || {}; panel.innerHTML = `<h3>Tratamento candidato: ${escape(treatment.name)}</h3><div class="detail-grid"><div class="detail-block"><h4>Objetivo</h4><p>${escape(treatment.therapeutic_goal)}</p></div><div class="detail-block"><h4>Elegibilidade</h4><p>${escape(eligibility.status)}</p><p>${escape((eligibility.reasons || []).join("; "))}</p><p>Lacunas: ${escape((eligibility.missing_requirements || []).join("; ") || "nenhuma")}</p></div><div class="detail-block"><h4>Diretrizes recuperadas</h4><p>${escape(evidence(eligibility.citations))}</p></div><div class="detail-block"><h4>Evidencia do paciente</h4><p>${escape(evidence(treatment.patient_evidence))}</p></div></div>`; return; }
  if (selectedNode.initial || selectedNode.terminal) { const context = selectedNode.generation_context; panel.innerHTML = `<h3>Desfecho ${selectedNode.initial ? "inicial" : "final"}: ${escape(selectedNode.hypothesis)}</h3><div class="detail-grid"><div class="detail-block"><h4>Como o desfecho foi solicitado</h4>${context ? `<pre>${escape(JSON.stringify(context, null, 2))}</pre>` : "<p>Trace indisponivel neste relatorio legado.</p>"}</div><div class="detail-block"><h4>Diretrizes da arvore de desfechos</h4><p>${escape(evidence(selectedNode.outcome_evidence))}</p></div><div class="detail-block"><h4>Trace de geracao</h4><pre>${escape(JSON.stringify(selectedNode.validation_trace || {}, null, 2))}</pre></div></div>`; return; }
  const trace = selectedNode.validation_trace || {}; const context = selectedNode.generation_context;
  panel.innerHTML = `<h3>${escape(selectedNode.hypothesis)}</h3><div class="detail-grid"><div class="detail-block"><h4>Mecanismo</h4><p>${escape(selectedNode.mechanism)}</p></div><div class="detail-block"><h4>Validacao</h4><p>Status: <strong>${escape(selectedNode.status)}</strong>${selectedNode.pruning_code ? ` · ${escape(selectedNode.pruning_code)}` : ""}</p><p>Fatos: ${escape((trace.resolved_patient_fact_ids || []).join(", ") || "nao registrado")}</p><p>Lacunas: ${escape((selectedNode.missing_information || []).join(", ") || "nenhuma")}</p></div><div class="detail-block"><h4>Cadeia causal</h4><p>${escape((selectedNode.causal_chain || []).join(" → ") || "nao registrada")}</p></div><div class="detail-block"><h4>Evidencia resolvida</h4><p>${escape(evidence(selectedNode.patient_evidence))}</p></div><div class="detail-block"><h4>Solicitacao ao modelo</h4>${context ? `<pre>${escape(JSON.stringify(context, null, 2))}</pre>` : "<p>Trace indisponivel neste relatorio legado.</p>"}</div><div class="detail-block"><h4>Trace de poda</h4><pre>${escape(JSON.stringify(trace, null, 2) || "Trace indisponivel")}</pre></div></div>`;
}

function applySectionFilters() { document.querySelectorAll("[data-section]").forEach((box) => { const view = document.querySelector(`[data-view="${box.dataset.section}"]`); if (view) view.hidden = !box.checked; }); }
$("#report-file").addEventListener("change", async (event) => { const file = event.target.files[0]; if (!file) return; try { setReport(JSON.parse(await file.text()), file.name); } catch { alert("O arquivo nao contem JSON valido."); } });
document.querySelectorAll("[data-section]").forEach((box) => box.addEventListener("change", applySectionFilters));
window.addEventListener("resize", () => { if (report) { const analysis = (report.candidate_treatments || [])[$("#treatment-select").value || 0]; if (analysis) drawEdges(visibleGraphNodes(graphNodes(analysis))); } });
