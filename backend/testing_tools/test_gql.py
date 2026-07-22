import httpx
import json
from backend.worker.S0_Extractor.github.queries import PROJECT_ITEMS_USER_QUERY

resp = httpx.post(
    'https://api.github.com/graphql', 
    json={'query': PROJECT_ITEMS_USER_QUERY, 'variables': {'org': 'Caserefro', 'projectNumber': 1}}, 
    headers={'Authorization': 'Bearer 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'}
)
print(json.dumps(resp.json(), indent=2))
