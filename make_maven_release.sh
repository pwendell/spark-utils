#!/bin/bash
# Quick-and-dirty automation of making maven releases. Not robust at all.
# Expects to be run in a totally empty directory.

GIT_USERNAME=pwendell
GIT_PASSWORD=XXX
GIT_TAG=v0.8.1-incubating
GIT_BRANCH=branch-0.8

git clone https://git-wip-us.apache.org/repos/asf/incubator-spark.git -b $GIT_BRANCH
cd incubator-spark
export MAVEN_OPTS="-Xmx3g -XX:MaxPermSize=1g -XX:ReservedCodeCacheSize=1g"

mvn -Phadoop2-yarn -Prepl-bin release:clean

mvn -DskipTests -Dmaven.test.skip=true \
  -Darguments='-DskipTests=true' -Darguments='-Dmaven.test.skip=true' \
  -Dusername=$GIT_USERNAME -Dpassword=$GIT_PASSWORD \
  -Phadoop2-yarn -Prepl-bin \
  -Dtag=$GIT_TAG -DautoVersionSubmodules=true \
  --batch-mode release:prepare

mvn -DskipTests -Dmaven.test.skip=true \
  -Darguments='-DskipTests=true' -Darguments='-Dmaven.test.skip=true' \
  -Phadoop2-yarn -Prepl-bin \
  release:perform
