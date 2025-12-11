{{/*
Expand the name of the chart.
*/}}
{{- define "kluisz-ai-canvas.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "kluisz-ai-canvas.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "kluisz-ai-canvas.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "kluisz-ai-canvas.labels" -}}
helm.sh/chart: {{ include "kluisz-ai-canvas.chart" . }}
{{ include "kluisz-ai-canvas.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels for kluisz app
*/}}
{{- define "kluisz-ai-canvas.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kluisz-ai-canvas.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: kluisz
{{- end }}

{{/*
Selector labels for postgresql
*/}}
{{- define "kluisz-ai-canvas.postgresql.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kluisz-ai-canvas.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: postgresql
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "kluisz-ai-canvas.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kluisz-ai-canvas.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL service name
*/}}
{{- define "kluisz-ai-canvas.postgresql.fullname" -}}
{{- printf "%s-postgresql" (include "kluisz-ai-canvas.fullname" .) }}
{{- end }}

{{/*
PostgreSQL connection string
*/}}
{{- define "kluisz-ai-canvas.postgresql.connectionString" -}}
{{- $host := include "kluisz-ai-canvas.postgresql.fullname" . }}
{{- $port := .Values.postgresql.service.port }}
{{- $user := .Values.postgresql.auth.username }}
{{- $password := .Values.postgresql.auth.password }}
{{- $database := .Values.postgresql.auth.database }}
{{- printf "postgresql://%s:%s@%s:%d/%s" $user $password $host (int $port) $database }}
{{- end }}
