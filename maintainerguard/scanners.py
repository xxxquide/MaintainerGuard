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
    grouped: dict[tuple[str, str, str, str, str], int] = {}
    for run_index, run in enumerate(data.get("runs", [])):
        scanner = (
            run.get("tool", {}).get("driver", {}).get("name")
            if isinstance(run, dict)
            else None
        ) or "SARIF scanner"
        rules = _sarif_rules(run) if isinstance(run, dict) else {}
        for result_index, result in enumerate(run.get("results", [])):
            rule_id = str(result.get("ruleId", f"sarif-{run_index + 1}-{result_index + 1}"))
            rule = rules.get(rule_id, {})
            text = (
                _sarif_message_text(result.get("message", {}))
                or _sarif_rule_text(rule)
                or "Static analysis finding"
            )
            affected = []
            for location in result.get("locations", []):
                label = _sarif_location_label(location)
                if label:
                    affected.append(label)
            severity = normalize_severity(_sarif_level(result, rule))
            category = _sarif_category(result, rule, text)
            key = (str(scanner), rule_id, text, severity, category)
            if key in grouped:
                existing = normalized[grouped[key]]
                for label in affected:
                    if label not in existing.affected:
                        existing.affected.append(label)
                continue
            grouped[key] = len(normalized)
            normalized.append(
                ScannerFinding(
                    id=rule_id,
                    scanner=str(scanner),
                    severity=severity,
                    title=text,
                    explanation=_maintainer_explanation(str(scanner), text, text, category),
                    category=category,
                    description=text,
                    affected=_unique_text(affected),
                    recommendation=_recommendation(category),
                )
            )
    return normalized


def _sarif_rules(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tool = run.get("tool", {})
    rule_sets = []
    if isinstance(tool, dict):
        driver = tool.get("driver", {})
        if isinstance(driver, dict):
            rule_sets.append(driver)
        extensions = tool.get("extensions", [])
        if isinstance(extensions, list):
            rule_sets.extend(extension for extension in extensions if isinstance(extension, dict))

    rules_by_id = {}
    for rule_set in rule_sets:
        rules = rule_set.get("rules", [])
        if not isinstance(rules, list):
            continue
        rules_by_id.update(
            {
                str(rule.get("id")): rule
                for rule in rules
                if isinstance(rule, dict) and rule.get("id")
            }
        )
    return rules_by_id


def _sarif_level(result: dict[str, Any], rule: dict[str, Any]) -> str:
    explicit = result.get("level")
    if explicit:
        return str(explicit)
    default_configuration = rule.get("defaultConfiguration", {})
    if isinstance(default_configuration, dict) and default_configuration.get("level"):
        return str(default_configuration["level"])
    properties = rule.get("properties", {})
    if isinstance(properties, dict):
        problem = properties.get("problem")
        if isinstance(problem, dict) and problem.get("severity"):
            return str(problem["severity"])
        if properties.get("severity"):
            return str(properties["severity"])
    return "warning"


def _sarif_category(result: dict[str, Any], rule: dict[str, Any], text: str) -> str:
    properties = rule.get("properties", {})
    tags: list[str] = []
    if isinstance(properties, dict):
        raw_tags = properties.get("tags", [])
        if isinstance(raw_tags, list):
            tags.extend(str(tag).lower() for tag in raw_tags)
        for key in ("security-severity", "precision"):
            if properties.get(key):
                tags.append(str(properties[key]).lower())
    combined = " ".join(
        [
            str(result.get("ruleId", "")),
            text,
            " ".join(tags),
        ]
    ).lower()
    if any(term in combined for term in ("secret", "credential", "token", "password")):
        return "secret"
    if any(term in combined for term in ("dependency", "cve", "osv", "advisory")):
        return "dependency"
    if any(term in combined for term in ("workflow", "supply-chain", "provenance", "build")):
        return "supply-chain"
    if any(
        term in combined
        for term in ("security", "cwe", "injection", "xss", "auth", "crypto", "codeql")
    ):
        return "code-scanning"
    return "static-analysis"


def _sarif_message_text(message: Any) -> str:
    if isinstance(message, dict):
        for key in ("text", "markdown"):
            if message.get(key):
                return str(message[key])
        return ""
    if message:
        return str(message)
    return ""


def _sarif_rule_text(rule: dict[str, Any]) -> str:
    for key in ("shortDescription", "fullDescription"):
        value = rule.get(key)
        if isinstance(value, dict):
            for text_key in ("text", "markdown"):
                if value.get(text_key):
                    return str(value[text_key])
    return ""


def _sarif_location_label(location: dict[str, Any]) -> str:
    physical = location.get("physicalLocation", {}) if isinstance(location, dict) else {}
    artifact = physical.get("artifactLocation", {}) if isinstance(physical, dict) else {}
    uri = artifact.get("uri") if isinstance(artifact, dict) else None
    if not uri:
        return ""
    region = physical.get("region", {}) if isinstance(physical, dict) else {}
    start_line = region.get("startLine") if isinstance(region, dict) else None
    if isinstance(start_line, int) and start_line > 0:
        return f"{uri}:{start_line}"
    return str(uri)


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
    clean_title = title.rstrip(".")
    return (
        f"{scanner} reported a {category} finding: {clean_title}. Review the supplied scanner "
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


def _unique_text(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


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
