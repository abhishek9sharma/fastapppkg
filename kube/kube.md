# Kubernetes Manifests — Field Reference & Helm Mapping

This project has two ways to deploy to Kubernetes:

| Approach | Location | Use when |
|---|---|---|
| Raw manifests | `kube/` | Learning, quick one-off apply, minikube hacking |
| Helm chart | `helm/fastapppkg/` | Repeatable deploys, multiple environments, values overrides |

---

## Files in `kube/`

```
kube/
├── deployment.yaml           # FastAPI app
├── service.yaml              # FastAPI service
├── ingress.yaml              # FastAPI ingress (HTTP → service)
├── temporal-deployment.yaml  # Temporal server + init container
├── temporal-service.yaml     # Temporal service (gRPC + UI ports)
├── temporal-ingress.yaml     # Temporal Web UI ingress
├── postgres-pvc.yaml         # Persistent volume claim for Postgres data
├── postgres-deployment.yaml  # Postgres 15 container
├── postgres-service.yaml     # Postgres service (TCP 5432)
├── deploykube.sh             # Apply all manifests in correct order
└── minikube.sh               # Start minikube with required addons
```

---

## Common fields across every resource

Every YAML in this project starts with these three fields:

```yaml
apiVersion: apps/v1   # Which Kubernetes API group and version handles this resource.
                      # apps/v1 → Deployments. v1 → Services, PVCs, Secrets. networking.k8s.io/v1 → Ingress.
kind: Deployment      # The resource type. Tells kubectl which controller to hand the object to.
metadata:             # Identity and organizational info about the resource itself (not the pods it creates).
  name: myapp         # Unique name within the namespace. Used in kubectl commands and cross-resource references.
  labels:             # Arbitrary key/value tags on THIS resource (the Deployment object).
    app: myapp        # Used to query/filter resources: kubectl get pods -l app=myapp
                      # NOT the same as spec.template.metadata.labels — those go on the pods.
```

---

## Key concepts: metadata, spec, labels, selector

### `metadata` vs `spec`

```
metadata   →  describes the resource ITSELF (name, labels, annotations)
spec       →  describes the DESIRED STATE you want Kubernetes to create/maintain
```

### Two `spec:` blocks in a Deployment

Deployments have two nested `spec:` blocks — they belong to different objects:

```yaml
spec:                        # ← Deployment spec: HOW to manage pods
  replicas: 2                #   how many pod copies to keep running
  selector: ...              #   which pods this Deployment owns
  strategy: ...              #   how to roll out updates (RollingUpdate / Recreate)
  template:                  #   blueprint for the pods to create
    metadata:                # ← Pod metadata: labels stamped onto every pod created
      labels:
        app: myapp
    spec:                    # ← Pod spec: WHAT runs inside each pod
      containers:
        - name: myapp
          image: myapp:latest
```

### `labels` vs `selector`

```
labels     →  tags you put ON a resource so others can find it
selector   →  a filter that says "give me resources WITH these labels"
```

They work as a pair — labels are the tags, selector is the query:

```yaml
# On the Deployment — tells it which pods it owns and is responsible for
spec:
  selector:
    matchLabels:
      app: myapp        # "I own pods that have label app=myapp"

# On the pod template — what labels get stamped onto every pod
  template:
    metadata:
      labels:
        app: myapp      # "I am a pod with label app=myapp"

# On the Service — tells it which pods to send traffic to
spec:
  selector:
    app: myapp          # "Route traffic to pods with label app=myapp"
```

The Deployment's `selector.matchLabels` and the pod template's `labels` MUST match exactly,
or the Deployment can't track its own pods. The Service's `selector` uses the same pod labels
to know where to send requests.

### `metadata.labels` (on the Deployment) vs `spec.template.metadata.labels` (on pods)

```
metadata.labels              →  labels on the Deployment object itself
                                used to find/filter the Deployment: kubectl get deploy -l app=myapp

spec.template.metadata.labels →  labels stamped onto every Pod the Deployment creates
                                  used by Services and the Deployment's own selector to find pods
```

