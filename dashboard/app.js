const dot = state => '<i class="dot ' + state + '"></i>';
const esc = value => String(value == null ? '—' : value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));

const SOURCE_STATUS_LABELS = {
  ADMISSIBLE: ['green','Acreditada'],
  ADMISSIBLE_TEMPORAL_SUBSTITUTION: ['green','Acreditada · sustitución temporal'],
  INCOMPATIBLE: ['yellow','Requiere corrección'],
  NOT_ACCREDITED: ['gray','No acreditada'],
  ACQUISITION_REQUIRED: ['yellow','Pendiente de adquisición'],
  TERRITORIAL_ACTION_REQUIRED: ['yellow','Pendiente territorial'],
  ELECTORAL_ACTION_REQUIRED: ['yellow','Pendiente electoral'],
  ACTION_REQUIRED: ['yellow','Requiere acción'],
  BLOCKED: ['red','Bloqueada'],
  UNAVAILABLE: ['gray','No disponible']
};

const ACTIVATION_STATE_LABELS = {
  ACTIVATED: ['green','Activada'],
  ACTIVABLE: ['blue','Activable'],
  ACTION_REQUIRED: ['yellow','Requiere acción'],
  BLOCKED: ['red','Bloqueada'],
  NOT_ACCREDITED: ['gray','No acreditada']
};

const REASON_LABELS = {
  TERRITORIAL_DURABLE_CANDIDATE: 'La fuente territorial vigente está acreditada.',
  TERRITORIAL_IDENTITY_MISMATCH: 'La fuente territorial registrada no corresponde con la identidad requerida.',
  TERRITORIAL_ARTIFACT_IDENTITY_MISMATCH: 'La fuente territorial debe volver a acreditarse con su identidad correcta.',
  TERRITORIAL_RECEIPT_CONTRADICTORY: 'La acreditación territorial contiene datos contradictorios y debe corregirse.',
  TERRITORIAL_POPULATION_YEAR_MISMATCH: 'La población acreditada no corresponde al año que necesita la legislatura.',
  TERRITORIAL_SECTION_YEAR_MISMATCH: 'El seccionado acreditado no corresponde al año que necesita la legislatura.',
  TERRITORIAL_PACKAGE_MISSING: 'Falta preparar y acreditar la fuente territorial.',
  TERRITORIAL_DECLARATION_MISSING: 'Falta declarar una fuente territorial oficial gobernada.',
  TERRITORIAL_TEMPORAL_IDENTITY_MISSING: 'Falta acreditar la relación temporal entre población y seccionado.',
  TERRITORIAL_RUN_INVALID: 'La adquisición territorial existente no puede acreditarse y debe repetirse.',
  TERRITORIAL_DIGEST_MISSING: 'La fuente territorial no tiene una huella verificable.',
  TERRITORIAL_COMPATIBILITY_REPORT_MISSING: 'Falta acreditar la compatibilidad entre población y geometría.',
  TERRITORIAL_RECEIPT_MISSING: 'Falta el comprobante durable de la fuente territorial.',
  TERRITORIAL_PROVENANCE_MISSING: 'Falta acreditar la procedencia oficial de la fuente territorial.',
  ELECTORAL_DURABLE_CANDIDATE: 'Los resultados electorales vigentes están acreditados.',
  ELECTORAL_IDENTITY_MISMATCH: 'Los resultados registrados no corresponden con la elección vigente.',
  ELECTORAL_ELECTION_MISMATCH: 'La fuente electoral pertenece a otra elección y debe sustituirse.',
  ELECTORAL_ARTIFACT_IDENTITY_MISMATCH: 'La fuente electoral debe volver a acreditarse con su identidad correcta.',
  ELECTORAL_PROVENANCE_MISMATCH: 'La procedencia electoral acreditada no coincide con la fuente esperada.',
  ELECTORAL_PACKAGE_MISSING: 'Falta preparar y acreditar los resultados electorales.',
  ELECTORAL_RECEIPT_MISSING: 'Falta el comprobante durable de los resultados electorales.',
  ELECTORAL_RECEIPT_KIND: 'El comprobante electoral disponible no es válido para Activación.',
  ELECTORAL_RUN_INVALID: 'La adquisición electoral existente no puede acreditarse y debe repetirse.',
  ELECTORAL_DIGEST_MISSING: 'La fuente electoral no tiene una huella verificable.',
  ELECTORAL_PROVENANCE_MISSING: 'Falta acreditar la procedencia de los resultados electorales.',
  ELECTORAL_PROVENANCE_REFERENCE_MISSING: 'Falta vincular los resultados con su fuente electoral oficial.',
  ELECTORAL_LEGACY_PROVENANCE_INCOMPLETE: 'La acreditación histórica de los resultados está incompleta.',
  ELECTORAL_PACKAGE_IDENTITY_NOT_DURABLE: 'La identidad de la fuente electoral aún no está acreditada de forma durable.',
  ELECTORAL_RECEIPT_SCHEMA: 'El comprobante electoral debe actualizarse al contrato vigente.',
  OFFICIAL_SPECIAL_ACQUISITION_AVAILABLE: 'Existe una fuente oficial identificada; falta adquirirla y acreditarla.',
  PROVISIONAL_NOT_PRODUCTION_ELIGIBLE: 'Los resultados disponibles son provisionales y todavía no pueden activarse.'
};

