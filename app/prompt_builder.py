def build_prompt(market_data: str) -> str:
    return f"""
You are a deterministic trading decision engine.

You MUST return ONLY valid JSON.
Do not include explanations, markdown, or extra text.

If you cannot determine a strong setup, return NO_TRADE.

Allowed decisions:
BUY, SELL, HOLD, NO_TRADE

STRICT RULES:
- Output must be valid JSON
- No trailing commas
- No missing braces
- No additional text before or after JSON
- All fields must be present

JSON schema:
{{
  "symbol": "string",
  "decision": "BUY | SELL | HOLD | NO_TRADE",
  "confidence": number (0 to 1),
  "reason": "string",
  "risk_notes": "string"
}}

Market data:
{market_data}
"""