They often have the same values but serve different purposes — one tags the Deployment, the other tags its pods.

---

## `deployment.yaml` — FastAPI app

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubefastapiapp          # Name used by the Service selector to route traffic to these pods.
spec:                           # ← DEPLOYMENT spec: tells k8s HOW to manage the pods
                                #   (how many, which pods to own, how to update them)
  replicas: 2                   # Number of pod copies to run simultaneously.
                                # k8s reschedules pods if a node dies to maintain this count.
  selector:                     # How this Deployment identifies the pods it owns and manages.
    matchLabels:
      app: kubefastapiapp       # "I own pods that have label app=kubefastapiapp."
                                # Must match spec.template.metadata.labels exactly.
  template:                     # Blueprint for every pod this Deployment creates.
    metadata:
      labels:
        app: kubefastapiapp     # Stamped onto every pod. Services and this selector match on it.
    spec:                       # ← POD spec: tells k8s WHAT to run inside each pod
                                #   (containers, volumes, init containers, resource limits)
      containers:
        - name: kubefastapiapp  # Container name — used in kubectl logs/exec commands.
          image: kubefastapiapp:latest  # Docker image. "latest" tag + imagePullPolicy: Never
                                        # means minikube uses the locally built image.
          ports:
            - containerPort: 80 # Documents which port the process inside listens on.
                                # Informational only — does NOT expose the port. The Service does that.
          imagePullPolicy: Never  # Never: use only locally available images (right for minikube).
                                  # IfNotPresent: pull if not cached. Always: always pull from registry.
```

**Helm equivalent:** `helm/fastapppkg/templates/fastapi-deployment.yaml`
`kubefastapiapp` → `{{ include "fastapppkg.fastapi.fullname" . }}` (e.g. `myapp-fastapi`)
`replicas: 2` → `{{ .Values.fastapi.replicaCount }}`

---

## `service.yaml` — FastAPI service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kubefastapiapp          # DNS name other pods use to reach this service:
                                # kubefastapiapp.<namespace>.svc.cluster.local
  labels:
    service: kubefastapiapp
spec:                           # ← SERVICE spec: tells k8s HOW to route traffic
                                #   (which pods to send to, on which ports, and how it's exposed)
  selector:
    app: kubefastapiapp         # Routes traffic to any pod with this label.
                                # Must match the pod labels in deployment.yaml.
  ports:
    - port: 80                  # Port the Service exposes to the cluster.
      targetPort: 80            # Port on the pod to forward traffic to.
                                # If omitted, defaults to the same value as port.
  type: ClusterIP               # ClusterIP: reachable only inside the cluster (default).
                                # NodePort: also reachable on each node's IP + a random high port.
                                # LoadBalancer: provisions a cloud load balancer (not for minikube).
```

**Helm equivalent:** `helm/fastapppkg/templates/fastapi-service.yaml`
`port: 80` → `{{ .Values.fastapi.service.port }}`

---

## `ingress.yaml` — FastAPI ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: minikube-ingress
  annotations:                  # Annotations pass config to the ingress controller (nginx here).
                                # This file has none, but nginx annotations look like:
                                # nginx.ingress.kubernetes.io/rewrite-target: /
spec:                           # ← INGRESS spec: tells the controller HOW to route HTTP traffic
                                #   (which hostnames and URL paths map to which Services)
  rules:
    - host: kubefastapiapp.test # The HTTP Host header the controller matches against.
                                # Add "$(minikube ip) kubefastapiapp.test" to /etc/hosts.
      http:
        paths:
          - path: /             # URL prefix to match. "/" catches all requests.
            pathType: Prefix    # Prefix: matches any path starting with "/".
                                # Exact: must match exactly. ImplementationSpecific: controller decides.
            backend:
              service:
                name: kubefastapiapp  # The Service to forward matched requests to.
                port:
                  number: 80          # Which port on that Service to use.
