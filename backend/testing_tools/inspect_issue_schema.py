"""
Schema Inspection Tool (`backend/testing_tools/inspect_issue_schema.py`)

CLI developer tool for inspecting raw GitHub Projects V2 GraphQL schemas.
Pulls a single issue (or first item on a project board) and dumps all project fields,
custom field values, content attributes, and timeline events to `schema_inspection_output.json`.

Use this dump to adapt the Extractor and Normalizer to custom corporate project boards!
"""

import os
import json
import sys
import argparse
import httpx

from http_utils import resolve_ssl_verify


INSPECT_PROJECT_SCHEMA_QUERY = """
query($owner: String!, $projectNumber: Int!) {
  user(login: $owner) {
    projectV2(number: $projectNumber) {
      id
      title
      fields(first: 30) {
        nodes {
          ... on ProjectV2FieldCommon {
            id
            name
            dataType
          }
          ... on ProjectV2SingleSelectField {
            id
            name
            dataType
            options {
              id
              name
            }
          }
          ... on ProjectV2IterationField {
            id
            name
            dataType
            configuration {
              iterations {
                id
                title
                startDate
                duration
              }
            }
          }
        }
      }
      items(first: 5) {
        nodes {
          id
          type
          content {
            ... on Issue {
              number
              title
              state
              createdAt
              updatedAt
              labels(first: 10) { nodes { name } }
              assignees(first: 5) { nodes { login } }
              repository { name owner { login } }
            }
            ... on PullRequest {
              number
              title
              state
              createdAt
              updatedAt
              mergedAt
              repository { name owner { login } }
            }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                field { ... on ProjectV2FieldCommon { name } }
                name
              }
              ... on ProjectV2ItemFieldIterationValue {
                field { ... on ProjectV2FieldCommon { name } }
                title
                startDate
                duration
              }
              ... on ProjectV2ItemFieldNumberValue {
                field { ... on ProjectV2FieldCommon { name } }
                number
              }
              ... on ProjectV2ItemFieldTextValue {
                field { ... on ProjectV2FieldCommon { name } }
                text
              }
              ... on ProjectV2ItemFieldDateValue {
                field { ... on ProjectV2FieldCommon { name } }
                date
              }
            }
          }
        }
      }
    }
  }
}
"""

# Org version fallback
INSPECT_PROJECT_SCHEMA_ORG_QUERY = INSPECT_PROJECT_SCHEMA_QUERY.replace("user(login: $owner)", "organization(login: $owner)")


INSPECT_ISSUE_TIMELINE_QUERY = """
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      number
      title
      state
      createdAt
      timelineItems(first: 50, itemTypes: [PROJECT_V2_ITEM_STATUS_CHANGED_EVENT, CLOSED_EVENT, REOPENED_EVENT, ISSUE_COMMENT]) {
        nodes {
          __typename
          ... on ProjectV2ItemStatusChangedEvent {
            createdAt
            previousStatus
            status
          }
          ... on ClosedEvent {
            createdAt
          }
          ... on ReopenedEvent {
            createdAt
          }
          ... on IssueComment {
            createdAt
            author { login }
            bodyText
          }
        }
      }
    }
  }
}
"""