const MAP_POINTS = {
  galicia:{x:18,y:27,label:'GAL'},principado_de_asturias:{x:34,y:17,label:'AST'},cantabria:{x:45,y:18,label:'CAN'},
  pais_vasco:{x:55,y:21,label:'PV'},comunidad_foral_de_navarra:{x:63,y:25,label:'NAV'},la_rioja:{x:55,y:30,label:'RIO'},
  aragon:{x:68,y:37,label:'ARA'},cataluna:{x:82,y:34,label:'CAT'},castilla_y_leon:{x:40,y:38,label:'CYL'},
  madrid:{x:49,y:50,label:'MAD'},castilla_la_mancha:{x:54,y:62,label:'CLM'},extremadura:{x:34,y:61,label:'EXT'},
  comunidad_valenciana:{x:70,y:61,label:'CV'},region_de_murcia:{x:66,y:73,label:'MUR'},andalucia:{x:46,y:78,label:'AND'},
  illes_balears:{x:87,y:62,label:'BAL'},canarias:{x:17,y:88,label:'ICA'},ceuta:{x:49,y:91,label:'CEU'},melilla:{x:59,y:92,label:'MEL'}
};

let activationRows = [];
let activationFilter = 'all';
let activationSelected = null;

function statusChip(code) {
  const pair = SOURCE_STATUS_LABELS[code] || ['gray', code || '—'];
  return '<span class="status-chip ' + pair[0] + '">' + esc(pair[1]) + '</span>';
}

function activationChip(state) {
  const pair = ACTIVATION_STATE_LABELS[state] || ['gray', state || '—'];
  return '<span class="status-chip ' + pair[0] + '">' + esc(pair[1]) + '</span>';
}

function renderKpis(kpis) {
  const root=document.querySelector('#kpis');
  const cards=[
    ['good','Cadena completa validada',kpis.complete,kpis.complete_names.join(' · ') || '—'],
    ['info','Preparados para continuar',kpis.ready,kpis.ready_names.join(' · ') || '—'],
    ['warn','Validación pendiente',kpis.pending,kpis.pending_names.join(' · ') || '—'],
    ['bad','Pendientes o bloqueados',kpis.blocked,kpis.blocked_names.join(' · ') || '—']
  ];
  root.innerHTML=cards.map(c=>'<article class="kpi '+c[0]+'"><p>'+c[1]+'</p><strong>'+c[2]+'</strong><span>'+esc(c[3])+'</span></article>').join('');
}

function renderTerritories(rows) {
  document.querySelector('#territories').innerHTML=rows.map(r=>
    '<tr class="'+(r.g==='green'?'highlight':'')+'"><td>'+esc(r.display_name || r.name)+'</td><td>'+dot(r.ft)+'</td><td>'+dot(r.g)+'</td><td>'+dot(r.fe)+'</td><td>'+dot(r.re)+'</td><td>'+esc(r.status)+'</td></tr>'
  ).join('');
}