```

**Helm equivalent:** `helm/fastapppkg/templates/fastapi-ingress.yaml`
Wrapped in `{{- if .Values.fastapi.ingress.enabled }}` — set `enabled: false` to skip creating it.
`host` → `{{ .Values.fastapi.ingress.host }}`

---

## Name/label relationships across FastAPI files

The same string `kubefastapiapp` appears in multiple places with different roles. This table shows how each occurrence connects the three files together and maps to Helm values.

| Value | File | Field | Role |
|---|---|---|---|
| `kubefastapiapp` | `deployment.yaml` | `metadata.name` | Name of the Deployment object itself. Used in `kubectl get/describe/delete deployment kubefastapiapp`. |
| `kubefastapiapp` | `deployment.yaml` | `spec.selector.matchLabels.app` | The Deployment's ownership query — "I manage pods with this label." Must match the pod template labels below. |
| `kubefastapiapp` | `deployment.yaml` | `spec.template.metadata.labels.app` | Stamped onto every pod the Deployment creates. This is the value the Service selector and Deployment selector both match against. |
| `kubefastapiapp` | `service.yaml` | `metadata.name` | Name of the Service object. Used as the DNS hostname inside the cluster (`kubefastapiapp.svc.cluster.local`) and referenced by the Ingress backend. |
| `kubefastapiapp` | `service.yaml` | `spec.selector.app` | The Service's pod query — "send traffic to pods with this label." Matches `spec.template.metadata.labels.app` in `deployment.yaml`. |
| `kubefastapiapp` | `ingress.yaml` | `spec.rules[].backend.service.name` | Tells the Ingress which Service to forward traffic to. Must match `metadata.name` in `service.yaml`. |
| `kubefastapiapp.test` | `ingress.yaml` | `spec.rules[].host` | The HTTP `Host` header the Ingress controller matches. Add `$(minikube ip) kubefastapiapp.test` to `/etc/hosts`. |
| `80` | `service.yaml` | `spec.ports[].port` | Port the Service exposes inside the cluster. |
| `80` | `ingress.yaml` | `spec.rules[].backend.service.port.number` | Must match the port above — Ingress forwards to this port on the Service. |

### How they chain together

```
Ingress (host: kubefastapiapp.test)
    │  backend.service.name = "kubefastapiapp"
    ▼
Service (metadata.name = "kubefastapiapp")
    │  spec.selector.app = "kubefastapiapp"
    ▼
Pod (labels.app = "kubefastapiapp")          ← created by ─►  Deployment
                                                               spec.selector.matchLabels.app = "kubefastapiapp"
```

### Helm values equivalents

| Raw manifest value | Helm values.yaml key | Template expression |
|---|---|---|
| `kubefastapiapp` (image name) | `fastapi.image.repository` | `{{ .Values.fastapi.image.repository }}` |
| `kubefastapiapp` (resource names) | derived from release name | `{{ include "fastapppkg.fastapi.fullname" . }}` |
| `kubefastapiapp.test` (host) | `fastapi.ingress.host` | `{{ .Values.fastapi.ingress.host }}` |
| `80` (service port) | `fastapi.service.port` | `{{ .Values.fastapi.service.port }}` |
| `ClusterIP` (service type) | `fastapi.service.type` | `{{ .Values.fastapi.service.type }}` |
| `2` (replicas) | `fastapi.replicaCount` | `{{ .Values.fastapi.replicaCount }}` |
| `Never` (pull policy) | `fastapi.image.pullPolicy` | `{{ .Values.fastapi.image.pullPolicy }}` |

In Helm, resource names like `kubefastapiapp` are replaced by `{{ include "fastapppkg.fastapi.fullname" . }}` which combines the release name + chart name (e.g. `myapp-fastapi`). This means you can deploy multiple releases into the same cluster without name collisions.

---

## `postgres-pvc.yaml` — Persistent volume claim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data           # Referenced by name in postgres-deployment.yaml volumes section.
spec:                           # ← PVC spec: tells k8s WHAT storage to provision
                                #   (how much, access mode, storage class)
  accessModes:
    - ReadWriteOnce             # RWO: only one node can mount this volume at a time (standard for databases).
                                # ReadWriteMany: multiple nodes simultaneously (requires special storage drivers).
                                # ReadOnlyMany: multiple nodes read-only.
  resources:
    requests:
      storage: 1Gi              # How much storage to reserve. minikube provisions this from the host machine.
                                # On cloud providers this creates an EBS volume, GCE PD, Azure Disk, etc.
```

