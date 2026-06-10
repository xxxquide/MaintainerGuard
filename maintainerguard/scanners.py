"""Normalize scanner output into a small evidence-friendly model."""

from __future__ import annotations

from typing import Any

from .models import ScannerFinding


def normalize_severity(value: Any) -> str:
    if not isinstance(value, str):
        return "Unknown"
    severity = (value or "unknown").strip().lower()
    return {
        "error": "High",
        "warning": "Medium",
        "note": "Low",
        "none": "Low",
        "info": "Low",
        "informational": "Low",
        "low": "Low",
        "medium": "Medium",
        "moderate": "Medium",
        "high": "High",
        "critical": "Critical",
    }.get(severity, "Unknown")


def normalize_scanner_input(data: dict[str, Any]) -> list[ScannerFinding]:
    if not isinstance(data, dict):
        raise ValueError("Scanner input must be a JSON object")
    if "runs" in data:
        return _from_sarif(data)
    if _looks_like_trivy(data):
        return _from_trivy(data)
    if _looks_like_osv(data):
        return _from_osv(data)
    if "findings" in data:
        return _from_generic(data)
    if "results" in data and isinstance(data["results"], list):
        return _from_secret_results(data)
    return []


def _from_generic(data: dict[str, Any]) -> list[ScannerFinding]:
    scanner = str(data.get("scanner", "generic-scanner"))
    normalized = []
    for index, item in enumerate(data.get("findings", [])):
        if not isinstance(item, dict):
            continue
        finding_id = str(item.get("id", f"{scanner}-{index + 1}"))
        title = str(item.get("title", item.get("message", "Scanner finding")))
        description = str(item.get("description", title))
        category = _category(item, scanner, title)
        affected = item.get("affected_files") or item.get("affected") or []
        dependency = item.get("dependency")
        if dependency:
            affected = [*affected, str(dependency)]
        advisory_id = str(item.get("advisory_id", item.get("advisory", "")))
        normalized.append(
            ScannerFinding(
                id=finding_id,
                scanner=scanner,
                severity=normalize_severity(str(item.get("severity", "unknown"))),
                title=title,
                explanation=_maintainer_explanation(scanner, title, description, category),
                category=category,
                description=description,
                affected=[str(value) for value in affected],
                affected_dependency=str(dependency or ""),
                advisory_id=advisory_id,
                recommendation=str(item.get("recommendation") or _recommendation(category)),
                blocking=bool(item.get("blocking", False)),
            )
        )
    return normalized


