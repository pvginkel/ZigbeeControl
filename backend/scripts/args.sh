mkdir -p $(pwd)/tmp

NAME=zigbee-control
ARGS="
    --network host
    -e FLASK_ENV=development
    -e APP_TABS_CONFIG=/data/tabs.yaml
    -e APP_AUTH_TOKEN=password!
    -v $(pwd)/test/tabs.yaml:/data/tabs.yaml
    -v $HOME/.kube:/root/.kube
"