On minikube, the `standard` storage class (provisioner: `k8s.io/minikube-hostpath`) fulfils this claim automatically — no pre-provisioning needed.

**Helm equivalent:** `helm/fastapppkg/templates/postgres-pvc.yaml`
`storage: 1Gi` → `{{ .Values.postgres.persistence.size }}`
Entire resource wrapped in `{{- if .Values.postgres.persistence.enabled }}`

---

## `postgres-deployment.yaml` — Postgres 15

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:                           # ← DEPLOYMENT spec: HOW to manage the postgres pods
  replicas: 1                   # Always 1 for a database — multiple replicas without clustering
                                # (e.g. Patroni) would cause split-brain data corruption.
  selector:                     # Which pods this Deployment owns.
    matchLabels:
      app: postgres
  template:                     # Blueprint for each postgres pod.
    metadata:
      labels:
        app: postgres           # Must match selector.matchLabels above and postgres Service selector.
    spec:                       # ← POD spec: WHAT runs inside each postgres pod
      containers:
        - name: postgres
          image: postgres:15    # Official Postgres image. Tag pins the major version —
                                # "latest" is risky for databases because major upgrades
                                # require a data migration (pg_upgrade).
          imagePullPolicy: IfNotPresent  # Pull from Docker Hub if not already cached locally.
          ports:
            - containerPort: 5432        # Standard Postgres port. Informational only.
          env:
            - name: POSTGRES_USER        # Superuser username created on first start.
              value: temporal            # Temporal server connects with this user.
            - name: POSTGRES_PASSWORD    # Password for the superuser.
              value: temporal            # In Helm this comes from a Secret, not a plain value.
            - name: POSTGRES_DB          # Name of the default database created on first start.
              value: temporal            # Temporal auto-setup also creates "temporal_visibility".
          readinessProbe:
            exec:
              command:
                - pg_isready             # Built-in Postgres utility that exits 0 when the server
                - -U                     # is accepting connections. Used by:
                - temporal               #  1. kubectl to determine pod readiness
            initialDelaySeconds: 5       #  2. deploykube.sh's kubectl wait command
            periodSeconds: 5             #  3. Temporal's initContainer (independently)
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data  # Where Postgres stores its data files inside the container.
              subPath: pgdata            # Mounts into a subdirectory of the PVC, not the root.
                                         # Required because Postgres refuses to start if the data
                                         # directory is non-empty, and PVC root contains lost+found.
      volumes:
        - name: postgres-data            # Declares the volume available to containers in this pod.
          persistentVolumeClaim:
            claimName: postgres-data     # Must match metadata.name in postgres-pvc.yaml.
```

**Helm equivalent:** `helm/fastapppkg/templates/postgres-deployment.yaml`
Credentials are pulled from a k8s Secret (`postgres-secret.yaml`) via `secretKeyRef` instead of plain `value:`.

---

## `postgres-service.yaml` — Postgres service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres                # DNS name Temporal uses to reach the database:
                                # postgres.<namespace>.svc.cluster.local
                                # This is the value set in temporal-deployment.yaml's POSTGRES_SEEDS.
  labels:
    service: postgres
spec:                           # ← SERVICE spec: HOW to route traffic to postgres pods
  selector:
    app: postgres               # Routes to pods with label app=postgres.
  ports:
    - port: 5432                # Standard Postgres port exposed on the Service.
      targetPort: 5432          # Port on the pod — same as containerPort.
  type: ClusterIP               # Not exposed outside the cluster. Access via:
                                # kubectl port-forward svc/postgres 5432:5432
```

