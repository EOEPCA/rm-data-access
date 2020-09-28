#!/usr/bin/env bash

# fail fast settings from https://dougrichardson.org/2018/08/03/fail-fast-bash-scripting.html
set -euov pipefail

# obtain current repository name
REPO_LOCAL_PATH=`git rev-parse --show-toplevel`
REPO_NAME=`basename $REPO_LOCAL_PATH`

# Check presence of environment variables
TRAVIS_BUILD_NUMBER="${TRAVIS_BUILD_NUMBER:-0}"

buildTag=travis_$TRAVIS_BUILD_NUMBER # We use a temporary build number for tagging, since this is a transient artefact

docker run --rm -d -p 8080:7000 --name ${REPO_NAME} eoepca/${REPO_NAME}:${buildTag} # Runs container from EOEPCA repository

sleep 15 # wait until the container is running

curl -s http://localhost:8080/search # trivial smoke test
