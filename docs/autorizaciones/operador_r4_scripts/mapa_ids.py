import re,subprocess,sys
cat=subprocess.check_output(['git','show','origin/main:configuracion/catalogo_territorios_espana_2025.yaml']).decode()
m={}
for tid,name in re.findall(r"territory_id: (aut\d\d|nac\d\d),.*?name: ([^,]+),",cat): m[name.strip()]=tid
out=[]
for l in open('docs/autorizaciones/p10_r4_resultado.tsv'):
    t,run,st=l.rstrip('\n').split('\t')
    k=re.sub(r'^\d\d ','',t)
    tid=m.get(k)
    if not tid: sys.exit('SIN_ID '+t)
    out.append(f'{tid}\t{run}\t-\t-')
open('docs/autorizaciones/p10_r4_paquetes.tsv','w').write('id\trun_p10\tartefacto\tcaduca\n'+'\n'.join(out)+'\n')
print(len(out))
