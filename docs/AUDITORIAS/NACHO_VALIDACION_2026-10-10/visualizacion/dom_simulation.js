// Version1.0.0 2026-10-10. Real generated app.js, JavaScriptCore, simulated DOM/MapLibre only.
// No browser rendering, no network, no install. All input comes from local frozen gallery.
const root='/private/tmp/ddd-nacho-validacion3-20261010/gallery/';
function assert(v,msg){if(!v)throw Error(msg)}
class Option{constructor(text,value){this.text=text;this.value=value}}
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.options=[];this._value='';this._html='';this.checked=false;this.className=''}
 add(o){this.options.push(o);if(this.options.length===1)this._value=o.value}
 get value(){return this._value}set value(v){this._value=this.tag==='select'&& !this.options.some(o=>o.value===v)?'':v}
 set selectedIndex(i){this._value=this.options[i]?this.options[i].value:''}get selectedIndex(){return this.options.findIndex(o=>o.value===this.value)}
 set innerHTML(s){this._html=s;if(s==='')this.children=[]}get innerHTML(){return this._html}
 append(e){this.children.push(e)}
 querySelector(s){if(s==='button'){return this.button||(this.button={})}if(s==='h2'){return{textContent:(this._html.match(/<h2>(.*?)<\/h2>/)||[])[1]}}throw Error('Unsupported simulated selector '+s)}
 querySelectorAll(s){if(s==='.metric span'){return this.children.flatMap(c=>[...c._html.matchAll(/<span>(.*?)<\/span>/g)].map(x=>({textContent:x[1]})))}throw Error('Unsupported simulated selector '+s)}
 get textContent(){return this._html.replace(/<[^>]*>/g,' ')+this.children.map(c=>c.textContent).join(' ')}
 click(){downloads.push(this.download)}
}
var meta=new Element('p'),profile=new Element('select'),pareto=new Element('input'),download=new Element('button'),compareA=new Element('select'),compareB=new Element('select'),cards=new Element('section'),selected=new Element('select'),reviewer=new Element('input'),reason=new Element('textarea');
profile.add(new Option('Todos',''));selected.add(new Option('Sin seleccionar',''));
var document={createElement:t=>new Element(t)},window={},mapsRecorded=[],downloads=[],downloadedSelections=[];
var maplibregl={Map:class{constructor(o){mapsRecorded.push(o)}remove(){}fitBounds(b){this.bounds=b}addControl(){}},NavigationControl:class{}};
var fetch=async function(path){return{json:async()=>JSON.parse(readFile(root+path))}};
var Blob=class{constructor(parts){this.parts=parts}},URL={createObjectURL(b){downloadedSelections.push(JSON.parse(b.parts.join('')));return'blob:mock'}};
const original=readFile(root+'app.js');
assert(original.endsWith('load();'),'Expected unmodified entrypoint');
// Capture the promise of the original initialization; all function bodies stay exact.
eval(original.slice(0,-7)+'window.initialLoad=load();');
window.initialLoad.then(async()=>{
 await Promise.resolve();await Promise.resolve();
 let tests={runtime:'local JavaScriptCore',DOM:'simulated',MapLibre:'simulated; no map rendered'};
 tests.initialCards=cards.children.length;tests.initialIDs=cards.children.map(x=>x.querySelector('h2').textContent);
 tests.invalidOptionsAbsent=!selected.options.some(o=>o.value==='C_hard_invalid');
 tests.initialComparison=[compareA.value,compareB.value];
 pareto.checked=true;pareto.onchange();tests.paretoIDs=cards.children.map(x=>x.querySelector('h2').textContent);
 pareto.checked=false;pareto.onchange();
 cards.children[1].querySelector('button').onclick();tests.selected=selected.value;
 reviewer.value='DIAGNOSTIC_ONLY';reason.value='No authorized promotion';download.onclick();
 tests.downloaded=downloadedSelections;tests.visibleLabels=cards.querySelectorAll('.metric span').map(x=>x.textContent);tests.visibleText=cards.textContent;
 tests.maps=mapsRecorded.map(o=>({container:o.container,featureCount:o.style.sources.candidate.data.features.length}));
 tests.objectiveExplanationVisible=/domina|[Oo]bjetivo|frente de Pareto|15%.*10%/.test(cards.textContent);
 tests.floorCapVisible=/Floor|Cap|800|1750/.test(cards.textContent);
 tests.invalidCausesVisible=/population_cap|population_floor|C_hard_invalid/.test(cards.textContent);
 tests.perDistrictPopulationVisible=/1150|1100|950|900/.test(cards.textContent);
 assert(tests.initialCards===2,'Two cards');assert(tests.paretoIDs.join()==='B_lower_max','Pareto B');
 assert(tests.invalidOptionsAbsent,'Invalid candidate cannot be selected');assert(tests.selected==='B_lower_max','B selected');
 assert(tests.maps.length===2&&tests.maps.every(m=>m.featureCount===16),'Both assets loaded');
 assert(tests.downloaded[0].candidate_id==='B_lower_max','Selection export');
 assert(!tests.floorCapVisible&&!tests.invalidCausesVisible&&!tests.perDistrictPopulationVisible,'Actual diagnostic omissions');
 var sections={checked:true},showInvalid={checked:true},invalid={hidden:false};
 const toggles=[];document.body={classList:{toggle:(k,v)=>toggles.push([k,v])}};
 const offline=readFile('/private/tmp/ddd-nacho-validacion3-20261010/diagnostico.html');
 const inline=offline.match(/<script>([\s\S]*?)<\/script>/)[1];eval(inline);
 sections.checked=false;sections.onchange();showInvalid.checked=false;showInvalid.onchange();
 assert(toggles[0][0]==='hide-grid'&&toggles[0][1]===true&&invalid.hidden,'Offline layer toggles');
 showInvalid.checked=true;showInvalid.onchange();assert(!invalid.hidden,'Rejected evidence restored');
 tests.offline_diagnostic_toggle_checks={DOM:'simulated',section_boundary_toggle:true,rejected_candidate_show_hide:true};
 print(JSON.stringify(tests,null,2));
}).catch(e=>{print('ERROR '+e.stack);quit(1)});
