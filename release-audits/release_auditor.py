# Audits a Spark release published to an Apache home directory.
# Requires GPG and Maven.
# usage:
#   python release_auditor.py 2>stderr_data

import os
import re
import shutil
import subprocess
import sys
import time
import urllib2

RELEASE_URL = "http://people.apache.org/~pwendell/spark-0.8.0-incubating-rc5/files"
RELEASE_KEY = "9E4FE3AF"
WORK_DIR = "/tmp/audit_%s" % int(time.time()) 
MAVEN_CMD = "mvn"
GPG_CMD = "gpg"

# Track failures
failures = []

def delete_work_dir_with_prompt():
  print "OK to delete scratch directory '%s'? (y/N): " % WORK_DIR
  response = raw_input()
  if response == "y":
    shutil.rmtree(WORK_DIR) 

def run_cmd(cmd):
  print >> sys.stderr, "Running command: %s" % cmd
  try:
    return subprocess.check_call(cmd, shell=True, stdout=sys.stderr)
  except Exception as e:
    print "Command failed: %s" % cmd
    print "Exception: %s" % e
    delete_work_dir_with_prompt()
    sys.exit(-1)

def run_cmd_with_output(cmd):
  print >> sys.stderr, "Running command: %s" % cmd
  return subprocess.check_output(cmd, shell=True)

def test(bool, str):
  if bool:
    return passed(str)
  failed(str)

def passed(str):
  print "[PASSED] %s" % str

def failed(str):
  failures.append(str)
  print "[FAILED] %s" % str

def get_url(url):
  return urllib2.urlopen(url).read()

if os.path.exists(WORK_DIR):
  print "Working directory '%s' already exists" % WORK_DIR
  sys.exit(-1)
os.mkdir(WORK_DIR)
os.chdir(WORK_DIR)

index_page = get_url(RELEASE_URL)
artifact_regex = r = re.compile("<a href=\"(.*.tgz)\">")
artifacts = r.findall(index_page)

for artifact in artifacts:
  print "==== Verifying download integrity for artifact: %s ====" % artifact

  artifact_url = "%s/%s" % (RELEASE_URL, artifact)
  run_cmd("wget %s" % artifact_url)

  key_file = "%s.asc" % artifact
  run_cmd("wget %s/%s" % (RELEASE_URL, key_file))

  run_cmd("wget %s%s" % (artifact_url, ".sha"))

  # Verify signature
  run_cmd("%s --recv-key %s" % (GPG_CMD, RELEASE_KEY))
  run_cmd("%s %s" % (GPG_CMD, key_file))
  passed("Artifact signature verified.")

  # Verify md5
  my_md5 = run_cmd_with_output("%s --print-md MD5 %s" % (GPG_CMD, artifact)).strip()
  release_md5 = get_url("%s.md5" % artifact_url).strip()
  test(my_md5 == release_md5, "Artifact MD5 verified.")

  # Verify sha
  my_sha = run_cmd_with_output("%s --print-md SHA512 %s" % (GPG_CMD, artifact)).strip()
  release_sha = get_url("%s.sha" % artifact_url).strip()
  test(my_sha == release_sha, "Artifact SHA verified.")

  # Verify Apache required files
  dir_name = "-".join(artifact.split("-")[:-1]) # get rid of "-rcX.tgz"
  run_cmd("tar xvzf %s" % artifact)
  base_files = os.listdir(dir_name)
  test("CHANGES.txt" in base_files, "Tarball contains CHANGES.txt file")
  test("NOTICE" in base_files, "Tarball contains NOTICE file")
  test("LICENSE" in base_files, "Tarball contains LICENSE file")
 
  os.chdir(os.path.join(WORK_DIR, dir_name))
  readme = "".join(open("README.md").readlines())
  disclaimer_part = "is an effort undergoing incubation"
  test(disclaimer_part in readme, "README file contains disclaimer")
  os.chdir(WORK_DIR)
 
for artifact in artifacts:
  print "==== Verifying build and tests for artifact: %s ====" % artifact
  os.chdir(os.path.join(WORK_DIR, dir_name))

  os.environ["MAVEN_OPTS"] = "-Xmx3g -XX:MaxPermSize=1g -XX:ReservedCodeCacheSize=1g"
  # Verify build
  print "==> Running build"
  run_cmd("sbt/sbt assembly")
  passed("sbt build successful")
  run_cmd("%s package -DskipTests" % MAVEN_CMD)    
  passed("Maven build successful")

  # Verify tests
  print "==> Performing unit tests"
  run_cmd("%s test" % MAVEN_CMD)
  passed("Tests successful")
  os.chdir(WORK_DIR)

delete_work_dir_with_prompt()

if len(failures) == 0:
  print "ALL TESTS PASSED"
else:
  print "SOME TESTS DID NOT PASS"
  for f in failures:
    print f
