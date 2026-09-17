# Known limitations (Windows) — no tricks, documented honestly

## Device detection

- Needs: iPhone via USB, unlocked, **"Trust"** tapped, plus Apple Mobile
  Device support (install **iTunes from Apple** or the **Apple Devices** app).
- Without that, the app reports "No iPhone connected" with causes + retry —
  it never invents a device. Install `pip install DenizSideloader[device]`
  (`pymobiledevice3`, open source) to enable the real backend.

## Installation backend

- Real on-device install uses the `pymobiledevice3` installation proxy.
  If that backend (or valid signing assets) is missing, the job **fails with
  next steps** — there is intentionally no fake "Success" path
  (see `tests/test_installation.py::test_honest_backend_limitation`).

## Installed Apps listing

- Shown only when the backend reliably reports it. Otherwise the page says
  so and hides Update/Remove instead of showing dead buttons.

## What this app will never do

DRM removal, decryption of protected apps, certificate/provisioning forgery,
credential theft or password storage, and Apple-security bypasses. Requests
in that direction will be declined (see SECURITY.md).
