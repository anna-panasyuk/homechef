import concurrent.futures
import json
import os
import re
from datetime import date as dtdate, timedelta
from pathlib import Path

PROMPT = Path("prompts/parse_listing.txt").read_text()
HELP_PROMPT = Path("prompts/cook_help.txt").read_text()
FIELDS = ("dish", "portions", "price_inr", "date", "pickup_window")
DATE_WORDS = re.compile(r"\b(kal|tomorrow|aaj|today|am|pm)\b", re.IGNORECASE)
QUESTION_STARTS = re.compile(r"^\s*(kaise|kya|kab|kitna)\b", re.IGNORECASE)


def _normalize(data: dict) -> dict:
    data.setdefault("missing", [])
    data.setdefault("intent", "listing")
    for k in FIELDS:
        if k not in data:
            data[k] = None
    if data["intent"] == "listing":
        for k in FIELDS:
            if data.get(k) in (None, "") and k not in data["missing"]:
                data["missing"].append(k)
    else:
        data["missing"] = []
    return data


def _rule_intent(text: str) -> str:
    has_num = bool(re.search(r"\d", text))
    if has_num:
        return "listing"
    if text.strip().endswith("?") or QUESTION_STARTS.search(text):
        return "question"
    return "listing"


def _gemini_parse(text: str, today: dtdate) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = PROMPT.replace("{today}", today.isoformat()).replace("{text}", text)
    resp = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(resp.text)


def _rule_parse(text: str, today: dtdate) -> dict:
    tl = text.lower()
    missing: list[str] = []

    if re.search(r"\b(kal|tomorrow)\b", tl):
        date_val = (today + timedelta(days=1)).isoformat()
    elif re.search(r"\b(aaj|today)\b", tl):
        date_val = today.isoformat()
    else:
        date_val = None
        missing.append("date")

    pickup = None
    m = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", text)
    if m:
        pickup = f"{int(m.group(1)):02d}:{m.group(2)}-{int(m.group(3)):02d}:{m.group(4)}"
    else:
        m2 = re.search(r"(\d{1,2})\s*-\s*(\d{1,2})\s*(am|pm)", tl)
        if m2:
            def to_hhmm(hh: str, ampm: str) -> str:
                h = int(hh)
                if ampm == "pm" and h < 12:
                    h += 12
                if ampm == "am" and h == 12:
                    h = 0
                return f"{h:02d}:00"
            pickup = f"{to_hhmm(m2.group(1), m2.group(3))}-{to_hhmm(m2.group(2), m2.group(3))}"
    if not pickup:
        missing.append("pickup_window")

    pickup_span = (m or m2).span() if (pickup) else None
    text_no_pickup = text
    if pickup_span:
        text_no_pickup = text[:pickup_span[0]] + " " + text[pickup_span[1]:]

    nums = [int(n) for n in re.findall(r"\d+", text_no_pickup)]
    portions = price = None
    if len(nums) >= 2:
        portions, price = nums[0], nums[-1]
    elif len(nums) == 1:
        portions = nums[0]
        missing.append("price_inr")
    else:
        missing.append("portions")
        missing.append("price_inr")

    dish_src = re.sub(r"\d+", " ", text_no_pickup)
    dish_src = DATE_WORDS.sub(" ", dish_src)
    dish_src = re.sub(r"[-:,.;!?]", " ", dish_src)
    dish = " ".join(dish_src.split()).strip() or None
    if not dish:
        missing.append("dish")

    return {
        "intent": "listing",
        "dish": dish, "portions": portions, "price_inr": price,
        "date": date_val, "pickup_window": pickup, "missing": missing,
    }


def _rule_parse_with_intent(text: str, today: dtdate) -> dict:
    if _rule_intent(text) == "question":
        return {
            "intent": "question",
            "dish": None, "portions": None, "price_inr": None,
            "date": None, "pickup_window": None, "missing": [],
        }
    return _rule_parse(text, today)


def parse_listing(text: str, today: dtdate | None = None) -> dict:
    today = today or dtdate.today()
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                data = ex.submit(_gemini_parse, text, today).result(timeout=5.0)
            return _normalize(data)
        except Exception:
            pass
    return _normalize(_rule_parse_with_intent(text, today))


def _gemini_help(text: str, channel: str, price_hint: str) -> str:
    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = (HELP_PROMPT
              .replace("{channel}", channel)
              .replace("{price_hint}", price_hint)
              .replace("{text}", text))
    resp = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
    )
    return (resp.text or "").strip()


def answer_help(text: str, channel: str, price_hint: str = "") -> str | None:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider != "gemini":
        return None
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            out = ex.submit(_gemini_help, text, channel, price_hint).result(timeout=5.0)
    except Exception:
        return None
    if not out:
        return None
    return out[:300]
