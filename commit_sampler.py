import argparse
import commands
import os
from Queue import Queue
import subprocess
import threading
import time

desc="""Run performance tests at several points in <target-ref>'s git lineage.

Only merge commits are tested. The number of commits tested is determined by
<sampled_merges>. The domain of merges over which to test is all commits
between <target-ref> and the common ancestor of <target-ref> and
<comparison-ref>. 

For instance:


            0<--0<--0<--0 [comparison-ref]
           /
   0<--0<--0<--0<--0<--0<--0<--0<--0<--0 [target-ref]
           =============================
                   SAMPLE SPACE

Note that <comparison-ref> need not be in a different branch. <comparison-ref>
can be an earlier commit directly in the lineage of <target-ref>.

# Test various points of the master branch since the last release branch
# was forked. 
--target-ref=origin/master
--reference-branch=origin/branch-0.7
--sampled-merges=10

"""

parser = argparse.ArgumentParser(description=desc, 
    formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('--target-ref', help="Ref whose parents will be sampled.",
    default="origin/master")
parser.add_argument('--comparison-ref', help="Ref for determining how far back to sample",
    default="origin/branch-0.7")
parser.add_argument("--spark-dir", help="Spark directory from which to determine git history.",
    default=os.path.join(os.getcwd(), "spark"))
parser.add_argument("--spark-perf-dir", help="Directory containing Spark perf tests.",
    default=os.getcwd())
parser.add_argument("--sampled-merges", help="How many merge commits to sample in target-ref.",
    default=10, type=int)
parser.add_argument("--summary-file", help="File to which summary information is printed.",
    default="results_%s" % time.strftime("%Y-%m-%d_%H-%M-%S"))
parser.add_argument("--test-timeout", help="Timeout in seconds after which tests are considered "
    "failed. ", default="1800", type=int)

args = parser.parse_args()
target_ref = args.target_ref
comparison_ref = args.comparison_ref
spark_dir = args.spark_dir
spark_perf_directory = args.spark_perf_dir
sample_count = args.sampled_merges
summary_file = open(args.summary_file, 'w')

start_dir = os.getcwd()
os.chdir(spark_dir)
config_file_path = os.path.join(spark_perf_directory, "config", "config.py")
initial_config_file = open(config_file_path).readlines()

def run_cmd(cmd):
  (code, result) = commands.getstatusoutput(cmd)
  if code != 0:
    raise Exception(result)
  return result.strip()
  #return subprocess.check_output([cmd], shell=True).strip()

# Port of subprocess.check_call with a timeout. Based on 
# http://stackoverflow.com/questions/1191374/subprocess-with-timeout.
def check_call_with_timeout(cmd, timeout):
    shared_process = Queue(1)
    shared_result = Queue(1)
    def target():
        process = subprocess.Popen(cmd, shell=True)
        shared_process.put(process)
        ret = process.wait()
        shared_result.put(ret)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        shared_process.get().terminate()
        thread.join()
        raise Exception("Command timed out: %s" % cmd)
    else:
        result = shared_result.get()
        if result != 0:
            raise Exception("Command returned non-zero exit (%s): %s" % (result, cmd))

def write_summary(s):
  summary_file.write(s)
  summary_file.flush()

# Determine which merges to test
merge_base = run_cmd("git merge-base %s %s" % (target_ref, comparison_ref))
previous_merge = run_cmd("git log %s --oneline --merges |head -n 1 |cut -d ' ' -f 1 " % merge_base)
all_merges = run_cmd("git log %s..%s --oneline --merges | cut -d ' ' -f 1" % 
    (previous_merge, target_ref)).split("\n")
step_size = len(all_merges) / sample_count
sampled_merges = all_merges[0::step_size]
sampled_merges_with_info = []
for ref in sampled_merges:
    result = run_cmd("git log %s -n 1 --pretty=format:%%s%%+cd" % ref)
    parts = result.split(os.linesep)
    desc = parts[0]
    date = parts[1]
    sampled_merges_with_info = sampled_merges_with_info + [(ref, desc, date)]

# Summarize merge info
write_summary("Sampled %s merges out of %s between %s and %s\n" % (
    len(sampled_merges), len(all_merges), target_ref, comparison_ref))
for (ref, desc, date) in sampled_merges_with_info:
    write_summary("%s\t%s\t%s\n" % (ref, date, desc))

def run_test((ref, desc, date)):
    out_file = open(config_file_path, 'w')
    for line in initial_config_file:
        out_file.write(line)
    out_file.write("COMMIT_ID = '%s'\n" % ref)
    out_file.write("OUTPUT_FILENAME = 'sample_%s_%s'\n" % (date, ref))
    out_file.close()
    check_call_with_timeout("./bin/run", args.test_timeout)

os.chdir(spark_perf_directory)
for (ref, desc, date) in sampled_merges_with_info:
    write_summary("Running test for commit %s\t%s\t%s\n" % (ref, date, desc))
    try:
      run_test((ref, desc, date))
      write_summary("Test for %s succeeded.\n" % ref)
    except Exception as e:
      write_summary("Test for %s failed.\n" % ref)
      write_summary("%s\n" % e)

restored_config_file = open(config_file_path, 'w')
for line in initial_config_file:
  restored_config_file.write(line)
os.chdir(start_dir)
summary_file.close()
