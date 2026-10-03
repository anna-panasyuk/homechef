"""End-to-end smoke test: browse, login, checkout, pay, close, handover."""
import re
import sys
import time
from datetime import date
import httpx

BASE = "http://localhost:8000"
SUNITA = "+913333333333"


def _sms(c: httpx.Client, phone: str, text: str) -> str:
    r = c.post("/phone/sms", data={"cook_phone": phone, "text": text})
    assert r.status_code == 200, (r.status_code, r.text)
    return r.json()["reply_text"]


def main() -> int:
    with httpx.Client(base_url=BASE, follow_redirects=True, timeout=15) as c:
        r = c.get("/")
        assert r.status_code == 200, r.status_code
        ids = [int(x) for x in re.findall(r'href="/dish/(\d+)"', r.text)]
        assert ids, "no open listings on index"
        lid = ids[0]
        print(f"ok  browse / (listing #{lid})")

        r = c.get(f"/dish/{lid}")
        assert r.status_code == 200
        print("ok  dish page")

        email = f"smoke+{int(time.time())}@example.com"
        r = c.post("/signup", data={"name": "Smoke", "email": email, "password": "smoke1234"})
        assert r.status_code == 200 and str(r.url).endswith("/")
        print("ok  signup/login")

        r = c.get(f"/checkout/{lid}")
        assert r.status_code == 200
        r = c.post(f"/checkout/{lid}", data={"qty": 1})
        assert r.status_code == 200
        m = re.search(r"/order/(\d+)", str(r.url))
        assert m, f"no order id in {r.url}"
        oid = int(m.group(1))
        print(f"ok  checkout -> order #{oid}")

        r = c.post(f"/pay/{oid}")
        assert r.status_code == 200
        r = c.get(f"/order/{oid}")
        assert "Pickup address" in r.text, "address missing after pay"
        print("ok  pay (address visible)")

        today = date.today().isoformat()
        r = c.post(f"/admin/close-orders?date={today}")
        assert r.status_code == 200
        r = c.get(f"/order/{oid}")
        assert "closed" in r.text
        print("ok  close-orders")

        r = c.post(f"/admin/handover/{oid}")
        assert r.status_code == 200
        r = c.get(f"/order/{oid}")
        assert "handed_over" in r.text
        print("ok  handover")

        reply = _sms(c, SUNITA, "kal 15 dal chawal 80")
        assert "confirm" in reply.lower() or "दर्ज" in reply, f"expected CONFIRM, got {reply!r}"
        print(f"ok  Sunita single-shot CONFIRM: {reply!r}")

        reply = _sms(c, SUNITA, "kal rajma chawal")
        assert "portion" in reply.lower() or "पोर्शन" in reply, f"expected ASK_PORTIONS, got {reply!r}"
        reply = _sms(c, SUNITA, "10 portion 70")
        assert "confirm" in reply.lower() or "दर्ज" in reply, f"expected CONFIRM, got {reply!r}"
        assert "rajma" in reply.lower(), f"dish not carried over: {reply!r}"
        print(f"ok  Sunita multi-turn CONFIRM: {reply!r}")

        new_phone = f"+9190{int(time.time()) % 1_000_000_000:09d}"
        r = c.post("/register-cook", data={
            "name": "Smoke Cook", "phone": new_phone, "area": "Koramangala",
            "address": "1 Demo Lane", "channel": "sms",
            "default_pickup": "12:00-14:00"})
        assert r.status_code == 200, (r.status_code, r.text[:200])
        reply = _sms(c, new_phone, "kal 50 poha 40, 12-2pm")
        assert "limit" in reply.lower() or "सीमा" in reply, f"expected OVER_LIMIT, got {reply!r}"
        print(f"ok  new cook OVER_LIMIT: {reply!r}")

        reply = _sms(c, SUNITA, "paisa kab milega?")
        assert reply, "empty help reply"
        assert "confirm" not in reply.lower() and "रुपये" not in reply[:40], f"looks like a listing reply: {reply!r}"
        print(f"ok  help answer: {reply!r}")

    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
