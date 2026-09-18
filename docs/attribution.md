# Attribution (Danksagung / Lizenzen Dritter)

Teile der Companion-Workflows in DenizSideloader sind von der Architektur
des Open-Source-Projekts **iloader** inspiriert bzw. daran angelehnt:

- iloader — https://github.com/nab138/iloader — **MIT License**
  (c) nab138. Copyright-Hinweis der MIT-Lizenz bleibt bestehen; der Code
  ist MIT-lizenziert und darf verwendet/modifiziert werden.
- Wichtig: Name, Logo und Branding von iloader sind **nicht** MIT-lizenziert
  (siehe deren `LICENSE-BRANDING`) und werden hier **nicht** verwendet.
  DenizSideloader nutzt ausschließlich eigenes Branding (Name, D-Logo, Blau).
- Zugehörige Projekte mit eigenem Dank: `idevice` + `isideload` (Rust-
  Bibliotheken des iloader-Autors), **SideStore** (GPL-3.0, eigene App),
  **LiveContainer** (eigene Lizenz, eigene App), **StikStore**.

## Was übernommen wurde (Ideen/Flows, in Python neu geschrieben)

- Installer-Flow Download → Install → Pairing (offizielle Release-URLs von
  SideStore/LiveContainer, keine eigenen Kopien, keine DRM-Umgehung)
- Anisette-Server-Auswahl (öffentliche Community-Serverliste) + lokaler
  Status-Reset
- Pairing-Datei-Export/-Löschen, Geräteauswahl, Zertifikats-/App-ID-Ansichten
- Keyring-basierte Ablage, Logging-Ansatz, Tastaturkürzel

## Bewusste Abweichungen (Sicherheit)

- iloader speichert auf Wunsch das Apple-Passwort im Keyring. DenizSideloader
  speichert **niemals** Apple-Passwörter — nur ein Benutzername-Hinweis, das
  Passwort lebt ausschließlich im RAM eines Vorgangs (siehe SECURITY.md).
- Die vollständige Apple-Anmeldung (GSA/SRP-Protokoll) + Apple-Portal-
  Operationen (Zertifikate/App-IDs anlegen/löschen) sind als Roadmap
  dokumentiert (docs/iloader-integration.md), nicht als Fake implementiert.
