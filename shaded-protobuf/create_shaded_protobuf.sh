#!/bin/bash
SCRATCH_DIR=/tmp/proto-scratch # Should exist and be empty
NEW_PACKAGE_NAME=com.google.protobuf_spark
NEW_PACKAGE_PATH=com/google/protobuf_spark
PROTO_VERSION=2.4.1 # Version to download
NEW_VERSION=2.4.1-shaded

set -e

if [ ! -d "$SCRATCH_DIR" ]; then
  echo "Scratch directory $SCRATCH_DIR does not exist"
  exit -1
fi

if [ "$(ls -A $SCRATCH_DIR)" ]; then
  echo "Scratch directory $SCRATCH_DIR is not empty"
  exit -1
fi

pushd $SCRATCH_DIR

# Download and shade protobuf
wget http://protobuf.googlecode.com/files/protobuf-$PROTO_VERSION.zip
unzip proto*zip
cd protobuf-$PROTO_VERSION/
find . -type f | grep -e pom.xml$ |  xargs -I {} sed -i "s/<groupId>com.google.protobuf<\/groupId>/<groupId>org.spark-project.protobuf<\/groupId>/" {}
find . -type f | grep -e pom.xml$ |  xargs -I {} sed -i "s/$PROTO_VERSION/$NEW_VERSION/" {}
find . -type f | grep -e \.xml$ -e \.java$ -e \.cc$ -e \.h$ -e \.proto$ | grep -v descriptor.pb.cc  |  xargs -I {} sed -i s/com.google.protobuf/$NEW_PACKAGE_NAME/ {}
mkdir -p java/src/main/java/$NEW_PACKAGE_PATH
mv java/src/main/java/com/google/protobuf/* java/src/main/java/$NEW_PACKAGE_PATH
rm -r java/src/test

# Build C++
./configure
make

# Build Java
pushd java
# Add javadoc maven plugin
sed -i "s/<\/project>/<reporting><plugins><plugin><groupId>org.apache.maven.plugins<\/groupId><artifactId>maven-javadoc-plugin<\/artifactId><version>2.9.1<\/version><\/plugin><\/plugins><\/reporting><\/project>/" pom.xml
mvn clean package javadoc:jar

# Source jar
pushd src/main/java
jar -cvf $SCRATCH_DIR/protobuf-java-$NEW_VERSION-sources.jar *
popd
cp target/protobuf-java-$NEW_VERSION-javadoc.jar $SCRATCH_DIR/
cp target/protobuf-java-$NEW_VERSION.jar $SCRATCH_DIR
cp pom.xml $SCRATCH_DIR/protobuf-java-$NEW_VERSION.pom

pushd $SCRATCH_DIR
gpg --sign --detach-sign -a protobuf-java-$NEW_VERSION.jar 
gpg --sign --detach-sign -a protobuf-java-$NEW_VERSION-sources.jar 
gpg --sign --detach-sign -a protobuf-java-$NEW_VERSION-javadoc.jar 
gpg --sign --detach-sign -a protobuf-java-$NEW_VERSION.pom
bundle_jar=$SCRATCH_DIR/protobuf-java-bundle.jar
jar -cvf $bundle_jar *pom *asc *jar
popd

popd
popd

echo "Created bundle jar at $bundle_jar"
