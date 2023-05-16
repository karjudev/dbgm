#!/bin/bash

# Endpoint of the Tika HELLO message
TIKA_ENDPOINT="http://${TIKA_HOST}:${TIKA_PORT}/tika"
# Endpoint of the anonymization service
ANONYMIZER_ENDPOINT="http://${ANONYMIZER_HOST}:${ANONYMIZER_PORT}/hello"
# Endpoint of the search engine service
SEARCH_ENGINE_ENDPOINT="http://${SEARCH_HOST}:${SEARCH_PORT}/hello"

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
        >&2 echo "${name} is unavailable at ${url}, sleeping ${TIMEOUT} seconds."
        sleep $TIMEOUT
    done
    # Waits the complete startup sleeping another time
    >&2 echo ""
    >&2 echo "${name} is online, sleeping again ${TIMEOUT}s to await complete startup."
    sleep $TIMEOUT
}

loop_until_connected "${TIKA_ENDPOINT}" "Apache Tika"
loop_until_connected "${ANONYMIZER_ENDPOINT}" "Anonymizer"
#loop_until_connected "${SEARCH_ENGINE_ENDPOINT}" "Search engine"

>&2 echo "All services up and running, starting Streamlit"

# Start the app
streamlit run Home.py