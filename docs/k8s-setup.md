# Kubernetes diegimas — 5 savaitė

Data: 2026-11-03

## 1. Klasteriai

| Aplinka | Platforma | Paskirtis | Būsena |
|---------|-----------|-----------|--------|
| Lab (dev) | minikube v1.39.0, Docker driver'is | CPU inference (ši savaitė) | atlikta |
| U1/U2 | kind `mlops-u1` (k8s/kind-config) | MLflow serveris, mokymo Job, inference U2 | atskiras, laboratoriniams nenaudojamas |
| Cloud | GKE Autopilot | CPU inference | neatlikta (GCP kreditai taupomi; alternatyva) |
| HPC | Universiteto K8s su GPU | GPU DDP training | neatlikta — prieigos prie HPC nėra |

Sprendimas: U1 kind klasteris paliekamas tik U1/U2 užduotims. Laboratoriniai darbai
vykdomi atskirame minikube klasteryje, kurį galima bet kada ištrinti ir atkurti.
Abu klasteriai vienu metu neveikia (RAM: WSL2 turi 11 GiB) — prieš `minikube start`
U1 konteineris sustabdomas (`docker stop mlops-u1-control-plane`).

## 2. Aplinka ir versijos

| Komponentas | Versija |
|-------------|---------|
| OS | Windows + WSL2 Ubuntu 22.04 |
| Docker Desktop | 27.5.1 (WSL integracija) |
| minikube | v1.39.0, kicbase v0.0.51, driver'is `docker` |
| Kubernetes serveris | v1.37.0, containerd 2.3.4 |
| kubectl | v1.37.1 (skew su serveriu: 0 minor) |
| Vaizdas | `mlops-cpu:v1.2.3-cpu` (ID `84b083e49dd3`, 387 MB; tas pats, kas GHCR `week3-cpu@sha256:a9fe8668…` ir AR `mlops-cpu:v1.2.3-cpu`) |

Senas pirmo bandymo profilis (`minikube`, K8s v1.31.4) ištrintas: kubectl 1.37
palaiko tik ±1 minor versijos skirtumą.

## 3. Minikube paleidimas (išmatuota)

```bash
# U1 klasterį sustabdome (ne triname!), kad užtektų RAM
docker stop mlops-u1-control-plane

# PDF siūlo --memory=8192; WSL2 turi 11 GiB, todėl riba sumažinta iki 6 GiB (cgroup cap, ne rezervacija)
minikube start --cpus=4 --memory=6144 --driver=docker
kubectl config current-context   # minikube
```

| Matavimas | Reikšmė |
|-----------|---------|
| `minikube start` trukmė (vaizdas jau parsiųstas) | 38,0 s |
| Tuščias klasteris (`docker stats`) | 754 MiB RAM, ~13 % CPU |
| `minikube image load mlops-cpu:v1.2.3-cpu` (387 MB) | 33,4 s |

### Vaizdai ir minikube

Minikube mazgas turi atskirą containerd vaizdų saugyklą — Docker Desktop vaizdų jis nemato.
Be `minikube image load` Pod'as bando traukti `docker.io/library/mlops-cpu` ir gauna
`ImagePullBackOff`. Manifeste `imagePullPolicy: IfNotPresent` — naudojamas įkeltas vaizdas.
Po kiekvieno vaizdo perbuild'inimo `image load` reikia kartoti (alternatyva — minikube registry addon).

```bash
docker tag mlops-cpu:local mlops-cpu:v1.2.3-cpu
minikube image load mlops-cpu:v1.2.3-cpu
minikube image ls | grep mlops-cpu    # docker.io/library/mlops-cpu:v1.2.3-cpu
```

## 4. CPU inference diegimas

```bash
kubectl apply -f k8s/namespace.yaml        # Namespace mlops
kubectl apply -f k8s/configmap.yaml        # MODEL_PATH, MLFLOW_TRACKING_URI
kubectl apply -f k8s/deployment-cpu.yaml   # 2 replikos, probes, resources
kubectl apply -f k8s/service-cpu.yaml      # ClusterIP 80 -> 8080
kubectl apply -f k8s/resourcequota.yaml    # namespace biudžetas

kubectl rollout status deployment/mlops-fraud-api -n mlops
kubectl port-forward svc/mlops-fraud-api 8080:80 -n mlops > /tmp/pf.log 2>&1 &
curl -s http://localhost:8080/health          # {"status":"ok"}
curl -s -X POST http://localhost:8080/predict -H "Content-Type: application/json" \
  -d '{"f0":0.1,"f1":-0.2,"f2":0.3,"f3":0.0,"f4":0.1,"f5":0.2,"f6":0.0,"f7":0.1,"f8":0.2,"f9":0.0}'
# {"prediction":0} — sutampa su 3 sav. (Docker) ir 4 sav. (Cloud Run) rezultatu
```