**Helm equivalent:** `helm/fastapppkg/templates/postgres-service.yaml`
`port` → `{{ .Values.postgres.service.port }}`

---

## `temporal-deployment.yaml` — Temporal server

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal
spec:                           # ← DEPLOYMENT spec: HOW to manage the temporal pods
  replicas: 1                   # Single replica for dev. Production uses separate deployments
                                # per Temporal role (frontend, history, matching, worker).
  selector:                     # Which pods this Deployment owns.
    matchLabels:
      app: temporal
  template:                     # Blueprint for each temporal pod.
    metadata:
      labels:
        app: temporal           # Must match selector.matchLabels above and temporal Service selector.
    spec:                       # ← POD spec: WHAT runs inside each temporal pod
      initContainers:           # Run to completion BEFORE any main container starts.
                                # If an initContainer fails, the pod restarts it (and main
                                # containers never start). This enforces startup ordering.
        - name: wait-for-postgres
          image: postgres:15    # Reuse the postgres image — it has pg_isready built in.
          command:
            - sh
            - -c
            - |
              until pg_isready -h postgres -p 5432 -U temporal; do
                echo "Waiting for PostgreSQL..."; sleep 2;
              done              # Loops until Postgres accepts connections, then exits 0.
                                # "postgres" resolves via k8s DNS to postgres-service.yaml.
      containers:
        - name: temporal
          image: temporalio/auto-setup:1.25.0  # All-in-one image: runs frontend, history,
                                               # matching, and worker services in a single container.
                                               # Also runs schema setup on first boot.
                                               # Pin the tag — Temporal schema migrations are
                                               # version-specific and not always backwards compatible.
          imagePullPolicy: IfNotPresent
          ports:
            - name: grpc
              containerPort: 7233   # gRPC frontend — what the Python SDK and tctl connect to.
            - name: ui
              containerPort: 8233   # Temporal Web UI — browser dashboard for workflows.
          env:
            - name: DB
              value: postgres12     # Tells auto-setup which DB driver to use.
                                    # "postgres12" = PostgreSQL 12+ (covers Postgres 15).
                                    # Other options: sqlite, cassandra, mysql.
            - name: POSTGRES_SEEDS
              value: postgres       # Hostname(s) of the Postgres server. Matches the Service name.
                                    # In Helm this is the release-scoped name (e.g. myapp-postgres).
            - name: DB_PORT
              value: "5432"         # Postgres port. Must be a string in YAML env values.
            - name: POSTGRES_USER
              value: temporal       # Must match POSTGRES_USER in postgres-deployment.yaml.
            - name: POSTGRES_PWD
              value: temporal       # Must match POSTGRES_PASSWORD in postgres-deployment.yaml.
                                    # In Helm this comes from secretKeyRef, not a plain value.
            - name: DYNAMIC_CONFIG_FILE_PATH
              value: config/dynamicconfig/development-sql.yaml
                                    # Path inside the container to Temporal's dynamic config file.
                                    # The auto-setup image ships this file for SQL backends.
                                    # It sets dev-friendly defaults (low rate limits, verbose logging).
```

**Helm equivalent:** `helm/fastapppkg/templates/temporal-deployment.yaml`
`postgres` hostname → `{{ include "fastapppkg.postgres.fullname" . }}`
`POSTGRES_USER` / `POSTGRES_PWD` → pulled from Secret via `secretKeyRef`

---

## `temporal-service.yaml` — Temporal service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: temporal                # DNS name the FastAPI worker uses: temporal.<namespace>.svc.cluster.local
                                # This is the value in TEMPORAL_HOST env var in deployment.yaml.
  labels:
    service: temporal
spec:                           # ← SERVICE spec: HOW to route traffic to temporal pods
  selector:
    app: temporal               # Routes to pods with label app=temporal.
  ports:
    - name: grpc                # Named ports let you reference them by name in Ingress/probes.
      port: 7233                # gRPC frontend — SDK clients and tctl connect here.
      targetPort: 7233
    - name: ui
      port: 8233                # Temporal Web UI — forwarded to temporal-ingress.yaml.
      targetPort: 8233
  type: ClusterIP
```

