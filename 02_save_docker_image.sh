#!/bin/bash

# --- Configuration ---
DOCKERHUB_USERNAME=troop60wa
NEW_VERSION="latest"
IMAGE_NAME="troop_60_router_image"

# --- Login to Docker Hub ---
docker login

# --- Tag and push image ---
docker tag $IMAGE_NAME:$NEW_VERSION $DOCKERHUB_USERNAME/$IMAGE_NAME:$NEW_VERSION
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:$NEW_VERSION
echo "Deployment complete."
echo "Check https://hub.docker.com/repositories/$DOCKERHUB_USERNAME"
echo "Check https://railway.com/dashboard"
