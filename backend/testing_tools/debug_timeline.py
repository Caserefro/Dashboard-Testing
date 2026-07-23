import os
import json
import httpx
from datetime import datetime

# Load queries from our extractor
from backend.worker.S0_Extractor.github.queries import PROJECT_ITEMS_USER_QUERY, PROJECT_ITEMS_ORG_QUERY, ISSUE_TIMELINE_QUERY
from backend.worker.S0_Extractor.github.timeline_parser import parse_iso_date
from http_utils import resolve_ssl_verify

def load_api_key():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    key = os.environ.get("GITHUB_TOKEN")
    if not key or key.startswith("ghp_dummy"):
        # Try local config
        config_path = os.path.join(os.path.dirname(__file__), "github_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("api_key")
    return key

def format_date(iso_str):
    if not iso_str:
        return "Unknown"
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def main():
    api_key = load_api_key()
    if not api_key:
        print("Could not find GITHUB_TOKEN in env or github_config.json")
        return
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Same config as run_live_github.py
    owner = "Caserefro"
    project_number = 2
    
    print(f"Fetching Project #{project_number} for {owner}...")
    
    # 1. Fetch tickets
    resp = httpx.post(
        "https://api.github.com/graphql", 
        json={"query": PROJECT_ITEMS_USER_QUERY, "variables": {"org": owner, "projectNumber": project_number}}, 
        headers=headers,
        verify=resolve_ssl_verify()
    )
    data = resp.json()
    
    nodes = data.get("data", {}).get("user", {}).get("projectV2", {}).get("items", {}).get("nodes", [])
    
    for n in nodes:
        content = n.get("content", {})
        item_type = n.get("type", "ISSUE")
        if item_type != "ISSUE":
            continue
            
        issue_num = content.get("number")
        title = content.get("title")
        created_at_str = content.get("createdAt")
        
        repo_node = content.get("repository", {})
        repo_owner = repo_node.get("owner", {}).get("login", owner)
        repo_name = repo_node.get("name", "TestRepo")
        
        # Get Estimate for display
        fields = n.get("fieldValues", {}).get("nodes", [])
        estimate = "None"
        for f in fields:
            if f.get("field", {}).get("name") == "Estimate":
                estimate = f.get("name") or f.get("title") or f.get("number")
                break
                
        print("\n" + "="*60)
        print(f"Ticket #{issue_num}: {title} (Estimate: {estimate})")
        print(f" - Created At: {format_date(created_at_str)}")
        
        # 2. Fetch timeline
        t_resp = httpx.post(
            "https://api.github.com/graphql", 
            json={"query": ISSUE_TIMELINE_QUERY, "variables": {"owner": repo_owner, "repo": repo_name, "issueNumber": issue_num}}, 
            headers=headers,
            verify=resolve_ssl_verify()
        )
        t_data = t_resp.json()
        
        data_node = t_data.get("data") or {}
        repo_node_resp = data_node.get("repository") or {}
        issue_node = repo_node_resp.get("issue") or {}
        timeline_node = issue_node.get("timelineItems") or {}
        t_nodes = timeline_node.get("nodes") or []
        
        if not t_nodes:
            print(" - No status changes found in timeline. Still in initial state.")
            # Calculate time spent in initial state until now
            now_sec = datetime.now().timestamp()
            created_sec = parse_iso_date(created_at_str)
            hours_spent = (now_sec - created_sec) / 3600.0
            print(f" - (Time currently spent in initial state: {hours_spent:.2f} hours)")
            continue
            
        # Parse timeline events chronologically
        events = sorted(t_nodes, key=lambda x: parse_iso_date(x.get("createdAt", "")))
        
        last_ts = parse_iso_date(created_at_str)
        
        for ev in events:
            if ev.get("__typename") != "ProjectV2ItemStatusChangedEvent":
                continue
                
            current_ts = parse_iso_date(ev.get("createdAt", ""))
            raw_status = ev.get("status", "") if isinstance(ev.get("status"), str) else ev.get("status", {}).get("name", "")
            
            hours_diff = (current_ts - last_ts) / 3600.0
            
            print(f" - Moved to '{raw_status}': {format_date(ev.get('createdAt'))}  (Time spent in previous state: {hours_diff:.2f} hours)")
            last_ts = current_ts

        # Time from last event until NOW
        now_sec = datetime.now().timestamp()
        final_hours = (now_sec - last_ts) / 3600.0
        print(f" - (Time spent in CURRENT state until right now: {final_hours:.2f} hours)")

if __name__ == "__main__":
    main()
