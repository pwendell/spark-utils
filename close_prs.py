#!/usr/bin/env python

#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Utility for closing pull requests based on github comments. Prints out
# a nice commit message you can push to ASF with 'git commit --allow-empty'.
# Need to set GITHUB_API_TOKEN env var. 

import base64
import json
import os
import re
import sys
import urllib2

# User facing configs
GITHUB_API_BASE = os.environ.get("GITHUB_API_BASE", "https://api.github.com/repos/apache/spark")
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN", "XXX_PUT_TOKEN_HERE_XXX")

CLOSE_REGEX_LIST = [".*mind closing this.*", ".*close this issue.*"]

def get_url(url):
    try:
        request = urllib2.Request(url)
        auth = base64.b64encode("%s:x-oauth-basic" % GITHUB_API_TOKEN)
        request.add_header("Authorization", "Basic %s" % auth)
        return urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print "Unable to fetch URL, exiting: %s" % url
        print e.info()
        sys.exit(-1)

def get_json(urllib_response):
    return json.load(urllib_response)

def get_json_multipage_url(base_url):
    result = []
    has_next_page = True
    page_num = 0
    while has_next_page:
	page = get_url(base_url + "?page=%s&per_page=100" % page_num)
	result = result + get_json(page)

	# Check if there is another page
	link_header = filter(lambda k: k.startswith("Link"), page.info().headers)[0]
	if not "next"in link_header:
	    has_next_page = False
	else:
	    page_num = page_num + 1

    return result

pr_index = get_json_multipage_url(GITHUB_API_BASE + "/pulls") 
print "Fetched %s PR's" % len(pr_index)

to_close = {} # pr num -> closing user
for pr in pr_index:
  print "Checking PR: %s" % pr['number']
  should_close = False

  page_num = 0
  comments = get_json(get_url(pr['comments_url']))
  for comment in comments:
      for close_regex in CLOSE_REGEX_LIST:
          if re.search(close_regex, comment['body'], flags=re.IGNORECASE) is not None:
              print "FOUND A CLOSE!!!!"
              to_close[pr['number']] = comment['user']['login']

print to_close

print "MAINTENANCE: Automated closing of pull requests."
print ""
print "This commit exists to close the following pull requests on Github:"
print ""
for (pr_num, closing_user) in to_close.items():
  print "Closes #%s (close requested by '%s')" % (pr_num, closing_user)
