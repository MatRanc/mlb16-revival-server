#!/bin/sh
# Add a root CA to every root CA file in RPCS3's PS3 firmware (original + ours), or put the originals back.
#   ./certswap.sh install [ca-file]    (default: certs/ca.pem next to this script; players use the host's ca.pem)
#   ./certswap.sh restore
# The originals stay in each file, so other games keep working and there's nothing to undo.
# RPCS3 folder: $RPCS3_DIR, else ~/.config/rpcs3 (Linux) or ~/Library/Application Support/rpcs3 (macOS).
set -e
if [ -z "$RPCS3_DIR" ]; then
  RPCS3_DIR="$HOME/.config/rpcs3"
  [ -d "$RPCS3_DIR" ] || RPCS3_DIR="$HOME/Library/Application Support/rpcs3"
fi
CERT="$RPCS3_DIR/dev_flash/data/cert"
BACKUP="$RPCS3_DIR/dev_flash/data/cert.orig"
CA="${2:-$(dirname "$0")/certs/ca.pem}"
[ -d "$CERT" ] || { echo "no $CERT - install the PS3 firmware in RPCS3 first, or set RPCS3_DIR"; exit 1; }
case "$1" in
  install)
    [ -f "$CA" ] || { echo "no CA file at $CA"; exit 1; }
    [ -d "$BACKUP" ] || cp -a "$CERT" "$BACKUP"
    # built from the backup each time, so re-running with another host's CA replaces the old one
    for f in "$BACKUP"/*.cer; do cat "$f" "$CA" > "$CERT/$(basename "$f")"; done
    echo "added $CA to $(ls "$BACKUP" | wc -l) cert files (untouched originals in $BACKUP)";;
  restore)
    [ -d "$BACKUP" ] && cp -a "$BACKUP"/. "$CERT"/ && echo "restored original certs";;
  *) echo "usage: $0 install [ca-file] | restore"; exit 1;;
esac