function renderLatest(latest) {
  document.querySelector('#latest-badge').textContent=latest ? (latest.display_name || latest.name) : '—';
  const items=latest ? [
    ['Run', latest.run_id ? '<a href="https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/'+latest.run_id+'">'+latest.run_id+'</a>' : '—'],
    ['Etapa',esc(latest.stage)],['Certificación',esc(latest.certification)],['Edición',esc(latest.edition)]
  ] : [['Estado','Sin producto territorial validado en la cadena vigente']];
  document.querySelector('#latest').innerHTML=items.map(item=>'<dt>'+item[0]+'</dt><dd>'+item[1]+'</dd>').join('');
}

function renderList(selector, rows, ordered=false) {
  const root=document.querySelector(selector);
  root.innerHTML=rows.map(r=>ordered?'<li><b>'+esc(r.territory)+'</b> — '+esc(r.action)+'</li>':'<li><span>'+esc(r.territory)+'</span> '+esc(r.action)+'</li>').join('');
}

function activationMatches(row, filter) {
  if(filter==='all') return true;
  if(filter==='activated') return row.activation && row.activation.state==='ACTIVATED';
  if(filter==='activable') return row.activation && row.activation.state==='ACTIVABLE';
  if(filter==='territorial') return !['ADMISSIBLE','ADMISSIBLE_TEMPORAL_SUBSTITUTION'].includes(row.territorial && row.territorial.status);
  if(filter==='electoral') return (row.electoral && row.electoral.status)!=='ADMISSIBLE';
  if(filter==='blocked') return row.activation && row.activation.state==='BLOCKED';
  if(filter==='temporal') return row.territorial && row.territorial.status==='ADMISSIBLE_TEMPORAL_SUBSTITUTION';
  return true;
}

function setActivationFilter(filter) {
  activationFilter = activationFilter===filter ? 'all' : filter;
  document.querySelectorAll('.activation-card').forEach(card=>card.classList.toggle('active', card.dataset.filter===activationFilter));
  const clear=document.querySelector('#activation-clear-filter');
  clear.hidden=activationFilter==='all';
  renderActivationMap();
  renderActivationTable();
}

function renderActivationKpis(sourceReadiness) {
  const root=document.querySelector('#activation-kpis');
  if(!sourceReadiness || sourceReadiness.status!=='READY') {
    root.innerHTML='<article class="activation-card gray-card"><span class="card-label">Activación</span><strong>—</strong><span class="card-note">Estado no disponible</span></article>';
    return;
  }
  const s=sourceReadiness.summary;
  const cards=[
    ['green-card','Activadas',s.activated,'Par durable vigente ya acreditado','activated'],
    ['blue-card','Activables ahora',s.activable,'Sin adquisición previa necesaria','activable'],
    ['yellow-card','Pendientes de fuente territorial',s.territorial_pending,'Población o seccionado aún requieren acción','territorial'],
    ['yellow-card','Pendientes de fuente electoral',s.electoral_pending,'Resultados electorales aún requieren acción','electoral'],
    ['red-card','Bloqueadas',s.blocked,'Requieren resolver un bloqueo real','blocked'],
    ['blue-card','Sustitución temporal acreditada',s.temporal_substitution,'Excepción oficial gobernada, no un fallo','temporal']
  ];
  root.innerHTML=cards.map(c=>
    '<button type="button" class="activation-card '+c[0]+'" data-filter="'+c[4]+'"><span class="card-label">'+esc(c[1])+'</span><strong>'+esc(c[2])+'</strong><span class="card-note">'+esc(c[3])+'</span></button>'
  ).join('');
  root.querySelectorAll('.activation-card').forEach(card=>card.addEventListener('click',()=>setActivationFilter(card.dataset.filter)));
}

