const dot = state => `<i class="dot ${state}"></i>`;
const esc = value => String(value ?? "—").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));

const SOURCE_STATUS_LABELS = {
  ADMISSIBLE: ["green", "Admisible"],
  ADMISSIBLE_TEMPORAL_SUBSTITUTION: ["green", "Admisible · sustitución acreditada"],
  INCOMPATIBLE: ["yellow", "Incompatible"],
  NOT_ACCREDITED: ["gray", "No acreditada"],
  ACQUISITION_REQUIRED: ["yellow", "Requiere adquisición"],
  TERRITORIAL_ACTION_REQUIRED: ["yellow", "Acción territorial requerida"],
  ELECTORAL_ACTION_REQUIRED: ["yellow", "Acción electoral requerida"],
  ACTION_REQUIRED: ["yellow", "Acción requerida"],
  BLOCKED: ["red", "Bloqueada"],
  UNAVAILABLE: ["gray", "No disponible"],
};

const PLANNER_ACTION_LABELS = {
  ACQUIRE: "Activar / adquirir fuente",
  BLOCKED_PROVISIONAL: "Resolver bloqueo electoral",
  REUSE: "Sin acción",
  REUSE_TEMPORAL_SUBSTITUTION: "Sin acción",
};

function statusChip(code) {
  const [cls,label]=SOURCE_STATUS_LABELS[code] || ["gray", code || "—"];
  return `<span class="status-chip ${cls}">${esc(label)}</span>`;
}

function renderSourceKpis(sourceReadiness) {
  const root=document.querySelector("#source-kpis");
  if(!root) return;
  if(!sourceReadiness || sourceReadiness.status!=="READY") {
    root.innerHTML='<article class="kpi warn"><p>Fuentes y vigencia</p><strong>—</strong><span>No disponible</span></article>';
    return;
  }
  const s=sourceReadiness.summary;
  const cards=[
    ["good","Fuentes admisibles",s.admissible],
    ["warn","Requieren acción",s.action_required],
    ["bad","Bloqueadas",s.blocked],
    ["info","Estado no disponible",s.unavailable],
  ];
  root.innerHTML=cards.map(([cls,label,value])=>`<article class="kpi ${cls}"><p>${label}</p><strong>${value}</strong><span>territorios</span></article>`).join("");
}

function yearPair(values) {
  if(!values) return "—";
  const pop=values.population_year ?? "—";
  const sec=values.section_year ?? "—";
  return `Pob. ${esc(pop)} · Secc. ${esc(sec)}`;
}

function nextStepsLabel(steps) {
  if(!steps || !steps.length) return "Sin acción sobre fuentes";
  return steps.map(step=>{
    const base=PLANNER_ACTION_LABELS[step.planner_action] || step.planner_action || "Revisar";
    const domain=step.domain==="territorial" ? "territorial" : "electoral";
    return `${base} · ${domain}`;
  }).join(" · ");
}

function renderSourceTerritories(sourceReadiness) {
  const root=document.querySelector("#source-territories");
  if(!root) return;
  if(!sourceReadiness || sourceReadiness.status!=="READY") {
    root.innerHTML='<tr><td colspan="9">No hay dictamen de fuentes disponible.</td></tr>';
    return;
  }
  root.innerHTML=sourceReadiness.territories.map(r=>{
    const electionYear=String(r.election?.election_date || "").slice(0,4) || "—";
    const activity=r.activity?.status==="NOT_OBSERVED" ? "—" : (r.activity?.label || "—");
    return `
      <tr>
        <td>${esc(r.display_name || r.name)}</td>
        <td><b>${esc(electionYear)}</b><span class="cell-note">${esc(r.election?.election_id)}</span></td>
        <td>${yearPair(r.territorial?.selected)}<span class="cell-note">Requerido: ${yearPair(r.territorial?.required)}</span></td>
        <td>${yearPair(r.territorial?.accredited)}</td>
        <td>${statusChip(r.territorial?.status)}<span class="cell-note">${esc(r.territorial?.reason || "—")}</span></td>
        <td>${statusChip(r.electoral?.status)}<span class="cell-note">${esc(r.electoral?.source || "—")}</span></td>
        <td>${statusChip(r.status)}</td>
        <td>${esc(activity)}</td>
        <td>${esc(nextStepsLabel(r.next_steps))}</td>
      </tr>`;
  }).join("");
}

