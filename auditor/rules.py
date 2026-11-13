"""Audit rules for NFS-e payloads sent by an API integration.

Each rule is a small function: (payload, profile) -> list of findings. Adding a
rule means adding a function to RULES and a test."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Callable, Dict, List

HIGH, MEDIUM, LOW = "high", "medium", "low"


@dataclass
class Finding:
    severity: str
    rule: str
    message: str


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()


def cnpj_is_valid(cnpj: str) -> bool:
    digits = re.sub(r"\D", "", cnpj or "")
    if len(digits) != 14 or len(set(digits)) == 1:
        return False

    def check(base: str, weights: List[int]) -> str:
        rest = sum(int(d) * w for d, w in zip(base, weights)) % 11
        return "0" if rest < 2 else str(11 - rest)

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = check(digits[:12], w1)
    return digits[12:] == d1 + check(digits[:12] + d1, [6] + w1)


def tax_regime(p: Dict, prof: Dict) -> List[Finding]:
    optant = p["provider"].get("simples_nacional_optant")
    expected = prof["tax_regime"] == "simples"
    if optant != expected:
        return [Finding(HIGH, "tax_regime",
                        f"Invoice declares Simples Nacional optant = {optant}, but the company is in {prof['tax_regime']}.")]
    return []


def provider_cnpj(p: Dict, prof: Dict) -> List[Finding]:
    if re.sub(r"\D", "", p["provider"]["cnpj"]) != re.sub(r"\D", "", prof["cnpj"]):
        return [Finding(HIGH, "provider_cnpj", "Provider CNPJ differs from the company profile.")]
    return []


def taker_cnpj(p: Dict, prof: Dict) -> List[Finding]:
    cnpj = p["taker"].get("cnpj", "")
    if not cnpj_is_valid(cnpj):
        return [Finding(HIGH, "taker_cnpj", f"Taker CNPJ {cnpj or '(empty)'} has invalid check digits.")]
    return []


def service_code(p: Dict, prof: Dict) -> List[Finding]:
    code = p["service"]["code"]
    if code not in prof["allowed_service_codes"]:
        return [Finding(HIGH, "service_code",
                        f"Service code {code} is not in the company's approved list {prof['allowed_service_codes']}.")]
    return []


def forbidden_wording(p: Dict, prof: Dict) -> List[Finding]:
    desc = _norm(p["service"]["description"])
    hits = [t for t in prof["forbidden_terms"] if _norm(t) in desc]
    if hits:
        return [Finding(HIGH, "description",
                        f"Description uses wording that contradicts the tax planning: {', '.join(hits)}.")]
    return []


def iss(p: Dict, prof: Dict) -> List[Finding]:
    a = p["amounts"]
    out: List[Finding] = []
    if not 0.02 <= a["iss_rate"] <= 0.05:
        out.append(Finding(HIGH, "iss_rate", f"ISS rate {a['iss_rate']:.2%} is outside the legal 2%-5% range."))
    elif abs(a["iss_rate"] - prof["iss_rate"]) > 1e-9:
        out.append(Finding(MEDIUM, "iss_rate", f"ISS rate {a['iss_rate']:.2%} differs from the expected {prof['iss_rate']:.2%}."))
    expected = round(a["service_value"] * a["iss_rate"], 2)
    if abs(expected - a["iss_value"]) > 0.01:
        out.append(Finding(HIGH, "iss_value", f"ISS value {a['iss_value']:.2f} != service value x rate ({expected:.2f})."))
    return out


def federal_taxes(p: Dict, prof: Dict) -> List[Finding]:
    a = p["amounts"]
    if prof["federal_taxes_expected"] and not any(a.get(k) for k in ("pis", "cofins", "csll", "irrf")):
        return [Finding(MEDIUM, "federal_taxes", "All federal taxes are zero, but the company's regime expects them.")]
    return []


def accountant(p: Dict, prof: Dict) -> List[Finding]:
    if re.sub(r"\D", "", p.get("accountant", {}).get("cnpj", "")) != re.sub(r"\D", "", prof["accountant_cnpj"]):
        return [Finding(LOW, "accountant", "Accounting firm is not registered on the invoice.")]
    return []


def delivery(p: Dict, prof: Dict) -> List[Finding]:
    if not p.get("send_email_to_taker") or not p["taker"].get("email"):
        return [Finding(LOW, "delivery", "Invoice will not be e-mailed to the taker (disabled or no e-mail).")]
    return []


RULES: List[Callable[[Dict, Dict], List[Finding]]] = [
    provider_cnpj, tax_regime, service_code, forbidden_wording, iss, federal_taxes, taker_cnpj, accountant, delivery,
]