function renderActivationContext(sourceReadiness) {
  const evidence=sourceReadiness && sourceReadiness.temporal_evidence ? sourceReadiness.temporal_evidence : {};
  const checked=evidence.checked_at ? new Date(evidence.checked_at) : null;
  document.querySelector('#activation-vigency').textContent=checked && !Number.isNaN(checked.getTime()) ? checked.toLocaleDateString('es-ES',{day:'2-digit',month:'long',year:'numeric'}) : (sourceReadiness && sourceReadiness.as_of ? sourceReadiness.as_of : '—');
  document.querySelector('#activation-vigency-provider').textContent=evidence.provider || 'Evidencia temporal del proyecto';
  const recent=sourceReadiness && sourceReadiness.summary ? sourceReadiness.summary.recent_activity : 0;
  document.querySelector('#activation-activity').textContent=recent ? recent+' registros durables observados' : 'Sin actividad reciente acreditada';
}

function renderActivationChain(sourceReadiness) {
  const root=document.querySelector('#activation-chain');
  const c=sourceReadiness && sourceReadiness.activation_chain ? sourceReadiness.activation_chain : null;
  if(!c) {
    root.innerHTML='<p class="activation-detail-empty">Cadena de Activación no disponible.</p>';
    return;
  }
  const total=c.total || 0;
  const steps=[
    ['Legislatura resuelta',c.legislature_resolved,'Elección vigente identificada'],
    ['Años resueltos',c.years_resolved,'Población y seccionado objetivo'],
    ['Fuente territorial',c.territorial_source,'Fuente territorial admisible'],
    ['Fuente electoral',c.electoral_source,'Resultados electorales admisibles'],
    ['Par durable',c.durable_pair,'Activación materializada y acreditada']
  ];
  root.innerHTML=steps.map((step,index)=>{
    const pct=total ? Math.round((step[1]/total)*100) : 0;
    return '<div class="activation-step"><div class="activation-step-head"><span class="activation-step-index">'+(index+1)+'</span><strong>'+esc(step[1])+'/'+esc(total)+'</strong></div><p>'+esc(step[0])+'</p><span>'+esc(step[2])+'</span><div class="activation-progress"><i style="width:'+pct+'%"></i></div></div>';
  }).join('');
}

function sourceYearCell(selected, required, status) {
  const main=selected == null ? '—' : selected;
  return '<span class="cell-main">'+esc(main)+'</span><span class="cell-note">Objetivo de la legislatura: '+esc(required)+'</span><span class="cell-note">'+esc((SOURCE_STATUS_LABELS[status] || ['','Pendiente'])[1])+'</span>';
}

function temporalLabel(row) {
  if(row.territorial && row.territorial.status==='ADMISSIBLE_TEMPORAL_SUBSTITUTION') return 'Sustitución temporal acreditada';
  const reason=row.territorial ? row.territorial.reason : null;
  if(reason==='TERRITORIAL_POPULATION_YEAR_MISMATCH') return 'Población pendiente de ajustar';
  if(reason==='TERRITORIAL_SECTION_YEAR_MISMATCH') return 'Seccionado pendiente de ajustar';
  return 'Sin excepción temporal acreditada';
}

function reasonLabel(reason) {
  return REASON_LABELS[reason] || 'Revisar la acreditación pendiente de esta fuente.';
}

function nextActionLabel(row) {
  const steps=row.next_steps || [];
  if(!steps.length) {
    if(row.activation && row.activation.state==='ACTIVATED') return 'Nada en fuentes. La Activación vigente ya está acreditada.';
    if(row.activation && row.activation.state==='ACTIVABLE') return 'Registrar el par durable de las dos fuentes ya acreditadas.';
    return 'Revisar el estado durable de Activación.';
  }
  return steps.map(step=>reasonLabel(step.reason)).join(' ');
}

