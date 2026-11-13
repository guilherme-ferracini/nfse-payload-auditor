# NFS-e Payload Auditor

[![tests](https://github.com/guilherme-ferracini/nfse-payload-auditor/actions/workflows/tests.yml/badge.svg)](https://github.com/guilherme-ferracini/nfse-payload-auditor/actions)

Audits the **service invoices (NFS-e) a company issues through an API integration** against its tax profile, and flags what would cause a tax problem **before it scales**: a wrong tax regime flag, wording that contradicts the tax planning, ISS outside the legal range, federal taxes missing, invalid CNPJs. Each invoice gets a status: **OK, REVIEW or BLOCK**.

## Why this exists

More and more companies issue invoices automatically from their own systems (a SaaS checkout, an ERP, a webhook) and the accountant only finds out what was sent when something goes wrong. In an advisory engagement I audited a client's live invoicing integration and found exactly this kind of issue in invoices already issued: a wrong regime flag, zero federal taxes and wording that contradicted how the service was classified.

This repo turns that manual audit into code, with fictional data:

- **One rule = one small function.** Easy to read, test and extend (`auditor/rules.py`).
- **Severity drives action.** Any high finding blocks the invoice; medium asks for review; low is housekeeping.
- **Company-specific policy as data.** Approved service codes, expected ISS rate and forbidden wording live in the client profile JSON, not in code.

## Rules

| Rule | Severity | Checks |
|---|---|---|
| `provider_cnpj` | high | the issuer is the company in the profile |
| `tax_regime` | high | the "Simples Nacional optant" flag matches the company's real regime |
| `service_code` | high | the service code is in the approved list |
| `description` | high | no wording that contradicts the tax planning (accent/case-insensitive) |
| `iss_rate` / `iss_value` | high / medium | ISS within the legal 2%–5% range, equal to the expected rate, value = base × rate |
| `taker_cnpj` | high | taker CNPJ has valid check digits |
| `federal_taxes` | medium | federal taxes are not all zero when the regime expects them |
| `accountant` | low | the accounting firm is registered on the invoice |
| `delivery` | low | the invoice will be e-mailed to the taker |

## Quickstart

```bash
python -m auditor samples/client_profile.json samples/payloads/*.json --out out/audit.md
python -m pytest -q
```

```
| Invoice | Value (R$) | High | Medium | Low | Status |
|---|---:|---:|---:|---:|---|
| 1001 | 4,800.00 | 0 | 0 | 0 | OK |
| 1002 | 1,200.00 | 2 | 1 | 2 | BLOCK |
| 1003 | 2,500.00 | 4 | 0 | 0 | BLOCK |
```

Full report: [`samples/sample_output/audit.md`](samples/sample_output/audit.md)

## Integration idea

Run the audit as a pre-issue check in the invoicing pipeline (or on a webhook after each issue) and alert the accounting team on any BLOCK, before the next invoice repeats the mistake.

## Notes

- The payload format is a simplified, provider-neutral JSON inspired by the national NFS-e standard. An adapter maps each provider's API format to it.
- All companies, CNPJs and invoices are fictional.

## License

MIT
