# Audits a Spark release published to an Apache home directory.
# Requires GPG and Maven.
# usage:
#   python release_auditor.py

import os
import re
import shutil
import subprocess
import sys
import time
import urllib2

RELEASE_URL = "http://people.apache.org/~pwendell/spark-0.8.0-incubating-rc6/files"
RELEASE_KEY = "9E4FE3AF"
RELEASE_REPOSITORY = "https://repository.apache.org/content/repositories/orgapachespark-059/"
RELEASE_VERSION = "0.8.0-incubating"
SCALA_VERSION = "2.9.3"
LOG_FILE_NAME = "spark_audit_%s" % time.strftime("%h_%m_%Y_%I_%M_%S")
LOG_FILE = open(LOG_FILE_NAME, 'w')
WORK_DIR = "/tmp/audit_%s" % int(time.time()) 
MAVEN_CMD = "mvn"
GPG_CMD = "gpg"

print "Starting tests, log output in %s. Test results printed below:" % LOG_FILE_NAME

# Track failures
failures = []

def clean_work_files():
  print "OK to delete scratch directory '%s'? (y/N): " % WORK_DIR
  response = raw_input()
  if response == "y":
    shutil.rmtree(WORK_DIR) 
  print "Should I delete the log output file '%s'? (y/N): " % LOG_FILE_NAME
  response = raw_input()
  if response == "y":
    os.unlink(LOG_FILE_NAME)

def run_cmd(cmd, exit_on_failure=True):
  print >> LOG_FILE, "Running command: %s" % cmd
  ret = subprocess.call(cmd, shell=True, stdout=LOG_FILE)
  if ret != 0 and exit_on_failure:
    print "Command failed: %s" % cmd
    clean_work_files()
    sys.exit(-1)
  return ret

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
  print "[**FAILED**] %s" % str

def get_url(url):
  return urllib2.urlopen(url).read()

original_dir = os.getcwd()

modules = ["spark-core", "spark-bagel", "spark-mllib", "spark-streaming",
           "spark-repl"]
modules = map(lambda m: "%s_%s" % (m, SCALA_VERSION), modules)

os.chdir("sbt_build")

# Check for directories that might interfere with tests
local_ivy_spark = "~/.ivy2/local/org/apache/spark"
cache_ivy_spark = "~/.ivy2/cache/org/apache/spark"
local_maven_kafka = "~/.m2/repository/org/apache/kafka"
local_maven_kafka = "~/.m2/repository/org/apache/spark"
def ensure_path_not_present(x):
  if os.path.exists(os.path.expanduser(x)):
    print "Please remove %s, it can interfere with testing published artifacts." % x
    sys.exit(-1)
map(ensure_path_not_present, [local_ivy_spark, cache_ivy_spark, local_maven_kafka])

os.environ["SPARK_VERSION"] = RELEASE_VERSION
os.environ["SPARK_RELEASE_REPOSITORY"] = RELEASE_REPOSITORY

for module in modules:
  os.environ["SPARK_MODULE"] = module
  ret = run_cmd("sbt/sbt clean update", exit_on_failure=False)
  test(ret == 0, "sbt build against '%s' module" % module) 

os.chdir(original_dir)
os.chdir("maven_build")
for module in modules:
  cmd = ('%s --update-snapshots -Dspark.release.repository="%s" -Dspark.version="%s" '
      '-Dspark.module="%s" clean compile' % 
      (MAVEN_CMD, RELEASE_REPOSITORY, RELEASE_VERSION, module))
  ret = run_cmd(cmd, exit_on_failure=False)
  test(ret == 0, "maven build against '%s' module" % module)
os.chdir(original_dir)

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
  run_cmd("%s --keyserver pgp.mit.edu --recv-key %s" % (GPG_CMD, RELEASE_KEY))
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

clean_work_files()

if len(failures) == 0:
  print "ALL TESTS PASSED"
else:
  print "SOME TESTS DID NOT PASS"
  for f in failures:
    print f

os.chdir(original_dir)
