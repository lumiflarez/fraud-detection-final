# Model serving ir vykdymo palyginimas — 7 savaitė

Data: 2026-11-03

## 1. Model Registry

- `scripts/register_model.py --run-id 4f3c6a6fa8d14b5fa3af36bae2acad40` (eksperimentas 4, `rf-n300-d10`, accuracy 0.99)
  → registruotas modelis `fraud-detector`, versija 1, alias'ai `@candidate` ir `@champion`.
- Nukrypimas nuo PDF: vietoj stadijų Staging/Production (MLflow 3 — deprecated) naudojami alias'ai,
  kaip reikalauja U2-R2 (`models:/fraud-detector@champion`). Patikra: `mlflow.sklearn.load_model("models:/fraud-detector@champion")`
  → ta pati prognozė kaip API (`0`).
- Vaizdas ↔ registras: InferenceService turi label'us `mlflow.registry/model=fraud-detector`, `mlflow.registry/version=1`;
  vaizdas `mlops-onnx:v1.2.3-cpu` (GHCR `week3-onnx@sha256:84d7fe59…`) eksportuotas iš to paties modelio.

## 2. KServe (minikube)

- Diegimas: cert-manager v1.16.2 → KServe v0.12.0 (`--server-side`) → cluster resources.
- Nukrypimai: (1) `kube-rbac-proxy` vaizdas perkeltas į `quay.io/brancz/kube-rbac-proxy:v0.18.0`
  (`gcr.io/kubebuilder` registras nebeegzistuoja); (2) `defaultDeploymentMode: RawDeployment` —
  be Istio/Knative (6 GiB minikube); prarandama scale-to-zero ir canary (papildoma užduotis 7.2 neįmanoma).
- `deploy/kserve/inference-service-onnx.yaml` → KServe sukūrė `fraud-detector-predictor` Deployment, Service ir HPA.
- HPA: min 1, max 2, CPU target žr. `kubectl get hpa -n mlops` (KServe raw režimas; anotacija `autoscaling.kserve.io/target`).
- Kvota po diegimo: `pods 4/10`, `requests.cpu 1250m/4`.

## 3. Vykdymo palyginimas (tabulinis modelis)

Aplinka: minikube v1.39.0 (4 CPU / 6 GiB), 100 nuoseklių `/predict` užklausų po 10 apšilimo, per `kubectl port-forward`
(įskaičiuota tunelio delsa — viršutinė riba). Skriptas: `scripts/benchmark_api.py`; žali JSON: `docs/week7/`.

| Servisas | Vaizdas | p50 (ms) | p95 (ms) | max (ms) |
|----------|---------|---------:|---------:|---------:|
| KServe InferenceService (ONNX Runtime) | `mlops-onnx:v1.2.3-cpu` (248 MB rootfs) | 2,04 | **2,53** | 3,0 |
| Deployment (sklearn, 5–6 sav.) | `mlops-cpu:sha-…` (380 MB rootfs) | 6,18 | **7,37** | 9,49 |

Išvada: ONNX Runtime p95 ≈ 2,9× mažesnis ir vaizdas 35 % mažesnis; abu toli nuo NFR-27 ribos (80 ms).
Vienas matavimas, ne SLA; lygiagrečios apkrovos testas — U2-E3 (Locust).

## 4. LLM dalis (vLLM, FP16 vs INT4) — neatlikta

Nėra GPU ir HPC prieigos. Manifestai `deploy/kserve/inference-service-vllm.yaml`, `hpa-vllm.yaml` ir
`scripts/benchmark_vllm.py` paliekami kurso versijoje. NFR-28 ir NFR-29 neišmatuoti.
Ką reikia mokėti paaiškinti: continuous batching (naujas request'as nelaukia batch'o pabaigos),
tokens/s ≠ vienam vartotojui kai sesijos dalijasi GPU, INT4 AWQ mažina VRAM ir didina pralaidumą kokybės sąskaita,
cost/token = (GPU $/h ÷ 3600) ÷ tokens/s.
