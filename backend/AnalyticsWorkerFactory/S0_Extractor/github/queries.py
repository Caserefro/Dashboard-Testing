"""
GraphQL Queries for GitHub Projects V2.
"""

# Query for fetching all project items and their custom fields (Status, Sprint, Estimate)
PROJECT_ITEMS_ORG_QUERY = """
query($org: String!, $projectNumber: Int!, $cursor: String) {
  organization(login: $org) {
    projectV2(number: $projectNumber) {
      items(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          type
          content {
            ... on Issue {
              repository {
                name
                owner { login }
              }
              number
              title
              state
              createdAt
              updatedAt
              labels(first: 10) {
                nodes {
                  name
                }
              }
            }
            ... on PullRequest {
              repository {
                name
                owner { login }
              }
              number
              title
              state
              createdAt
              updatedAt
              mergedAt
              reviews(first: 1) {
                totalCount
              }
              commits {
                totalCount
              }
            }
          }
          fieldValues(first: 20) {
            nodes {
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
            }
          }
        }
      }
    }
  }
}
"""

PROJECT_ITEMS_USER_QUERY = PROJECT_ITEMS_ORG_QUERY.replace("organization", "user")

# Query for fetching the history of a specific Issue (Status changes, Reviews)
ISSUE_TIMELINE_QUERY = """
query($owner: String!, $repo: String!, $issueNumber: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      timelineItems(first: 100, after: $cursor, itemTypes: [PROJECT_V2_ITEM_STATUS_CHANGED_EVENT, CLOSED_EVENT, REOPENED_EVENT, ISSUE_COMMENT]) {
        pageInfo {
          hasNextPage
          endCursor
        }
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
            author {
              login
            }
            bodyText
          }
        }
      }
    }
  }
}
"""

PR_TIMELINE_QUERY = """
query($owner: String!, $repo: String!, $prNumber: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      timelineItems(first: 100, after: $cursor, itemTypes: [REVIEW_REQUESTED_EVENT, REVIEW_DISMISSED_EVENT, READY_FOR_REVIEW_EVENT]) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          __typename
          ... on ReviewRequestedEvent {
            createdAt
          }
          ... on ReviewDismissedEvent {
            createdAt
          }
        }
      }
    }
  }
}
"""

# Query for fetching official ProjectV2 Iteration Field settings (Sprints) directly from GitHub
PROJECT_SPRINT_ITERATIONS_ORG_QUERY = """
query($org: String!, $projectNumber: Int!) {
  organization(login: $org) {
    projectV2(number: $projectNumber) {
      fields(first: 20) {
        nodes {
          ... on ProjectV2IterationField {
            name
            configuration {
              iterations {
                id
                title
                startDate
                duration
              }
              completedIterations {
                id
                title
                startDate
                duration
              }
            }
          }
        }
      }
    }
  }
}
"""

PROJECT_SPRINT_ITERATIONS_USER_QUERY = PROJECT_SPRINT_ITERATIONS_ORG_QUERY.replace("organization", "user")