function setDashboardView(view) {
  const selected=view==="sources" ? "sources" : "operational";
  document.querySelectorAll(".dashboard-view").forEach(el=>{ el.hidden = el.id !== `view-${selected}`; });
  document.querySelectorAll(".tab-button").forEach(btn=>btn.classList.toggle("active",btn.dataset.view===selected));
  if(window.location.hash !== `#${selected}`) history.replaceState(null,"",`#${selected}`);
}

function wireDashboardTabs() {
  document.querySelectorAll(".tab-button").forEach(btn=>btn.addEventListener("click",()=>setDashboardView(btn.dataset.view)));
  setDashboardView(window.location.hash==="#sources" ? "sources" : "operational");
}

function renderKpis(kpis) {
  const root=document.querySelector("#kpis");
  const cards=[
    ["good","Cadena completa validada",kpis.complete,kpis.complete_names.join(" · ") || "—"],
    ["info","Preparados para continuar",kpis.ready,kpis.ready_names.join(" · ") || "—"],
    ["warn","Validación pendiente",kpis.pending,kpis.pending_names.join(" · ") || "—"],
    ["bad","Pendientes o bloqueados",kpis.blocked,kpis.blocked_names.join(" · ") || "—"],
  ];
  root.innerHTML=cards.map(([cls,label,value,names])=>`<article class="kpi ${cls}"><p>${label}</p><strong>${value}</strong><span>${esc(names)}</span></article>`).join("");
}
function renderTerritories(rows) {
  document.querySelector("#territories").innerHTML=rows.map(r=>`
    <tr class="${r.g==="green"?"highlight":""}">
      <td>${esc(r.display_name || r.name)}</td><td>${dot(r.ft)}</td><td>${dot(r.g)}</td><td>${dot(r.fe)}</td><td>${dot(r.re)}</td><td>${esc(r.status)}</td>
    </tr>`).join("");
}
function renderLatest(latest) {
  document.querySelector("#latest-badge").textContent=latest?.display_name || latest?.name || "—";
  const items=latest ? [
    ["Run", latest.run_id ? `<a href="https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/${latest.run_id}">${latest.run_id}</a>` : "—"],
    ["Etapa",esc(latest.stage)],["Certificación",esc(latest.certification)],["Edición",esc(latest.edition)]
  ] : [["Estado","Sin producto territorial validado en la cadena vigente"]];
  document.querySelector("#latest").innerHTML=items.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join("");
}
function renderList(selector, rows, ordered=false) {
  const root=document.querySelector(selector);
  root.innerHTML=rows.map(r=>ordered?`<li><b>${esc(r.territory)}</b> — ${esc(r.action)}</li>`:`<li><span>${esc(r.territory)}</span> ${esc(r.action)}</li>`).join("");
}
async function bootstrap(){
  const response=await fetch("status.json",{cache:"no-cache"});
  if(!response.ok) throw new Error(`status.json HTTP ${response.status}`);
  const data=await response.json();
  document.querySelector("#snapshot").textContent=data.generated_at.slice(0,10);
  renderKpis(data.kpis); renderTerritories(data.territories); renderLatest(data.latest_validated);
  renderList("#alerts",data.alerts); renderList("#next",data.next_actions,true);
  renderSourceKpis(data.source_readiness);
  renderSourceTerritories(data.source_readiness);
  const sourceSnapshot=document.querySelector("#source-snapshot");
  if(sourceSnapshot) sourceSnapshot.textContent=data.source_readiness?.as_of || data.generated_at.slice(0,10);
  wireDashboardTabs();
  document.querySelector("#footer-territories").textContent=`${data.country_display_name || "ES · España"} · ${data.territories.length} territorios monitorizados`;
  document.querySelector("#footer-validated").textContent=`${data.kpis.complete} cadenas completas validadas`;
}
bootstrap().catch(error=>{
  console.error(error);
  document.querySelector("#territories").innerHTML=`<tr><td colspan="6">No se pudo cargar el estado operativo: ${esc(error.message)}</td></tr>`;
});
