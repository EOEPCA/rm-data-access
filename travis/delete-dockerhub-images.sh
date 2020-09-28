#!/bin/bash
# Based on kizbitz/dockerhub-v2-api-organization.sh at https://gist.github.com/kizbitz/175be06d0fbbb39bc9bfa6c0cb0d4721

# Example for the Docker Hub V2 API
# Returns all images and tags associated with a Docker Hub organization account.
# Requires 'jq': https://stedolan.github.io/jq/

# set username, password, and organization
ORG="eoepca"
if [ -z "$DOCKER_USERNAME" ]; then
  echo "Please enter your Dockerhub account name for organization $ORG: "
  read -r USERNAME
  export DOCKER_USERNAME=${USERNAME}
fi
if [ -z "$DOCKER_PASSWORD" ]; then
  echo "Please enter your Dockerhub password for accout $DOCKER_USERNAME, part of $ORG organization:"
  read -r PASSWORD
  export DOCKER_PASSWORD=${PASSWORD}
fi

ALL=false
while [ "$1" != "" ]; do
    case $1 in
        -a | --all )            ALL=true
                                ;;
        -h | --help )           #usage
                                exit
                                ;;
        * )                     #usage
                                exit 1
    esac
    shift
done

# -------

set -e

# get token
echo "Retrieving token ..."
TOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"username": "'${DOCKER_USERNAME}'", "password": "'${DOCKER_PASSWORD}'"}' https://hub.docker.com/v2/users/login/ | jq -r .token)

# get list of repositories
echo "Retrieving repository list ..."
REPO_LIST=$(curl -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/?page_size=200 | jq -r '.results|.[]|.name')

# obtain current repository name
REPO_LOCAL_PATH=`git rev-parse --show-toplevel`
REPO_NAME=`basename $REPO_LOCAL_PATH`

# delete images and/or tags
echo "Deleting images and tags for organization: ${ORG}"

echo $REPO_LIST
for i in ${REPO_LIST}
do
  if [ "$i" = "$REPO_NAME" ] || [ "$ALL" = "true" ]; then
    echo "\nEntering repository $i"

    # Delete by tags starting with "travis_"
    IMAGE_TAGS=$(curl -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${i}/tags/?page_size=300 | jq -r '.results|.[]| select (.name | startswith("travis_")) | .name')
    for j in ${IMAGE_TAGS}
    do
      echo -n "  - ${j} ... "
      curl -X DELETE -s -H "Authorization: JWT ${TOKEN}" https://hub.docker.com/v2/repositories/${ORG}/${i}/tags/${j}/
      echo "DELETED"
    done
  fi
done

echo "\nFinished"