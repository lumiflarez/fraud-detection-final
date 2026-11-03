# CI/CD — 6 savaitė

Data: 2026-11-03

## Pipeline (`.github/workflows/ml-pipeline.yml`)

lint (ruff, taisyklės `ruff.toml`) → test (pytest `tests/test_model.py`, `tests/test_api.py`) →
model-gate (`scripts/check_model_gate.py --threshold 0.95`) → build-push (tik `push` į `main`).

build-push: `docker build -f docker/Dockerfile.cpu` → `ghcr.io/lumiflarez/fraud-detection-final/mlops-cpu:sha-<commit>`
→ bot'as perrašo `k8s/deployment-cpu.yaml` image eilutę ir commit'ina (`ci: bump image to sha-…`).
CI klasterio neliečia — klasterį su Git sinchronizuoja ArgoCD (GitOps).

Nukrypimai nuo PDF: kurso `data-validation` ir `governance` job'ai (15–16 sav.) išjungti iki tų savaičių;
`build-push` prieš build'ą leidžia `scripts/bootstrap.py` (CI nepasiekia lokalaus DVC remote);
GHCR paketas viešas (privačių paketų kvota 500 MB buvo viršyta → `error from registry: denied`).

## ArgoCD (minikube)

- Diegimas: `kubectl apply -n argocd --server-side --force-conflicts -f …/argo-cd/stable/manifests/install.yaml`
  (`applicationsets` CRD per didelis client-side apply).
- `argocd-cm`: `kustomize.buildOptions: --load-restrictor LoadRestrictionsNone` — overlay'ai rodo į `../../../k8s/`.
- Application `mlops-fraud-api`: repo `lumiflarez/fraud-detection-final`, `path: deploy/overlays/production`
  (ne `k8s/` — ten yra vėlesnių savaičių manifestai), `automated` + `prune` + `selfHeal`.
- Rezultatas: Synced/Healthy, 3 replikos su `sha-67cf849…` vaizdu.

## Įrodymai

| Kas | Kur |
|-----|-----|
| Žalias paleidimas (4 job'ai) | Actions run 41680554103 |
| Raudonas paleidimas: `lint` fail → `build-push` skipped | Actions run 41655721898 |
| Bot'o commit | `7cbf19f ci: bump image to sha-67cf849…` |

## Rollback

### A. Git revert (GitOps, rekomenduojama)
```bash
git revert <commit-kuris-pakeitė-image>     # pvz. bot'o "ci: bump image to …"
git push origin main                        # ArgoCD per ≤3 min pritaiko ankstesnį vaizdą
```

### B. ArgoCD istorija
```bash
argocd app history mlops-fraud-api
argocd app rollback mlops-fraud-api <revision>   # pastaba: automated sync laikinai išjungiamas
```

### C. Rankinis vaizdo pin'as
```bash
# k8s/deployment-cpu.yaml -> image: ghcr.io/lumiflarez/fraud-detection-final/mlops-cpu:sha-<ankstesnis>
git commit -am "rollback: pin sha-<ankstesnis>" && git push
```
Kiekvienu atveju tikrinti: `kubectl rollout status deployment/mlops-fraud-api -n mlops`, `curl localhost:8080/health`.
