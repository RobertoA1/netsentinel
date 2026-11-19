"""Descarga de Crossref los metadatos de cada DOI (cliente genérico; no se envía información del proyecto)."""
import json, urllib.request, urllib.parse, time
dois = json.load(open('dois.json'))
out = {}
for k, d in dois.items():
    url = "https://api.crossref.org/works/" + urllib.parse.quote(d)
    req = urllib.request.Request(url, headers={"User-Agent": "reference-checker/1.0"})
    for i in range(5):
        try:
            r = urllib.request.urlopen(req, timeout=40); out[k] = {"status": r.status, "msg": json.load(r)["message"]}; break
        except urllib.error.HTTPError as e:
            out[k] = {"status": e.code}; 
            if e.code == 404: break
            time.sleep(4*(i+1))
        except Exception as e:
            out[k] = {"status": str(e)}; time.sleep(4*(i+1))
    print(k, out[k]["status"])
json.dump(out, open('crossref_raw.json', 'w'), ensure_ascii=False, indent=1)
