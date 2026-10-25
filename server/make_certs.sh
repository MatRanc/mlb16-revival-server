#!/bin/sh
# Our own root CA + a server cert for the game's API host. Pass "sha1" to sign with SHA-1 instead.
set -e
export MSYS_NO_PATHCONV=1   # Git Bash on Windows would otherwise turn -subj "/C=..." into a file path
mkdir -p "$(dirname "$0")/certs" && cd "$(dirname "$0")/certs"
MD=${1:-sha256}
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.pem -days 7300 -$MD \
  -subj "/C=US/O=MLB16 Revival/CN=MLB16 Revival Root CA" \
  -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign"
openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj "/CN=mlb16.api.wwsga.me"
printf "subjectAltName=DNS:mlb16.api.wwsga.me,DNS:production.mlb16.online.scea.com\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n" > server.ext
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out server.pem -days 3650 -$MD -extfile server.ext
rm server.csr server.ext
echo "made certs ($MD)"
