#!/bin/bash
# Assumes you've already manually patched and set-up akka
# This just packages up akka in a way that can be uploaded to sonatype

SCRATCH_DIR=/tmp/proto-akka # Should exist and be empty
VERSION_STRING=2.2.3-shaded-protobuf

# TODO: Java 1.5 and other things in pom

set -e

if [ ! -d "$SCRATCH_DIR" ]; then
  echo "Scratch directory $SCRATCH_DIR does not exist"
  exit -1
fi

if [ "$(ls -A $SCRATCH_DIR)" ]; then
  echo "Scratch directory $SCRATCH_DIR is not empty"
  exit -1
fi

OUT_DIR=$SCRATCH_DIR/output
mkdir $OUT_DIR

pushd $SCRATCH_DIR
git clone https://github.com/pwendell/akka.git -b 2.2.3-shaded-proto
pushd akka
sbt akka-actor/package && sbt akka-actor/doc && sbt akka-actor/make-pom
sbt akka-remote/package && sbt akka-remote/doc && sbt akka-remote/make-pom
sbt akka-slf4j/package && sbt akka-slf4j/doc && sbt akka-slf4j/make-pom
sbt akka-zeromq/package && sbt akka-zeromq/doc && sbt akka-zeromq/make-pom

for package in actor remote slf4j zeromq; do
  prefix=akka-$package-$VERSION_STRING
  pushd akka-$package
  package_dir=$OUT_DIR/akka-$package
  mkdir $package_dir
  pushd src/main/scala
  jar -cvf $package_dir/$prefix-sources.jar *
  popd
  pushd target/api
  jar -cvf $package_dir/$prefix-javadoc.jar *
  popd
  pushd target/classes
  jar -cvf $package_dir/$prefix.jar * 
  popd
  cp target/*pom $package_dir
  popd

  pushd $package_dir
    ls *jar *pom | xargs -I {} gpg --sign --detach-sign -a {}
    jar -cvf $prefix-bundle.jar *
  popd
done

popd
popd