function renderActivationMap() {
  const root=document.querySelector('#activation-map-points');
  const rows=activationRows;
  root.innerHTML=rows.map(row=>{
    const p=MAP_POINTS[row.territory_id];
    if(!p) return '';
    const state=(row.activation && row.activation.state ? row.activation.state : 'NOT_ACCREDITED').toLowerCase();
    const muted=!activationMatches(row,activationFilter);
    const selected=row.territory_id===activationSelected;
    const temporal=row.territorial && row.territorial.status==='ADMISSIBLE_TEMPORAL_SUBSTITUTION';
    return '<button type="button" class="map-point state-'+state+(muted?' muted':'')+(selected?' selected':'')+(temporal?' temporal':'')+'" style="left:'+p.x+'%;top:'+p.y+'%" data-territory="'+esc(row.territory_id)+'" aria-label="'+esc((row.display_name||row.name)+' · '+((ACTIVATION_STATE_LABELS[row.activation && row.activation.state]||['','No acreditada'])[1]))+'" title="'+esc(row.display_name||row.name)+'">'+esc(p.label)+'</button>';
  }).join('');
  root.querySelectorAll('.map-point').forEach(point=>point.addEventListener('click',()=>selectActivationTerritory(point.dataset.territory)));
}

function renderActivationDetail(row) {
  const title=document.querySelector('#activation-detail-title');
  const badge=document.querySelector('#activation-detail-badge');
  const root=document.querySelector('#activation-detail');
  if(!row) {
    title.textContent='Selecciona un territorio';
    badge.className='status-chip gray';
    badge.textContent='—';
    root.className='activation-detail-empty';
    root.textContent='El mapa y el cuadro maestro abren aquí la situación de cada territorio.';
    return;
  }
  const statePair=ACTIVATION_STATE_LABELS[row.activation && row.activation.state] || ['gray','No acreditada'];
  title.textContent=row.display_name || row.name;
  badge.className='status-chip '+statePair[0];
  badge.textContent=statePair[1];
  root.className='activation-detail';
  const election=row.election && row.election.election_date ? row.election.election_date : '—';
  const pop=row.territorial && row.territorial.selected ? row.territorial.selected.population_year : '—';
  const sec=row.territorial && row.territorial.selected ? row.territorial.selected.section_year : '—';
  const electoral=(SOURCE_STATUS_LABELS[row.electoral && row.electoral.status] || ['','Pendiente'])[1];
  root.innerHTML=
    '<p class="activation-detail-lead">'+esc(temporalLabel(row))+'</p>'+
    '<div class="detail-grid">'+
      '<div class="detail-item"><span>Elección vigente</span><strong>'+esc(election)+'</strong></div>'+
      '<div class="detail-item"><span>Población</span><strong>'+esc(pop)+'</strong></div>'+
      '<div class="detail-item"><span>Secciones / geometría</span><strong>'+esc(sec)+'</strong></div>'+
      '<div class="detail-item"><span>Resultados electorales</span><strong>'+esc(electoral)+'</strong></div>'+
    '</div>'+
    '<div class="detail-action"><span>Siguiente acción</span><strong>'+esc(nextActionLabel(row))+'</strong></div>';
}

function selectActivationTerritory(territoryId) {
  activationSelected=territoryId;
  const row=activationRows.find(item=>item.territory_id===territoryId);
  renderActivationDetail(row || null);
  renderActivationMap();
  renderActivationTable();
}

function renderActivationTable() {
  const root=document.querySelector('#activation-territories');
  const filtered=activationRows.filter(row=>activationMatches(row,activationFilter));
  const labels={all:'Todos los territorios',activated:'Activadas',activable:'Activables ahora',territorial:'Pendientes de fuente territorial',electoral:'Pendientes de fuente electoral',blocked:'Bloqueadas',temporal:'Sustitución temporal acreditada'};
  document.querySelector('#activation-filter-label').textContent=(labels[activationFilter] || labels.all)+' · '+filtered.length;
  root.innerHTML=filtered.map(row=>{
    const t=row.territorial || {};
    const selected=t.selected || {};
    const required=t.required || {};
    const electoral=row.electoral || {};
    const selectedClass=row.territory_id===activationSelected?'selected-row':'';
    const electoralSource=electoral.source || 'Fuente electoral';
    const action=nextActionLabel(row);
    const actionClass=(row.activation && row.activation.state==='ACTIVATED')?'next-action ok':'next-action';
    return '<tr class="'+selectedClass+'">'+
      '<td><button type="button" class="territory-link" data-territory="'+esc(row.territory_id)+'">'+esc(row.display_name || row.name)+'</button></td>'+
      '<td>'+sourceYearCell(selected.population_year,required.population_year,t.status)+'</td>'+
      '<td>'+sourceYearCell(selected.section_year,required.section_year,t.status)+'</td>'+
      '<td>'+statusChip(electoral.status)+'<span class="cell-source">'+esc(electoralSource)+'</span></td>'+
      '<td><span class="cell-main">'+esc(temporalLabel(row))+'</span></td>'+
      '<td>'+activationChip(row.activation && row.activation.state)+'</td>'+
      '<td><span class="'+actionClass+'">'+esc(action)+'</span></td>'+
    '</tr>';
  }).join('');
  root.querySelectorAll('.territory-link').forEach(button=>button.addEventListener('click',()=>selectActivationTerritory(button.dataset.territory)));
}

