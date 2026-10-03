REPLIES = {
    "ASK_DISH": {
        "sms": "Dish ka naam bhejiye. Example: Masala Dosa",
        "voice": "कृपया पकवान का नाम बताइए।",
    },
    "ASK_PORTIONS": {
        "sms": "Kitne portions? Number bhejiye.",
        "voice": "कितने पोर्शन बनाएंगे? संख्या बताइए।",
    },
    "ASK_PRICE": {
        "sms": "Price per portion (INR) bhejiye.",
        "voice": "प्रति पोर्शन कीमत रुपये में बताइए।",
    },
    "ASK_DATE": {
        "sms": "Kis din? Example: kal, 05-10",
        "voice": "किस दिन के लिए सूची है?",
    },
    "ASK_PICKUP": {
        "sms": "Pickup window bhejiye. Example: 12-2pm",
        "voice": "पिकअप का समय बताइए।",
    },
    "CONFIRM": {
        "sms": "Listing confirmed: {dish} x{portions} @{price_inr} INR, {date} {pickup}.",
        "voice": "आपकी सूची दर्ज हो गई है।",
    },
    "OVER_LIMIT": {
        "sms": "Limit {limit} portions hai. Kam karke bhejiye.",
        "voice": "आपकी सीमा {limit} पोर्शन है। कृपया कम करें।",
    },
    "CLOSED_NOTICE": {
        "sms": "Orders band. {count} orders, advance {advance} INR.",
        "voice": "ऑर्डर बंद हो गए हैं। अग्रिम भुगतान भेजा जा रहा है।",
    },
    "HANDOVER_NOTICE": {
        "sms": "Handover done. Settlement {amount} INR.",
        "voice": "हैंडओवर पूरा। शेष भुगतान भेजा गया।",
    },
    "WELCOME": {
        "sms": "HomeChef me swagat! Kal ka dish bhejiye: dish, portions, price, pickup time. Sawaal bhi pooch sakte hain.",
        "voice": "होमशेफ में आपका स्वागत है। कल की सूची भेजें: पकवान, पोर्शन, कीमत और पिकअप समय।",
    },
    "HELP_FALLBACK": {
        "sms": "Abhi jawab nahi de paye. Thodi der baad try kijiye ya apne self-help group coordinator se poochiye.",
        "voice": "अभी उत्तर नहीं दे पाए। कृपया बाद में प्रयास करें या अपने समूह समन्वयक से पूछें।",
    },
}


def reply(key: str, channel: str = "sms", **kwargs) -> str:
    tpl = REPLIES.get(key, {}).get(channel, "")
    try:
        return tpl.format(**kwargs)
    except Exception:
        return tpl
