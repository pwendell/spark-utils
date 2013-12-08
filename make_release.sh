## Quick and dirty script to package up release tarballs for Spark.
## This should be copied into and run in an otherwise empty directory.
## This script assumes that a release has already been cut using the
## Maven release plug-in. 

# Would be nice to add:
  # Re-write in Python
  # Send output to stderr and have useful logging in stdout
  # Have this call the maven release plugin to actually create
  #  releases

RELEASE_TAG=fba8738
RELEASE_VERSION=0.8.1-incubating
RC_NAME=rc1
USER_NAME=pwendell # user with account at people.apache.org

set -e

# Base directory for releases
git clone https://git-wip-us.apache.org/repos/asf/incubator-spark.git
cd incubator-spark
git checkout --force $RELEASE_TAG
rm .gitignore
rm -rf .git
cd ..

# Source release
cp -r incubator-spark spark-$RELEASE_VERSION
tar cvzf spark-$RELEASE_VERSION.tgz spark-$RELEASE_VERSION
gpg --armour --output spark-$RELEASE_VERSION.tgz.asc --detach-sig spark-$RELEASE_VERSION.tgz
gpg --print-md MD5 spark-$RELEASE_VERSION.tgz > spark-$RELEASE_VERSION.tgz.md5
gpg --print-md SHA512 spark-$RELEASE_VERSION.tgz > spark-$RELEASE_VERSION.tgz.sha
rm -rf spark-$RELEASE_VERSION

# Hadoop 1 release
cp -r incubator-spark spark-$RELEASE_VERSION-bin-hadoop1
cd spark-$RELEASE_VERSION-bin-hadoop1
export MAVEN_OPTS="-Xmx3g -XX:MaxPermSize=1g -XX:ReservedCodeCacheSize=1g"
mvn -Dhadoop.version=1.0.4 -DskipTests clean package
find . -name test-classes -type d | xargs rm -rf
find . -name classes -type d | xargs rm -rf
cd ..
tar cvzf spark-$RELEASE_VERSION-bin-hadoop1.tgz spark-$RELEASE_VERSION-bin-hadoop1
gpg --armour --output spark-$RELEASE_VERSION-bin-hadoop1.tgz.asc --detach-sig spark-$RELEASE_VERSION-bin-hadoop1.tgz
gpg --print-md MD5 spark-$RELEASE_VERSION-bin-hadoop1.tgz > spark-$RELEASE_VERSION-bin-hadoop1.tgz.md5
gpg --print-md SHA512 spark-$RELEASE_VERSION-bin-hadoop1.tgz > spark-$RELEASE_VERSION-bin-hadoop1.tgz.sha
rm -rf spark-$RELEASE_VERSION-bin-hadoop1

# Hadoop 2 release
cp -r incubator-spark spark-$RELEASE_VERSION-bin-cdh4
cd spark-$RELEASE_VERSION-bin-cdh4
export MAVEN_OPTS="-Xmx3g -XX:MaxPermSize=1g -XX:ReservedCodeCacheSize=1g"
mvn -Dhadoop.version=2.0.0-mr1-cdh4.2.0 -DskipTests package
find . -name test-classes -type d | xargs rm -rf
find . -name classes -type d | xargs rm -rf
cd ..
tar cvzf spark-$RELEASE_VERSION-bin-cdh4.tgz spark-$RELEASE_VERSION-bin-cdh4
gpg --armour --output spark-$RELEASE_VERSION-bin-cdh4.tgz.asc --detach-sig spark-$RELEASE_VERSION-bin-cdh4.tgz
gpg --print-md MD5 spark-$RELEASE_VERSION-bin-cdh4.tgz > spark-$RELEASE_VERSION-bin-cdh4.tgz.md5
gpg --print-md SHA512 spark-$RELEASE_VERSION-bin-cdh4.tgz > spark-$RELEASE_VERSION-bin-cdh4.tgz.sha
rm -rf spark-$RELEASE_VERSION-bin-cdh4

# Copy data
ssh $USER_NAME@people.apache.org mkdir /home/USER_NAME/public_html/spark-$RELEASE_VERSION-$RC_NAME
scp spark* USER_NAME@people.apache.org:/home/USER_NAME/public_html/spark-$RELEASE_VERSION-$RC_NAME/

# Docs
cd incubator-spark
cd docs
jekyll build
ssh USER_NAME@people.apache.org mkdir /home/USER_NAME/public_html/spark-$RELEASE_VERSION-$RC_NAME-docs
scp -r _site/* USER_NAME@people.apache.org:/home/USER_NAME/public_html/spark-$RELEASE_VERSION-$RC_NAME-docs/
