# 11 · Notification & Communication Architecture

**Status:** Draft for approval · **Covers:** deliverable item 19

## 1. Model

```
Event (domain occurrence)
  → NotificationRouter (template + audience resolution + preferences)
      ├─ in-app Notification row (all roles w/ logins)
      └─ SMSMessage row(s) → SMSProvider adapter → delivery status tracking
```

- **Two channels v1:** in-app notifications (bell + dashboard list) and SMS. Email adapter slot exists but is not wired (most guardians are phone-first, A8).
- Every outbound SMS persists (`sms_messages`) with provider message id, attempts, and final status — the comms log is the bursar/admin truth for "did we tell the parent?".

## 2. Events & templates (REQ-COM-01)

| Event code | Trigger | Default channels | Configurable |
|---|---|---|---|
| PAYMENT_CONFIRMED | ledger PAYMENT posted | SMS + in-app (parent), in-app (bursar) | text, on/off |
| RECEIPT_VOIDED | receipt void | in-app (bursar/head) | — |
| FEE_REMINDER | manual batch or scheduled (balance>0 & threshold age) | SMS | text, audience filter |
| REPORT_AVAILABLE | report published | SMS + in-app (parent) | text |
| EXAM_CLEARANCE_WARNING | clearance BLOCKED near exams | in-app (head/bursar) | — |
| EMERGENCY_BROADCAST | admin action | SMS to all guardians + in-app | text, audience (school/band/class) |
| ANNOUNCEMENT | admin/teacher (class-scoped) | in-app (+ optional SMS) | text |
| IMPORT_COMPLETED / FAILED | import job ends | in-app (actor) | — |
| MARKS_LOCKED / OVERRIDDEN | academic events | in-app (teacher) | — |

Templates live in `communication_templates` (per event+channel) with variables (`{{student_name}}`, `{{amount}}`, `{{balance}}`, `{{term}}`, `{{school_name}}`); editing is `SEND_COMMUNICATION` + audited. No provider/message text hard-coded (REQ-CFG-01).

## 3. Phone handling (REQ-COM-02)

- Normalize on input everywhere (forms + imports): accept `024…`, `23324…`, `+233 24…` → store `+233XXXXXXXXX`; validate prefix against Ghana mobile ranges; invalid ⇒ field error at source.
- Send-time guard re-validates; invalid numbers → `SKIPPED` with reason (BR-N01).
- Respect `sms_opt_out` and preferred contact windows (BR-N02): bulk sends scheduled inside windows; transactional payment confirmations exempt (configurable).

## 4. Provider abstraction (REQ-COM-03)

```
interface SMSProvider:
    send(to_e164, body, reference) -> ProviderSendResult(message_id)
    delivery_status(message_id) -> status          # where supported
adapters: ArkeselAdapter, HubtelAdapter, ConsoleAdapter (dev: prints)
```

- Selection is a school setting (`comms.provider`); both adapters ship, both start in **sandbox/test credentials** mode; LIVE requires env-provided keys (never DB-stored, never returned by API — REQ-SEC-02).
- Credentials: `ARKesel_API_KEY`, `HUBTEL_CLIENT_ID/SECRET` env vars; `payment_provider_configs`-style registry stores only the env var names.
- Failover: if primary provider errors 3× (BR-N03), message marked FAILED and queued for manual retry; optional auto-failover to secondary provider is a setting (default OFF to control cost).

## 5. Bulk send mechanics

- Broadcast composer: audience builder (school / band / grade / class / debtors-over-X-days / custom list), live recipient count, cost estimate (segments × rate from provider config), preview, confirmation dialog, send.
- Delivery is queued through the background worker (Redis queue): throttle default 10 msg/s (provider-friendly), progress shown to sender, cancellable before dispatch.
- Deduplication: same event+recipient+template+day suppresses repeats (protects against webhook replays re-triggering PAYMENT_CONFIRMED).

## 6. In-app notifications

- `notifications` rows; unread badge polls on 60 s interval (lightweight `?since=` endpoint — low bandwidth), not websockets (v1).
- Parent portal aggregates children's notifications; deep links (e.g., to receipt/report) included where scoped access allows.

## 7. Failure & privacy posture

- Provider outage: sends queue up to 24 h then expire with FAILED + admin alert (REQ-ERR-01 `SMS_PROVIDER_UNAVAILABLE`).
- Message bodies never log full guardian PII beyond name+reference; audit shows template id + recipient count.
- Emergency broadcast is rate-limited (1 per 10 min) and audited.
