#!/usr/bin/env python3
"""
WhatsApp Reminder Otomatis via Fonnte API
Dijalankan oleh GitHub Actions setiap hari jam 08:00 WIB
CSV format: separator titik koma (;), tanggal DD-MM (tanpa tahun)
"""

import csv
import os
import time
import logging
import requests
from datetime import datetime

# ============================================================
# Konfigurasi dibaca dari Environment Variable (GitHub Secrets)
# ============================================================
FONNTE_TOKEN = os.environ.get("FONNTE_TOKEN", "")
TARGET_GROUP = os.environ.get("TARGET_GROUP", "")
CSV_PATH     = "Event_Nasional_updated.csv"
HARI_SEBELUM = 3   # Kirim reminder H-3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def load_events(csv_path: str) -> list:
    events = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            tanggal_str = row.get("Tanggal", "").strip()
            if not tanggal_str:
                continue
            try:
                # Format tanggal: DD-MM (tanpa tahun)
                # Tambahkan tahun berjalan agar bisa dibandingkan
                tahun_ini = datetime.now().year
                tanggal = datetime.strptime(f"{tanggal_str}-{tahun_ini}", "%d-%m-%Y").date()
                events.append({
                    "no"        : row.get("No.", ""),
                    "nama"      : row.get("Nama Peristiwa / Lokasi Kejadian", "").strip(),
                    "tanggal"   : tanggal,
                    "deskripsi" : row.get("Deskripsi Event", "").strip(),
                    "keywords"  : row.get("Keywords Pencarian untuk Patroli", "").strip(),
                })
            except ValueError:
                log.warning(f"Format tanggal tidak dikenali: '{tanggal_str}' — dilewati.")
    log.info(f"Memuat {len(events)} event dari {csv_path}")
    return events


def format_message(event: dict, selisih: int) -> str:
    tanggal_fmt = event["tanggal"].strftime("%d %B")
    return (
        f"🔔 *REMINDER H-{selisih}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *{event['nama']}*\n"
        f"📅 Tanggal: {tanggal_fmt}\n"
        f"📝 {event['deskripsi']}\n"
        f"🔍 *Keywords:* {event['keywords']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Pesan ini dikirim otomatis oleh sistem reminder._"
    )


def kirim_pesan(pesan: str) -> bool:
    url     = "https://api.fonnte.com/send"
    headers = {"Authorization": FONNTE_TOKEN}
    payload = {
        "target"     : TARGET_GROUP,
        "message"    : pesan,
        "countryCode": "62",
    }
    try:
        resp   = requests.post(url, headers=headers, data=payload, timeout=30)
        result = resp.json()
        if result.get("status") is True:
            log.info(f"✅ Pesan terkirim ke {TARGET_GROUP}")
            return True
        else:
            log.error(f"❌ Gagal kirim: {result}")
            return False
    except Exception as e:
        log.error(f"❌ Error: {e}")
        return False


def main():
    if not FONNTE_TOKEN or not TARGET_GROUP:
        log.error("❌ FONNTE_TOKEN atau TARGET_GROUP belum diset di GitHub Secrets!")
        return

    hari_ini = datetime.now().date()
    log.info(f"📅 Hari ini: {hari_ini}")

    events   = load_events(CSV_PATH)
    terkirim = 0

    for event in events:
        selisih = (event["tanggal"] - hari_ini).days
        if selisih == HARI_SEBELUM:
            log.info(f"📨 Kirim reminder: {event['nama']}")
            pesan = format_message(event, selisih)
            if kirim_pesan(pesan):
                terkirim += 1
            time.sleep(2)

    log.info(f"✅ Selesai. {terkirim} pesan terkirim hari ini.")


if __name__ == "__main__":
    main()
