#!/usr/bin/env bash

ORIG_DIR="$(pwd)"
cd "$(dirname "$0")"
BIN_DIR="$(pwd)"

trap "cd '${ORIG_DIR}'" EXIT

# Work in the docs/ directory
cd "${BIN_DIR}/.."

# Set context dependant on whether this script has been invoked by Travis or not

rm -rf output
mkdir -p output

for doc in SDD ICD; do
  # Prepare output/ directory
  cp -r $doc/images output/$doc
  cp -r $doc/stylesheets output/$doc

  # Document Generation - using asciidoctor docker image
  #
  # HTML version
  docker run --rm -v $PWD/$doc:/documents/ -v $PWD/output/$doc:/output --name asciidoc-to-html asciidoctor/docker-asciidoctor asciidoctor -r asciidoctor-diagram -D /output/ index.adoc
  # PDF version
  docker run --rm -v $PWD/$doc:/documents/ -v $PWD/output/$doc:/output --name asciidoc-to-pdf asciidoctor/docker-asciidoctor asciidoctor-pdf -r asciidoctor-diagram -D /output/ index.adoc
done