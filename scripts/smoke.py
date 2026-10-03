"""End-to-end smoke test: browse, login, checkout, pay, close, handover."""
import re
import sys
from datetime import date
import httpx

BASE = "http://localhost:8000"


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

        r = c.post("/login", data={"name": "Smoke", "phone": "+919999900000", "otp": ""})
        assert r.status_code == 200 and "OTP" in r.text
        r = c.post("/login", data={"name": "Smoke", "phone": "+919999900000", "otp": "1234"})
        assert r.status_code == 200 and str(r.url).endswith("/")
        print("ok  login")

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

    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
