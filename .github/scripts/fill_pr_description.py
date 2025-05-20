import os
import re
from github import Github

repo_name = os.environ["GITHUB_REPOSITORY"]
pr_number = int(os.environ["PR_NUMBER"])
token = os.environ["GH_TOKEN"]

g = Github(token)
repo = g.get_repo(repo_name)
pr = repo.get_pull(pr_number)


# Pattern: feature/#12345_desc or bugfix/#12345_desc etc.
pattern = re.compile(r'^(feature|bugfix|improvements|chore)/#(\d+)_')

# Find merged branch names by looking for merge commits in the PR
merged_branches = set()
for commit in pr.get_commits():
    parents = commit.parents
    if len(parents) > 1:
        # This is a merge commit, try to find the source branch
        # For each parent except the first (which is usually the base), try to find a PR that was merged
        for parent in parents[1:]:
            # Search for PRs with this parent as the merge commit
            pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')
            for merged_pr in pulls:
                if merged_pr.merge_commit_sha == parent.sha:
                    merged_branches.add(merged_pr.head.ref)
                    break

# Parse branch names for tickets
tickets = {}
for branch in merged_branches:
    m = pattern.match(branch)
    if m:
        header = m.group(1).capitalize()
        ticket = m.group(2)
        tickets.setdefault(header, set()).add(ticket)

# Format the description
desc = ""
for header, nums in tickets.items():
    desc += f"### {header}\n"
    for num in sorted(nums):
        desc += f"- Kunnusta/tickets#{num}\n"
    desc += "\n"

if desc:
    pr.edit(body=desc)
