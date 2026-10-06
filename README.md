# ArestradA V4 — Final Candidate

Safety-first XAU/USD market intelligence bot. V4 is isolated from V3.1.

## Included
- Twelve Data provider abstraction; M5/M15/H1/H4/D1 retrieval
- OHLC/Data Guard with stale, duplicate/order and abnormal-range checks
- EMA20/50, RSI14, ATR14, candle metrics, confirmed pivots without future access
- MTF structure, closed-candle BOS/CHOCH logic, protected swing, liquidity sweep/break, S/D, FVG, context
- BUY/SELL/WAIT/BLOCKED decision engine with evidence/counter-evidence and hard gates
- Structural/ATR risk plan (no lot sizing until verified broker specs exist)
- Fail-closed News Guard; UNKNOWN is blocked by default
- SQLite persistence, immutable/idempotent payment charge handling, users, subscriptions, access grants, audit log
- FREE/PRO/ELITE/SPECIAL/INTERNAL entitlements
- Telegram dashboard, Market Pulse, Full Analysis, Account, Upgrade, owner stats foundation
- Telegram Stars XTR recurring 30-day invoice flow with pre-checkout validation and successful-payment idempotency
- /terms, /privacy and /paysupport
- Sequential replay foundation and automated safety tests

## Important production truth
The software can be final as code, but no trading strategy can truthfully be certified profitable or reliable without live-provider replay, shadow and paper-validation data. The bot therefore remains fail-closed and should not market confluence as probability. PAYMENT_ENABLED defaults to false until payment flow is tested with the real bot.

## Termux
```bash
unzip ArestradA_V4_FINAL.zip
cd arestrada-v4
bash install_termux.sh
nano .env
./run.sh --health
./run.sh --once
./run.sh --poll
```
Never share `.env`, Telegram token, API key, passwords, or wallet seed/private key.

## Validation
```bash
python -m pytest -q
python -m compileall -q src
```

## Production recommendation
For 24/7 operation use an always-on Linux host and HTTPS webhook/worker architecture. Long polling in Termux remains suitable for development but Android/XOS can suspend it.
