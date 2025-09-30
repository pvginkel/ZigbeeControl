mkdir -p $(pwd)/tmp

NAME=electronics-inventory
ARGS="
    --network host
    -e APP_TABS_CONFIG=/data/tabs.yaml
    -v $(pwd)/test/tabs.yaml:/data/tabs.yaml
    -v $HOME/.kube:/root/.kube
"
