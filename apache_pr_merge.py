#!/usr/bin/python

# Utility for creating well-formed pull request merges and pushing them to Apache.
#   usage: ./apache-pr-merge.py    (see config env vars below)
#
# This utility assumes you already have local a Spark git folder and that you
# have added remotes corresponding to both (i) the github apache Spark 
# mirror and (ii) the apache git repo.

import json
import os
import subprocess
import sys
import tempfile
import urllib2

# Location of your Spark git development area
SPARK_HOME =       os.environ.get("SPARK_HOME", "/home/patrick/Documents/spark")
# Remote name which points to the Gihub site
PR_REMOTE_NAME =   os.environ.get("PR_REMOTE_NAME", "apache-github")
# Remote name which points to Apache git
PUSH_REMOTE_NAME = os.environ.get("PUSH_REMOTE_NAME", "apache")

GIT_API_BASE = "https://api.github.com/repos/apache/incubator-spark"

def get_json(url):
  try:
    return json.load(urllib2.urlopen(url))
  except urllib2.HTTPError as e:
    print "Unable to fetch URL, exiting: %s" % url
    sys.exit(-1)

def fail(msg):
  print msg
  sys.exit(-1)

def run_cmd(cmd):
  subprocess.check_call(cmd.split(" "), shell=True)

def continue_maybe(prompt):
  result = raw_input("\n%s (y/n): " % prompt)
  if result.lower() != "y":
    fail("Okay, exiting")

pr_num = raw_input("Which pull request would you like to merge? (e.g. 34): ")
pr = get_json("%s/pulls/%s" % (GIT_API_BASE, pr_num))

if  pr["merged"] == True:
  fail("Pull request %s has already been merged" % pr_num)

if bool(pr["mergeable"]) == False:
  fail("Pull request %s is not mergeable in its current form" % pr_num)

url = pr["url"]
title = pr["title"]
body = pr["body"]
target_ref = pr["base"]["ref"]
user_login = pr["user"]["login"]
base_ref = pr["head"]["ref"]
pr_repo_desc = "%s/%s" % (user_login, base_ref)

print ("\n=== Pull Request #%s ===" % pr_num)
print("title\t%s\nsource\t%s\ntarget\t%s\nurl\t%s" % (
  title, pr_repo_desc, target_ref, url))
continue_maybe("Proceed with merging pull request #%s?" % pr_num)

os.chdir(SPARK_HOME)

pr_branch_name = "MERGE_PR_%s" % pr_num
target_branch_name = "MERGE_PR_%s_%s" % (pr_num, target_ref.upper())
run_cmd("git fetch %s pull/%s/head:%s" % (PR_REMOTE_NAME, pr_num, pr_branch_name))
run_cmd("git fetch %s %s:%s" % (PUSH_REMOTE_NAME, target_ref, target_branch_name))
run_cmd("git checkout %s" % target_branch_name)

merge_message = "Merge pull request #%s from %s\n\n%s\n\n%s" % (pr_num, pr_repo_desc, title, body)
# This is a bit of a hack to get the merge messages with linebreaks to format correctly
merge_message_parts = merge_message.split("\n\n")
merge_message_flags = " ".join(['-m "%s"' % p for p in merge_message_parts])

run_cmd('git merge %s %s --no-ff' % (pr_branch_name, merge_message_flags))

continue_maybe("Merge complete (local ref %s). Push to %s?" % (
  target_branch_name, PUSH_REMOTE_NAME))

run_cmd('git push %s %s:%s' % (PUSH_REMOTE_NAME, target_branch_name, target_ref))

run_cmd("git checkout @{-1}")
run_cmd("git branch -D %s" % pr_branch_name)
run_cmd("git branch -D %s" % target_branch_name)
print("Pull request #%s merged!" % pr_num)