**Helm equivalent:** `helm/fastapppkg/templates/temporal-service.yaml`
Port values → `{{ .Values.temporal.service.grpcPort }}` / `{{ .Values.temporal.service.uiPort }}`

---

## `temporal-ingress.yaml` — Temporal Web UI ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: temporal-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
                                # Temporal UI holds long-polling connections to stream workflow
                                # events. Default nginx timeout is 60s — this extends it to 1h
                                # to prevent the UI from constantly reconnecting.
spec:                           # ← INGRESS spec: HOW to route HTTP traffic to the Temporal Web UI
  rules:
    - host: temporal.test       # Add "$(minikube ip) temporal.test" to /etc/hosts.
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: temporal
                port:
                  number: 8233  # Routes to the "ui" port on the temporal Service — NOT 7233.
                                # 7233 is gRPC (binary protocol) and cannot be proxied by
                                # a standard HTTP ingress controller.
```

> **Why there is no ingress for gRPC (port 7233):** Ingress controllers speak HTTP/1.1 by default. gRPC uses HTTP/2 with binary framing. To expose 7233 externally you would need either a gRPC-aware ingress annotation (`nginx.ingress.kubernetes.io/backend-protocol: GRPC`) or a TCP proxy. For local use, `kubectl port-forward svc/temporal 7233:7233` is simpler.

---

## How raw manifest values map to `helm/fastapppkg/values.yaml`

Every hardcoded value in the `kube/` files has a corresponding key in `values.yaml`. Changing a value in `values.yaml` (or with `--set`) updates all templates that reference it.

```yaml
# values.yaml                          # kube/ hardcoded equivalent
fastapi:
  image:
    repository: kubefastapiapp         # image: kubefastapiapp:latest  (in deployment.yaml)
    tag: latest
    pullPolicy: Never                  # imagePullPolicy: Never
  replicaCount: 1                      # replicas: 2  (original had 2, Helm defaults to 1)
  service:
    type: ClusterIP                    # type: ClusterIP  (in service.yaml)
    port: 80                           # port: 80 / targetPort: 80
  ingress:
    enabled: true                      # (no equivalent — Helm can toggle the whole resource)
    host: kubefastapiapp.test          # host: kubefastapiapp.test  (in ingress.yaml)

temporal:
  image:
    repository: temporalio/auto-setup  # image: temporalio/auto-setup:1.25.0
    tag: "1.25.0"
    pullPolicy: IfNotPresent
  replicaCount: 1
  service:
    grpcPort: 7233                     # port: 7233  (in temporal-service.yaml)
    uiPort: 8233                       # port: 8233
  env:
    - name: DYNAMIC_CONFIG_FILE_PATH   # env.DYNAMIC_CONFIG_FILE_PATH  (in temporal-deployment.yaml)
      value: config/dynamicconfig/...

postgres:
  image:
    repository: postgres               # image: postgres:15
    tag: "15"
    pullPolicy: IfNotPresent
  auth:
    username: temporal                 # POSTGRES_USER: temporal  (in postgres-deployment.yaml)
    password: temporal                 # POSTGRES_PASSWORD: temporal
    database: temporal                 # POSTGRES_DB: temporal
  service:
    port: 5432                         # port: 5432  (in postgres-service.yaml)
  persistence:
    enabled: true                      # (no equivalent — Helm can toggle PVC creation)
    size: 1Gi                          # storage: 1Gi  (in postgres-pvc.yaml)
```

---

## Startup order

Both approaches enforce the same three-tier startup order:

```
1. postgres pod
   └─ readinessProbe (pg_isready) must pass
   └─ kubectl wait gates deploykube.sh here

