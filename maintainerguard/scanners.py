"""Normalize scanner output into a small evidence-friendly model.

Format detection is explicit and positive: each adapter declares a structural
signature, and a payload that matches none of them raises
``UnsupportedScannerInput`` instead of normalizing to an empty list. Returning
an empty list for an unrecognised payload is indistinguishable from a clean
scan, which is the more dangerous of the two failure modes.
"""

from __future__ import annotations

from typing import Any

from .models import ScannerFinding


class UnsupportedScannerInput(ValueError):
    """Raised when no adapter recognises the supplied scanner payload."""


_SEVERITY_NAMES = {
    "error": "High",
    "warning": "Medium",
    "note": "Low",
    "none": "Low",
    "info": "Low",
    "informational": "Low",
    "unknown": "Unknown",
    "negligible": "Low",
    "low": "Low",
    "medium": "Medium",
    "moderate": "Medium",
    "high": "High",
    "critical": "Critical",
}

# GitHub's documented mapping for the SARIF security-severity property.
# docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning
_SECURITY_SEVERITY_BANDS = ((9.0, "Critical"), (7.0, "High"), (4.0, "Medium"), (0.0, "Low"))

# SARIF suppression states that represent an accepted maintainer decision.
_ACCEPTED_SUPPRESSIONS = {"accepted", "underreview", "under_review", ""}

# baselineState values meaning "this finding does not originate from this change".
_PRE_EXISTING_BASELINE_STATES = {"unchanged", "absent"}

_CWE_CATEGORY = (
    ({"798", "259", "321", "312", "532"}, "secret"),
    ({"1104", "494", "829"}, "supply-chain"),
    ({"1035", "937"}, "dependency"),
    ({"79", "89", "78", "94", "502", "611", "918", "22", "77", "20"}, "code-scanning"),
)


