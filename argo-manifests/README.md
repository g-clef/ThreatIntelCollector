# Argo CD Manifests for TI Collector

This directory contains the Kubernetes manifests for deploying the TI Collector application using Argo CD's app-of-apps pattern.

## Directory Structure

```
argo-manifests/
└── ti-collector/
    ├── namespace.yaml       # Creates ti-collector namespace
    ├── pv.yaml             # 100Gi NFS-backed PersistentVolume
    ├── pvc.yaml            # PVC bound to the static PV
    ├── cronjob.yaml        # Daily CronJob to collect threat intelligence
    └── kustomization.yaml  # Kustomize configuration
```

## Deployment to homelab-argo-aoa Repository

Copy the `ti-collector` directory to your homelab-argo-aoa repository:

```bash
cp -r argo-manifests/ti-collector /path/to/homelab-argo-aoa/apps/
```

Then commit and push to the homelab-argo-aoa repository:

```bash
cd /path/to/homelab-argo-aoa
git add apps/ti-collector
git commit -m "Add ti-collector application"
git push
```

Argo CD will automatically detect and deploy the application due to the auto-sync and self-heal policies configured in the app-of-apps pattern.

## Manual Deployment (without Argo CD)

If you need to deploy manually for testing:

```bash
kubectl apply -k argo-manifests/ti-collector
```

## One-Off Job

The one-off job manifest is kept separate in `kubernetes/ti-collector-oneoff-job.yaml` for manual execution when needed:

```bash
kubectl apply -f kubernetes/ti-collector-oneoff-job.yaml
```

After the job completes, delete it:

```bash
kubectl delete job ti-collector-oneoff -n ti-collector
```

## Storage

The application uses NFS-backed storage with the `minio-nfs` StorageClass:
- **Type:** Static PersistentVolume (no-provisioner)
- **Backend:** NFS at 192.168.1.197:/volume1/minio/ti-collector
- **Access Mode:** ReadWriteMany (shared across pods)
- **Capacity:** 100Gi
- **Mount Options:** NFSv4.1

**Important:** Ensure the NFS export path `/volume1/minio/ti-collector` exists on the NAS before deploying.

## Verification

After deployment, verify the resources:

```bash
# Check namespace
kubectl get namespace ti-collector

# Check PVC
kubectl get pvc -n ti-collector

# Check CronJob
kubectl get cronjob -n ti-collector

# View CronJob schedule and last run
kubectl describe cronjob ti-collector-cron -n ti-collector

# Check job history (created by CronJob)
kubectl get jobs -n ti-collector

# View logs from the most recent job
kubectl logs -n ti-collector -l job-name=<job-name>
```

## Triggering Manual Run

To trigger the CronJob manually without waiting for the schedule:

```bash
kubectl create job --from=cronjob/ti-collector-cron ti-collector-manual-$(date +%s) -n ti-collector
```