2. temporal pod
   └─ initContainer: polls pg_isready on the postgres Service until exit 0
   └─ main container: auto-setup creates "temporal" + "temporal_visibility" DBs,
      runs schema migrations, then starts all Temporal services
   └─ kubectl wait gates deploykube.sh here

3. fastapi pod
   └─ lifespan startup: asyncio.create_task(run_worker()) connects to temporal:7233
   └─ /workflow/run endpoint is now live
```

---

## Apply commands

### Raw manifests (run via deploykube.sh)
```bash
bash kube/deploykube.sh
```

### Helm (one command, order is automatic)
```bash
eval $(minikube docker-env)
docker build -t kubefastapiapp:latest .
helm install myapp ./helm/fastapppkg

# upgrade after changes
helm upgrade myapp ./helm/fastapppkg
```

### Access services
```bash
# Add to /etc/hosts (run once):
echo "$(minikube ip)  kubefastapiapp.test temporal.test" | sudo tee -a /etc/hosts

# Trigger a workflow
curl -X POST http://kubefastapiapp.test/workflow/run

# Temporal Web UI
open http://temporal.test

# Temporal gRPC (local dev / tctl)
kubectl port-forward svc/temporal 7233:7233

# Postgres (local inspection)
kubectl port-forward svc/postgres 5432:5432
psql -h localhost -U temporal -d temporal
```

---

## Docker Compose alternatives

Two compose files live at the project root as a lighter alternative to Kubernetes for local development.

### `docker-compose.yaml` — all three services

Starts Postgres, Temporal, and FastAPI in a single command. Postgres gets a named volume so data survives restarts.

```
postgres  (healthcheck: pg_isready)
    ↓  service_healthy
temporal  (auto-setup: creates both DBs + runs migrations + starts server)
    ↓  service_started
fastapi   (restart: on-failure handles the race with Temporal startup)
```

```bash
docker compose up --build

# trigger a workflow
curl -X POST http://localhost:8000/workflow/run

# Temporal Web UI
open http://localhost:8233
```

### `docker-compose.external-pg.yaml` — external Postgres

Use when Postgres is already running elsewhere (local machine, RDS, Cloud SQL, etc.). Runs schema migrations as a one-shot container before starting Temporal.

```
temporal-migrate  (admin-tools: creates + migrates both schemas, then exits 0)
    ↓  service_completed_successfully
temporal          (auto-setup: schemas already exist, skips setup, starts server)
    ↓  service_started
fastapi
```

**Temporal requires exactly two databases / schema sets:**

| Database | Contains |
|---|---|
| `temporal` | Workflow execution state, activity state, timers, task queues |
| `temporal_visibility` | Search attributes, workflow listing, advanced visibility queries |

The `temporal-migrate` service runs `temporal-sql-tool` against both. Steps per database:
1. `create-database` — creates the database (skipped if it already exists)
2. `setup-schema -v 0.0` — creates the `schema_version` table
3. `update-schema -d <path>` — applies all versioned SQL files up to the latest

Schema files come from inside `temporalio/admin-tools:latest` at:
- `/etc/temporal/schema/postgresql/v12/temporal/versioned/`
- `/etc/temporal/schema/postgresql/v12/visibility/versioned/`

```bash
# 1. copy and fill in your postgres details
cp .env.external-pg.example .env

# 2. start (migrations run first, then temporal, then fastapi)
docker compose -f docker-compose.external-pg.yaml --env-file .env up --build

# re-running is safe — create-database is skipped, update-schema is idempotent
```

**Why `host.docker.internal` for a local Postgres?**
Containers cannot reach `localhost` on your machine — that resolves to the container itself. `host.docker.internal` is a Docker-managed hostname that points to the host machine's loopback. On Linux, the `extra_hosts: host.docker.internal:host-gateway` entry in both compose services wires this up (Docker Desktop on Mac/Windows handles it automatically).

**Postgres user needs `CREATE DATABASE` privilege** so `temporal-migrate` can create the two databases. If your existing user does not have it, grant it first:
```sql
ALTER USER temporal CREATEDB;
```
