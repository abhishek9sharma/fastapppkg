{{/*
Expand the name of the chart.
*/}}
{{- define "fastapppkg.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "fastapppkg.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
FastAPI component name
*/}}
{{- define "fastapppkg.fastapi.fullname" -}}
{{- printf "%s-fastapi" (include "fastapppkg.fullname" .) }}
{{- end }}

{{/*
Temporal component name
*/}}
{{- define "fastapppkg.temporal.fullname" -}}
{{- printf "%s-temporal" (include "fastapppkg.fullname" .) }}
{{- end }}

{{/*
Postgres component name
*/}}
{{- define "fastapppkg.postgres.fullname" -}}
{{- printf "%s-postgres" (include "fastapppkg.fullname" .) }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "fastapppkg.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
