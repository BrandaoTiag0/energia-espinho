import requests

BASE = ("https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
        "consumos_horario_codigo_postal/records")

def pedir(where=None, ordem=None):
    params = {"limit": 1}
    if where:
        params["where"] = where
    if ordem:
        params["order_by"] = ordem
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

print("Registos no conjunto:", pedir()["total_count"])
print("Registos do 4500:", pedir(where='codigo_postal="4500"')["total_count"])

for nome, where in [("conjunto todo", None), ("4500", 'codigo_postal="4500"')]:
    primeiro = pedir(where, "datahora asc")["results"]
    ultimo = pedir(where, "datahora desc")["results"]
    if primeiro and ultimo:
        print(nome, "- primeiro:", primeiro[0]["dt_consumo"], primeiro[0]["hr_consumo"],
              "| último:", ultimo[0]["dt_consumo"], ultimo[0]["hr_consumo"])
    else:
        print(nome, "- sem registos")
