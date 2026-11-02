#!/usr/bin/env bash
# Check that the three source files in learning/sources match the hashes in SHA256SUMS.
# The files are not stored in this repo. Put your copies in learning/sources/ first.
# Where to get them: the CSV is data.gov.hk dataset `hk-censtatd-spending-spending-data`;
# add the official links for the two guide PDFs in the README before publishing.
set -euo pipefail
cd "$(dirname "$0")/sources"
if [ ! -f SHA256SUMS ]; then echo "SHA256SUMS missing"; exit 1; fi
shasum -a 256 -c SHA256SUMS
