# STEP017A — Network Security Boundary

Status: DESIGN FROZEN; network implementation/deployment/security testing NOT RUN.
Related: [architecture](STEP017A_LAN_PRODUCT_ARCHITECTURE.md), [HTTP contract](STEP017A_FRAME_HTTP_CONTRACT.md).

## 1. Trust model and decision

STEP017 is a trusted-LAN prototype, not a secure Internet architecture. No public Internet exposure, router port forwarding, cloud backend or Internet remote control is allowed.

| Option | Benefit | Cost / MVP decision |
| --- | --- | --- |
| Plain HTTP inside restricted trusted LAN | Reuses stack; minimum deployment/key management | Selected; no confidentiality or authenticated origin |
| TLS | Can protect transport with correctly provisioned/verified trust | Certificate lifecycle and MCU trust provisioning; excluded from MVP |
| Application authentication | Could restrict readers/event writers | Secret/token lifecycle and access policy; excluded under trusted-LAN assumption |

This decision is conditional on trusted LAN and non-sensitive display content. Untrusted/shared networks, sensitive content or Internet exposure require a new security review before deployment, not silent reuse of this prototype.
Anyone with network access may read frames or submit/alter events through the unauthenticated existing API. HTTP cannot resist interception, modification, replay or spoofing. SHA-256 ETag detects mismatched bytes/identity, but an attacker can replace both; it is not authentication or encryption.

## 2. Host exposure

Existing server binds loopback by default. Future controlled LAN deployment must deliberately select the intended LAN interface and restrict firewall access to intended participants; do not automatically expose all interfaces or change machine firewall/router settings. This stage performs no deployment/network changes.
Review the whole existing service surface, not just the new frame GET: event mutation routes, source refresh routes, simulator/static assets and generated API docs are not magically protected. No new dashboard or account system is added. Access restrictions and actual reachability must be checked at the future deployment gate.

## 3. Credentials and logs

Real Wi-Fi SSID/password must be local-only, ignored and not committed. Future repository templates may contain placeholders only. This stage creates neither templates nor real credential files.
Never place real credentials in source, tests, docs, PROJECT_STATE, logs or commit history. Do not dump private configuration while diagnosing; redact secrets before preserving logs/evidence. Private configuration must not silently fall back to example values.

## 4. Host address and discovery

| Approach | Tradeoff | Decision |
| --- | --- | --- |
| Explicit configured Host address/URL | Simple and auditable; operator must maintain address | Selected |
| mDNS | Friendly naming but extra discovery/reliability behavior | Excluded |
| Automatic discovery | Less manual setup but broader protocol/trust scope | Excluded |

Device uses an explicitly configured intended Host address and the frozen frame route. No scanning, discovery, remote selection or redirect following. Address changes require controlled local configuration, not a new service discovery feature. Do not record actual private network addresses unnecessarily in public examples.

## 5. Exclusions and evidence

No provisioning UI, captive portal, cloud registry, OTA, mobile app, public account system or production Internet security claim. Future security and failure tests are listed in [stage plan](STEP017A_STAGE_TEST_PLAN.md), all NOT RUN here. Historical H0/H1 and offline physical PASS provide no network security evidence.
