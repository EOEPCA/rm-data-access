#!/usr/bin/env bash

# fail fast settings from https://dougrichardson.org/2018/08/03/fail-fast-bash-scripting.html
set -eov pipefail

# Check presence of environment variables
TRAVIS_BUILD_NUMBER="${TRAVIS_BUILD_NUMBER:-0}"

# obtain current repository name
REPO_LOCAL_PATH=`git rev-parse --show-toplevel`
REPO_NAME=`basename $REPO_LOCAL_PATH`

# Create a Docker image and tag it as 'travis_<build number>'
buildTag=travis_$TRAVIS_BUILD_NUMBER # We use a temporary build number for tagging, since this is a transient artefact

if [ -n "${DOCKER_USERNAME}" -a -n "${DOCKER_PASSWORD}" ]
then
  echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  docker pull eoepca/${REPO_NAME}:${buildTag}  # have to pull locally in order to tag as a release

  # Tag and push as a Release following the SemVer approach, e.g. 0.1.1-Alpha
  docker tag eoepca/${REPO_NAME}:${buildTag} eoepca/${REPO_NAME}:${TRAVIS_TAG} # This recovers the GitHub release/tag number
  docker push eoepca/${REPO_NAME}:${TRAVIS_TAG}

  # Tag and push as `latest`
  docker tag eoepca/${REPO_NAME}:${buildTag} eoepca/${REPO_NAME}:latest
  docker push eoepca/${REPO_NAME}:latest
else
  echo "WARNING: No credentials - Cannot push to docker hub"
fi
