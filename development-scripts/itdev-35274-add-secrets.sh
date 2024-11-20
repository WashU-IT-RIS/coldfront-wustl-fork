echo -n '' | gcloud secrets create ITSM_PROTOCOL \
--replication-policy=automatic \
--data-file=-

echo -n '' | gcloud secrets create ITSM_HOST \
--replication-policy=automatic \
--data-file=-

echo -n '' | gcloud secrets create ITSM_REST_API_PORT \
--replication-policy=automatic \
--data-file=-

echo -n '' | gcloud secrets create ITSM_SERVICE_USER \
--replication-policy=automatic \
--data-file=-

echo -n '' | gcloud secrets create ITSM_SERVICE_PASSWORD \
--replication-policy=automatic \
--data-file=-

echo -n '' | gcloud secrets create ITSM_SERVICE_PROVISION_ENDPOINT \
--replication-policy=automatic \
--data-file=-

echo -n '' | gcloud secrets create ITSM_TO_COLDFRONT_MAP_PATH \
--replication-policy=automatic \
--data-file=-


echo -n 'https' | gcloud secrets versions add ITSM_PROTOCOL --data-file=-
echo -n 'itsm.ris.wustl.edu' | gcloud secrets versions add ITSM_HOST --data-file=-
echo -n '8443' | gcloud secrets versions add ITSM_REST_API_PORT --data-file=-
echo -n 'RIS-SVC-LIMSREST' | gcloud secrets versions add ITSM_SERVICE_USER --data-file=-
echo -n '3nDf2F5ffTNCq4' | gcloud secrets versions add ITSM_SERVICE_PASSWORD --data-file=-
echo -n '/v2/rest/attr/info/service_provision/' | gcloud secrets versions add ITSM_SERVICE_PROVISION_ENDPOINT --data-file=-
echo -n 'coldfront/plugins/qumulo/static/migration_mappings/itsm_to_coldfront_map.yaml' | gcloud secrets versions add ITSM_TO_COLDFRONT_MAP_PATH --data-file=-


kubectl delete secrets -n coldfront coldfront-secrets
kubectl create secret -n coldfront generic coldfront-secrets \
      --from-literal=AD_USER_PASS=$(gcloud secrets versions access latest --secret="AD_ADMIN_PASSWORD") \
      --from-literal=AD_USERNAME=$(gcloud secrets versions access latest --secret="AD_ADMIN_USERNAME") \
      --from-literal=OIDC_RP_CLIENT_ID=$(gcloud secrets versions access latest --secret="OIDC_RP_CLIENT_ID") \
      --from-literal=OIDC_RP_CLIENT_SECRET=$(gcloud secrets versions access latest --secret="OIDC_RP_CLIENT_SECRET") \
      --from-literal=QUMULO_PASS=$(gcloud secrets versions access latest --secret="QUMULO_ADMIN_PASSWORD") \
      --from-literal=QUMULO_USER=$(gcloud secrets versions access latest --secret="QUMULO_ADMIN_USERNAME") \
      --from-literal=SECRET_KEY=$(gcloud secrets versions access latest --secret="SECRET_KEY") \
      --from-literal=ITSM_PROTOCOL=$(gcloud secrets versions access latest --secret="ITSM_PROTOCOL") \
      --from-literal=ITSM_HOST=$(gcloud secrets versions access latest --secret="ITSM_HOST") \
      --from-literal=ITSM_REST_API_PORT=$(gcloud secrets versions access latest --secret="ITSM_REST_API_PORT") \
      --from-literal=ITSM_SERVICE_USER=$(gcloud secrets versions access latest --secret="ITSM_SERVICE_USER") \
      --from-literal=ITSM_SERVICE_PASSWORD=$(gcloud secrets versions access latest --secret="ITSM_SERVICE_PASSWORD") \
      --from-literal=ITSM_SERVICE_PROVISION_ENDPOINT=$(gcloud secrets versions access latest --secret="ITSM_SERVICE_PROVISION_ENDPOINT") \
      --from-literal=ITSM_TO_COLDFRONT_MAP_PATH=$(gcloud secrets versions access latest --secret="ITSM_TO_COLDFRONT_MAP_PATH")


# sanity checks
kubectl describe -n coldfront secrets/coldfront-secrets
kubectl get secret -n coldfront coldfront-secrets -o jsonpath={.data.AD_GROUPS_OU} | base64 -d
kubectl get secret -n coldfront coldfront-secrets -o jsonpath={.data.ITSM_TO_COLDFRONT_MAP_PATH} | base64 -d