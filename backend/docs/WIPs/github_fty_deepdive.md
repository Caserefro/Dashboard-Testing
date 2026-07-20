# GitHub First-Time Yield (FTY) Deep Dive

## The Problem
Our current `NormalizedTicket` considers an issue completely "clean" (First-Time Yield) if it is marked as `DONE` and `is_first_time_yield=True`. Right now, the GitHub backend JSON simply checks the top-level status or relies on a basic flag. However, real-world development involves **Rework Loops** (e.g. `In Progress -> In Review -> Rejected -> In Progress`).

To calculate an *authentic* First Time Yield, the Extractor (S0) must query the history of the issue to count how many times it was moved backwards in the board.

## Proposed Integration: GitHub Timeline / Events API

To detect rework loops, we will query the GitHub Issue Timeline API or the ProjectV2 Item GraphQL API to analyze state transitions.

### Approach 1: GraphQL ProjectV2 Item Timeline (Preferred)
Since Project ATLAS uses GitHub Projects (V2), we can query the `projectItems` and their historical field value changes.
* **Documentation**: [GitHub GraphQL API - ProjectV2Item](https://docs.github.com/en/graphql/reference/objects#projectv2item)

**Example Query:**
```graphql
query {
  node(id: "PVTI_LADOCyFims4BdqvczgzPhMg") {
    ... on ProjectV2Item {
      fieldValues(first: 20) {
        nodes {
          ... on ProjectV2ItemFieldSingleSelectValue {
            name
            updatedAt
          }
        }
      }
    }
  }
}
```
*Note: GitHub's GraphQL API for historical project board transitions can be notoriously limited. If `fieldValues` does not expose the full chronological history of column changes, we must fallback to Approach 2.*

### Approach 2: REST API - Issue Events (Fallback)
If the project board columns are linked directly to Issue Labels or Issue States (`Open` vs `Closed`), we can use the REST Events API for the underlying issue.
* **Documentation**: [GitHub REST API - List issue events](https://docs.github.com/en/rest/issues/events?apiVersion=2022-11-28#list-issue-events)
* **Endpoint**: `GET /repos/{owner}/{repo}/issues/{issue_number}/events`

**Logic:**
1. S0 Extractor identifies all issues in the board.
2. For each issue, it makes a secondary request to the `/events` endpoint.
3. It parses the events looking for `labeled` / `unlabeled` (if board columns are label-driven) or `moved_columns_in_project` (if supported).
4. **Scoring**: If the sequence of column moves regresses (e.g., column index goes `0 -> 1 -> 2 -> 1`), we flag `is_first_time_yield = False` and increment a `rework_loops` counter.

### Rate Limiting Considerations
GitHub REST API is limited to 5,000 requests per hour. If a board has 300 issues, doing a deep dive on every issue would cost 300 requests. 
**Optimization Strategy**: S0 should *only* deep-dive into issues whose `updatedAt` timestamp is newer than the last synchronized baseline date! (Delta syncing).

## S1 Normalizer Updates
Once S0 extracts the rework loop count:
1. `NormalizedTicket` will have an explicit `rework_loops: int` property.
2. `is_first_time_yield` will strictly be evaluated as `rework_loops == 0`.
