# Migration to homelab-k8s-cluster with Argo CD

This document describes the changes made to migrate ThreatIntelCollector from SMB-backed storage to MinIO/NFS storage and deploy it using Argo CD's app-of-apps pattern.

## Summary of Changes

### Application Code
**No changes required** - The Python application and configuration are storage-agnostic.

### Namespace Change
- **Old:** `ti`
- **New:** `ti-collector`

### Storage Changes

#### Removed
- SMB CSI driver configuration
- SMB-specific mount options
- Static PersistentVolume definition
- SMB secrets

#### Added
- Static PV and PVC using `minio-nfs` StorageClass
- NFS-backed storage on Synology NAS at 192.168.1.197:/volume1/minio/ti-collector

### Files Modified in kubernetes/ Directory

1. **ti-collector-pv.yaml** (updated)
   - Replaced SMB CSI driver with NFS volume type
   - Points to NFS server at 192.168.1.197:/volume1/minio/ti-collector
   - Uses `minio-nfs` StorageClass (static provisioning)
   - Includes both PV and PVC definitions
   - Changed namespace to `ti-collector`

2. **ti-collector-pvc.yaml** (standalone PVC)
   - References the static PV via `volumeName: ti-collector-pv`
   - Uses `minio-nfs` StorageClass
   - Changed namespace to `ti-collector`

3. **ti-collector-cronjob.yaml**
   - Added namespace: `ti-collector`
   - Removed `imagePullSecrets` (images are public)
   - Cleaned up YAML formatting

4. **ti-collector-oneoff-job.yaml**
   - Added namespace: `ti-collector`
   - Updated image version from 1.3 to 1.4
   - Removed `imagePullSecrets`
   - Fixed indentation

#### Deleted Files
- `ti-collector-smb-secrets.yaml` - no longer needed

### New Argo CD Manifests

Created in `argo-manifests/ti-collector/` for deployment to homelab-argo-aoa repository:

- **namespace.yaml** - Creates ti-collector namespace
- **pv.yaml** - 100Gi NFS-backed PersistentVolume
- **pvc.yaml** - PVC bound to the static PV
- **cronjob.yaml** - Daily CronJob for threat intelligence collection
- **kustomization.yaml** - Kustomize configuration for the application

## Deployment Steps

### 1. Update ThreatIntelCollector Repository

The kubernetes manifests in this repository have been updated. Commit these changes:

```bash
git add .
git commit -m "Migrate to minio-nfs storage and update for ti-collector namespace"
git push
```

### 2. Deploy to Argo CD

Copy the Argo manifests to your homelab-argo-aoa repository:

```bash
cp -r argo-manifests/ti-collector /path/to/homelab-argo-aoa/apps/
cd /path/to/homelab-argo-aoa
git add apps/ti-collector
git commit -m "Add ti-collector application"
git push
```

Argo CD will automatically sync and deploy the application.

### 3. Verify Deployment

```bash
# Check if namespace was created
kubectl get namespace ti-collector

# Check PVC status
kubectl get pvc -n ti-collector

# Check CronJob
kubectl get cronjob -n ti-collector

# View CronJob details
kubectl describe cronjob ti-collector-cron -n ti-collector
```

### 4. Monitor First Run

The CronJob runs daily. To trigger a manual run for testing:

```bash
kubectl create job --from=cronjob/ti-collector-cron ti-collector-test -n ti-collector
```

Watch the job:

```bash
kubectl get jobs -n ti-collector -w
```

View logs:

```bash
kubectl logs -n ti-collector -l job-name=ti-collector-test -f
```

## Storage Comparison

| Aspect | Old (SMB) | New (NFS) |
|--------|-----------|-----------|
| StorageClass | ti-collector | minio-nfs |
| Backend | SMB share (//192.168.1.197/ti_reports) | NFS share (192.168.1.197:/volume1/minio/ti-collector) |
| Volume Type | CSI (smb.csi.k8s.io) | NFS (native Kubernetes) |
| Provisioning | Static PV | Static PV |
| Access Mode | ReadWriteMany | ReadWriteMany |
| Capacity | 100Gi | 100Gi |
| Secrets | Required (SMB credentials) | Not required |
| Mount Options | dir_mode, file_mode, vers=3.0 | nfsvers=4.1 |

## Rollback Plan

If you need to rollback to the SMB-based deployment:

1. Revert the git commits in this repository
2. Remove the ti-collector app from Argo CD:
   ```bash
   kubectl delete -k argo-manifests/ti-collector
   ```
3. Restore the old SMB secrets and PV configuration
4. Apply the old manifests manually

## Additional Notes

- **No data migration required** - Starting fresh with new storage
- **One-off job** kept in `kubernetes/ti-collector-oneoff-job.yaml` for manual execution
- **Image version** updated to 1.4 across all manifests
- **Public images** - No imagePullSecrets needed

## Testing Checklist

- [ ] NFS export path `/volume1/minio/ti-collector` exists on NAS (192.168.1.197)
- [ ] Namespace created successfully
- [ ] PV created and available
- [ ] PVC bound to static PV
- [ ] CronJob created with correct schedule
- [ ] Manual job execution works
- [ ] Data persists between job runs
- [ ] APTNotes repository cloned to /RAID/APTNotes
- [ ] APTCyberMonitor repository cloned to /RAID/APTCyberMonitor
- [ ] Reports downloaded successfully