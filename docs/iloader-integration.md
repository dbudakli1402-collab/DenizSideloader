# iloader-Integration: Analyse, Portierung, Lücken

Referenz: https://github.com/nab138/iloader (Tauri 2 + React/TS, MIT-Code,
Branding ausgenommen). Eigene Analyse, kein Code kopiert (Sprachwechsel),
Ideen mit Attribution (docs/attribution.md).

## iloader-Architektur (Feststellungen)

- Backend (Rust): `idevice`-Crate (usbmuxd, house_arrest, afc, remote_pairing,
  pair) + `isideload`-Crate (AppleAccount GSA-Login + 2FA, Anisette Remote-v3,
  DeveloperSession für Zertifikate/App-IDs, Sideloader für Sign+Install).
- Frontend: Account-Login, Pairing-/Certificates-/AppIDs-Pages, Anisette-
  Server-Dropdown (+ custom), Installer-Buttons mit offiziellen GitHub-URLs,
  Operation-Steps (download → install → pairing), Keyring-Speicherung,
  Frontend-Log-Streaming, Shortcuts (u. a. Ctrl+R/P/L).
- Installer-URLs (offiziell): SideStore stable/nightly, LiveContainer+
  SideStore stable/nightly (github.com/SideStore/SideStore,
  github.com/LiveContainer/LiveContainer).

## Portiert (echt, getestet)

| iloader | DenizSideloader |
|---|---|
| Installer-Buttons + URLs | `app/companion/models.py` + `installers.py` (Download → Install → Pairing via house_arrest) |
| Anisette-Server-Auswahl + custom | `app/companion/anisette.py` (Liste, Normalisierung, HTTPS-Check, State-Reset) |
| Pairing verwalten | Export/Löschen/Liste (`app/device/pairing.py`) |
| Geräteauswahl + Refresh | vorhanden, wiederverwendet |
| Keyring-Ablage | vorhanden (`keyring`), plus „Schlüsselbund nicht verwenden“-Option |
| Logs im Frontend | Logs-Seite + Auto-Refresh (5 s) |
| Shortcuts | Strg+R/P/L ergänzt (plus bestehende Strg+1–7, Strg+K) |
| Login-Formular | Struktur portiert; Passwort nur im RAM (siehe unten) |

## Bewusst NICHT portiert / Roadmap

- **Apple-Passwort speichern** („Save Credentials“): abgelehnt per SECURITY.md.
  Nur Benutzername-Hinweis; Passwort lebt im RAM eines Vorgangs.
- **Vollständige Apple-Anmeldung (GSA/SRP + 2FA) und Apple-Portal-APIs**
  (Zertifikate/App-IDs anlegen, löschen, Teams): Dafür existiert aktuell keine
  Python-Bibliothek (nur Rust-`isideload`). Eine saubere Nachimplementierung
  des Apple-Protokolls ist ein eigenes Großvorhaben (Account-Sperr-Risiko beim
  Testen!) und wird NICHT gefakt. Status: Interface + UI vorbereitet
  (`AppleSession`, Zertifikats-/App-ID-Dialoge mit lokalem Stand), Roadmap.
- Zertifikats-/App-ID-Seiten zeigen daher lokale Profile + Bibliotheks-
  Bundle-IDs und kennzeichnen den Portal-Status ehrlich.
