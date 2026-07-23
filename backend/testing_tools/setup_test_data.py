import httpx
import sys

def main():
    pat = ""
    repo = "Caserefro/TestRepo"
    
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    issues_to_create = [
        {"title": "Clean First Pass Ticket", "body": "A normal ticket to test FTY 100%."},
        {"title": "Rework Loop Ticket", "body": "A ticket that will have 2 mock rework loops."},
        {"title": "Scope Creep Ticket", "body": "A ticket with massive mock cycle time to trigger outlier detection."},
        {"title": "Standard Feature Ticket", "body": "Baseline standard ticket."},
        {"title": "Frontend Layout Bug", "body": "A bug ticket to test Bug SP."}
    ]
    
    from http_utils import resolve_ssl_verify
    print(f"Creating issues in {repo}...")
    for issue in issues_to_create:
        resp = httpx.post(f"https://api.github.com/repos/{repo}/issues", headers=headers, json=issue, verify=resolve_ssl_verify())
        if resp.status_code == 201:
            print(f"Created: {issue['title']} (URL: {resp.json()['html_url']})")
        else:
            print(f"Failed to create {issue['title']}: {resp.text}")

if __name__ == "__main__":
    main()
