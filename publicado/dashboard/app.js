const dot = state => `<i class="dot ${state}"></i>`;
const esc = value => String(value ?? "—").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));

function renderKpis(kpis) {
  const root=document.querySelector("#kpis");
  const cards=[
    ["good","Cadenas completas",kpis.complete,kpis.complete_names.join(" · ") || "—"],
    ["info","Preparados para continuar",kpis.ready,kpis.ready_names.join(" · ") || "—"],
    ["warn","Revalidación / validación pendiente",kpis.pending,kpis.pending_names.join(" · ") || "—"],
    ["bad","Pendientes o bloqueados",kpis.blocked,kpis.blocked_names.join(" · ") || "—"],
  ];
  root.innerHTML=cards.map(([cls,label,value,names])=>`<article class="kpi ${cls}"><p>${label}</p><strong>${value}</strong><span>${esc(names)}</span></article>`).join("");
}
function renderTerritories(rows) {
  document.querySelector("#territories").innerHTML=rows.map(r=>`
    <tr class="${r.g==="green"?"highlight":""}">
      <td>${esc(r.name)}</td><td>${dot(r.ft)}</td><td>${dot(r.fe)}</td><td>${dot(r.g)}</td><td>${dot(r.re)}</td><td>${esc(r.status)}</td>
    </tr>`).join("");
}
function renderLatest(latest) {
  document.querySelector("#latest-badge").textContent=latest?.name || "—";
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
  document.querySelector("#footer-territories").textContent=`${data.territories.length} territorios monitorizados`;
  document.querySelector("#footer-validated").textContent=`${data.kpis.complete} cadenas completas`;
}
bootstrap().catch(error=>{
  console.error(error);
  document.querySelector("#territories").innerHTML=`<tr><td colspan="6">No se pudo cargar el estado operativo: ${esc(error.message)}</td></tr>`;
});
