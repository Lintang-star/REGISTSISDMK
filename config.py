"""Konfigurasi dashboard SISDMK Kabupaten Bogor.

Semua teks, kontak, dan definisi form ada di sini supaya mudah diubah
tanpa menyentuh logika aplikasi.
"""

APP_TITLE = "Pendaftaran Akun SISDMK – Kabupaten Bogor"
APP_SUBTITLE = "Layanan pengajuan akun SISDMK untuk fasilitas pelayanan kesehatan baru"

# ---------------------------------------------------------------- Kontak
# Ganti sesuai kebutuhan. Jika repo GitHub Anda publik, pertimbangkan
# memindahkan nomor ke .streamlit/secrets.toml.
KONTAK = {
    "wa_helpdesk": "085710123008",
    "wa_admin_sdmk": "+62 852-8064-2447",
    "telp_kantor": "(021) 87912517",
    "alamat": "Jln. Tegar Beriman, Kel. Pakansari, Kec. Cibinong, Kab. Bogor",
}

URL_LOGIN_SISDMK = "https://sisdmk.kemkes.go.id/login"
URL_REGFAS = "https://registrasifasyankes.kemkes.go.id"
URL_FORM_ASISTEN = "https://forms.gle/LqKc6KUB4pEpmueYA"

# ---------------------------------------------------------------- SLA
SLA_AKUN_JAM = 24          # akun SISDMK dibuat maksimal 1 hari
SLA_SATUSEHAT_JAM = 24     # muncul di SatuSehat 1x24 jam setelah aktivasi

# ---------------------------------------------------------------- Status
# Alur normal (berurutan)
STATUS_ALUR = [
    "Diajukan",
    "Verifikasi Data",
    "Akun Dibuat",
    "Sinkronisasi SatuSehat",
    "Aktif di SatuSehat",
]
# Status di luar alur
STATUS_KHUSUS = ["Perlu Perbaikan", "Ditolak"]
SEMUA_STATUS = STATUS_ALUR + STATUS_KHUSUS

KETERANGAN_STATUS = {
    "Diajukan": "Pengajuan diterima oleh sistem.",
    "Verifikasi Data": "Admin sedang memeriksa kelengkapan dan kesesuaian data.",
    "Akun Dibuat": "Akun SISDMK sudah dibuat. Silakan login dan segera ganti password.",
    "Sinkronisasi SatuSehat": "Akun diaktivasi. Data akan muncul di SatuSehat dalam 1x24 jam.",
    "Aktif di SatuSehat": "Akun sudah muncul dan aktif di SatuSehat Kemenkes.",
    "Perlu Perbaikan": "Data perlu diperbaiki. Lihat catatan admin dan hubungi helpdesk.",
    "Ditolak": "Pengajuan tidak dapat diproses. Lihat catatan admin.",
}

STATUS_HELPDESK = ["Baru", "Diproses", "Selesai"]

# ---------------------------------------------------------------- Wilayah
KECAMATAN_KAB_BOGOR = sorted([
    "Babakan Madang", "Bojonggede", "Caringin", "Cariu", "Ciampea", "Ciawi",
    "Cibinong", "Cibungbulang", "Cigombong", "Cigudeg", "Cijeruk", "Cileungsi",
    "Ciomas", "Cisarua", "Ciseeng", "Citeureup", "Dramaga", "Gunung Putri",
    "Gunung Sindur", "Jasinga", "Jonggol", "Kemang", "Klapanunggal",
    "Leuwiliang", "Leuwisadeng", "Megamendung", "Nanggung", "Pamijahan",
    "Parung", "Parungpanjang", "Rancabungur", "Rumpin", "Sukajaya",
    "Sukamakmur", "Sukaraja", "Tajurhalang", "Tamansari", "Tanjungsari",
    "Tenjo", "Tenjolaya",
])

# ---------------------------------------------------------------- Form
# Tipe field: text | textarea | date | select | kec | phone | email
# 'required' default True.

_ALAMAT = [
    {"key": "alamat", "label": "Alamat", "type": "textarea"},
    {"key": "desa", "label": "Desa / Kelurahan", "type": "text"},
    {"key": "kec", "label": "Kecamatan", "type": "kec"},
    {"key": "telp", "label": "Telp", "type": "phone"},
    {"key": "email", "label": "Email", "type": "email"},
]

_PENANGGUNG_JAWAB = [
    {"key": "nama_pj", "label": "Nama Penanggung Jawab (Pj)", "type": "text"},
    {"key": "nama_pic", "label": "Nama PIC SISDMK", "type": "text"},
    {"key": "wa_pic", "label": "No. WA PIC", "type": "phone",
     "help": "Dipakai untuk kirim info akun & verifikasi tracking."},
]