def normalize_severity(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _severity_from_score(float(value))
    if not isinstance(value, str):
        return "Unknown"
    severity = (value or "unknown").strip().lower()
    return _SEVERITY_NAMES.get(severity, "Unknown")


def _severity_from_score(score: float) -> str:
    for threshold, name in _SECURITY_SEVERITY_BANDS:
        if score >= threshold:
            return name
    return "Low"


def normalize_scanner_input(data: Any) -> list[ScannerFinding]:
    """Route a scanner payload to its adapter.

    Accepts a JSON object or, for scanners such as gitleaks that report a bare
    array of findings, a JSON array.
    """
    if isinstance(data, list):
        if _looks_like_gitleaks(data):
            return _from_gitleaks(data)
        raise UnsupportedScannerInput(
            "Scanner input is a JSON array that does not match a known scanner. "
            "Supported array format: gitleaks --report-format json."
        )
    if not isinstance(data, dict):
        raise UnsupportedScannerInput(
            f"Scanner input must be a JSON object or array, got {type(data).__name__}"
        )
    if isinstance(data.get("runs"), list):
        return _from_sarif(data)
    if _looks_like_trivy(data):
        return _from_trivy(data)
    if _looks_like_osv(data):
        return _from_osv(data)
    if _looks_like_semgrep(data):
        return _from_semgrep(data)
    if isinstance(data.get("findings"), list):
        return _from_generic(data)
    if _looks_like_secret_results(data):
        return _from_secret_results(data)
    raise UnsupportedScannerInput(
        "No scanner adapter recognised this payload. Recognised shapes: SARIF "
        "('runs'), Trivy ('Results'), OSV ('results[].packages'), Semgrep "
        "('results[].check_id'), gitleaks (top-level array), generic "
        "('findings'), secret results ('scanner' + 'results'). "
        f"Top-level keys seen: {sorted(str(key) for key in data)[:12]}."
    )


# --------------------------------------------------------------------------- #
# generic
# --------------------------------------------------------------------------- #


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


# --------------------------------------------------------------------------- #
# SARIF
# --------------------------------------------------------------------------- #


def _from_sarif(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized: list[ScannerFinding] = []
    grouped: dict[tuple[str, str, str, str, str], int] = {}
    for run_index, run in enumerate(data.get("runs", [])):
        if not isinstance(run, dict):
            continue
        scanner = run.get("tool", {}).get("driver", {}).get("name") or "SARIF scanner"
        rules = _sarif_rules(run)
        for result_index, result in enumerate(run.get("results", [])):
            if not isinstance(result, dict):
                continue
            if _sarif_is_suppressed(result) or _sarif_is_pre_existing(result):
                continue
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
            severity = _sarif_severity(result, rule)
            cwe = _sarif_cwe(rule)
            category = _sarif_category(result, rule, text, cwe)
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
                    cwe=cwe,
                    fingerprint=_sarif_fingerprint(result),
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


def _sarif_is_suppressed(result: dict[str, Any]) -> bool:
    """True when a maintainer has accepted a suppression for this result."""
    suppressions = result.get("suppressions")
    if not isinstance(suppressions, list) or not suppressions:
        return False
    for suppression in suppressions:
        if not isinstance(suppression, dict):
            continue
        status = str(suppression.get("status", "")).strip().lower().replace(" ", "")
        if status in _ACCEPTED_SUPPRESSIONS:
            return True
    return False


def _sarif_is_pre_existing(result: dict[str, Any]) -> bool:
    """True when baselineState marks the result as not originating here."""
    state = result.get("baselineState")
    if not isinstance(state, str):
        return False
    return state.strip().lower() in _PRE_EXISTING_BASELINE_STATES


def _sarif_fingerprint(result: dict[str, Any]) -> str:
    """A stable identity for cross-run deduplication and baseline comparison."""
    for key in ("fingerprints", "partialFingerprints"):
        values = result.get(key)
        if not isinstance(values, dict) or not values:
            continue
        for name in ("primaryLocationLineHash", *sorted(values)):
            if values.get(name):
                return str(values[name])
    return ""


def _sarif_severity(result: dict[str, Any], rule: dict[str, Any]) -> str:
    """CodeQL-style security-severity wins; then explicit SARIF levels."""
    score = _sarif_security_severity(result, rule)
    if score is not None:
        return _severity_from_score(score)
    return normalize_severity(_sarif_level(result, rule))


def _sarif_security_severity(result: dict[str, Any], rule: dict[str, Any]) -> float | None:
    for holder in (result, rule):
        properties = holder.get("properties", {}) if isinstance(holder, dict) else {}
        if not isinstance(properties, dict):
            continue
        raw = properties.get("security-severity", properties.get("security_severity"))
        if raw is None:
            continue
        try:
            return float(str(raw).strip())
        except (TypeError, ValueError):
            continue
    return None


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
        # Real CodeQL output uses a flat "problem.severity" key.
        for key in ("problem.severity", "severity"):
            if properties.get(key):
                return str(properties[key])
    return "warning"


def _sarif_cwe(rule: dict[str, Any]) -> str:
    """Extract CWE identifiers from rule tags, e.g. external/cwe/cwe-089."""
    properties = rule.get("properties", {}) if isinstance(rule, dict) else {}
    tags = properties.get("tags", []) if isinstance(properties, dict) else []
    found: list[str] = []
    for tag in tags if isinstance(tags, list) else []:
        text = str(tag).lower()
        if "cwe-" not in text:
            continue
        digits = "".join(
            character for character in text.rsplit("cwe-", 1)[1] if character.isdigit()
        )
        if digits:
            identifier = f"CWE-{int(digits)}"
            if identifier not in found:
                found.append(identifier)
    return ",".join(found)


def _sarif_category(
    result: dict[str, Any], rule: dict[str, Any], text: str, cwe: str = ""
) -> str:
    numbers = {item.split("-")[-1] for item in cwe.split(",") if item}
    for known, category in _CWE_CATEGORY:
        if numbers & known:
            return category
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


# --------------------------------------------------------------------------- #
# Trivy
# --------------------------------------------------------------------------- #

_TRIVY_CLASSES = ("Vulnerabilities", "Misconfigurations", "Secrets", "Licenses")


def _looks_like_trivy(data: dict[str, Any]) -> bool:
    results = data.get("Results")
    if not isinstance(results, list):
        return False
    if any(key in data for key in ("SchemaVersion", "ArtifactName", "ArtifactType")):
        return True
    return any(
        isinstance(result, dict)
        and any(isinstance(result.get(key), list) for key in _TRIVY_CLASSES)
        for result in results
    )


def _from_trivy(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized: list[ScannerFinding] = []
    for result in data.get("Results", []):
        if not isinstance(result, dict):
            continue
        target = _text(result.get("Target"), "container image or artifact")
        normalized.extend(_trivy_vulnerabilities(result, target))
        normalized.extend(_trivy_misconfigurations(result, target))
        normalized.extend(_trivy_secrets(result, target))
        normalized.extend(_trivy_licenses(result, target))
    return normalized


def _trivy_vulnerabilities(result: dict[str, Any], target: str) -> list[ScannerFinding]:
    normalized = []
    for index, vulnerability in enumerate(result.get("Vulnerabilities") or []):
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


def _trivy_misconfigurations(result: dict[str, Any], target: str) -> list[ScannerFinding]:
    normalized = []
    for index, misconfiguration in enumerate(result.get("Misconfigurations") or []):
        if not isinstance(misconfiguration, dict):
            continue
        if str(misconfiguration.get("Status", "FAIL")).strip().upper() not in {"FAIL", ""}:
            continue
        identifier = _text(
            misconfiguration.get("ID") or misconfiguration.get("AVDID"),
            f"trivy-misconf-{index + 1}",
        )
        title = _text(misconfiguration.get("Title"), identifier)
        description = _text(misconfiguration.get("Description"), title)
        resolution = _text(misconfiguration.get("Resolution"), _recommendation("supply-chain"))
        location = target
        cause = misconfiguration.get("CauseMetadata")
        if isinstance(cause, dict):
            start_line = cause.get("StartLine")
            if isinstance(start_line, int) and start_line > 0:
                location = f"{target}:{start_line}"
        normalized.append(
            ScannerFinding(
                id=identifier,
                scanner="Trivy",
                severity=normalize_severity(misconfiguration.get("Severity")),
                title=title,
                explanation=(
                    f"Trivy reported misconfiguration {identifier} in {location}. "
                    "Review whether the flagged setting is intentional for this repository."
                ),
                category="supply-chain",
                description=description,
                affected=[location],
                recommendation=resolution,
            )
        )
    return normalized


def _trivy_secrets(result: dict[str, Any], target: str) -> list[ScannerFinding]:
    normalized = []
    for index, secret in enumerate(result.get("Secrets") or []):
        if not isinstance(secret, dict):
            continue
        identifier = _text(secret.get("RuleID"), f"trivy-secret-{index + 1}")
        title = _text(secret.get("Title"), identifier)
        start_line = secret.get("StartLine")
        location = (
            f"{target}:{start_line}"
            if isinstance(start_line, int) and start_line > 0
            else target
        )
        normalized.append(
            ScannerFinding(
                id=identifier,
                scanner="Trivy",
                severity=normalize_severity(secret.get("Severity")),
                title=title,
                explanation=(
                    f"Trivy reported a possible secret ({identifier}) in {location}. "
                    "Verify the finding and rotate the credential if it is real."
                ),
                category="secret",
                description=_text(secret.get("Match"), title),
                affected=[location],
                recommendation=_recommendation("secret"),
            )
        )
    return normalized


def _trivy_licenses(result: dict[str, Any], target: str) -> list[ScannerFinding]:
    normalized = []
    for index, license_finding in enumerate(result.get("Licenses") or []):
        if not isinstance(license_finding, dict):
            continue
        name = _text(license_finding.get("Name"), f"trivy-license-{index + 1}")
        package = _text(license_finding.get("PkgName"), "")
        file_path = _text(license_finding.get("FilePath"), target)
        affected = [file_path]
        if package:
            affected.append(package)
        normalized.append(
            ScannerFinding(
                id=f"license:{name}",
                scanner="Trivy",
                severity=normalize_severity(license_finding.get("Severity")),
                title=f"License {name} reported for {package or file_path}",
                explanation=(
                    f"Trivy reported license {name} for {package or file_path}. "
                    "Confirm the license is compatible with this project's policy."
                ),
                category="license",
                description=_text(license_finding.get("Category"), name),
                affected=affected,
                affected_dependency=package,
                recommendation=_recommendation("license"),
            )
        )
    return normalized


# --------------------------------------------------------------------------- #
# OSV
# --------------------------------------------------------------------------- #


def _looks_like_osv(data: dict[str, Any]) -> bool:
    results = data.get("results")
    if not isinstance(results, list):
        return False
    return any(isinstance(item, dict) and "packages" in item for item in results)


def _from_osv(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized = []
    for result in data.get("results", []):
        if not isinstance(result, dict):
            continue
        source = result.get("source", {})
        source_path = str(source.get("path", "")) if isinstance(source, dict) else ""
        for package in result.get("packages", []):
            if not isinstance(package, dict):
                continue
            package_data = package.get("package", {})
            if not isinstance(package_data, dict):
                package_data = {}
            package_name = package_data.get("name", "unknown-package")
            version = package_data.get("version", "unknown-version")
            for vulnerability in package.get("vulnerabilities", []):
                if not isinstance(vulnerability, dict):
                    continue
                advisory_id = str(vulnerability.get("id", "OSV advisory"))
                summary = str(
                    vulnerability.get(
                        "summary", vulnerability.get("details", "Dependency advisory")
                    )
                )
                affected = [f"{package_name}@{version}"]
                if source_path:
                    affected.insert(0, source_path)
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
                        affected=affected,
                        affected_dependency=f"{package_name}@{version}",
                        advisory_id=advisory_id,
                        recommendation=_recommendation("dependency"),
                    )
                )
    return normalized


def _osv_severity(vulnerability: dict[str, Any]) -> str:
    database_specific = vulnerability.get("database_specific", {})
    database_severity = (
        database_specific.get("severity") if isinstance(database_specific, dict) else None
    )
    normalized = normalize_severity(database_severity)
    if normalized != "Unknown":
        return normalized
    for item in vulnerability.get("severity", []):
        if not isinstance(item, dict):
            continue
        try:
            score = float(str(item.get("score", "")).split("/")[0])
        except ValueError:
            # CVSS vector strings carry no directly comparable numeric score.
            continue
        return _severity_from_score(score)
    return "Unknown"


# --------------------------------------------------------------------------- #
# Semgrep native JSON
# --------------------------------------------------------------------------- #


def _looks_like_semgrep(data: dict[str, Any]) -> bool:
    results = data.get("results")
    if not isinstance(results, list):
        return False
    return any(
        isinstance(item, dict) and ("check_id" in item or "extra" in item) for item in results
    )


def _from_semgrep(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized = []
    for index, item in enumerate(data.get("results", [])):
        if not isinstance(item, dict):
            continue
        check_id = str(item.get("check_id", f"semgrep-{index + 1}"))
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        metadata = extra.get("metadata") if isinstance(extra.get("metadata"), dict) else {}
        message = str(extra.get("message", check_id)).strip()
        path = str(item.get("path", ""))
        start = item.get("start") if isinstance(item.get("start"), dict) else {}
        line = start.get("line")
        location = f"{path}:{line}" if path and isinstance(line, int) and line > 0 else path
        cwe = _semgrep_cwe(metadata)
        category = _sarif_category({"ruleId": check_id}, {}, message, cwe)
        recommendation = _recommendation(category)
        fix = extra.get("fix")
        if isinstance(fix, str) and fix.strip():
            recommendation = (
                f"Semgrep suggests replacing the flagged expression with `{fix.strip()}`. "
                + recommendation
            )
        normalized.append(
            ScannerFinding(
                id=check_id,
                scanner=str(data.get("scanner") or "Semgrep"),
                severity=normalize_severity(extra.get("severity", "warning")),
                title=message.splitlines()[0] if message else check_id,
                explanation=_maintainer_explanation(
                    "Semgrep", message or check_id, message, category
                ),
                category=category,
                description=message,
                affected=[location] if location else [],
                recommendation=recommendation,
                cwe=cwe,
                fingerprint=str(extra.get("fingerprint", "")),
            )
        )
    return normalized


def _semgrep_cwe(metadata: dict[str, Any]) -> str:
    raw = metadata.get("cwe")
    entries = raw if isinstance(raw, list) else [raw] if raw else []
    found: list[str] = []
    for entry in entries:
        text = str(entry).upper()
        if "CWE-" not in text:
            continue
        digits = "".join(
            character for character in text.split("CWE-", 1)[1][:8] if character.isdigit()
        )
        if digits:
            identifier = f"CWE-{int(digits)}"
            if identifier not in found:
                found.append(identifier)
    return ",".join(found)


# --------------------------------------------------------------------------- #
# gitleaks native JSON (top-level array)
# --------------------------------------------------------------------------- #

_GITLEAKS_KEYS = {"RuleID", "Secret", "Match", "Fingerprint", "Entropy", "StartLine"}


def _looks_like_gitleaks(data: list[Any]) -> bool:
    if not data:
        # An empty array is the shape gitleaks writes for a clean scan.
        return True
    return any(isinstance(item, dict) and _GITLEAKS_KEYS & set(item) for item in data)


def _from_gitleaks(data: list[Any]) -> list[ScannerFinding]:
    normalized = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        rule_id = _text(item.get("RuleID"), f"gitleaks-{index + 1}")
        description = _text(item.get("Description"), f"Possible secret matched by rule {rule_id}")
        file_path = _text(item.get("File"), "")
        start_line = item.get("StartLine")
        location = (
            f"{file_path}:{start_line}"
            if file_path and isinstance(start_line, int) and start_line > 0
            else file_path
        )
        commit = _text(item.get("Commit"), "")
        commit_detail = f" in commit {commit[:12]}" if commit else ""
        normalized.append(
            ScannerFinding(
                id=rule_id,
                scanner="gitleaks",
                severity="High",
                title=description,
                explanation=(
                    f"gitleaks matched rule {rule_id} at "
                    f"{location or 'an unspecified location'}{commit_detail}. "
                    "Verify the finding and rotate the credential if it is real."
                ),
                category="secret",
                description=description,
                affected=[location] if location else [],
                recommendation=_recommendation("secret"),
                fingerprint=_text(item.get("Fingerprint"), ""),
            )
        )
    return normalized


# --------------------------------------------------------------------------- #
# generic secret result arrays
# --------------------------------------------------------------------------- #


def _looks_like_secret_results(data: dict[str, Any]) -> bool:
    """Legacy shape: an explicit scanner name plus a plain result array.

    The explicit ``scanner`` key is required so that native tool output which
    also uses ``results`` (Semgrep, OSV) can never land here by accident.
    """
    if not isinstance(data.get("results"), list):
        return False
    return bool(str(data.get("scanner", "")).strip())


def _from_secret_results(data: dict[str, Any]) -> list[ScannerFinding]:
    normalized = []
    scanner = str(data.get("scanner", "secret-scanner"))
    for index, item in enumerate(data.get("results", [])):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "Possible secret reported by scanner"))
        normalized.append(
            ScannerFinding(
                id=str(item.get("id", f"secret-{index + 1}")),
                scanner=scanner,
                severity=normalize_severity(str(item.get("severity", "high"))),
                title=title,
                explanation=(
                    "The supplied secret-scanner output reports a possible secret. "
                    "Verify the finding and rotate exposed credentials if confirmed."
                ),
                category="secret",
                description=str(item.get("description", title)),
                affected=[str(item.get("file"))] if item.get("file") else [],
                recommendation=_recommendation("secret"),
                blocking=bool(item.get("blocking", False)),
            )
        )
    return normalized


# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #


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
        "license": "Confirm the reported license is compatible with the project's licensing policy.",
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
