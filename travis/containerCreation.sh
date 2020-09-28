#!/usr/bin/env bash

# fail fast settings from https://dougrichardson.org/2018/08/03/fail-fast-bash-scripting.html
set -eov pipefail

# obtain current repository name
REPO_LOCAL_PATH=`git rev-parse --show-toplevel`
REPO_NAME=`basename $REPO_LOCAL_PATH`

./gradlew shadowJar

# Check presence of environment variables
TRAVIS_BUILD_NUMBER="${TRAVIS_BUILD_NUMBER:-0}"

# Create a Docker image and tag it as 'travis_<build number>'
buildTag=travis_$TRAVIS_BUILD_NUMBER # We use a temporary build number for tagging, since this is a transient artefact

docker build -t eoepca/${REPO_NAME} .
docker tag eoepca/${REPO_NAME} eoepca/${REPO_NAME}:$buildTag # Tags container in EOEPCA repository with buildTag

if [ -n "${DOCKER_USERNAME}" -a -n "${DOCKER_PASSWORD}" ]
then
  echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  docker push eoepca/${REPO_NAME}:$buildTag   # defaults to docker hub EOEPCA repository
else
  echo "WARNING: No credentials - Cannot push to docker hub"
fi
