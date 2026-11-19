"""Verifica cada DOI contra la API de Crossref y genera refs.json + bitacora (cliente generico, sin datos del proyecto)."""
import json, urllib.request, urllib.parse, html, time, datetime
DOIS = {
 'garcia2014':'10.1016/j.cose.2014.05.011','hevner2004':'10.2307/25148625','peffers2007':'10.2753/MIS0742-1222240302',
 'sommer2010':'10.1109/SP.2010.25','greshake2023':'10.1145/3605764.3623985','bilge2012':'10.1145/2420950.2420969',
 'moustafa2015':'10.1109/MilCIS.2015.7348942','sharafaldin2018':'10.5220/0006639801080116','khraisat2019':'10.1186/s42400-019-0038-7',
 'ring2019':'10.1016/j.cose.2019.06.005','gonzalez2021':'10.3390/s21144759','ullah2018':'10.1016/j.jnca.2017.10.016',
 'liu2024logprompt':'10.1145/3639478.3643108','ma2024llmparser':'10.1145/3597503.3639150','yao2024':'10.1016/j.hcc.2024.100211',
 'mcnemar1947':'10.1007/BF02295996','efron1979':'10.1214/aos/1176344552','wilcoxon1945':'10.2307/3001968','cohen1960':'10.1177/001316446002000104',
 'wilson1927':'10.1080/01621459.1927.10502953','bangor2008':'10.1080/10447310802205776','saito2015':'10.1371/journal.pone.0118432',
 'davis2006':'10.1145/1143844.1143874','tariq2025':'10.1145/3723158','xu2025':'10.1145/3769676','oskera2025':'10.23919/CNSM67658.2025.11297465',
 'borchani2020':'10.1016/S1353-4858(20)30030-1','karlsen2024':'10.1007/s10922-024-09831-x','sarhan2021':'10.1007/s11036-021-01843-0',
 'pietraszek2004':'10.1007/978-3-540-30143-1_6','alahmari2020':'10.1109/CyberSA49311.2020.9139638','rombaldo2026':'10.1093/cybsec/tyag030',
 'woesle2026':'10.1109/ACCESS.2026.3700492','zhan2025':'10.18653/v1/2025.findings-naacl.395','divakaran2025':'10.1109/MSEC.2024.3504512',
 'palma2025':'10.3390/jcp5030055','jiang2026':'10.1109/ISCTIS70043.2026.11572627',
}
out={}; log=[]
for k,d in DOIS.items():
    url='https://api.crossref.org/works/'+urllib.parse.quote(d)
    for _ in range(3):
        try:
            m=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'reference-checker/1.0'}),timeout=30))['message']; break
        except Exception as e: m=None; err=str(e); time.sleep(3)
    if not m: log.append((k,d,url,'FALLO: '+err)); continue
    out[k]=m; log.append((k,d,url,'OK'))
    time.sleep(0.5)
json.dump({'meta':out,'log':log,'date':datetime.date.today().isoformat()},open('refs_raw.json','w'),ensure_ascii=False,indent=1)
print(sum(1 for l in log if l[3]=='OK'),'ok de',len(log)); [print(l) for l in log if l[3]!='OK']
