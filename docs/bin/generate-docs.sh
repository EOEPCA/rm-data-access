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

# write an index.html for a nicer navigation
cat > output/index.html <<EOL
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="ie=edge" />
    <title>Document</title>
  </head>
  <body>
    <h1>Data Access Service Documentation</h1>
    <div>
      <ul>
        <li><a href="SDD/">Software Design Document</a></li>
        <li><a href="ICD/">Interface Control Document</a></li>
      </ul>
    </div>
  </body>
</html>
EOL

for doc in SDD ICD; do
  # Prepare output/ directory
  mkdir output/$doc
  cp -r $doc/images output/$doc
  cp -r $doc/stylesheets output/$doc

  # Document Generation - using asciidoctor docker image
  #
  # HTML version
  docker run --rm -v $PWD/$doc:/documents/ -v $PWD/output/$doc:/output --name asciidoc-to-html asciidoctor/docker-asciidoctor asciidoctor -r asciidoctor-diagram -D /output/ index.adoc
  # PDF version
  docker run --rm -v $PWD/$doc:/documents/ -v $PWD/output/$doc:/output --name asciidoc-to-pdf asciidoctor/docker-asciidoctor asciidoctor-pdf -r asciidoctor-diagram -D /output/ index.adoc
done