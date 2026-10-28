const scalar=(props,names)=>{for(const n of names){if(props[n]!==undefined&&props[n]!==null&&props[n]!=="")return props[n]}return null};
const formatNumber=v=>typeof v==="number"?new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(v):String(v??"—");
const formatPercent=v=>{if(v===null||v===undefined||v==="")return"—";const n=Number(v);if(!Number.isFinite(n))return String(v);const pct=Math.abs(n)<=1?n*100:n;return pct.toLocaleString("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2})+" %"};
function districtHtml(props,spec){
  const id=scalar(props,["district_id","DISTRICT_ID","id"]),pop=scalar(props,["population","district_pop","POPULATION"]),target=scalar(props,["target_population","target","TARGET"]),dev=scalar(props,["relative_deviation","population_target_ratio"]),mun=scalar(props,["municipalities","municipality_names","MUNICIPALITIES"]);
  let extra="";
  if(spec?.kind==="canonical_m08"){
    const winner=scalar(props,["winner_party"]),winnerVotes=scalar(props,["winner_votes"]),winnerShare=scalar(props,["winner_share"]),totalVotes=scalar(props,["total_votes"]);
    extra=`<dt>Partido ganador</dt><dd>${formatNumber(winner)}</dd><dt>Votos del ganador</dt><dd>${formatNumber(winnerVotes)}</dd><dt>Porcentaje del ganador</dt><dd>${formatPercent(winnerShare)}</dd><dt>Votos totales</dt><dd>${formatNumber(totalVotes)}</dd>`;
  }
  return`<p class="district-title">Distrito ${formatNumber(id)}</p><dl class="detail-list"><dt>Población</dt><dd>${formatNumber(pop)}</dd><dt>Objetivo</dt><dd>${formatNumber(target)}</dd><dt>Desviación</dt><dd>${dev===null?"—":formatPercent(dev)}</dd><dt>Municipios</dt><dd>${formatNumber(mun)}</dd>${extra}</dl>`;
}