def load_api_key() -> str:
    """Tries loading token from env or local config."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    key = os.environ.get("GITHUB_TOKEN") or os.environ.get("ATLAS_GITHUB_API_KEY")
    if not key or key.startswith("ghp_dummy"):
        config_path = os.path.join(os.path.dirname(__file__), "github_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("api_key", key)
    return key or ""


def inspect_schema(owner: str, project_number: int, issue_number: int = None, is_org: bool = False, no_ssl: bool = False):
    api_key = load_api_key()
    if not api_key:
        print("[ERROR] No valid GITHUB_TOKEN or github_config.json API key found.", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    ssl_verify = False if no_ssl else resolve_ssl_verify()

    query = INSPECT_PROJECT_SCHEMA_ORG_QUERY if is_org else INSPECT_PROJECT_SCHEMA_QUERY
    variables = {"owner": owner, "projectNumber": project_number}

    print(f"[*] Querying Project #{project_number} schema for '{owner}'...")
    try:
        resp = httpx.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=20.0,
            verify=ssl_verify
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[ERROR] GraphQL request failed: {e}", file=sys.stderr)
        sys.exit(1)

    root = data.get("data", {}).get("organization" if is_org else "user", {}).get("projectV2", {})
    if not root:
        print(f"[ERROR] Could not find ProjectV2 #{project_number} for owner '{owner}'. Output:\n{json.dumps(data, indent=2)}")
        sys.exit(1)

    project_title = root.get("title")
    fields = root.get("fields", {}).get("nodes", [])
    items = root.get("items", {}).get("nodes", [])

    print(f"[SUCCESS] Connected to Project: '{project_title}'")
    print(f" Found {len(fields)} fields and {len(items)} sample items.")

    # Target item selection
    target_item = None
    if issue_number:
        for itm in items:
            cnt = itm.get("content", {})
            if cnt.get("number") == issue_number:
                target_item = itm
                break
    if not target_item and items:
        target_item = items[0]

    timeline_data = None
    if target_item:
        cnt = target_item.get("content", {})
        num = cnt.get("number")
        repo_node = cnt.get("repository", {})
        r_name = repo_node.get("name")
        r_owner = repo_node.get("owner", {}).get("login") or owner

        if num and r_name:
            print(f"[*] Querying timeline for Issue #{num} in {r_owner}/{r_name}...")
            try:
                t_resp = httpx.post(
                    "https://api.github.com/graphql",
                    json={"query": INSPECT_ISSUE_TIMELINE_QUERY, "variables": {"owner": r_owner, "repo": r_name, "issueNumber": num}},
                    headers=headers,
                    timeout=15.0,
                    verify=ssl_verify
                )
                if t_resp.status_code == 200:
                    timeline_data = t_resp.json().get("data", {}).get("repository", {}).get("issue", {})
            except Exception as e:
                print(f"[WARNING] Timeline query skipped: {e}")

    inspection_bundle = {
        "project_metadata": {
            "title": project_title,
            "number": project_number,
            "owner": owner,
            "is_org": is_org
        },
        "available_project_fields": fields,
        "sample_item_inspected": target_item,
        "issue_timeline_inspected": timeline_data
    }

    output_path = os.path.join(os.path.dirname(__file__), "schema_inspection_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(inspection_bundle, f, indent=2)

    print("\n" + "=" * 60)
    print("  PROJECT FIELD SUMMARY (For AI / Normalizer Adaptation)")
    print("=" * 60)
    for fld in fields:
        name = fld.get("name")
        dtype = fld.get("dataType")
        opts = [o.get("name") for o in fld.get("options", [])] if "options" in fld else []
        if dtype == "ITERATION" and "configuration" in fld:
            config = fld.get("configuration", {})
            iters = [f"{i.get('title')} ({i.get('startDate')})" for i in config.get("iterations", [])]
            opt_str = f" Iterations: {iters}"
        else:
            opt_str = f" Options: {opts}" if opts else ""
        print(f" - Field: '{name}' | Type: {dtype}{opt_str}")

    print(f"\n[DONE] Full raw JSON dump saved to:\n  {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Inspect GitHub Project V2 schema and issue fields.")
    parser.add_argument("--owner", type=str, default="Caserefro", help="GitHub Owner (user or org)")
    parser.add_argument("--project", type=int, default=1, help="Project V2 Number")
    parser.add_argument("--issue", type=int, default=None, help="Specific Issue Number (optional)")
    parser.add_argument("--org", action="store_true", help="Set flag if owner is an Organization")
    parser.add_argument("--no-ssl", action="store_true", help="Bypass SSL certificate verification (for corporate proxy)")

    args = parser.parse_args()
    inspect_schema(owner=args.owner, project_number=args.project, issue_number=args.issue, is_org=args.org, no_ssl=args.no_ssl)


if __name__ == "__main__":
    main()
