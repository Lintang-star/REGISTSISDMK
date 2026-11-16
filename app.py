"""Dashboard Pendaftaran Akun SISDMK – Kabupaten Bogor.

Jalankan:  streamlit run app.py
"""
import hmac
import os
import re
from datetime import date

import pandas as pd
import streamlit as st

import config
import db

st.set_page_config(page_title=config.APP_TITLE, page_icon="🏥", layout="wide")
db.init_db()

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    .kode-box {font-size: 1.8rem; font-weight: 700; letter-spacing: 2px;
               padding: .6rem 1rem; border-radius: 10px;
               background: rgba(46,134,193,.12); border: 1px dashed #2E86C1;
               text-align: center;}
    </style>
    """,
    unsafe_allow_html=True,
)

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


# ============================================================ Helper
def fmt_waktu(s) -> str:
    dt = db.parse_waktu(s) if isinstance(s, str) else s
    return dt.strftime("%d %b %Y, %H:%M WIB")


def render_field(prefix: str, f: dict):
    key = f"{prefix}_{f['key']}"
    label = f["label"] + (" *" if f.get("required", True) else "")
    tipe = f.get("type", "text")
    help_ = f.get("help")
    if tipe == "textarea":
        return st.text_area(label, key=key, help=help_, height=90)
    if tipe == "date":
        return st.date_input(label, value=None, key=key, help=help_,
                             min_value=date(2000, 1, 1), max_value=date(2060, 12, 31),
                             format="DD/MM/YYYY")
    if tipe == "select":
        return st.selectbox(label, f["options"], index=None, placeholder="Pilih...",
                            key=key, help=help_)
    if tipe == "kec":
        return st.selectbox(label, config.KECAMATAN_KAB_BOGOR, index=None,
                            placeholder="Pilih kecamatan...", key=key, help=help_)
    placeholder = "08xxxxxxxxxx" if tipe == "phone" else None
    return st.text_input(label, key=key, help=help_, placeholder=placeholder)


def validasi(fields: list[dict], data: dict) -> list[str]:
    err = []
    for f in fields:
        v = data.get(f["key"])
        kosong = v is None or (isinstance(v, str) and not v.strip())
        if kosong:
            if f.get("required", True):
                err.append(f"**{f['label']}** wajib diisi.")
            continue
        if f["type"] == "email" and not EMAIL_RE.match(v.strip()):
            err.append(f"**{f['label']}** bukan format email yang valid.")
        if f["type"] == "phone":
            n = re.sub(r"\D", "", v)
            if not 8 <= len(n) <= 15:
                err.append(f"**{f['label']}** harus berupa nomor telepon yang valid.")
    return err


def admin_password():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return os.environ.get("ADMIN_PASSWORD")


# ============================================================ Halaman
def halaman_beranda():
    st.title("🏥 " + config.APP_TITLE)
    st.caption(config.APP_SUBTITLE)

    s = db.statistik()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pengajuan", s["total"])
    c2.metric("Dalam Proses", int(s["per_status"][["Diajukan", "Verifikasi Data"]].sum()))
    c3.metric("Akun Dibuat / Sinkronisasi",
              int(s["per_status"][["Akun Dibuat", "Sinkronisasi SatuSehat"]].sum()))
    c4.metric("Aktif di SatuSehat", int(s["per_status"]["Aktif di SatuSehat"]))

    st.subheader("Alur Singkat")
    cols = st.columns(4)
    langkah = [
        ("1️⃣ Daftar", "Isi form pengajuan sesuai jenis faskes."),
        ("2️⃣ Verifikasi", "Admin memeriksa data Anda."),
        ("3️⃣ Akun Jadi", f"Maksimal {config.SLA_AKUN_JAM // 24} hari. User ID dikirim via WhatsApp."),
        ("4️⃣ SatuSehat", f"Muncul di SatuSehat {config.SLA_SATUSEHAT_JAM // 24}x24 jam setelah aktivasi."),
    ]
    for col, (judul, isi) in zip(cols, langkah):
        with col.container(border=True):
            st.markdown(f"**{judul}**")
            st.write(isi)

    st.info("Sudah mengajukan? Buka menu **Pantau Akun** dan masukkan kode tiket Anda.")

    if s["total"]:
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Pengajuan per Jenis Faskes")
            st.bar_chart(s["per_jenis"])
        with g2:
            st.subheader("Pengajuan per Kecamatan (Top 15)")
            st.bar_chart(s["per_kec"])


def halaman_daftar():
    st.title("📝 Form Pendaftaran Akun SISDMK")
    st.write("Untuk fasilitas kesehatan **yang belum memiliki** akun SISDMK.")

    jenis = st.selectbox(
        "Jenis fasilitas",
        list(config.JENIS_FASKES),
        format_func=lambda j: f"{config.JENIS_FASKES[j]['ikon']} {j}",
    )
    fields = config.JENIS_FASKES[jenis]["fields"]

    if jenis in ("Klinik", "Praktik Mandiri"):
        st.caption(
            f"Belum punya Kode Registrasi Fasyankes? Daftar dulu di {config.URL_REGFAS} "
            "(lihat panduan di menu Info SISDMK)."
        )

    with st.form(f"form_{jenis}", clear_on_submit=False):
        kiri, kanan = st.columns(2)
        nilai = {}
        for i, f in enumerate(fields):
            with (kiri if i % 2 == 0 else kanan):
                nilai[f["key"]] = render_field(jenis, f)
        setuju = st.checkbox("Saya menyatakan data di atas benar dan dapat dipertanggungjawabkan.")
        kirim = st.form_submit_button("Kirim Pengajuan", type="primary")

    if not kirim:
        return

    err = validasi(fields, nilai)
    if not setuju:
        err.append("Anda harus menyetujui pernyataan kebenaran data.")
    if err:
        for e in err:
            st.error(e)
        return

    ganda = db.cek_duplikat(jenis, nilai["nama_faskes"], nilai["kec"])
    if ganda:
        st.warning(
            f"Pengajuan untuk **{nilai['nama_faskes']}** di Kec. {nilai['kec']} sudah ada "
            f"dengan kode **{ganda}**. Cek statusnya di menu **Pantau Akun**, atau hubungi helpdesk."
        )
        return

    # tanggal -> string
    for k, v in nilai.items():
        if isinstance(v, date):
            nilai[k] = v.isoformat()
    kode = db.simpan_pengajuan(jenis, nilai)
    st.success("Pengajuan berhasil dikirim! Simpan kode tiket berikut.")
    st.markdown(f"<div class='kode-box'>{kode}</div>", unsafe_allow_html=True)
    st.write(
        f"Gunakan kode ini + **4 digit terakhir No. WA PIC** di menu **Pantau Akun**. "
        f"Akun diproses maksimal {config.SLA_AKUN_JAM // 24} hari; "
        f"info dikirim via WhatsApp ke PIC."
    )


def halaman_pantau():
    st.title("🔎 Pantau Perkembangan Akun")
    st.write("Masukkan kode tiket dan 4 digit terakhir No. WA PIC yang didaftarkan.")

    with st.form("form_pantau"):
        c1, c2 = st.columns(2)
        kode = c1.text_input("Kode Tiket", placeholder="SDMK-260101-AB12")
        wa = c2.text_input("4 digit terakhir No. WA PIC", max_chars=4)
        cari = st.form_submit_button("Cek Status", type="primary")

    if cari:
        p = db.cek_tiket(kode, wa)
        if not p:
            st.error("Tiket tidak ditemukan atau verifikasi WA tidak cocok.")
            st.session_state.pop("tiket_aktif", None)
            return
        st.session_state["tiket_aktif"] = p["kode"]

    kode_aktif = st.session_state.get("tiket_aktif")
    if not kode_aktif:
        return
    p = db.detail_pengajuan(kode_aktif)
    riw = db.riwayat(kode_aktif)
    tampilkan_tracking(p, riw)


def tampilkan_tracking(p: dict, riw: list[dict]):
    tercapai = {r["status"]: r["waktu"] for r in riw}
    target = db.target_waktu(p, riw)

    st.subheader(f"{p['nama_faskes']}  ·  {p['jenis_faskes']}")
    st.caption(f"Kode tiket: {p['kode']} · Diajukan {fmt_waktu(p['dibuat'])}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Status Saat Ini", p["status"])
    if target["akun"]:
        m2.metric("Target Akun Jadi", fmt_waktu(target["akun"]))
    else:
        m2.metric("Akun Dibuat", fmt_waktu(tercapai["Akun Dibuat"]))
    if target["satusehat"]:
        m3.metric("Estimasi Muncul di SatuSehat", fmt_waktu(target["satusehat"]))
    elif "Aktif di SatuSehat" in tercapai:
        m3.metric("Aktif di SatuSehat", fmt_waktu(tercapai["Aktif di SatuSehat"]))
    else:
        m3.metric("Estimasi Muncul di SatuSehat", "1x24 jam setelah aktivasi")

    if p["status"] in config.STATUS_KHUSUS:
        st.warning(f"**{p['status']}** — {p['catatan'] or config.KETERANGAN_STATUS[p['status']]}")

    selesai = [s for s in config.STATUS_ALUR if s in tercapai]
    st.progress(len(selesai) / len(config.STATUS_ALUR))

    st.markdown("#### Tahapan")
    ada_aktif = False
    for s in config.STATUS_ALUR:
        if s in tercapai:
            ikon, info = "✅", fmt_waktu(tercapai[s])
        elif not ada_aktif and p["status"] not in config.STATUS_KHUSUS:
            ikon, info, ada_aktif = "⏳", "sedang/berikutnya"
        else:
            ikon, info = "⚪", "menunggu"
        st.markdown(f"{ikon} **{s}** — {config.KETERANGAN_STATUS[s]}  \n&nbsp;&nbsp;&nbsp;&nbsp;_{info}_")

    if p["status"] in ("Akun Dibuat", "Sinkronisasi SatuSehat"):
        st.info(
            f"Silakan login di {config.URL_LOGIN_SISDMK} dan **ganti password** setelah login. "
            f"Jika belum menerima User ID, hubungi WA {config.KONTAK['wa_helpdesk']}."
        )

    with st.expander("Riwayat lengkap"):
        st.dataframe(
            pd.DataFrame(riw).rename(columns={"status": "Status", "catatan": "Catatan", "waktu": "Waktu"}),
            hide_index=True, use_container_width=True,
        )


def halaman_info():
    st.title("ℹ️ Informasi SISDMK")
    st.markdown(
        """
