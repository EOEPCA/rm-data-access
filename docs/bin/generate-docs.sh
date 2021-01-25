#!/usr/bin/env bash

ORIG_DIR="$(pwd)"
cd "$(dirname "$0")"
BIN_DIR="$(pwd)"

trap "cd '${ORIG_DIR}'" EXIT

# Work in the docs/ directory
cd "${BIN_DIR}/.."

# Set context dependant on whether this script has been invoked by Travis or not

for doc in SDD ICD; do
  cd $doc
  # Prepare output/ directory
  rm -rf output
  mkdir -p output
  cp -r images output
  cp -r stylesheets output

  # Docuemnt Generation - using asciidoctor docker image
  #
  # HTML version
  docker run --rm -v $PWD:/documents/ --name asciidoc-to-html asciidoctor/docker-asciidoctor asciidoctor -r asciidoctor-diagram -D /documents/output index.adoc
  # PDF version
  docker run --rm -v $PWD:/documents/ --name asciidoc-to-pdf asciidoctor/docker-asciidoctor asciidoctor-pdf -r asciidoctor-diagram -D /documents/output index.adoc

  cd -
done