#!/bin/bash

# Endpoint of the Elasticsearch HELLO message
ELASTIC_ENDPOINT="http://${SEARCH_ES_HOST}:${SEARCH_ES_PORT}/_cluster/health?wait_for_status=yellow"

# Timeout in seconds between two trials
TIMEOUT=10

# Loops until the given URL returns "200 OK"
function loop_until_connected {
    # URL of the endpoint
    url=$1
    # Name of the service
    name=$2
    # Loops until working
    until curl --silent --fail -X GET ${url}; do
        >&2 echo "${name} is unavailable, sleeping ${TIMEOUT} seconds."
        sleep $TIMEOUT
    done
    # Waits the complete startup sleeping another time
    >&2 echo ""
    >&2 echo "${name} is online, sleeping again ${TIMEOUT}s to await complete startup."
    sleep $TIMEOUT
}

loop_until_connected "${ELASTIC_ENDPOINT}" "Elasticsearch"
>&2 echo "All services up and running."

>&2 echo "Loading juridic dictionary from ${SEARCH_JURIDIC_KEYWORDS}"
python /code/load_keywords.py "${SEARCH_JURIDIC_KEYWORDS}"
>&2 echo "Starting the Search Engine"

# Start the backend app
uvicorn app.main:app --host "0.0.0.0" --port "8081"