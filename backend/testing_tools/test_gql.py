import httpx
import json
from backend.worker.S0_Extractor.github.queries import PROJECT_ITEMS_USER_QUERY
from http_utils import resolve_ssl_verify

resp = httpx.post(
    'https://api.github.com/graphql', 
    json={'query': PROJECT_ITEMS_USER_QUERY, 'variables': {'org': 'Caserefro', 'projectNumber': 1}}, 
    headers={'Authorization': 'Bearer '},
    verify=resolve_ssl_verify()
)
print(json.dumps(resp.json(), indent=2))
