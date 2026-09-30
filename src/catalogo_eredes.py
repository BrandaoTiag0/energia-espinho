import requests

BASE = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets"
PALAVRAS = ("horar", "postal", "diari", "concelho", "municip", "freguesia", "quarto")

todos = []
offset = 0
while True:
    r = requests.get(BASE, params={"limit": 100, "offset": offset}, timeout=60)
    r.raise_for_status()
    dados = r.json()
    lote = dados.get("results", [])
    todos.extend(lote)
    offset += 100
    if not lote or offset >= dados.get("total_count", 0):
        break

print("Conjuntos no portal:", len(todos))
for d in todos:
    meta = (d.get("metas") or {}).get("default") or {}
    id_ = d.get("dataset_id", "")
    titulo = meta.get("title", "")
    if any(p in (id_ + " " + titulo).lower() for p in PALAVRAS):
        print(id_, "|", titulo, "| dados:", str(meta.get("data_processed", ""))[:10])
