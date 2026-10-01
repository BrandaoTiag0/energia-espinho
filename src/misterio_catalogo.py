"""Mystery, step 1: which E-Redes datasets could explain the single-rate jump?

Lists every dataset in the E-Redes Open Data catalogue whose title or id
mentions tariffs, installations, meters, clients or readings, with its columns.
Only the Python standard library is used.

Usage: py src/misterio_catalogo.py
"""
import json
import urllib.request

CATALOG = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets"
KEYWORDS = ["tarif", "instala", "contador", "cliente", "leitura", "cpe", "smart", "inteligente", "estimad"]


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "energia-espinho/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


datasets = []
offset = 0
while True:
    page = get(f"{CATALOG}?limit=100&offset={offset}")
    datasets += page.get("results", [])
    offset += 100
    if offset >= page.get("total_count", 0):
        break

print("Datasets in the catalogue:", len(datasets))
print()

for d in datasets:
    dataset_id = d.get("dataset_id", "")
    title = ((d.get("metas") or {}).get("default") or {}).get("title", "")
    text = (dataset_id + " " + title).lower()
    if not any(k in text for k in KEYWORDS):
        continue
    print("=" * 70)
    print(title)
    print("id:", dataset_id)
    for f in d.get("fields", []):
        print(f"   {f.get('name', '')}  ({f.get('type', '')})  {f.get('label', '')}")
    print()