**SISDMK** (Sistem Informasi Sumber Daya Manusia Kesehatan) adalah sistem milik Kementerian
Kesehatan untuk mendata dan mengelola SDM kesehatan di fasilitas pelayanan kesehatan. Data SDM
yang dikelola di SISDMK terhubung dengan **SatuSehat SDMK**.
        """
    )
    c1, c2 = st.columns(2)
    c1.link_button("Login SISDMK", config.URL_LOGIN_SISDMK, use_container_width=True)
    c2.link_button("Registrasi Fasyankes (Regfas)", config.URL_REGFAS, use_container_width=True)

    t1, t2, t3 = st.tabs(["Alur Pendaftaran", "Registrasi Fasyankes (Regfas)", "Dokumen yang Disiapkan"])
    with t1:
        st.markdown(
            f"""
1. Pastikan fasilitas Anda sudah memiliki **Kode Registrasi Fasyankes** (Klinik & Praktik Mandiri).
2. Isi form di menu **Daftar Akun** sesuai jenis faskes.
3. Simpan **kode tiket** yang diberikan.
4. Admin memverifikasi data. Akun dibuat maksimal **{config.SLA_AKUN_JAM // 24} hari**.
5. Anda menerima **User ID** via WhatsApp. Login lalu **ganti password**.
6. Setelah aktivasi, data muncul di **SatuSehat** dalam **{config.SLA_SATUSEHAT_JAM // 24}x24 jam**.
7. Pantau semua tahapan di menu **Pantau Akun**.
            """
        )
    with t2:
        st.markdown(
            f"""
1. Daftar di {config.URL_REGFAS} lalu tunggu validasi (1x24 jam baru bisa login).
2. Siapkan Google Drive berisi dokumen (lihat tab *Dokumen*).
3. Lengkapi pengisian data sampai selesai dan keluar **barcode kode Regfas**.
4. Cantumkan **link Google Drive** pada isian dokumen di form Regfas.
5. Selesai.
            """
        )
    with t3:
        st.markdown(
            """
Untuk **Praktik Mandiri** siapkan di satu folder Google Drive:

- SIP aktif
- STR aktif
- Surat permohonan registrasi fasyankes
- Dokumentasi: foto ruang praktik, foto kegiatan edukasi, foto sarana cuci tangan
- Dokumen SPO Pelayanan dan SPO Pendaftaran

Atur akses folder agar dapat dilihat oleh verifikator.
            """
        )

    st.subheader("Kantor Pelayanan")
    st.write(f"📍 {config.KONTAK['alamat']}  \n☎️ {config.KONTAK['telp_kantor']}")


def halaman_helpdesk():
    st.title("🛟 Helpdesk Pendaftaran Akun")
    t1, t2, t3, t4 = st.tabs(["FAQ", "Kirim Keluhan", "Cek Tiket Helpdesk", "Kontak"])

    with t1:
        for q, a in config.FAQ:
            with st.expander(q):
                st.markdown(a)

    with t2:
        st.caption("Form keluhan SatuSehat SDMK / SISDMK. Data NIK dipakai hanya untuk verifikasi.")
        with st.form("form_helpdesk", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nama = c1.text_input("Nama *")
            profesi = c2.selectbox("Profesi *", config.PROFESI, index=None, placeholder="Pilih...")
            nik = c1.text_input("NIK", max_chars=16)
            str_no = c2.text_input("STR")
            sip_no = c1.text_input("SIP")
            faskes = c2.text_input("Faskes *")
            kontak = c1.text_input("No. WA untuk balasan *", placeholder="08xxxxxxxxxx")
            keluhan = st.text_area("Keluhan *", height=120)
            kirim = st.form_submit_button("Kirim Keluhan", type="primary")
        if kirim:
            err = []
            if not nama.strip(): err.append("Nama wajib diisi.")
            if not profesi: err.append("Profesi wajib dipilih.")
            if not faskes.strip(): err.append("Faskes wajib diisi.")
            if not keluhan.strip(): err.append("Keluhan wajib diisi.")
            if not 8 <= len(re.sub(r"\D", "", kontak)) <= 15: err.append("No. WA tidak valid.")
            if nik and not re.fullmatch(r"\d{16}", nik.strip()): err.append("NIK harus 16 digit angka.")
            if err:
                for e in err: st.error(e)
            else:
                kode = db.simpan_helpdesk(dict(
                    nama=nama.strip(), profesi=profesi, nik=nik.strip(), str_no=str_no.strip(),
                    sip_no=sip_no.strip(), faskes=faskes.strip(), keluhan=keluhan.strip(), kontak=kontak))
                st.success("Keluhan terkirim. Simpan kode tiket berikut:")
                st.markdown(f"<div class='kode-box'>{kode}</div>", unsafe_allow_html=True)

    with t3:
        with st.form("form_cek_hd"):
            c1, c2 = st.columns(2)
            k = c1.text_input("Kode Tiket Helpdesk", placeholder="HD-260101-AB12")
            w = c2.text_input("4 digit terakhir No. WA", max_chars=4)
            cek = st.form_submit_button("Cek")
        if cek:
            h = db.cek_helpdesk(k, w)
            if not h:
                st.error("Tiket tidak ditemukan atau verifikasi WA tidak cocok.")
            else:
                st.markdown(f"**Status:** {h['status']}  ·  Dikirim {fmt_waktu(h['dibuat'])}")
                st.write(h["keluhan"])
                if h["balasan"]:
                    st.success(f"**Balasan admin:** {h['balasan']}")

    with t4:
        st.markdown(
            f"""
- WhatsApp helpdesk: **{config.KONTAK['wa_helpdesk']}**
- WhatsApp admin SDMK (data tidak valid): **{config.KONTAK['wa_admin_sdmk']}**
- Telepon kantor: **{config.KONTAK['telp_kantor']}**
- Alamat: {config.KONTAK['alamat']}
            """
        )


def halaman_admin():
    st.title("🔐 Admin")
    pw = admin_password()
    if not pw:
        st.error("Password admin belum diatur. Isi `ADMIN_PASSWORD` di `.streamlit/secrets.toml` "
                 "(lokal) atau di Secrets Streamlit Cloud.")
        return

    if not st.session_state.get("admin_ok"):
        with st.form("login_admin"):
            masuk = st.text_input("Password admin", type="password")
            if st.form_submit_button("Masuk", type="primary"):
                if hmac.compare_digest(masuk, pw):
                    st.session_state["admin_ok"] = True
                    st.rerun()
                else:
                    st.error("Password salah.")
        return

    if st.sidebar.button("Keluar admin"):
        st.session_state["admin_ok"] = False
        st.rerun()

    t1, t2 = st.tabs(["Pengajuan Akun", "Keluhan Helpdesk"])

    with t1:
        df = db.daftar_pengajuan()
        f1, f2 = st.columns(2)
        fs = f1.multiselect("Filter status", config.SEMUA_STATUS)
        fj = f2.multiselect("Filter jenis", list(config.JENIS_FASKES))
        if fs: df = df[df["status"].isin(fs)]
        if fj: df = df[df["jenis_faskes"].isin(fj)]
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.download_button("⬇️ Unduh CSV", df.to_csv(index=False).encode("utf-8"),
                           "pengajuan_sisdmk.csv", "text/csv")

        st.divider()
        st.subheader("Proses Pengajuan")
        semua = db.daftar_pengajuan()
        if semua.empty:
            st.info("Belum ada pengajuan.")
        else:
            pilih = st.selectbox(
                "Pilih pengajuan", semua["kode"],
                format_func=lambda k: f"{k} — {semua.loc[semua['kode'] == k, 'nama_faskes'].iat[0]}")
            d = db.detail_pengajuan(pilih)
            with st.expander("Data lengkap pengajuan", expanded=True):
                st.json(d["data"])
                st.caption(f"WA PIC (format 62): {d['wa_pic']}")
            with st.form("ubah_status"):
                idx = config.SEMUA_STATUS.index(d["status"])
                status = st.selectbox("Status baru", config.SEMUA_STATUS, index=idx)
                catatan = st.text_area("Catatan untuk pemohon (tampil di Pantau Akun)",
                                       value=d["catatan"])
                if st.form_submit_button("Simpan Perubahan", type="primary"):
                    db.ubah_status(pilih, status, catatan)
                    st.success("Status diperbarui.")
                    st.rerun()

    with t2:
        hd = db.daftar_helpdesk()
        if hd.empty:
            st.info("Belum ada keluhan.")
        else:
            tampil = hd.copy()
            tampil["nik"] = tampil["nik"].apply(lambda x: (x[:4] + "********" + x[-4:]) if x and len(x) == 16 else x)
            st.dataframe(tampil.drop(columns=["balasan"]), hide_index=True, use_container_width=True)
            pilih = st.selectbox("Balas tiket", hd["kode"])
            row = hd[hd["kode"] == pilih].iloc[0]
            with st.form("balas_hd"):
                status = st.selectbox("Status", config.STATUS_HELPDESK,
                                      index=config.STATUS_HELPDESK.index(row["status"]))
                balasan = st.text_area("Balasan", value=row["balasan"] or "")
                if st.form_submit_button("Simpan", type="primary"):
                    db.balas_helpdesk(pilih, status, balasan)
                    st.success("Tersimpan.")
                    st.rerun()


# ============================================================ Navigasi
MENU = {
    "🏠 Beranda": halaman_beranda,
    "📝 Daftar Akun": halaman_daftar,
    "🔎 Pantau Akun": halaman_pantau,
    "ℹ️ Info SISDMK": halaman_info,
    "🛟 Helpdesk": halaman_helpdesk,
    "🔐 Admin": halaman_admin,
}

with st.sidebar:
    st.markdown("### SISDMK Kab. Bogor")
    pilihan = st.radio("Menu", list(MENU), label_visibility="collapsed")
    st.divider()
    st.caption(f"Butuh bantuan? WA {config.KONTAK['wa_helpdesk']}")

MENU[pilihan]()
