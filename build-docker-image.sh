#!/bin/bash

if [[ "$1" =~ [0-9]\.[0-9]\.[0-9] ]]; then
  TAG=$1
  echo "Building with tag: ${TAG}"
else
  echo "Please supply tag"
  exit 1
fi

if [ "${TARGET_ENV}" == "" ] || [ "${REGISTRY_URL}" == "" ]; then
  echo "Environment not set, please run env_setup script in ops folder"
  exit 1
fi

set -e

docker build -t ${REGISTRY_URL}/${GOOGLE_PROJECT_ID}/kauri-importer-backend:${TAG} -f Dockerfile .
docker push ${REGISTRY_URL}/${GOOGLE_PROJECT_ID}/kauri-importer-backend:${TAG}
