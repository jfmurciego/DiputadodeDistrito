#!/usr/bin/env python3
"""Versión1.0.0; fecha2026-10-12; diagnóstico Cantabria; origen MITECO.
Descarga Range puntual; CRC central obligatorio; sin ZIP completo ni retries.
"""
import requests,struct,pathlib,json,hashlib,datetime,zlib
URL='https://www.miteco.gob.es/content/dam/miteco/es/costas/participacion-publica/anexos/39-cantabria/2026/20260921-des01-14-39-0001/des01-14-39-0001-documentacion.zip'
BASE=pathlib.Path(__file__).resolve().parent
central=(BASE/'ZIP_CENTRAL_RANGE.bin').read_bytes()
records=[];offset=0
while True:
 offset=central.find(b'PK\x01\x02',offset)
 if offset<0:break
 h=struct.unpack_from('<4s6H3L5H2L',central,offset);n,x,c=h[10:13];name=central[offset+46:offset+46+n].decode(errors='replace')
 if name.startswith(('3.2 ','3.1 ','1.1 ')):
  start=h[-1];end=start+30+n+256+h[8]-1
  response=requests.get(URL,headers={'Range':f'bytes={start}-{end}'},timeout=40)
  assert response.status_code==206,(response.status_code,'Range required')
  raw=response.content;local=struct.unpack_from('<4s5H3L2H',raw,0);assert local[0]==b'PK\x03\x04';ln,lx=local[-2:];data=raw[30+ln+lx:30+ln+lx+h[8]];assert len(data)==h[8]
  decoded=zlib.decompress(data,-15);assert len(decoded)==h[9];assert zlib.crc32(decoded)==h[7],name
  target=BASE/name;target.write_bytes(decoded)
  records.append({'file':name,'url':URL,'organismo':'MITECO Demarcación de Costas en Cantabria','archive_edition':'Expediente DES01/14/39/0001, documentación consulta2026; Estudio2023 no deslinde definitivo2025','acquired_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'GET','Range':f'bytes={start}-{end}','Content-Range':response.headers.get('Content-Range'),'HTTP_status':response.status_code,'member_localoffset':start,'compressed_bytes':h[8],'uncompressed_bytes':h[9],'zip_method':h[4],'crc32_central_hex':f'{h[7]:08x}','crc32_verified':True,'sha256_range_response':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(decoded).hexdigest(),'licencia':'Documento oficial consulta pública; licencia cartográfica adicional no indicada','command':'python extraer_miembros_zip.py: requests GET Range, ZIP localheader, deflate raw, comprobar CRC central'})
 offset+=46+n+x+c
(BASE/'RECIBOS.json').write_text(json.dumps({'version':'1.0.0','nombre':'Extracción puntual ZIP MITECO Regatón','fecha':'2026-10-12','estado':'DIAGNOSTIC','alcance':'Tres miembros PDF, no ZIP completo','origen':'Expediente MITECO DES01/14/39/0001','central_dir_sha256':hashlib.sha256(central).hexdigest(),'sources':records},ensure_ascii=False,indent=2)+'\n')
print([(r['file'],r['uncompressed_bytes'],r['crc32_verified']) for r in records])
