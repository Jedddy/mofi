# Ko-fi webhook fixtures

These fixtures contain deterministic placeholders only. They are decoded values
from Ko-fi's form-encoded `data` field; adapter tests encode them back into the
form field before sending a request.

| Fixture | Evidence | Purpose |
| --- | --- | --- |
| `donation.json` | Sanitized legacy Mofi sample | Donation baseline |
| `subscription.json` | Sanitized legacy Mofi sample | Subscription baseline |
| `commission.synthetic.json` | Synthetic; authenticated capture still required | Conservative Commission common fields |
| `shop_order_physical.json` | Sanitized legacy Mofi sample | Physical order and shipping |
| `shop_order_digital.json` | Synthetic variant of the legacy sample | Digital order without shipping |
| `donation_private.json` | Synthetic variant of the legacy sample | Private payment without a message |
| `donation_extra_field.json` | Synthetic variant of the legacy sample | Forward-compatible added field |
| `unknown_payment.json` | Synthetic | Future payment type |
| `duplicate_first.json` | Synthetic retry pair | First delivery of a message ID |
| `duplicate_retry.json` | Synthetic retry pair | Repeated delivery of the same message ID |
| `invalid_token.json` | Synthetic variant of the legacy sample | Verification failure |
| `malformed.txt` | Synthetic | Invalid JSON form value |

No fixture is presented as a current authenticated Ko-fi capture. Before a
release claims verified Commission compatibility, replace or supplement the
synthetic Commission fixture with a redacted delivery generated from the
authenticated Ko-fi Webhooks page.
