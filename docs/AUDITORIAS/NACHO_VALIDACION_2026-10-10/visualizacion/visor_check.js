// V1.0.0, 2026-10-10. districtHtml/helpers copied exactly from current DDD visor (not historical code).
// Source function bodies are loaded from the separately hashed extraction; no DOM/browser/network.
const root='/private/tmp/ddd-nacho-validacion3-20261010/';
eval(readFile(root+'visor_pure_functions.js')+'\nglobalThis.visorPure={districtHtml,formatNumber,formatPercent};');
const frozen=JSON.parse(readFile(root+'frozen_results.json')).ranking;
const propsAssets={};const outputs=[];
for(const name of ['A_lower_L1','B_lower_max','C_hard_invalid']){
 const asset=JSON.parse(readFile(root+'assets_metric/'+name+'.geojson'));
 for(let d=0;d<4;d++){
  const municipalities=asset.features.filter(f=>f.properties.district_id===d).map(f=>'M'+(Number(f.properties.municipality)+1)).join(',');
  const props={district_id:d,population:frozen.candidates[name].population[d],target_population:1000,
   relative_deviation:(frozen.candidates[name].population[d]-1000)/1000,
   municipalities,floor:800,cap:1750,municipality_split_count:0,
   hard_constraint_violations:frozen.actual_DDD_engine_results[name].violations};
  const rendered=visorPure.districtHtml(props,{kind:'canonical_m06'});
  const checks={population_visible:rendered.includes('<dd>'+visorPure.formatNumber(props.population)+'</dd>'),
   target_visible:rendered.includes('<dt>Objetivo</dt><dd>'+visorPure.formatNumber(1000)+'</dd>'),
   deviation_visible:rendered.includes(visorPure.formatPercent(props.relative_deviation)),
   municipalities_list_visible:rendered.includes('<dt>Municipios</dt><dd>'+municipalities+'</dd>'),
   floor_cap_not_visible:!rendered.includes('Floor')&&!rendered.includes('Cap')&&!rendered.includes('1750'),
   split_count_not_shown:!rendered.includes('dividido')&&!rendered.includes('split_count'),
   granular_failures_not_shown:!rendered.includes('population_cap:')&&!rendered.includes('population_floor:')&&!rendered.includes('population_tolerance:')};
  if(!Object.values(checks).every(Boolean))throw Error(name+' district'+d+' assertion failed');
  outputs.push({candidate:name,district:d,input_properties:props,html:rendered,checks});
 }
}
print(JSON.stringify({runtime:'local JavaScriptCore',pure_functions_only:true,DOM:false,browser_render:false,
 frozen_candidates_only:true,case_count:outputs.length,outputs},null,2));
