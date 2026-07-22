import httpx
import json
from backend.worker.S0_Extractor.github.queries import PROJECT_ITEMS_USER_QUERY

resp = httpx.post(
    'https://api.github.com/graphql', 
    json={'query': PROJECT_ITEMS_USER_QUERY, 'variables': {'org': 'Caserefro', 'projectNumber': 1}}, 
    headers={'Authorization': 'Bearer '}
)
print(json.dumps(resp.json(), indent=2))