function renderActivation(sourceReadiness) {
  renderActivationKpis(sourceReadiness);
  if(!sourceReadiness || sourceReadiness.status!=='READY') {
    activationRows=[];
    renderActivationContext(sourceReadiness || {});
    renderActivationChain(sourceReadiness || {});
    document.querySelector('#activation-territories').innerHTML='<tr><td colspan="7">No hay dictamen de Activación disponible.</td></tr>';
    return;
  }
  activationRows=sourceReadiness.territories || [];
  document.querySelector('#activation-snapshot').textContent=sourceReadiness.as_of || '—';
  renderActivationContext(sourceReadiness);
  renderActivationChain(sourceReadiness);
  renderActivationMap();
  renderActivationTable();
  renderActivationDetail(activationSelected ? activationRows.find(row=>row.territory_id===activationSelected) : null);
  document.querySelector('#activation-clear-filter').addEventListener('click',()=>{activationFilter='all';setActivationFilter('none');activationFilter='all';document.querySelectorAll('.activation-card').forEach(card=>card.classList.remove('active'));document.querySelector('#activation-clear-filter').hidden=true;renderActivationMap();renderActivationTable();});
}

function setDashboardView(view) {
  const selected=view==='activation' ? 'activation' : 'operational';
  document.querySelectorAll('.dashboard-view').forEach(el=>{el.hidden=el.id!==('view-'+selected);});
  document.querySelectorAll('.tab-button').forEach(btn=>btn.classList.toggle('active',btn.dataset.view===selected));
  if(window.location.hash!==('#'+selected)) history.replaceState(null,'','#'+selected);
}

function wireDashboardTabs() {
  document.querySelectorAll('.tab-button').forEach(btn=>btn.addEventListener('click',()=>setDashboardView(btn.dataset.view)));
  const hash=window.location.hash;
  setDashboardView(hash==='#activation' || hash==='#sources' ? 'activation' : 'operational');
}

async function bootstrap(){
  const response=await fetch('status.json',{cache:'no-cache'});
  if(!response.ok) throw new Error('status.json HTTP '+response.status);
  const data=await response.json();
  document.querySelector('#snapshot').textContent=data.generated_at.slice(0,10);
  renderKpis(data.kpis);
  renderTerritories(data.territories);
  renderLatest(data.latest_validated);
  renderList('#alerts',data.alerts);
  renderList('#next',data.next_actions,true);
  renderActivation(data.source_readiness);
  wireDashboardTabs();
  document.querySelector('#footer-territories').textContent=(data.country_display_name || 'ES · España')+' · '+data.territories.length+' territorios monitorizados';
  document.querySelector('#footer-validated').textContent=data.kpis.complete+' cadenas completas validadas';
}

bootstrap().catch(error=>{
  console.error(error);
  document.querySelector('#territories').innerHTML='<tr><td colspan="6">No se pudo cargar el estado operativo: '+esc(error.message)+'</td></tr>';
  const activation=document.querySelector('#activation-territories');
  if(activation) activation.innerHTML='<tr><td colspan="7">No se pudo cargar el estado de Activación.</td></tr>';
});
