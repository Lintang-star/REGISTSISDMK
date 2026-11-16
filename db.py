"""Lapisan database (SQLite).

Semua akses data ada di file ini. Kalau nanti ingin pindah ke Supabase,
Google Sheets, atau PostgreSQL, cukup ganti isi fungsi-fungsi di sini.
"""
import json
import random
import re
import sqlite3
import string
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

import config

WIB = ZoneInfo("Asia/Jakarta")
DB_PATH = Path(__file__).parent / "data" / "sisdmk.db"


def sekarang() -> datetime:
    return datetime.now(WIB).replace(microsecond=0)


def _now_str() -> str:
    return sekarang().isoformat(sep=" ")


def parse_waktu(s: str) -> datetime:
    return datetime.fromisoformat(s)


def normalisasi_hp(no: str) -> str:
    """08123 -> 628123, +62 812 -> 62812."""
    digit = re.sub(r"\D", "", no or "")
    if digit.startswith("0"):
        digit = "62" + digit[1:]
    return digit


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS pengajuan (
                kode TEXT PRIMARY KEY,
                jenis_faskes TEXT NOT NULL,
                nama_faskes TEXT NOT NULL,
                kecamatan TEXT,
                wa_pic TEXT,
                data_json TEXT NOT NULL,
                status TEXT NOT NULL,
                catatan TEXT DEFAULT '',
                dibuat TEXT NOT NULL,
                diperbarui TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS riwayat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kode TEXT NOT NULL,
                status TEXT NOT NULL,
                catatan TEXT DEFAULT '',
                waktu TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS helpdesk (
                kode TEXT PRIMARY KEY,
                nama TEXT, profesi TEXT, nik TEXT, str_no TEXT, sip_no TEXT,
                faskes TEXT, keluhan TEXT, kontak TEXT,
                status TEXT NOT NULL,
                balasan TEXT DEFAULT '',
                dibuat TEXT NOT NULL,
                diperbarui TEXT NOT NULL
            );
            """
        )


def _kode(prefix: str) -> str:
    acak = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{sekarang():%y%m%d}-{acak}"


# ------------------------------------------------------------ Pengajuan
def cek_duplikat(jenis: str, nama: str, kecamatan: str):
    """Kembalikan kode pengajuan aktif (belum ditolak) dengan data yang sama."""
    with _conn() as c:
        r = c.execute(
            "SELECT kode FROM pengajuan WHERE jenis_faskes=? AND LOWER(nama_faskes)=LOWER(?) "
            "AND kecamatan=? AND status!='Ditolak' LIMIT 1",
            (jenis, nama.strip(), kecamatan),
        ).fetchone()
    return r["kode"] if r else None


def simpan_pengajuan(jenis: str, data: dict) -> str:
    waktu = _now_str()
    with _conn() as c:
        kode = _kode("SDMK")
        while c.execute("SELECT 1 FROM pengajuan WHERE kode=?", (kode,)).fetchone():
            kode = _kode("SDMK")
        c.execute(
            "INSERT INTO pengajuan VALUES (?,?,?,?,?,?,?,?,?,?)",
            (kode, jenis, data["nama_faskes"].strip(), data.get("kec"),
             normalisasi_hp(data.get("wa_pic", "")),
             json.dumps(data, ensure_ascii=False, default=str),
             "Diajukan", "", waktu, waktu),
        )
        c.execute(
            "INSERT INTO riwayat (kode,status,catatan,waktu) VALUES (?,?,?,?)",
            (kode, "Diajukan", "Pengajuan diterima.", waktu),
        )
    return kode


def cek_tiket(kode: str, wa_akhir: str):
    """Pencarian publik: butuh kode tiket + 4 digit terakhir WA PIC."""
    kode = (kode or "").strip().upper()
    wa_akhir = re.sub(r"\D", "", wa_akhir or "")
    if len(wa_akhir) < 4:
        return None
    with _conn() as c:
        r = c.execute("SELECT * FROM pengajuan WHERE kode=?", (kode,)).fetchone()
    if r and (r["wa_pic"] or "").endswith(wa_akhir[-4:]):
        return dict(r)
    return None


def riwayat(kode: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT status, catatan, waktu FROM riwayat WHERE kode=? ORDER BY id", (kode,)
        ).fetchall()
    return [dict(r) for r in rows]


def daftar_pengajuan() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT kode, jenis_faskes, nama_faskes, kecamatan, wa_pic, status, catatan, "
            "dibuat, diperbarui FROM pengajuan ORDER BY dibuat DESC", c)


def detail_pengajuan(kode: str):
    with _conn() as c:
        r = c.execute("SELECT * FROM pengajuan WHERE kode=?", (kode,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["data"] = json.loads(d.pop("data_json"))
    return d


def ubah_status(kode: str, status: str, catatan: str = "") -> None:
    waktu = _now_str()
    with _conn() as c:
        c.execute(
            "UPDATE pengajuan SET status=?, catatan=?, diperbarui=? WHERE kode=?",
            (status, catatan, waktu, kode),
        )
        # Jika admin melompati tahap, isi tahap yang terlewat agar tracking konsisten.
        if status in config.STATUS_ALUR:
            ada = {r["status"] for r in c.execute(
                "SELECT status FROM riwayat WHERE kode=?", (kode,)).fetchall()}
            for s in config.STATUS_ALUR[: config.STATUS_ALUR.index(status)]:
                if s not in ada:
                    c.execute(
                        "INSERT INTO riwayat (kode,status,catatan,waktu) VALUES (?,?,?,?)",
                        (kode, s, "(otomatis)", waktu),
                    )
        c.execute(
            "INSERT INTO riwayat (kode,status,catatan,waktu) VALUES (?,?,?,?)",
            (kode, status, catatan, waktu),
        )


def target_waktu(p: dict, riw: list[dict]) -> dict:
    """Hitung estimasi: akun jadi (<=1 hari) & muncul di SatuSehat (+1x24 jam)."""
    tercapai = {r["status"]: parse_waktu(r["waktu"]) for r in riw}
    hasil = {"akun": None, "satusehat": None}
    if "Akun Dibuat" not in tercapai:
        hasil["akun"] = parse_waktu(p["dibuat"]) + timedelta(hours=config.SLA_AKUN_JAM)
    if "Sinkronisasi SatuSehat" in tercapai and "Aktif di SatuSehat" not in tercapai:
        hasil["satusehat"] = tercapai["Sinkronisasi SatuSehat"] + timedelta(
            hours=config.SLA_SATUSEHAT_JAM)
    return hasil


# ------------------------------------------------------------ Helpdesk
def simpan_helpdesk(d: dict) -> str:
    waktu = _now_str()
    with _conn() as c:
        kode = _kode("HD")
        c.execute(
            "INSERT INTO helpdesk VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (kode, d["nama"], d["profesi"], d.get("nik", ""), d.get("str_no", ""),
             d.get("sip_no", ""), d["faskes"], d["keluhan"], normalisasi_hp(d["kontak"]),
             "Baru", "", waktu, waktu),
        )
    return kode


def cek_helpdesk(kode: str, wa_akhir: str):
    kode = (kode or "").strip().upper()
    wa_akhir = re.sub(r"\D", "", wa_akhir or "")
    if len(wa_akhir) < 4:
        return None
    with _conn() as c:
        r = c.execute("SELECT * FROM helpdesk WHERE kode=?", (kode,)).fetchone()
    if r and (r["kontak"] or "").endswith(wa_akhir[-4:]):
        return dict(r)
    return None


def daftar_helpdesk() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query("SELECT * FROM helpdesk ORDER BY dibuat DESC", c)


def balas_helpdesk(kode: str, status: str, balasan: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE helpdesk SET status=?, balasan=?, diperbarui=? WHERE kode=?",
            (status, balasan, _now_str(), kode),
        )


# ------------------------------------------------------------ Statistik
def statistik() -> dict:
    df = daftar_pengajuan()
    return {
        "total": len(df),
        "per_status": df["status"].value_counts().reindex(config.SEMUA_STATUS, fill_value=0),
        "per_jenis": df["jenis_faskes"].value_counts(),
        "per_kec": df["kecamatan"].value_counts().head(15),
    }
