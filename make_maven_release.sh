#!/bin/bash
# Quick-and-dirty automation of making maven releases. Not robust at all.
# Expects to be run in a totally empty directory.

GIT_USERNAME=pwendell
GIT_PASSWORD=XXX
GIT_TAG=v0.9.0-incubating
GIT_BRANCH=branch-0.9

git clone https://git-wip-us.apache.org/repos/asf/incubator-spark.git -b $GIT_BRANCH
cd incubator-spark
export MAVEN_OPTS="-Xmx3g -XX:MaxPermSize=1g -XX:ReservedCodeCacheSize=1g"

mvn -Phadoop2-yarn -Prepl-bin release:clean

mvn -DskipTests -Darguments='-DskipTests=true -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0' \
  -Dusername=$GIT_USERNAME -Dpassword=$GIT_PASSWORD \
  -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0 \
  -Pyarn -Prepl-bin \
  -Dtag=$GIT_TAG -DautoVersionSubmodules=true \
  --batch-mode release:prepare

mvn -DskipTests -Darguments='-DskipTests=true -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0' \
  -Dhadoop.version=2.2.0 -Dyarn.version=2.2.0 \
  -Pyarn -Prepl-bin \
  release:perform
