from fundamentalista import processar_ativo
import json
d = processar_ativo('PETR4')
if d:
    print(json.dumps(d['mercado'], indent=4))
else:
    print("FAILED")
