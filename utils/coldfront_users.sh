#!/bin/bash

if [ -z $1 ]; then
    echo "Error: missing POD ID"
    echo "USAGE $0 <POD ID> <Storage Resource>"
    exit 1
fi

if [[ $2 != "Storage2" && $2 != "Storage3" ]]; then
    echo "Error: missing storage resource argument (Storage2 or Storage3)"
    echo "USAGE $0 <POD ID> <Storage Resource>"
    exit 1
fi

COLDFRONT_CONTAINER=$1
STORAGE_RESOURCE=$2

kubectl exec $COLDFRONT_CONTAINER -n coldfront -- /bin/bash -c "mkdir -p /tmp/utils"
kubectl cp utils/coldfront_ad_utils.py $COLDFRONT_CONTAINER:/tmp/utils/coldfront_ad_utils.py -n coldfront
kubectl cp utils/user_list.py $COLDFRONT_CONTAINER:/tmp/user_list.py -n coldfront
kubectl exec $COLDFRONT_CONTAINER -n coldfront -- /bin/bash -c "PYTHONPATH=/tmp USER_LIST_ID_ONLY=True USER_LIST_RESOURCE=${STORAGE_RESOURCE} coldfront shell < /tmp/user_list.py"
kubectl cp -n coldfront $COLDFRONT_CONTAINER:/tmp/"${STORAGE_RESOURCE}-AllocationPIs.csv" "${PWD}/${STORAGE_RESOURCE}-AllocationPIs.csv"
kubectl cp -n coldfront $COLDFRONT_CONTAINER:/tmp/"${STORAGE_RESOURCE}-UserList.csv" "${PWD}/${STORAGE_RESOURCE}-UserList.csv"

exit 0
