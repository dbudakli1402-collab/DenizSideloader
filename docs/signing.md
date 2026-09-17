# Signing — how it legitimately works

iOS only runs apps signed with an Apple-issued certificate plus a
provisioning profile that lists your device (UDID). This app **uses only
that mechanism** — nothing is forged, bypassed, or decrypted.

## What you need

| Account | Cost | App expiry | Notes |
| ------- | ---- | ---------- | ----- |
| Free Apple ID | free | **7 days** | a few sideloaded apps max; re-install weekly |
| Paid Developer | ~99 USD/year | **~12 months** | more devices, longer validity |

## Workflow in this app

1. Add your provisioning profile(s) (`.mobileprovision`, exported from Xcode
   or the Apple Developer portal) under **Settings → Signing**.
2. Choose account type (free/paid) so expiry expectations are shown honestly.
3. Enter your Apple ID email if you like — this stores only the **username
   hint** in Windows Credential Manager. Your **password is never stored**
   anywhere (not JSON, not `.env`, not logs, not git).
4. During install, the app embeds your existing profile into the IPA working
   copy (`embedded.mobileprovision`) and proceeds to the device backend.
5. Without valid assets, installation **stops with guidance** instead of
   pretending to succeed.

## Providers (`app/signing/`)

- `SigningProvider` — interface (`is_available`, `list_identities`, `sign`).
- `AppleDeveloperSigning` — free/paid modeling, honest embed flow.
- `LocalProvisioning` — reuses profiles already on disk; generates nothing.
- `FutureProviders` — add new classes implementing the interface.

## Limits (documented, not worked around)

- Free signing expires after ~7 days (Apple policy).
- Bundle IDs must match your provisioning profile.
- The device UDID must be registered in the profile.