Pastaba apie `port-forward`: tunelis prisiriša prie vieno Pod'o; per rolling update tas
Pod'as pakeičiamas ir tunelis nutrūksta (`Exit 1`) — reikia paleisti iš naujo. Service'as
tuo metu veikia: patikrinta iš klasterio vidaus
(`kubectl exec … python3 -c "urllib.request.urlopen('http://mlops-fraud-api.mlops.svc/health')"` → `{"status":"ok"}`).

### Išmatuota (2 replikos)

| Matavimas | Reikšmė | Deklaruota manifeste |
|-----------|---------|----------------------|
| Rolling update (`rollout restart`, 2 replikos) iki Ready | 25,1 s | NFR-19 tikslas ≤ 60 s |
| Pod'o RAM (`kubectl top`) | 131 Mi kiekvienas | requests 256Mi, limits 512Mi |
| Pod'o CPU ramybėje | 4–5 m | requests 250m, limits 1 |
| Visas klasteris su API + metrics-server | 1,32 GiB RAM, 281 m CPU | (tuščias: 754 MiB) |
| Rolling update eiga | 1 naujas Ready → 1 senas terminuojamas → 2/2 | `strategy: RollingUpdate` (numatytoji) |

Mastelio keitimas `replicas: 2 → 3` (per failą, ne `kubectl scale`): trečias Pod'as Ready per
kelias sekundes, endpoints — 3 IP, kvota `pods 3/10`; grąžinta į 2.

## 5. ResourceQuota

`kubectl describe resourcequota mlops-quota -n mlops` su 2 replikomis:

| Resursas | Used | Hard |
|----------|------|------|
| pods | 2 | 10 |
| requests.cpu | 500m | 4 |
| requests.memory | 512Mi | 8Gi |
| limits.cpu | 2 | 8 |
| limits.memory | 1Gi | 16Gi |
| requests.nvidia.com/gpu | 0 | 2 |

Kai kvota apima CPU/RAM, kiekvienas Pod'as namespace'e privalo turėti requests/limits —
kitaip API serveris jį atmeta. GPU eilutė minikube klasteryje be GPU — nekenksminga.

## 6. GPU DDP training (HPC) — neatlikta

`k8s/job-training-ddp.yaml`, `k8s/service-headless-ddp.yaml`, `k8s/job-training-single-node.yaml`,
`k8s/pvc-data.yaml` ir `src/train_ddp.py` paliekami repozitorijoje (kurso versija), bet Job nebuvo
paleistas: nėra prieigos prie universiteto HPC klasterio, o 3 sav. GPU vaizdas (`mlops-gpu`) nebuvo
sukurtas. Pagal užduoties taisykles GPU dalis neprivaloma. Esmė, kurią reikia mokėti paaiškinti:

- `Job` vs `Deployment`: Job baigiasi (`Completed`), Deployment laikomas gyvas amžinai;
- `parallelism: 2`, `completions: 2`, `completionMode: Indexed` → stabilūs Pod'ų vardai
  `…-0/-1` ir `JOB_COMPLETION_INDEX` → `torchrun --node_rank`;
- headless Service (`clusterIP: None`, `publishNotReadyAddresses: true`) → kiekvienas Pod'as
  gauna DNS vardą, kad rank 0 būtų `master_addr`;
- `nvidia.com/gpu: 1` limit — GPU yra nedalomas resursas, be limit'o scheduler'is jo neskiria.

Galima CPU alternatyva ateityje: tas pats skriptas su `backend="gloo"` ir 2 procesais be GPU.

## 7. Valymas

```bash
pkill -f "port-forward"                      # tuneliai
kubectl delete namespace mlops               # visi laboratorijos objektai
minikube stop                                # arba: minikube delete (viskas iš naujo ~40 s)
docker start mlops-u1-control-plane          # grąžinti U1 klasterį
kubectl config use-context kind-mlops-u1
```
