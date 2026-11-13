import copy
import json
from pathlib import Path

from auditor.__main__ import audit
from auditor.rules import cnpj_is_valid

S = Path(__file__).parents[1] / "samples"
PROFILE = json.loads((S / "client_profile.json").read_text())
OK = json.loads((S / "payloads" / "nfse_1001_ok.json").read_text())
BAD_REGIME = json.loads((S / "payloads" / "nfse_1002_regime_and_wording.json").read_text())
BAD_DATA = json.loads((S / "payloads" / "nfse_1003_invalid_data.json").read_text())


def rules_hit(payload):
    return {f.rule for f in audit(payload, PROFILE)}


def test_clean_invoice_has_no_findings():
    assert audit(OK, PROFILE) == []


def test_regime_wording_and_zero_taxes():
    hit = rules_hit(BAD_REGIME)
    assert {"tax_regime", "description", "federal_taxes", "accountant", "delivery"} <= hit


def test_invalid_code_rate_and_cnpj():
    hit = rules_hit(BAD_DATA)
    assert {"service_code", "iss_rate", "iss_value", "taker_cnpj"} <= hit


def test_wording_check_ignores_accents_and_case():
    p = copy.deepcopy(OK)
    p["service"]["description"] = "Serviço com LOCAÇÃO DE EQUIPAMENTO"
    assert "description" in rules_hit(p)


def test_iss_value_must_match_rate():
    p = copy.deepcopy(OK)
    p["amounts"]["iss_value"] = 100.00
    assert "iss_value" in rules_hit(p)


def test_findings_sorted_by_severity():
    sev = [f.severity for f in audit(BAD_REGIME, PROFILE)]
    assert sev == sorted(sev, key=["high", "medium", "low"].index)


def test_cnpj_validation():
    assert cnpj_is_valid("11.222.333/0001-81")
    assert not cnpj_is_valid("98.765.432/0001-99")
