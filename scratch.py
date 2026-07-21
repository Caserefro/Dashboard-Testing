import os
import requests
import json
import time

TOKEN = "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"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/vnd.github.v3+json"
}
GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL = "https://api.github.com/repos/Caserefro/Dashboard-Testing/issues"

def run_graphql(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed: {response.status_code} {response.text}")

def create_issue(title, labels):
    payload = {
        "title": title, 
        "body": f"Dummy issue for testing label `{labels[0]}`.",
        "labels": labels
    }
    res = requests.post(REST_URL, headers=HEADERS, json=payload)
    if res.status_code != 201:
        raise Exception(f"Failed to create issue: {res.text}")
    return res.json()["node_id"]

print("Creating labeled issues...")
issue3_node_id = create_issue("Production Bug Ticket", ["bug"])
issue4_node_id = create_issue("Scope Creep Ticket", ["Additional Scope"])
print(f"Issue 3 ID: {issue3_node_id}")
print(f"Issue 4 ID: {issue4_node_id}")

project_id = "PVT_kwHOB8LB7s4Bd_KJ"
status_field_id = "PVTSSF_lAHOB8LB7s4Bd_KJzhYcq18"
options = {'Todo': 'f75ad846', 'In Progress': '47fc9ee4', 'In Review': '589b63a1', 'Merged': '98236657'}

mutation_add = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item { id }
  }
}
"""
item3_id = run_graphql(mutation_add, {"projectId": project_id, "contentId": issue3_node_id})["data"]["addProjectV2ItemById"]["item"]["id"]
item4_id = run_graphql(mutation_add, {"projectId": project_id, "contentId": issue4_node_id})["data"]["addProjectV2ItemById"]["item"]["id"]
print(f"Project Item 3 (Bug) ID: {item3_id}")
print(f"Project Item 4 (Scope) ID: {item4_id}")

mutation_move = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId
    itemId: $itemId
    fieldId: $fieldId
    value: { singleSelectOptionId: $value }
  }) {
    projectV2Item { id }
  }
}
"""

def set_status(item_id, status_name):
    run_graphql(mutation_move, {
        "projectId": project_id,
        "itemId": item_id,
        "fieldId": status_field_id,
        "value": options[status_name]
    })
    print(f"Moved {item_id} to {status_name}")
    time.sleep(1)

print("Moving Issue 3 (Bug)...")
set_status(item3_id, "Todo")
set_status(item3_id, "In Progress")
set_status(item3_id, "In Review")
set_status(item3_id, "Merged")

print("Moving Issue 4 (Additional Scope)...")
set_status(item4_id, "Todo")
set_status(item4_id, "In Progress")

print("All done!")
