# Fraud Detection API - Reikalavimai v1.4

Data: 2026-09-15 | Autoriai: Saule

## 1.1 Problemos aprasymas

Sukurti realaus laiko fraud scoring API korteliu transakcijoms.
Tikslas: recall >= 0.92, false positive <= 0.5%.

## 2. Funkciniai reikalavimai

| ID    | Reikalavimas                              | Prioritetas |
|-------|-------------------------------------------|-------------|
| FR-01 | POST /predict priima JSON transakcija     | Must        |
| FR-02 | Grazina prediction ir score               | Must        |
| FR-03 | GET /health grazina status                | Must        |

## 3. Nefunkciniai reikalavimai

| ID     | Kategorija | Reikalavimas           | KPI                    |
|--------|------------|------------------------|------------------------|
| NFR-01 | Nasumas    | Inference latency      | p95 <= 80 ms @ 500 RPS |
| NFR-02 | Kokybe     | Sukciavimo aptikimas   | Recall >= 0.92         |
| NFR-03 | Kokybe     | False positive rate    | <= 0.5%                |
| NFR-04 | Dreifas    | Precision degradacija  | < 3% per 14 dienu      |
| NFR-05 | Saziningumas | TPR skirtumas regionu | <= 5%                  |
| NFR-06 | Kastai     | Inference kaina        | <= $0.0002/req        |
| NFR-07 | Prieinamumas | Uptime               | >= 99.95%              |

## 3.1 Eksperimentų sekimo ir atkartojamumo NFR (v1.1)