JENIS_FASKES = {
    "Klinik": {
        "ikon": "🏥",
        "fields": [
            {"key": "kode_regfas", "label": "Kode Registrasi Fasyankes", "type": "text",
             "help": "Didapat dari registrasifasyankes.kemkes.go.id"},
            {"key": "nama_faskes", "label": "Nama Klinik", "type": "text"},
            {"key": "jenis", "label": "Jenis", "type": "select",
             "options": ["Klinik Pratama", "Klinik Utama"]},
            {"key": "tipe", "label": "Type", "type": "select",
             "options": ["Rawat Jalan", "Rawat Inap"]},
            {"key": "pemilik", "label": "Pemilik", "type": "text"},
            *_ALAMAT,
            {"key": "no_izin", "label": "Nomor Izin Operasional", "type": "text"},
            {"key": "tgl_izin", "label": "Tgl Berlaku Izin", "type": "date"},
            *_PENANGGUNG_JAWAB,
        ],
    },
    "Praktik Mandiri": {
        "ikon": "🩺",
        "fields": [
            {"key": "kode_regfas", "label": "Kode Registrasi Fasyankes", "type": "text",
             "help": "Didapat dari registrasifasyankes.kemkes.go.id"},
            {"key": "nama_faskes", "label": "Nama Praktik Mandiri", "type": "text"},
            {"key": "pemilik", "label": "Pemilik", "type": "text"},
            *_ALAMAT,
            {"key": "no_sip", "label": "Nomor SIP", "type": "text"},
            {"key": "tgl_sip", "label": "Tgl Berlaku SIP", "type": "date"},
            *_PENANGGUNG_JAWAB,
        ],
    },
    "Apotek": {
        "ikon": "💊",
        "fields": [
            {"key": "nama_faskes", "label": "Nama Apotek", "type": "text"},
            {"key": "pemilik", "label": "Pemilik", "type": "text"},
            *_ALAMAT,
            {"key": "sip_sipa", "label": "SIP / SIPA", "type": "text"},
            {"key": "no_sio", "label": "Nomor SIO", "type": "text"},
            {"key": "tgl_sio", "label": "Tgl Berlaku SIO", "type": "date"},
            *_PENANGGUNG_JAWAB,
        ],
    },
    "Perusahaan": {
        "ikon": "🏭",
        "fields": [
            {"key": "nama_faskes", "label": "Nama Perusahaan", "type": "text"},
            {"key": "produk", "label": "Produk yang Dihasilkan", "type": "text"},
            {"key": "pemilik", "label": "Pemilik", "type": "text"},
            *_ALAMAT,
            {"key": "sip_sipa", "label": "SIP / SIPA", "type": "text"},
            {"key": "no_sio_nib", "label": "Nomor SIO / NIB", "type": "text"},
            {"key": "tgl_sio_nib", "label": "Tgl Berlaku SIO / NIB", "type": "date"},
            *_PENANGGUNG_JAWAB,
        ],
    },
    "Optik": {
        "ikon": "👓",
        "fields": [
            {"key": "nama_faskes", "label": "Nama Optik", "type": "text"},
            {"key": "pemilik", "label": "Pemilik", "type": "text"},
            *_ALAMAT,
            {"key": "no_sip", "label": "Nomor SIP", "type": "text"},
            {"key": "tgl_sip", "label": "Tgl Berlaku SIP", "type": "date"},
            {"key": "no_sio", "label": "Nomor SIO", "type": "text"},
            {"key": "tgl_sio", "label": "Tgl Berlaku SIO", "type": "date"},
            *_PENANGGUNG_JAWAB,
        ],
    },
}

# ---------------------------------------------------------------- Helpdesk
PROFESI = [
    "Dokter", "Dokter Gigi", "Perawat", "Bidan", "Apoteker",
    "Tenaga Teknis Kefarmasian", "Asisten Tenaga Kesehatan", "Tenaga Kesehatan Lainnya",
    "Non-Nakes / Admin",
]

FAQ = [
    ("Akun SISDMK sudah dibuat, kapan muncul di SatuSehat?",
     "Akun SISDMK dibuat dalam 1 hari kerja. Setelah akun diaktivasi, data akan "
     "muncul di SatuSehat Kemenkes dalam **1x24 jam**. Pantau di menu **Pantau Akun**."),
    ("Sudah dapat User ID, apa yang harus dilakukan?",
     f"Login di {URL_LOGIN_SISDMK}, lalu **segera ganti password** setelah login pertama. "
     "Password awal dikirim admin lewat WhatsApp, bukan ditampilkan di website ini."),
    ("Nama pemohon berbeda dengan nama faskes",
     f"Pengajuan perlu diklarifikasi. Silakan hubungi WhatsApp helpdesk {KONTAK['wa_helpdesk']}."),
    ("Data tidak sesuai / tidak valid",
     f"Periksa kembali data terhadap dokumen izin (SIP/SIO/izin operasional). "
     f"Jika masih bermasalah, hubungi admin SDMK di WhatsApp {KONTAK['wa_admin_sdmk']}."),
    ("Bagaimana verifikasi Asisten (Tenaga Kesehatan)?",
     f"Update ulang pekerjaan di SatuSehat SDMK, lalu isi formulir berikut: {URL_FORM_ASISTEN}. "
     f"Info lebih lanjut WhatsApp {KONTAK['wa_helpdesk']}."),
    ("Pekerjaan di SatuSehat SDMK tidak sesuai faskes praktik mandiri",
     "Ulangi pengisian pekerjaan pada SatuSehat SDMK dan sesuaikan dengan **nama faskes "
     "praktik mandirinya**."),
    ("Belum punya Kode Registrasi Fasyankes (Regfas)?",
     f"Daftar dulu di {URL_REGFAS}. Lihat langkah lengkap di menu **Info SISDMK**."),
]
