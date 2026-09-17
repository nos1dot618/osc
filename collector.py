#!/usr/bin/env python3

"""
Generate data.json for the static site.

Environment:
  USERNAME      GitHub username (default: nos1dot618)
  GITHUB_TOKEN  GitHub token used only by the collector
  OUTPUT        output path (default: data.json)

The collector includes:
  - pull requests
  - pull request reviews
  - issues
  - commits

Events whose repository owner is USERNAME are excluded.
"""

# pylint: disable=missing-function-docstring

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API = "https://api.github.com/graphql"
USERNAME = os.environ.get("USERNAME", "nos1dot618")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = Path(os.environ.get("OUTPUT", "data.json"))

if not TOKEN:
    print("error: GITHUB_TOKEN is required", file=sys.stderr)
    sys.exit(1)

QUERY = r"""
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    login
    name
    avatarUrl
    contributionsCollection(from: $from, to: $to) {
      pullRequestContributions(first: 100) {
        nodes {
          occurredAt
          pullRequest {
            title
            url
            state
            repository { nameWithOwner owner { login } }
          }
        }
      }
      issueContributions(first: 100) {
        nodes {
          occurredAt
          issue {
            title
            url
            state
            repository { nameWithOwner owner { login } }
          }
        }
      }
      pullRequestReviewContributions(first: 100) {
        nodes {
          occurredAt
          pullRequest {
            title
            url
            state
            repository { nameWithOwner owner { login } }
          }
          pullRequestReview {
            state
          }
        }
      }
      commitContributionsByRepository(maxRepositories: 100) {
        repository {
          nameWithOwner
          owner { login }
        }
        contributions(first: 100) {
          nodes {
            occurredAt
            commitCount
          }
        }
      }
    }
  }
}
"""


def gh(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = Request(
        API,
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]["user"]


def year_ranges(start_year=2013):
    now = datetime.now(timezone.utc)
    for year in range(start_year, now.year + 1):
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if start > now:
            break
        yield start, min(end, now)


def collect():
    events = []
    own = USERNAME.lower()
    profile = None

    for start, end in year_ranges():
        print(f"info: collecting {start.year}…", flush=True)
        data = gh(
            QUERY,
            {
                "login": USERNAME,
                "from": start.isoformat(),
                "to": end.isoformat(),
            },
        )

        if profile is None:
            profile = {
                "login": data["login"],
                "name": data["name"],
                "avatarUrl": data["avatarUrl"],
            }

        cc = data["contributionsCollection"]

        for node in cc["pullRequestContributions"]["nodes"]:
            pr = node["pullRequest"]
            repo = pr["repository"]
            if repo["owner"]["login"].lower() == own:
                continue
            events.append(
                {
                    "id": f"pr:{pr['url']}:{node['occurredAt']}",
                    "type": "pr",
                    "occurredAt": node["occurredAt"],
                    "title": pr["title"],
                    "url": pr["url"],
                    "repo": repo["nameWithOwner"],
                    "owner": repo["owner"]["login"],
                    "state": pr["state"].lower(),
                }
            )

        for node in cc["issueContributions"]["nodes"]:
            issue = node["issue"]
            repo = issue["repository"]
            if repo["owner"]["login"].lower() == own:
                continue
            events.append(
                {
                    "id": f"issue:{issue['url']}:{node['occurredAt']}",
                    "type": "issue",
                    "occurredAt": node["occurredAt"],
                    "title": issue["title"],
                    "url": issue["url"],
                    "repo": repo["nameWithOwner"],
                    "owner": repo["owner"]["login"],
                    "state": issue["state"].lower(),
                }
            )

        for node in cc["pullRequestReviewContributions"]["nodes"]:
            pr = node["pullRequest"]
            repo = pr["repository"]
            if repo["owner"]["login"].lower() == own:
                continue
            review = node["pullRequestReview"]
            events.append(
                {
                    "id": f"review:{pr['url']}:{node['occurredAt']}",
                    "type": "review",
                    "occurredAt": node["occurredAt"],
                    # pylint: disable=line-too-long
                    "title": f"{review['state'].replace('_', ' ').title()} review on “{pr['title']}”",
                    "url": pr["url"],
                    "repo": repo["nameWithOwner"],
                    "owner": repo["owner"]["login"],
                    "state": review["state"].lower(),
                }
            )

        for group in cc["commitContributionsByRepository"]:
            repo = group["repository"]
            if repo["owner"]["login"].lower() == own:
                continue
            for node in group["contributions"]["nodes"]:
                events.append(
                    {
                        "id": f"commit:{repo['nameWithOwner']}:{node['occurredAt']}",
                        "type": "commit",
                        "occurredAt": node["occurredAt"],
                        "title": (
                            f"{node['commitCount']} commit"
                            f"{'s' if node['commitCount'] != 1 else ''} "
                            f"to {repo['nameWithOwner']}"
                        ),
                        "url": f"https://github.com/{repo['nameWithOwner']}/commits",
                        "repo": repo["nameWithOwner"],
                        "owner": repo["owner"]["login"],
                        "commitCount": node["commitCount"],
                    }
                )

    unique = {event["id"]: event for event in events}
    events = sorted(unique.values(), key=lambda e: e["occurredAt"], reverse=True)

    payload = {
        "schemaVersion": 1,
        "username": USERNAME,
        "policy": {
            "include": ["pull requests", "code reviews", "issues", "commits"],
            "excludeOwnRepositories": True,
            "excludedOwner": USERNAME,
            "visibility": "public",
        },
        "profile": profile,
        "events": events,
    }

    OUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="UTF-8"
    )
    print(f"success: wrote {len(events)} events to {OUT}")


if __name__ == "__main__":
    collect()
