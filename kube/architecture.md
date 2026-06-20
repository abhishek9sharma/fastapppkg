# Kubernetes Architecture — fastapppkg

```
                        ┌─────────────────────────────────────────────────────────┐
                        │                     MINIKUBE CLUSTER                    │
                        │                                                         │
  ┌──────────┐          │  ┌─────────────────────────────────────────────────┐   │
  │          │  :80     │  │              NGINX Ingress Controller           │   │
  │  Browser │──────────┼──► kubefastapiapp.test  ──► kubefastapiapp svc    │   │
  │  / curl  │          │  │  temporal.test        ──► temporal svc :8233   │   │
  │          │          │  └───────────────────────────────┬─────────────────┘   │
  └──────────┘          │                                  │                     │
                        │           ┌─────────────────────▼──────────────────┐  │
                        │           │         kubefastapiapp Service          │  │
                        │           │              ClusterIP :80              │  │
                        │           └─────────────────────┬──────────────────┘  │
                        │                                  │                     │
                        │           ┌─────────────────────▼──────────────────┐  │
                        │           │      kubefastapiapp Deployment          │  │
                        │           │         (replicas: 2)  :80              │  │
                        │           │                                         │  │
                        │           │  Pod 1: FastAPI app                     │  │
                        │           │  Pod 2: FastAPI app                     │  │
                        │           │                                         │  │
                        │           │  POST /workflow/run                     │  │
                        │           │    └─► connects to Temporal gRPC        │  │
                        │           └──────────────┬──────────────────────────┘  │
                        │                          │ gRPC :7233                  │
                        │           ┌──────────────▼──────────────────────────┐  │
                        │           │          temporal Service                │  │
                        │           │   ClusterIP :7233 (gRPC)                │  │
                        │           │            :8233 (Web UI)               │  │
                        │           └──────────────┬──────────────────────────┘  │
                        │                          │                             │
                        │           ┌──────────────▼──────────────────────────┐  │
                        │           │       temporal Deployment (x1)          │  │
                        │           │    temporalio/auto-setup:1.25.0         │  │
                        │           │                                         │  │
                        │           │    initContainer: wait-for-postgres     │  │
                        │           │      └─► pg_isready -h postgres :5432   │  │
                        │           └──────────────┬──────────────────────────┘  │
                        │                          │ :5432                       │
                        │           ┌──────────────▼──────────────────────────┐  │
                        │           │          postgres Service                │  │
                        │           │         ClusterIP :5432                 │  │
                        │           └──────────────┬──────────────────────────┘  │
                        │                          │                             │
                        │           ┌──────────────▼──────────────────────────┐  │
                        │           │        postgres Deployment (x1)         │  │
                        │           │           postgres:15                   │  │
                        │           │                                         │  │
                        │           │   user: temporal / db: temporal         │  │
                        │           └──────────────┬──────────────────────────┘  │
                        │                          │                             │
                        │           ┌──────────────▼──────────────────────────┐  │
                        │           │      PersistentVolumeClaim 1Gi          │  │
                        │           │         postgres-data (RWO)             │  │
                        │           └─────────────────────────────────────────┘  │
                        │                                                         │
                        │  ╌╌╌╌╌ local access only (kubectl port-forward) ╌╌╌╌  │
                        │           Temporal gRPC :7233  ◄── workers connect     │
                        └─────────────────────────────────────────────────────────┘

  Request flow:
  Browser → Ingress → kubefastapiapp svc → FastAPI pod
                                               └─► POST /workflow/run
                                                     └─► Temporal gRPC :7233
                                                           └─► executes PrintWorkflow
                                                                 └─► result returned to caller
```

## Startup order

```
1. postgres        readinessProbe (pg_isready) must pass
       ↓
2. temporal        initContainer polls postgres until ready
                   auto-setup creates DBs + runs schema migrations
       ↓
3. fastapi         connects worker to temporal:7233 on startup
                   POST /workflow/run is now live
```

## Exposed endpoints

| Host | Port | What |
|---|---|---|
| `kubefastapiapp.test` | 80 | FastAPI app (via Ingress) |
| `temporal.test` | 80 | Temporal Web UI (via Ingress → svc :8233) |
| `localhost` | 7233 | Temporal gRPC (`kubectl port-forward svc/temporal 7233:7233`) |
| `localhost` | 5432 | Postgres (`kubectl port-forward svc/postgres 5432:5432`) |
