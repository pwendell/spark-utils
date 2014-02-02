#!/bin/bash

# Quick-and-dirty automation of making maven and binary releases. Not robust at all.
# Publishes releases to Maven and packages/copies binary release artifacts.
# Expects to be run in a totally empty directory.

# Would be nice to add:
  # Re-write in Python
  # Send output to stderr and have useful logging in stdout
  # Have this call the maven release plugin to actually create
  #  releases

GIT_USERNAME=pwendell
GIT_PASSWORD=XXX
GPG_PASSPHRASE=XXX
GIT_BRANCH=branch-0.9
RELEASE_VERSION=0.9.0-incubating
RC_NAME=rc2
USER_NAME=pwendell

set -e

GIT_TAG=v$RELEASE_VERSION

# Artifact publishing

git clone https://git-wip-us.apache.org/repos/asf/incubator-spark.git -b $GIT_BRANCH
cd incubator-spark
export MAVEN_OPTS="-Xmx3g -XX:MaxPermSize=1g -XX:ReservedCodeCacheSize=1g"

mvn -Pyarn release:clean

mvn -DskipTests \
  -Darguments="-DskipTests=true -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0 -Dgpg.passphrase=${GPG_PASSPHRASE}" \
  -Dusername=$GIT_USERNAME -Dpassword=$GIT_PASSWORD \
  -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0 \
  -Pyarn \
  -Dtag=$GIT_TAG -DautoVersionSubmodules=true \
  --batch-mode release:prepare

mvn -DskipTests \
  -Darguments="-DskipTests=true -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0 -Dgpg.passphrase=${GPG_PASSPHRASE}" \
  -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0 \
  -Pyarn \
  release:perform

rm -rf incubator-spark

# Source and binary tarballs
git clone https://git-wip-us.apache.org/repos/asf/incubator-spark.git
cd incubator-spark
git checkout --force $GIT_TAG
release_hash=`git rev-parse HEAD`

rm .gitignore
rm -rf .git
cd ..

cp -r incubator-spark spark-$RELEASE_VERSION
tar cvzf spark-$RELEASE_VERSION.tgz spark-$RELEASE_VERSION
echo $GPG_PASSPHRASE | gpg --passphrase-fd 0 --armour --output spark-$RELEASE_VERSION.tgz.asc \
  --detach-sig spark-$RELEASE_VERSION.tgz
echo $GPG_PASSPHRASE | gpg --passphrase-fd 0 --print-md MD5 spark-$RELEASE_VERSION.tgz > \
  spark-$RELEASE_VERSION.tgz.md5
echo $GPG_PASSPHRASE | gpg --passphrase-fd 0 --print-md SHA512 spark-$RELEASE_VERSION.tgz > \
  spark-$RELEASE_VERSION.tgz.sha
rm -rf spark-$RELEASE_VERSION

make_binary_release() {
  NAME=$1
  MAVEN_FLAGS=$2

  cp -r incubator-spark spark-$RELEASE_VERSION-bin-$NAME
  cd spark-$RELEASE_VERSION-bin-$NAME
  export MAVEN_OPTS="-Xmx3g -XX:MaxPermSize=1g -XX:ReservedCodeCacheSize=1g"
  mvn $MAVEN_FLAGS -DskipTests clean package
  find . -name test-classes -type d | xargs rm -rf
  find . -name classes -type d | xargs rm -rf
  cd ..
  tar cvzf spark-$RELEASE_VERSION-bin-$NAME.tgz spark-$RELEASE_VERSION-bin-$NAME
  echo $GPG_PASSPHRASE | gpg --passphrase-fd 0 --armour \
    --output spark-$RELEASE_VERSION-bin-$NAME.tgz.asc \
    --detach-sig spark-$RELEASE_VERSION-bin-$NAME.tgz
  echo $GPG_PASSPHRASE | gpg --passphrase-fd 0 --print-md \
    MD5 spark-$RELEASE_VERSION-bin-$NAME.tgz > \
    spark-$RELEASE_VERSION-bin-$NAME.tgz.md5
  echo $GPG_PASSPHRASE | gpg --passphrase-fd 0 --print-md \
    SHA512 spark-$RELEASE_VERSION-bin-$NAME.tgz > \
    spark-$RELEASE_VERSION-bin-$NAME.tgz.sha
  rm -rf spark-$RELEASE_VERSION-bin-$NAME
}

make_binary_release "hadoop1"  "-Dhadoop.version=1.0.4"
make_binary_release "cdh4"     "-Dhadoop.version=2.0.0-mr1-cdh4.2.0"
make_binary_release "hadoop2"  "-Pyarn -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0"

# Copy data
echo "Copying release tarballs"
ssh $USER_NAME@people.apache.org \
  mkdir /home/$USER_NAME/public_html/spark-$RELEASE_VERSION-$RC_NAME
rc_folder=spark-$RELEASE_VERSION-$RC_NAME
scp spark* \
  $USER_NAME@people.apache.org:/home/$USER_NAME/public_html/$rc_folder/

# Docs
cd incubator-spark
cd docs
jekyll build
echo "Copying release documentation"
rc_docs_folder=${rc_folder}-docs
rsync -r _site/* $USER_NAME@people.apache.org /home/$USER_NAME/public_html/$rc_docs_folder

echo "Release $RELEASE_VERSION completed:"
echo "Git tag:\t $GIT_TAG"
echo "Release commit:\t $release_hash"
echo "Binary location:\t http://people.apache.org/~$USER_NAME/$rc_folder"
echo "Doc location:\t http://people.apache.org/~$USER_NAME/$rc_docs_folder"
