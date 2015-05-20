#!/bin/sh

# Loads credentials from Jenkins environment in a way that can be passed
# easily to Spark release scripts. Prints out a temporary credential dir for cleanup.
#
# NOTE: This should always be called in a script that destorys the temporary directory.
#
# We assume the following are set in Jenkins password env vars:
# JENKINS_ASF_RSA_KEY
#   generated with 'cat <key-file> | tr "\n" ","' to encode newlines
# JENKINS_GPG_KEY 
#   generated with 'gpg --export-secret-key -a "Your Name" | tr "\n" ","' to encode newlines
# JENKINS_GPG_PASSPHRASE
# JENKINS_ASF_USERNAME
# JENKINS_ASF_PASSWORD

set -e
TMP_DIR_TEMPLATE="jenkins-credentials-XXXXXXXX"
TMP_RSA_KEY_NAME="rsa.tmp"
TMP_GPG_KEY_NAME="gpg.tmp"

basedir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
tmpdir=$(mktemp -d $basedir/$TMP_DIR_TEMPLATE)

pushd $tmpdir
echo "$JENKINS_ASF_RSA_KEY" | tr "," "\n" > $TMP_RSA_KEY_NAME
chmod 700 $TMP_RSA_KEY_NAME
echo "$JENKINS_GPG_KEY" | tr "," "\n" > $TMP_GPG_KEY_NAME
chmod 700 $TMP_GPG_KEY_NAME
export GNUPGHOME=$tmpdir
gpg --allow-secret-key-import --import $TMP_GPG_KEY_NAME
popd

# Set-up env vars needed by Spark release scripts
export GPG_KEY=$tmpdir/$TMP_GPG_KEY_NAME
export GPG_PASSPHRASE=$JENKINS_GPG_PASSPHRASE
export ASF_RSA_KEY=$tmpdir/$TMP_RSA_KEY_NAME
export ASF_USERNAME=$JENKINS_ASF_USERNAME
export ASF_PASSWORD=$JENKINS_ASF_PASSWORD

echo "$tmpdir"
