# Cost Analysis - Week 4

## Assumptions

- Region: europe-west1
- Requests: 1000/day, avg 80ms, 512Mi RAM
- Storage: 5 GB GCS, 2 GB Artifact Registry

## Monthly estimate

| Service | Estimate USD/month |
|---------|-------------------|
| Cloud Run | 15-40 |
| GCS | 0.10-1 |
| Artifact Registry | 0.20-2 |
| **Total** | **~20-45** |

## Managed vs self-managed

| Option | Setup | Ops/month | TCO (est.) |
|--------|-------|-----------|------------|
| Cloud Run | 2h | Low | $20-45 |
| Vertex Endpoint | 4h | Low | $80-200 |
| GKE (2 nodes) | 2d | High | $150-350 |

## Decision

Pasirinkome Cloud Run, nes:
- HTTPS endpoint su TLS ir autoscaling gautas per ~1–2 min. `terraform apply`, be serverio, sertifikatų ar firewall konfigūravimo;
- `min_instances = 0` (scale-to-zero): be srauto mokame ~0 — laboratorijos apkrovai išlaidos realiai ~0 USD/mėn.;
- OS patching, TLS atnaujinimai ir mastelio didinimas — Google atsakomybė.
Kompromisas: mažiau kontrolės (nėra GPU, custom operatorių) — tokiems poreikiams tiktų GKE (5 savaitė).