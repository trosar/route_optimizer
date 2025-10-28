#!/bin/bash

# --- Configuration ---
NEW_VERSION="latest"
IMAGE_NAME="troop_60_router_image"
CONTAINER_NAME="troop_60_router"
PORT_MAPPING="5100:5000"

# --- Check if env vars are setup (only for local) ---
if [ ! -f env_vars.env ] || [ $(wc -c < env_vars.env) -lt 100 ]; then
    echo "
APP_PASSWORD=set_value_here
SHEET_CSV_URL=set_google_sheets_url_here
" > env_vars.env 
    echo "Please set the password and sheet CSV URL in the "
    echo "env_vars.env"
    echo "file and then re-run this command"
    exit 1
fi

# --- Deployment ---
echo "Building new image: $IMAGE_NAME:$NEW_VERSION"
docker build -t "$IMAGE_NAME:$NEW_VERSION" .

echo "Stopping and removing old container: $CONTAINER_NAME"
docker rm -f "$CONTAINER_NAME"

echo "Starting new container: $CONTAINER_NAME with image $IMAGE_NAME:$NEW_VERSION"
docker run --env-file env_vars.env -d -p "$PORT_MAPPING" --name "$CONTAINER_NAME" --restart always "$IMAGE_NAME:$NEW_VERSION"

echo "New container deployed. Check logs with 'docker logs $CONTAINER_NAME'."

echo "Pruning old, unused images..."
docker image prune -f

echo "Build complete."