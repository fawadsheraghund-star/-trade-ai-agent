# Live Trading Setup Instructions (Documentation Only)

Important: This document provides setup and safety instructions for enabling live trading in the Fawad Trade AI Agent. It does NOT enable live trading. Keep LIVE_ENABLE=false until you complete all steps below and explicitly switch it on in your production environment.

Summary
- Mode: TEST first (USE_TESTNET=true). LIVE disabled by default (LIVE_ENABLE=false).
- Purpose: describe configuration, safety checks, confirmation flow, and spot/futures considerations to prepare for live mode.

1) Preconditions (do before enabling live)
- Keep LIVE_ENABLE=false until signoff.
- Ensure code is free of syntax errors and missing imports.
- Create and run unit and integration tests for trading logic, error handling, and confirmation flows.
- Configure persistent storage for DB and audit logs (host volume or named docker volume).

2) Secrets & API keys (safety checklist)
- Use a secrets manager (recommended) or platform secret storage; do NOT commit keys to the repo.
- Required production secrets:
  - EXCHANGE_API_KEY
  - EXCHANGE_API_SECRET
  - TELEGRAM_TOKEN
  - BOT_OWNER_TELEGRAM_ID
- Key safety checks at startup:
  - Mask keys in logs (show only prefix/suffix).
  - Validate keys by a read-only test call before allowing any trade path to proceed.
  - Refuse to enable any live-order action if keys are missing or malformed.
- Exchange-level safety:
  - Use least privilege for keys (no withdrawal permission).
  - Enable IP whitelisting where available.
  - Use subaccounts to isolate production keys if possible.

3) Owner confirmation flow (manual confirmation per order)
- Require explicit owner confirmation for each live order.
- Recommended flow:
  1. Bot prepares an order proposal (symbol, side, size/notional, price, SL/TP, confidence).
  2. Owner must confirm via a secure channel (owner-only Telegram callback or one-time token).
  3. One-time token approach: generate token via security module (short TTL, one-time use); owner supplies token to confirm; validate token before placing order.
- Implement safe_place_order wrapper that enforces LIVE_ENABLE and owner confirmation.
- All confirmation events and decisions must be audited.

4) Spot vs Futures support (checks & config)
- Decide supported market types (spot, futures, or both) and implement explicit handling.
- For spot:
  - Use spot-specific API calls. Do not assume leverage.
  - Validate minimum order sizes and symbol format.
- For futures:
  - Confirm separate API permissions and possibly separate keys/subaccounts.
  - Enforce leverage caps and notional limits in code.
  - Add checks for margin mode (isolated vs cross) and ensure correct ccxt params.
- TradeEngine must accept market_type parameter and translate it to exchange-specific flags.

5) Risk controls & limits (must configure)
- Configurable limits to set before live:
  - MAX_ORDER_PCT (percent of equity per order)
  - MAX_OPEN_POSITION_NOTIONAL (aggregate exposure cap)
  - DAILY_MAX_DRAWDOWN (circuit breaker)
  - MIN/MAX order size validation against exchange metadata
- Implement circuit-breaker to pause trading on severe error or threshold breach.

6) Testing & rollout plan
- Stage 1: Local & unit tests (no external keys).
- Stage 2: Staging testnet run (USE_TESTNET=true, testnet keys). Run full E2E flows for spot and futures where applicable.
- Stage 3: Canary live runs (small notional, owner confirmation required). Monitor closely.
- Verify audit logs after each step.

7) Monitoring & alerting
- Audit log path: configure SECURITY_AUDIT_LOG (persisted volume).
- Stream logs to stdout/stderr for container logging and to a centralized logging service in production.
- Configure alerts for order failures, unauthorized attempts, and threshold breaches.

8) Manual enable instructions (operator steps — perform only after all checks)
1. Ensure all items in sections above are completed and verified in staging.
2. Store production API keys in secret manager and inject them into production environment.
3. Confirm BOT_OWNER_TELEGRAM_ID is set correctly.
4. Set LIVE_ENABLE=true in production environment (do NOT commit to repo). Restart service to pick up change.
5. Execute a small, owner-confirmed test order to validate the full pipeline.
6. Monitor system for at least 24–72 hours.

9) Emergency rollback
- Immediately set LIVE_ENABLE=false to block further orders.
- Revoke API keys at exchange if compromise is suspected.
- Inspect SECURITY_AUDIT_LOG and operational logs for root cause.

10) Recommended environment variables for live readiness
- USE_TESTNET=true  # keep true for staging; set to false only after signoff
- LIVE_ENABLE=false
- EXCHANGE_ID=binance
- EXCHANGE_API_KEY= (in secrets manager)
- EXCHANGE_API_SECRET= (in secrets manager)
- BOT_OWNER_TELEGRAM_ID=123456789
- CONFIRM_TOKEN_TTL=300
- SECURITY_AUDIT_LOG=/data/security_audit.log
- MAX_ORDER_PCT=3.0
- MAX_OPEN_POSITION_NOTIONAL=10000

Notes
- This file is documentation only and does not change runtime configuration.
- Do not enable LIVE_ENABLE until you fully complete testing, security review, and operational readiness verification.

