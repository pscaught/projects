#!/bin/bash -i

DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P )
ENV=test_env
cd "${DIR}"
source "${DIR}/${ENV}/bin/activate"

python server.py