def _from_sarif(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized = []
    for run_index, run in enumerate(data.get("runs", [])):
        scanner = (
            run.get("tool", {}).get("driver", {}).get("name")
            if isinstance(run, dict)
            else None
        ) or "SARIF scanner"
        for result_index, result in enumerate(run.get("results", [])):
            message = result.get("message", {})
            text = message.get("text", "Static analysis finding") if isinstance(message, dict) else str(message)
            affected = []
            for location in result.get("locations", []):
                uri = (
                    location.get("physicalLocation", {})
                    .get("artifactLocation", {})
                    .get("uri")
                )
                if uri:
                    affected.append(str(uri))
            finding_id = str(result.get("ruleId", f"sarif-{run_index + 1}-{result_index + 1}"))
            normalized.append(
                ScannerFinding(
                    id=finding_id,
                    scanner=str(scanner),
                    severity=normalize_severity(str(result.get("level", "warning"))),
                    title=text,
                    explanation=_maintainer_explanation(str(scanner), text, text, "code-scanning"),
                    category="code-scanning",
                    description=text,
                    affected=affected,
                    recommendation=_recommendation("code-scanning"),
                )
            )
    return normalized


def _looks_like_trivy(data: dict[str, Any]) -> bool:
    results = data.get("Results")
    if not isinstance(results, list):
        return False
    return any(
        isinstance(result, dict) and isinstance(result.get("Vulnerabilities"), list)
        for result in results
    )


def _from_trivy(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized = []
    for result in data.get("Results", []):
        if not isinstance(result, dict):
            continue
        target = _text(result.get("Target"), "container image or artifact")
        for index, vulnerability in enumerate(result.get("Vulnerabilities", [])):
            if not isinstance(vulnerability, dict):
                continue
            advisory_id = _text(vulnerability.get("VulnerabilityID"), f"trivy-{index + 1}")
            package = _text(vulnerability.get("PkgName"), "unknown-package")
            installed_version = _text(vulnerability.get("InstalledVersion"), "unknown-version")
            fixed_version = _text(vulnerability.get("FixedVersion"), "")
            title = _text(vulnerability.get("Title"), advisory_id)
            description = _text(vulnerability.get("Description"), title)
            recommendation = (
                f"Update {package} to {fixed_version} or rebuild the affected artifact/image."
                if fixed_version
                else _recommendation("dependency")
            )
            normalized.append(
                ScannerFinding(
                    id=advisory_id,
                    scanner="Trivy",
                    severity=normalize_severity(vulnerability.get("Severity")),
                    title=title,
                    explanation=(
                        f"Trivy reported {advisory_id} in {package} {installed_version} "
                        f"for {target}. Review whether the vulnerable package is reachable "
                        "and whether a rebuilt image or patched dependency is available."
                    ),
                    category="dependency",
                    description=description,
                    affected=[target, f"{package}@{installed_version}"],
                    affected_dependency=f"{package}@{installed_version}",
                    advisory_id=advisory_id,
                    recommendation=recommendation,
                )
            )
    return normalized


def _looks_like_osv(data: dict[str, Any]) -> bool:
    results = data.get("results")
    if not isinstance(results, list):
        return False
    return any(isinstance(item, dict) and "packages" in item for item in results)


def _from_osv(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized = []
    for result in data.get("results", []):
        for package in result.get("packages", []):
            package_data = package.get("package", {})
            package_name = package_data.get("name", "unknown-package")
            version = package_data.get("version", "unknown-version")
            for vulnerability in package.get("vulnerabilities", []):
                advisory_id = str(vulnerability.get("id", "OSV advisory"))
                summary = str(vulnerability.get("summary", vulnerability.get("details", "Dependency advisory")))
                normalized.append(
                    ScannerFinding(
                        id=advisory_id,
                        scanner="OSV",
                        severity=_osv_severity(vulnerability),
                        title=summary,
                        explanation=(
                            f"The supplied OSV result associates {package_name} {version} "
                            f"with {advisory_id}. Review reachability and available patched versions."
                        ),
                        category="dependency",
                        description=summary,
                        affected=[f"{package_name}@{version}"],
                        affected_dependency=f"{package_name}@{version}",
                        advisory_id=advisory_id,
                        recommendation=_recommendation("dependency"),
                    )
                )
    return normalized


def _from_secret_results(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized = []
    scanner = str(data.get("scanner", "secret-scanner"))
    for index, item in enumerate(data.get("results", [])):
        if not isinstance(item, dict):
            continue
        normalized.append(
            ScannerFinding(
                id=str(item.get("id", f"secret-{index + 1}")),
                scanner=scanner,
                severity=normalize_severity(str(item.get("severity", "high"))),
                title=str(item.get("title", "Possible secret reported by scanner")),
                explanation=(
                    "The supplied secret-scanner output reports a possible secret. "
                    "Verify the finding and rotate exposed credentials if confirmed."
                ),
                category="secret",
                description=str(item.get("description", item.get("title", "Possible secret reported by scanner"))),
                affected=[str(item.get("file"))] if item.get("file") else [],
                recommendation=_recommendation("secret"),
                blocking=bool(item.get("blocking", True)),
            )
        )
    return normalized


def _maintainer_explanation(scanner: str, title: str, description: str, category: str) -> str:
    return (
        f"{scanner} reported a {category} finding: {title}. Review the supplied scanner "
        f"evidence before merge. Scanner detail: {description}"
    )


def _category(item: dict[str, Any], scanner: str, title: str) -> str:
    explicit = item.get("category")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    combined = f"{scanner} {title} {item.get('description', '')}".lower()
    if item.get("dependency") or "osv" in combined or "advisory" in combined:
        return "dependency"
    if "secret" in combined or "credential" in combined or "gitleaks" in combined:
        return "secret"
    if "workflow" in combined or "supply" in combined or "provenance" in combined or "build" in combined:
        return "supply-chain"
    if "codeql" in combined or "semgrep" in combined or "static" in combined:
        return "static-analysis"
    return "generic"


def _recommendation(category: str) -> str:
    return {
        "dependency": "Review reachability, available patched versions, and whether the dependency change is required.",
        "secret": "Verify whether the value is real; if confirmed, rotate it and remove it from history as appropriate.",
        "supply-chain": "Review workflow permissions, release behavior, pinned actions, provenance, and build/install scripts.",
        "static-analysis": "Review the affected code path and confirm whether the scanner signal is reachable and actionable.",
        "code-scanning": "Review the affected code path and confirm whether the code-scanning alert is relevant to this change.",
    }.get(category, "Review the supplied scanner evidence and decide whether maintainer action is required.")


def _text(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _osv_severity(vulnerability: dict[str, Any]) -> str:
    database_severity = vulnerability.get("database_specific", {}).get("severity")
    normalized = normalize_severity(database_severity)
    if normalized != "Unknown":
        return normalized
    for item in vulnerability.get("severity", []):
        if not isinstance(item, dict):
            continue
        try:
            score = float(str(item.get("score", "")).split("/")[0])
        except ValueError:
            continue
        if score >= 9:
            return "Critical"
        if score >= 7:
            return "High"
        if score >= 4:
            return "Medium"
        return "Low"
    return "Unknown"
