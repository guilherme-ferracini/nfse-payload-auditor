# NFS-e audit: Orbita Tecnologia Ltda (fictional)

| Invoice | Value (R$) | High | Medium | Low | Status |
|---|---:|---:|---:|---:|---|
| 1001 | 4,800.00 | 0 | 0 | 0 | OK |
| 1002 | 1,200.00 | 2 | 1 | 2 | BLOCK |
| 1003 | 2,500.00 | 4 | 0 | 0 | BLOCK |

## Invoice 1001 (2026-10-05)
- No findings.

## Invoice 1002 (2026-10-07)
- **HIGH** `tax_regime`: Invoice declares Simples Nacional optant = True, but the company is in regime_normal.
- **HIGH** `description`: Description uses wording that contradicts the tax planning: locacao de equipamento.
- **MEDIUM** `federal_taxes`: All federal taxes are zero, but the company's regime expects them.
- **LOW** `accountant`: Accounting firm is not registered on the invoice.
- **LOW** `delivery`: Invoice will not be e-mailed to the taker (disabled or no e-mail).

## Invoice 1003 (2026-10-09)
- **HIGH** `service_code`: Service code 14.01.01 is not in the company's approved list ['01.05.01', '01.07.01'].
- **HIGH** `iss_rate`: ISS rate 1.50% is outside the legal 2%-5% range.
- **HIGH** `iss_value`: ISS value 40.00 != service value x rate (37.50).
- **HIGH** `taker_cnpj`: Taker CNPJ 98.765.432/0001-99 has invalid check digits.
