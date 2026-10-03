The {{team}} team keeps the manifests of its release in the ConfigMap `release-manifests` in namespace `{{ns}}`
(keys `hpa.yaml`, `pdb.yaml`, `cronjob.yaml`, `flowschema.yaml`). They were written for an old Kubernetes release and
some `apiVersion` values are no longer served by this cluster, so applying them would fail.

Update the ConfigMap so that every manifest uses the stable `apiVersion` that this cluster serves for its kind.
Keep each manifest's kind and name; only the API version should change.
