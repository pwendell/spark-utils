#!/usr/bin/python

# Display participation for each contributor over the course of a release.

# This performs a slightly more elegant version of `git shortlog` where
# each contributor's pull requests (rather than commits) are shown in a 
# group. This is helpful for large releases where merges have happened
# which include hundreds of commits.

# IMPORTANT: This will miss commits that were not merged via pull requests.
#            This should be cross-referenced with `git shortlog` output.

import collections
import os
import subprocess

SPARK_HOME = "/home/patrick/Documents/spark"
OLD_TAG = "v0.7.0"
NEW_TAG = "v0.8.0-incubating"

os.chdir(SPARK_HOME)

# (author name, author e-mail) => [list of PR descriptions]
authors_to_pr = collections.defaultdict(list)

def run_with_output(cmd):
  return subprocess.check_output(cmd, shell=True)

merged_prs = run_with_output('git log --merges %s..%s'
  ' --format="%%h %%f"' % (OLD_TAG, NEW_TAG)).strip().split("\n")

for pr in merged_prs:
  (hsh, subject) = pr.split(" ")
  if "pull-request" not in subject: # Filters out internal merges
    continue

  # Find commits added by the merge
  merge_base = run_with_output("git merge-base %s^1 %s^2" % (hsh, hsh)).strip()
  commits = (run_with_output('git log %s..%s^2 --format="%%h %%ae %%an"' % (merge_base, hsh))
    .strip().split("\n"))
  # Find unique authors in this PR (there may be multiple)
  authors = set(map(lambda x: (x.split(" ")[1], " ".join(x.split(" ")[2:])), commits))
  # Get and format commit body for the PR merge commit
  body = run_with_output('git show %s --format="%%b"' % hsh).replace("\n", " ")[:80]

  for a in authors:
    authors_to_pr[a].append((subject, body, hsh))

for (author, prs) in sorted(authors_to_pr.items(), key=lambda x: x[0][0]):
  (email, name) = author
  print "%s (%s)" % (email, name)
  for pr in prs:
    (subject, body, hsh) = pr
    print "%s [%s] %s" % (body, subject, hsh)
  print ""

print "Total contributors: %s" % len(authors_to_pr)
