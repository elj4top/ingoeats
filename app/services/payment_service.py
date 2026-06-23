import hashlib
import hmac
import httpx
from app.core.config import settings

BASE = "https://api.paystack.co"


def _headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type":  "application/json",
    }


def register_merchant_subaccount(business_name: str, bank_code: str, account_number: str) -> str:
    try:
        res = httpx.post(f"{BASE}/subaccount", headers=_headers(), json={
            "business_name":     business_name,
            "settlement_bank":   bank_code,
            "account_number":    account_number,
            "percentage_charge": settings.PLATFORM_COMMISSION_PERCENT,
            "currency":          "KES",
        }, timeout=10)
        res.raise_for_status()
        data = res.json()
    except httpx.HTTPError as e:
        raise ValueError(f"Paystack subaccount request failed: {e}") from e

    if not data.get("status"):
        raise ValueError(data.get("message"))
    return data["data"]["subaccount_code"]


def register_rider_recipient(full_name: str, phone_number: str) -> str:
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]

    try:
        res = httpx.post(f"{BASE}/transferrecipient", headers=_headers(), json={
            "type":           "mobile_money",
            "name":           full_name,
            "account_number": phone_number,
            "bank_code":      "MPESA",
            "currency":       "KES",
        }, timeout=10)
        res.raise_for_status()
        data = res.json()
    except httpx.HTTPError as e:
        raise ValueError(f"Paystack recipient request failed: {e}") from e

    if not data.get("status"):
        raise ValueError(data.get("message"))
    return data["data"]["recipient_code"]


def initiate_payment(email: str, amount_kes: float, reference: str, subaccount_code: str, order_id: int) -> dict:
    try:
        res = httpx.post(f"{BASE}/transaction/initialize", headers=_headers(), json={
            "email":      email,
            "amount":     round(amount_kes * 100),
            "currency":   "KES",
            "reference":  reference,
            "subaccount": subaccount_code,
            "bearer":     "account",
            "metadata":   {"order_id": order_id},
        }, timeout=10)
        res.raise_for_status()
        data = res.json()
    except httpx.HTTPError as e:
        raise ValueError(f"Paystack transaction init failed: {e}") from e

    if not data.get("status"):
        raise ValueError(data.get("message"))

    return {
        "authorization_url": data["data"]["authorization_url"],
        "access_code":       data["data"]["access_code"],
        "reference":         data["data"]["reference"],
    }


def release_rider_payment(recipient_code: str, amount_kes: float, order_id: int) -> str:
    try:
        res = httpx.post(f"{BASE}/transfer", headers=_headers(), json={
            "source":    "balance",
            "amount":    round(amount_kes * 100),
            "recipient": recipient_code,
            "reason":    f"IngoEats delivery payout — Order #{order_id}",
            "currency":  "KES",
        }, timeout=10)
        res.raise_for_status()
        data = res.json()
    except httpx.TimeoutException as e:
        # Distinct from other HTTP errors: the transfer may have actually gone
        # through on Paystack's end even though we didn't get a response.
        # Don't auto-retry this — flag for manual reconciliation against the
        # Paystack dashboard before resending.
        raise ValueError(
            f"Paystack transfer timed out for order {order_id} — "
            f"verify manually in Paystack dashboard before retrying: {e}"
        ) from e
    except httpx.HTTPError as e:
        raise ValueError(f"Paystack transfer request failed: {e}") from e

    if not data.get("status"):
        raise ValueError(data.get("message"))
    return data["data"]["transfer_code"]


def verify_signature(payload_bytes: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload_bytes,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)