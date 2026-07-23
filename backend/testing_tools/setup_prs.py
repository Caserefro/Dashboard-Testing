import httpx
from http_utils import resolve_ssl_verify
import base64
import time

def main():
    pat = ""
    repo = "Caserefro/TestRepo"
    
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Create two more issues with specific labels
    new_issues = [
        {"title": "Backend Processing Bug", "body": "Testing bug SP.", "labels": ["bug"]},
        {"title": "Extra Scope Feature", "body": "Testing additional scope.", "labels": ["additional scope"]}
    ]
    
    # for issue in new_issues:
    #     resp = httpx.post(f"https://api.github.com/repos/{repo}/issues", headers=headers, verify=resolve_ssl_verify(), json=issue)
    #     if resp.status_code == 201:
    #         print(f"Created: {issue['title']} #{resp.json()['number']}")
    #     else:
    #         print(f"Failed to create issue: {resp.text}")

    # 2. To create PRs, we need a branch. We'll get the default branch SHA and branch from it.
    resp = httpx.get(f"https://api.github.com/repos/{repo}/git/refs/heads/main", headers=headers, verify=resolve_ssl_verify())
    if resp.status_code != 200:
        resp = httpx.get(f"https://api.github.com/repos/{repo}/git/refs/heads/master", headers=headers, verify=resolve_ssl_verify())
    
    if resp.status_code != 200:
        print("Repo looks empty. Initializing with a README...")
        content = base64.b64encode(b"# Test Repo\nInitialized for testing.").decode('utf-8')
        httpx.put(
            f"https://api.github.com/repos/{repo}/contents/README.md",
            headers=headers, verify=resolve_ssl_verify(),
            json={
                "message": "Initial commit",
                "content": content
            }
        )
        # Give GitHub a second to create the ref
        time.sleep(2)
        resp = httpx.get(f"https://api.github.com/repos/{repo}/git/refs/heads/main", headers=headers, verify=resolve_ssl_verify())
    
    if resp.status_code != 200:
        print("Still could not find main branch after init. Exiting.")
        return
        
    base_sha = resp.json()["object"]["sha"]
    
    # We will create PRs for #1, #2, #3
    pr_targets = [
        {"issue_number": 1, "title": "Clean First Pass Ticket"},
        {"issue_number": 2, "title": "Rework Loop Ticket"},
        {"issue_number": 3, "title": "Scope Creep Ticket"}
    ]
    
    for target in pr_targets:
        branch_name = f"refs/heads/feature/issue-{target['issue_number']}-{int(time.time())}"
        
        # Create branch
        resp = httpx.post(
            f"https://api.github.com/repos/{repo}/git/refs",
            headers=headers, verify=resolve_ssl_verify(),
            json={"ref": branch_name, "sha": base_sha}
        )
        
        if resp.status_code != 201:
            print(f"Failed to create branch for #{target['issue_number']}: {resp.text}")
            continue
            
        # Create a dummy commit (create a file)
        file_path = f"dummy_file_{target['issue_number']}.txt"
        content = base64.b64encode(b"Dummy content to trigger PR").decode('utf-8')
        resp = httpx.put(
            f"https://api.github.com/repos/{repo}/contents/{file_path}",
            headers=headers, verify=resolve_ssl_verify(),
            json={
                "message": f"Fixes #{target['issue_number']}",
                "content": content,
                "branch": branch_name.replace("refs/heads/", "")
            }
        )
        
        if resp.status_code not in (200, 201):
            print(f"Failed to create commit for #{target['issue_number']}: {resp.text}")
            continue
            
        # Open PR
        resp = httpx.post(
            f"https://api.github.com/repos/{repo}/pulls",
            headers=headers, verify=resolve_ssl_verify(),
            json={
                "title": f"Resolve {target['title']} (PR for #{target['issue_number']})",
                "body": f"This PR fixes #{target['issue_number']}. \n\nWe are using this to test PR metrics and linking.",
                "head": branch_name.replace("refs/heads/", ""),
                "base": "main" # Assuming main
            }
        )
        
        if resp.status_code == 201:
            pr_num = resp.json()['number']
            print(f"Created PR #{pr_num} for Issue #{target['issue_number']}")
            
            # If it's the Rework Loop Ticket, simulate a review requesting changes (a loop)
            if target['issue_number'] == 2:
                print(f"Creating a rework loop (review request) for PR #{pr_num}...")
                httpx.post(
                    f"https://api.github.com/repos/{repo}/pulls/{pr_num}/reviews",
                    headers=headers, verify=resolve_ssl_verify(),
                    json={
                        "body": "This needs more work. Please fix the mock logic.",
                        "event": "REQUEST_CHANGES"
                    }
                )
                # And create a second commit to simulate fixing the review
                content2 = base64.b64encode(b"Fixed the logic").decode('utf-8')
                httpx.put(
                    f"https://api.github.com/repos/{repo}/contents/dummy_file_{target['issue_number']}_v2.txt",
                    headers=headers, verify=resolve_ssl_verify(),
                    json={
                        "message": f"Address review for #{target['issue_number']}",
                        "content": content2,
                        "branch": branch_name.replace("refs/heads/", "")
                    }
                )
                
        else:
            print(f"Failed to create PR for #{target['issue_number']}: {resp.text}")

if __name__ == "__main__":
    main()
