#!/usr/bin/env bash
set -euo pipefail

# Compatibility shims for local env files.
if [[ -n "${MODAL_KEY_ID:-}" && -z "${MODAL_TOKEN_ID:-}" ]]; then
  export MODAL_TOKEN_ID="${MODAL_KEY_ID}"
elif [[ -n "${MODAL_KEY:-}" && -z "${MODAL_TOKEN_ID:-}" ]]; then
  export MODAL_TOKEN_ID="${MODAL_KEY}"
fi
if [[ -n "${MODAL_SECRET:-}" && -z "${MODAL_TOKEN_SECRET:-}" ]]; then
  export MODAL_TOKEN_SECRET="${MODAL_SECRET}"
fi

if ! command -v modal >/dev/null 2>&1; then
  echo "missing modal CLI; install with: python -m pip install modal" >&2
  exit 2
fi

modal token info | sed -E 's/^(Token: ).*/\1[redacted]/'

report_path="$(mktemp)"
modal billing report --for "this month" --json > "${report_path}"
python3 - "${report_path}" <<'PY'
import decimal
import json
import sys

rows = json.load(open(sys.argv[1]))
total = sum(decimal.Decimal(str(row.get("Cost", "0"))) for row in rows)
by_description = {}
for row in rows:
    description = row.get("Description", "")
    by_description[description] = by_description.get(description, decimal.Decimal("0")) + decimal.Decimal(str(row.get("Cost", "0")))

print(f"billing_rows={len(rows)}")
print(f"month_to_date_pre_credit_usd={total:.2f}")
print("top_descriptions_pre_credit_usd:")
for description, cost in sorted(by_description.items(), key=lambda item: item[1], reverse=True)[:10]:
    print(f"  {description or '[unknown]'}: {cost:.2f}")
print("note=Modal billing reports are pre-credit/pre-reservation; exact remaining grants require the Usage & Billing dashboard.")
print("starter_monthly_free_credit_remaining=0.00" if total >= decimal.Decimal("30") else f"starter_monthly_free_credit_remaining={decimal.Decimal('30') - total:.2f}")
print("team_monthly_free_credit_remaining=0.00" if total >= decimal.Decimal("100") else f"team_monthly_free_credit_remaining={decimal.Decimal('100') - total:.2f}")
PY
rm -f "${report_path}"
