import httpx

def main():
    pat = ""
    repo = "Caserefro/TestRepo"
    
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # We want to merge PR #8 (Clean) and PR #9 (Rework Loop)
    prs_to_merge = [8, 9]
    
    for pr_num in prs_to_merge:
        print(f"Merging PR #{pr_num}...")
        resp = httpx.put(
            f"https://api.github.com/repos/{repo}/pulls/{pr_num}/merge",
            headers=headers,
            json={
                "commit_title": f"Merge PR #{pr_num}",
                "merge_method": "merge"
            }
        )
        
        if resp.status_code == 200:
            print(f"Successfully merged PR #{pr_num}!")
        else:
            print(f"Failed to merge PR #{pr_num}: {resp.text}")

if __name__ == "__main__":
    main()