| ID     | Kategorija       | Reikalavimas                                                    | KPI                                   |
|--------|------------------|-----------------------------------------------------------------|---------------------------------------|
| NFR-08 | Atkartojamumas   | Bet kuris istorinis run atkuriamas `python reproduce.py <run_id>` | <= 2 min (be duomenų atsisiuntimo), delta accuracy <= 0.005 |
| NFR-09 | Atsekamumas      | Kiekvienas eksperimentas turi MLflow run ID, git commit ir duomenų md5 tag'us; kiekvienas diegiamas modelis – `model_id` | 100 % run'ų |
| NFR-10 | Duomenų versija  | Mokymo duomenų versija fiksuota DVC (`dvc.lock` md5 = run'o `dvc_raw_md5`) | 100 % run'ų |

## 3.2 Konteinerizacijos NFR (v1.2)

Šiame demonstraciniame darbe dydžio/laiko tikslai vertinami pagal realius matavimus. Neįvykdytas tikslas registruojamas su priežastimi, o ne pakeičiamas fiktyviu rezultatu.

| ID | Reikalavimas | Patikra / įrodymas |
|---|---|---|
| NFR-11 | CPU rootfs <=500 MB; ONNX rootfs <=300 MB tikslas | `docs/image-sizes.md`: platforma, `du --apparent-size` rootfs baitai ir image ID JSON; Docker `.Size` atskirai (containerd turinys suspaustas) |
| NFR-12 | ONNX parengtis <=5 s tikslas | `docs/week3/onnx-runtime.json`: docker run pradžia -> pirmas HTTP200, vaizdas vietinis; ne build ar pull laikas |
| NFR-13 | 0 CRITICAL prieš publikavimą | Trivy JSON sutampa su image ID; `scan-report --gate`, CI exit-code1; HIGH radiniams peržiūra ir sprendimas |
| NFR-14 | CPU/ONNX/GPU servisai ne root | `docker exec ... id`, UID !=0; HTTP/Docker health; GPU papildomai tikras CUDA skaičiavimas |

**Išmatuota (2026-10-26, linux/amd64, Docker Desktop 27.5.1; šaltiniai `docs/image-sizes.md`, `docs/week3/*.json`, `docs/security-scan.md`):**

| NFR | Tikslas | Išmatuota | Rezultatas |
|-----|---------|-----------|------------|
| NFR-11 | CPU rootfs <= 500 MB; ONNX <= 300 MB | rootfs: single 480,63 MB, cpu 379,92 MB, onnx 247,85 MB (`docs/week3/image-sizes.json`) | atitinka |
| NFR-12 | ONNX parengtis <= 5 s | 3,112 s nuo `docker run` iki pirmo HTTP 200 `/health`, vaizdas vietinis (`docs/week3/onnx-runtime.json`) | atitinka (vienas matavimas, ne SLA) |
| NFR-13 | 0 CRITICAL prieš publikavimą | cpu/onnx: 0 CRITICAL, 44 HIGH = 8 skirtingi CVE, visi Debian bazinio vaizdo OS paketuose, be pataisos (`docs/week3/trivy-*.json`, analizė `docs/security-scan.md`); vartas PASS | atitinka; HIGH priimti su pagrindimu |
| NFR-14 | API vartotojas ne root | UID 1000 (`mluser`) cpu ir onnx (`docs/week3/cpu-runtime.json`, `onnx-runtime.json`); GPU vaizdas nedarytas | atitinka |

**GHCR vaizdai:**
- `ghcr.io/lumiflarez/week3-cpu:v1.2.3-cpu@sha256:a9fe8668a46c95d98b16e8ff60ce3e47e12532061357ffe99bcfa4ebab430682` 
- `ghcr.io/lumiflarez/week3-onnx:v1.2.3-cpu@sha256:84d7fe59f2e34bd122b34fd50e262e6ad6d42f09a4140828f446992a50bc797e`

## 3.3 Debesijos NFR (v1.3)

| ID     | Reikalavimas            | KPI                          | Išmatuota / įrodymas |
|--------|-------------------------|------------------------------|----------------------|
| NFR-15 | Mėnesio infra kaina     | <= 50 USD (GCP kreditai)     | Billing ataskaita: <X> USD; žr. `docs/cost-analysis.md` |
| NFR-16 | Kaina vienai užklausai  | <= 0.0002 USD                | ~0.000003 USD (skaičiavimas `docs/cost-analysis.md`) |
| NFR-17 | Valdomo endpoint SLA    | Uptime >= 99.9 %             | Cloud Run SLA (Google); gyvas `/health` → `{"status":"ok"}` |
| NFR-18 | IaC atkartojamumas      | `terraform apply` < 15 min   | Pilnas apply: <Y> min (6 resursai) |

## 3.4 Kubernetes NFR (v1.4)

Matavimų aplinka: minikube v1.39.0 (K8s v1.37.0, Docker driver'is, 4 CPU / 6 GiB cap), vaizdas `mlops-cpu:v1.2.3-cpu` (= GHCR `week3-cpu@sha256:a9fe8668…`), 2026-11-03. Komandos ir pilni matavimai — `docs/k8s-setup.md`. GPU DDP Job neatliktas (nėra HPC prieigos); pagal užduoties taisykles GPU dalis neprivaloma.

| ID     | Reikalavimas              | KPI                            | Išmatuota / įrodymas |
|--------|---------------------------|--------------------------------|----------------------|
| NFR-19 | Deployment rollout laikas | <= 60 s (2 replikos)           | 25,1 s: `kubectl rollout restart` → 2/2 Ready (`time kubectl rollout status`); vaizdas jau mazge (`minikube image load` 33,4 s atskirai) |
| NFR-20 | GPU mokymo Job trukmė     | <= 30 min (2 GPU, sample)      | Neišmatuota — HPC neprieinamas, Job nepaleistas; manifestai `k8s/job-training-*.yaml`, `src/train_ddp.py` repozitorijoje |
| NFR-21 | GPU utilizacija mokant    | >= 70 % vidurkis               | Neišmatuota — ta pati priežastis |
| NFR-22 | Inference HA              | >= 2 replikos, rolling update  | 2 replikos Running; rolling update be prastovos (Service atsakė `/health` iš klasterio vidaus per keitimą); Pod'as 131 Mi / 4–5 m CPU ramybėje (requests 256Mi/250m); ResourceQuota `pods 2/10`, `requests.cpu 500m/4` |

## 10.x Agentinis elgesys (v1.9)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-38 | Drift aptikimo latencija  | <= 5 min nuo trigger        |
| NFR-39 | Autonominio retrain limit | <= 3 per diena              |
| NFR-40 | Incidento pranesimas      | <= 2 min po deploy          |
| NFR-41 | Agento audito aprėptis    | 100% tool call įrašų        |

## 11.x Stebėsena ir AIOps (v1.10)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-42 | Metrikų scrape intervalas | <= 30 s                     |
| NFR-43 | Alert pranešimo laikas    | <= 2 min nuo firing         |
| NFR-44 | Dreifo report generavimas | <= 10 min                   |
| NFR-45 | Struktūrinio log aprėptis | 100% request handler'ių     |

## 12.x Scaling ir FinOps (v1.11)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-46 | Autoscale reakcijos laikas | <= 3 min iki target replikų |
| NFR-47 | Maks. replikos apkrovoje  | Iki 50                      |
| NFR-48 | Spot kaštų mažinimas      | >= 60% vs on-demand         |
| NFR-49 | Uptime scaling metu       | >= 99.9%                    |

## 13.x Saugumas ir compliance (v1.12)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-50 | Critical CVE produkcijoje | 0 critical                  |
| NFR-51 | Gatekeeper atitiktis      | 100% deployment'ų           |
| NFR-52 | Inference audito aprėptis | 100% /predict               |
| NFR-53 | PII atmetimas API         | 100% PII laukų blokuojama   |

## 14.x Edge ir federated learning (v1.13)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-54 | Edge modelio dydis        | <= 5 MB                     |
| NFR-55 | Edge inference p95        | <= 50 ms (local)            |
| NFR-56 | FL klientu skaicius       | >= 3                        |
| NFR-57 | FL vs centralized gap     | <= 2 pp accuracy            |

## 15.x Testavimas ir validavimas (v1.14)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-58 | Data contract checks      | >= 10 expectations          |
| NFR-59 | E2E pipeline test         | 100% pass CI                |
| NFR-60 | Model regression gate     | accuracy >= 0.95            |
| NFR-61 | Traceability coverage     | 100% critical NFR mapped    |

## 16.x Governance ir capstone (v1.15)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-62 | Model card completeness   | >= 8 sections               |
| NFR-63 | EU AI Act risk documented | tier + mitigations          |
| NFR-64 | Governance report coverage| >= 90% critical NFRs        |
| NFR-65 | Capstone checklist        | 100% critical items green   |

## 7. Keitimo istorija

| Versija | Data       | Autorius | Pakeitimai |
|---------|------------|----------|------------|
| 1.1 | 2026-10-26 | Saule | MLflow + DVC pipeline, NFR-08..10 |
| 1.2 | 2026-10-26 | Saule | Docker cpu/onnx vaizdai, Trivy + SBOM, NFR-11..14 išmatuoti |
| 1.3 | 2026-10-28 | Saule | GCP Terraform, Cloud Run, cost analysis, NFR-15..18 |
| 1.4 | 2026-11-03 | Saule | Kubernetes (minikube) inference Deployment + Service + ResourceQuota, NFR-19..22; GPU DDP neatlikta (HPC) |
