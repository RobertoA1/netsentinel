"""Búsqueda bibliográfica en Crossref (cliente genérico, sin datos del proyecto). Uso: python crossref_search.py "consulta" [n]"""
import sys, json, urllib.parse, urllib.request, time
def search(q, rows=8, since=2021):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({
        "query.bibliographic": q, "rows": rows, "filter": f"from-pub-date:{since}-01-01,type:journal-article",
        "select": "DOI,title,author,container-title,issued,volume,issue,page,article-number,type,is-referenced-by-count"})
    req = urllib.request.Request(url, headers={"User-Agent": "reference-checker/1.0"})
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=40))["message"]["items"]
        except Exception as e:
            time.sleep(3 * (i + 1))
    return []
if __name__ == "__main__":
    for it in search(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8):
        au = it.get("author", [{}])
        a = ", ".join(f"{x.get('family','')}" for x in au[:3])
        print(f"{it['DOI']} | {a} | {it.get('issued',{}).get('date-parts',[[None]])[0][0]} | {(it.get('container-title') or [''])[0][:40]} | {it['title'][0][:110]} | cites={it.get('is-referenced-by-count')}")
