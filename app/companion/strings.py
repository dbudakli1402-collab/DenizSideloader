"""Minimal DE/EN strings for the Companion view (iloader ships many locales;
we start honest with two and grow on demand)."""

from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    "de": {
        "account": "Account",
        "apple_id": "Apple-ID",
        "email_ph": "Apple-ID E-Mail …",
        "pass_ph": "Apple-ID Passwort …",
        "save_user": "Benutzername speichern (nie das Passwort)",
        "login": "Anmelden",
        "management": "Verwaltung",
        "mgmt_pairing": "Pairing-Datei",
        "mgmt_refresh": "Geräte aktualisieren",
        "mgmt_certs": "Zertifikate",
        "mgmt_appids": "App-IDs",
        "devices": "Geräte",
        "pick_device": "Gerät auswählen",
        "no_devices": "Keine Geräte gefunden.",
        "refresh": "Aktualisieren",
        "installers": "Installer",
        "pick_build": "Build wählen",
        "import_ipa": "IPA\nimportieren",
        "settings": "Einstellungen",
        "anisette": "Anisette-Server:",
        "custom": "Eigenen Anisette-Server verwenden",
        "standard": "Standard-Server verwenden",
        "reset_ani": "Anisette-Status zurücksetzen",
        "del_pair": "Gespeichertes Pairing löschen",
        "view_logs": "Logs ansehen (Strg+L)",
        "no_keyring": "Schlüsselbund nicht verwenden",
        "language": "Sprache",
    },
    "en": {
        "account": "Account",
        "apple_id": "Apple ID",
        "email_ph": "Apple ID email…",
        "pass_ph": "Apple ID password…",
        "save_user": "Save username (never the password)",
        "login": "Login",
        "management": "Management",
        "mgmt_pairing": "Pairing File",
        "mgmt_refresh": "Refresh Devices",
        "mgmt_certs": "Certificates",
        "mgmt_appids": "App IDs",
        "devices": "Devices",
        "pick_device": "Select a device",
        "no_devices": "No devices found.",
        "refresh": "Refresh",
        "installers": "Installers",
        "pick_build": "Choose a build",
        "import_ipa": "Import\nIPA",
        "settings": "Settings",
        "anisette": "Anisette Server:",
        "custom": "Use custom Anisette server",
        "standard": "Use standard servers",
        "reset_ani": "Reset Anisette State",
        "del_pair": "Delete Stored Pairing",
        "view_logs": "View Logs (Ctrl+L)",
        "no_keyring": "Don't use keyring",
        "language": "Language",
    },
}


def text(lang: str, key: str) -> str:
    table = STRINGS.get(lang, STRINGS["de"])
    return table.get(key, STRINGS["de"].get(key, key))
