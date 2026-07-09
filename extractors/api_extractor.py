import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

def fetch_raw_azure_devops(org_url: str, project: str, pat: str) -> dict:
    """
    Fetches raw work items JSON from Azure DevOps REST API (/_apis/wit/wiql).
    In Layer 1, we do ZERO normalization or field filtering; we extract 100% raw JSON.
    """
    url = f"{org_url.rstrip('/')}/{project}/_apis/wit/wiql?api-version=7.1"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DMS-API-Extractor-Docker/1.0"
    }
    if pat:
        import base64
        auth_str = base64.b64encode(f":{pat}".encode('utf-8')).decode('utf-8')
        headers["Authorization"] = f"Basic {auth_str}"
    
    # Example WIQL query fetching recent work items
    payload = json.dumps({
        "query": "SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType] FROM workitems WHERE [System.TeamProject] = @project ORDER BY [System.ChangedDate] DESC"
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode('utf-8'))

def fetch_raw_github_projects(org: str, project_number: int, token: str) -> dict:
    """
    Fetches raw project items JSON from GitHub Projects v2 GraphQL API.
    """
    url = "https://api.github.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DMS-API-Extractor-Docker/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    graphql_query = """
    query($org: String!, $number: Int!) {
      organization(login: $org) {
        projectV2(number: $number) {
          title
          items(first: 50) {
            nodes {
              id
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
                  ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
                  ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
                }
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({
        "query": graphql_query,
        "variables": {"org": org, "number": project_number}
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode('utf-8'))

def run_extraction_test_mode() -> dict:
    """
    Returns high-fidelity raw API payload snapshots if running inside our initial Docker verification check without live tokens.
    Demonstrates exactly what Azure DevOps and GitHub raw API outputs look like when dumped into the volume bridge.
    """
    return {
        "metadata": {
            "extractor_version": "1.0.0-docker",
            "extracted_at_iso": datetime.now(timezone.utc).isoformat(),
            "status": "SUCCESS_RAW_SNAPSHOT",
            "environment": "Docker Sandbox Layer 1"
        },
        "raw_azure_devops_payload": {
            "queryType": "flat",
            "asOf": datetime.now(timezone.utc).isoformat(),
            "workItems": [
                {"id": 1042, "url": "https://dev.azure.com/dms-team/_apis/wit/workItems/1042"},
                {"id": 1043, "url": "https://dev.azure.com/dms-team/_apis/wit/workItems/1043"},
                {"id": 1044, "url": "https://dev.azure.com/dms-team/_apis/wit/workItems/1044"}
            ],
            "rawFieldSamples": {
                "1042": {
                    "System.Id": 1042,
                    "System.Title": "Implement OIDC login for DMS Extractor",
                    "System.State": "Active",
                    "System.WorkItemType": "User Story",
                    "Microsoft.VSTS.Scheduling.StoryPoints": 5.0
                },
                "1043": {
                    "System.Id": 1043,
                    "System.Title": "Fix Burndown Curve calculation rounding",
                    "System.State": "Resolved",
                    "System.WorkItemType": "Bug",
                    "Microsoft.VSTS.Scheduling.StoryPoints": 2.0
                }
            }
        },
        "raw_github_projects_payload": {
            "data": {
                "organization": {
                    "projectV2": {
                        "title": "DMS Sprint Board 2026",
                        "items": {
                            "nodes": [
                                {
                                    "id": "PVTI_lADOB123456",
                                    "fieldValues": {
                                        "nodes": [
                                            {"text": "Refactor Qt FTY Gauge widget", "field": {"name": "Title"}},
                                            {"name": "In Progress", "field": {"name": "Status"}},
                                            {"number": 3.0, "field": {"name": "Story Points"}}
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    }

def main():
    print("==========================================================================")
    print(" 🐳 [DMS Layer 1] API Extractor Docker Container Executing")
    print("==========================================================================")
    
    # 1. Determine output volume path (defaults to /app/raw_data inside container, or ./raw_data on host)
    output_dir = os.environ.get("RAW_DATA_OUTPUT_DIR", "/app/raw_data")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"api_raw_dump_{timestamp_str}.json")

    # 2. Check for live API credentials in Docker environment variables
    azure_pat = os.environ.get("AZURE_DEVOPS_PAT")
    azure_org = os.environ.get("AZURE_ORG_URL")
    azure_proj = os.environ.get("AZURE_PROJECT")
    
    github_token = os.environ.get("GITHUB_TOKEN")
    github_org = os.environ.get("GITHUB_ORG")
    github_proj_num = os.environ.get("GITHUB_PROJECT_NUMBER")

    payload = {}
    if azure_pat and azure_org and azure_proj:
        print(f" -> Fetching live raw Azure DevOps data from: {azure_org}/{azure_proj}")
        try:
            payload["azure_devops"] = fetch_raw_azure_devops(azure_org, azure_proj, azure_pat)
        except Exception as e:
            payload["azure_devops_error"] = str(e)
    
    if github_token and github_org and github_proj_num:
        print(f" -> Fetching live raw GitHub Projects data from org: {github_org}, project: {github_proj_num}")
        try:
            payload["github_projects"] = fetch_raw_github_projects(github_org, int(github_proj_num), github_token)
        except Exception as e:
            payload["github_projects_error"] = str(e)
            
    if not payload:
        print(" -> No live API tokens provided in container environment.")
        print(" -> Generating high-fidelity raw API snapshot for verification & downstream testing...")
        payload = run_extraction_test_mode()

    # 3. Dump 100% Raw JSON Blob to volume bridge
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    print(f" ✅ [SUCCESS] Raw API JSON dumped to volume bridge: {output_file}")
    print(f" 📦 File size: {os.path.getsize(output_file)} bytes")
    print(" -> This file is now ready for ingestion by our sandboxed offline Analytics Worker (--network=none)!")
    print("==========================================================================")

if __name__ == "__main__":
    main()
