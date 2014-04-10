import os
import re
import subprocess
import sys
import time

""" Test basic properties of a cluster configuration.

    This script verifies basic functioning of the Spark/Shark/Hadoop setup in a cluster created
    with the Spark EC2 scripts.
"""

SPARK_SHELL =   "./spark/bin/spark-shell"
PYSPARK_SHELL = "./spark/bin/pyspark"
SHARK_SHELL =   "./shark/shark-withinfo"
HDFS_BIN =      "./ephemeral-hdfs/bin/hadoop dfs"

def run_cmd(cmd, stdin=""):
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, bufsize=0, shell=True)
  time.sleep(0.5)
  (stdout, stderr) = p.communicate(stdin)
  return stdout

run_cmd("%s -rmr /test" % HDFS_BIN)

# Verify ephemeral HDFS configuration matches local disk setup
ephemeral_hdfs_conf = "".join(open("./ephemeral-hdfs/conf/hdfs-site.xml").readlines())
ephemeral_mounts = re.findall("/mnt\d*", ephemeral_hdfs_conf)
for mount in ephemeral_mounts:
  print "Ephemeral mount: %s" % mount
  assert os.path.exists(mount) and os.path.isdir(mount), ("Mount point %s is referenced in "
    "ephemeral HDFS config, but is not a directory." % mount) 
    
# Get the actual mount points 
system_mounts = run_cmd("mount | awk '{print $3}' | grep '/mnt' | sed 's,^\/,,'").strip().split("\n")
for sys_mount in system_mounts:
  path = "/%s" % sys_mount
  assert path in ephemeral_mounts, "Mount point %s not used in ephemeral HDFS config." % path

spark_local_check = \
"""
sc.master.startsWith("local");
exit;
"""
result = run_cmd(SPARK_SHELL, spark_local_check)
assert "res0: Boolean = false" in result, "Spark is running in local mode"

create_kv_data = \
"""
sc.makeRDD(1 to 10000, 100).map(x => "%s,%s".format(x % 10, x)).saveAsTextFile("/test");
exit;
"""
run_cmd(SPARK_SHELL, create_kv_data)

result = run_cmd("%s -ls /test | grep part | wc" % HDFS_BIN)
assert "100" in result, "HDFS files weren't correctly created."

read_kv_data = \
"""
sc.textFile("/test/").count;
exit;
"""
result = run_cmd(SPARK_SHELL, read_kv_data)
assert "res0: Long = 10000" in result, "Spark shell couldn't read HDFS generated data."

group_by_kv_data = \
"""
sc.textFile("/test/").map(l => (l.split(",")(0), l.split(",")(1))).groupByKey.count;
exit;
"""
result = run_cmd(SPARK_SHELL, group_by_kv_data)
assert "res0: Long = 10" in result, "Spark shell couldn't perform group by"

read_kv_data_pyspark = \
"""
sc.textFile("/test").count()
exit()
"""
# DISABLED - need to ask Josh what the right way to do this is
#result = run_cmd(PYSPARK_SHELL, read_kv_data_pyspark)
#assert "10000" in result, "PySpark shell couldn't read HDFS generated data."

create_shark_table = \
"""
./shark/bin/shark-withinfo -e "DROP TABLE IF EXISTS test; CREATE EXTERNAL TABLE test (key STRING, value STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE LOCATION '/test';"
"""
run_cmd(create_shark_table)

read_kv_data_shark = \
"""
./shark/bin/shark-withinfo -e "SELECT count(*) from test;"
"""
result = run_cmd(read_kv_data_shark)
assert "10000" in result, "Shark couldn't read HDFS generated data."

group_by_kv_data_shark = \
"""
./shark/bin/shark-withinfo -e "SELECT COUNT (*) FROM test GROUP BY key;"
"""
result = run_cmd(group_by_kv_data_shark)
occurances = len(re.compile("1000").findall(result))
print result
assert occurances == 10, "Shark could not group by keys correctly"

print "ALL TESTS PASSED"
