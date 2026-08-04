#!/usr/bin/env bash
# Regenerate real-scanner fixtures from actual scanner binaries.
# Versions used to produce the committed fixtures (2026-08-04):
#   trivy 0.73.0 | gitleaks 8.30.1 | osv-scanner 2.4.0 | semgrep OSS | reviewdog 0.21.0
# Requires those binaries on PATH. Run from the repository root.
set -euo pipefail
OUT="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

# Deliberately vulnerable fixture project: SAST findings, vulnerable deps,
# insecure Dockerfile, and two real-shaped leaked credentials.
mkdir -p "$WORK/src" "$WORK/config"
cat > "$WORK/src/app.py" <<'PY'
import subprocess, os, yaml, pickle
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
GITHUB_PAT = "ghp_16C7e42F292c6912E7710c838347Ae178B4a"
def run(cmd): subprocess.call(cmd, shell=True)
def load(d): return yaml.load(d)
def unpick(b): return pickle.loads(b)
def q(conn, uid): conn.execute("SELECT * FROM u WHERE id = '%s'" % uid)
PY
cat > "$WORK/requirements.txt" <<'REQ'
requests==2.19.1
PyYAML==5.1
Django==2.2.0
jinja2==2.10
urllib3==1.24.1
REQ
cat > "$WORK/Dockerfile" <<'DOCKER'
FROM python:3.9
ADD . /app
RUN pip install -r /app/requirements.txt
DOCKER
printf 'AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\nDB_PASSWORD=hunter2supersecret\n' > "$WORK/config/prod.env"
git -C "$WORK" init -q . && git -C "$WORK" add -A
git -C "$WORK" -c user.email=fixture@local -c user.name=fixture commit -qm init

cd "$WORK"
trivy fs --scanners vuln,misconfig,secret --format json   --quiet . > "$OUT/trivy-fs.json"
trivy fs --scanners vuln,misconfig,secret --format sarif  --quiet . > "$OUT/trivy-fs.sarif"
gitleaks dir . --report-format json  --report-path "$OUT/gitleaks.json"  --no-banner || true
gitleaks dir . --report-format sarif --report-path "$OUT/gitleaks.sarif" --no-banner || true
osv-scanner scan source -L requirements.txt --format json  > "$OUT/osv.json"  || true
osv-scanner scan source -L requirements.txt --format sarif > "$OUT/osv.sarif" || true
semgrep --config=p/default --json  --quiet . > "$OUT/semgrep.json"
# semgrep --sarif is intentionally not committed: it embeds full rule metadata
# for the whole ruleset (~2 MB). The SARIF path is covered by trivy-fs.sarif
# and gitleaks.sarif. Uncomment if you need it locally.
# semgrep --config=p/default --sarif --quiet . > "$OUT/semgrep.sarif"
echo "fixtures written to $OUT"
