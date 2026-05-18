# Challenge Session Dashboard

**Dashboard Analisis Revisi Anggaran RKA TI 2026 — PMO Infrastruktur, IT Directorate BRI**

Status: aktif diperbarui (sinkron per 2026-05-18)

---

## Deskripsi

Aplikasi desktop yang memproses file Excel "Challenge Session" (window revisi pengadaan RKA TI) dan menghasilkan dashboard HTML interaktif untuk analisis:

- **Switching flow** antar proyek (bertambah/berkurang alokasi)
- **Delta TPC** — perubahan Total Project Cost awal vs revisi
- **Delta Kebutuhan** — selisih Alokasi Update ISG (col AB) vs Kebutuhan 1 Thn Revisi INF (col AF)
- **Perubahan scope/nama** proyek
- **Selisih vs minimum alokasi ISG**
- **Proyek baru (unplanned)**, yang dibatalkan, dan yang ditunda

---

## Cara Install

```bash
pip install -r requirements.txt
```

Dependensi:
- `openpyxl` — baca Excel lokal (DLP-safe, tidak upload ke browser)
- `PySide6` — desktop GUI

---

## Cara Menjalankan

### Opsi 1 — GUI (double-click)

```
run.bat
```

1. Klik **Pilih File** → pilih file `Challenge Session.xlsx`
2. Klik **Process & Generate Dashboard**
3. Dashboard otomatis terbuka di browser

### Opsi 2 — CLI

```bash
python generate_dashboard.py "Challenge Session.xlsx"
```

---

## Output

File HTML di folder `output/`:
- `dashboard_CS_YYYYMMDD_HHMMSS.html` — timestamped
- `dashboard_latest.html` — alias file terbaru

---

## Fitur Dashboard

Dashboard terdiri dari **1 halaman** dengan 2 bagian:

### Bagian Atas — KPI Cards (8 card, klik untuk detail)

| Card | Isi |
|---|---|
| Switching In | Proyek yang bertambah alokasi |
| Switching Out | Proyek yang berkurang alokasi |
| Delta TPC | Perubahan Total Project Cost (awal vs revisi) |
| Delta Kebutuhan vs Alokasi ISG | Selisih col AF (INF) vs col AB (ISG) |
| Perubahan Scope/Nama | Proyek yang nama/scope-nya diubah |
| Selisih vs Min ISG | Gap antara yang diminta INF vs minimum ISG |
| Unplanned Baru | Proyek baru dari Nota Dinas |
| Batal / Ditunda | Proyek yang dibatalkan atau ditunda |

**Klik card** → modal berisi daftar proyek terkait → **klik proyek** → drawer detail lengkap

### Bagian Bawah — Tabel Semua Proyek

- Search multi-field (nama, ID RKA, vendor, nota dinas)
- Filter: Status, DEPT, Planned/Unplanned, Jenis Perubahan
- Sort semua kolom
- Badge delta: `SW` `TPC` `Scope` `Baru`
- Kolom: ID RKA · Nama Proyek · DEPT · Status · Alokasi Revisi · Realisasi · Switching · Δ TPC · Δ Kebutuhan
- Klik baris → drawer detail

### Drawer Detail Proyek

- Delta boxes: TPC, Kebutuhan, Scope, Selisih ISG (highlight warna)
- Riwayat switching (bertambah/berkurang dari proyek mana)
- Keterangan revisi & catatan update progress
- Tombol "← Kembali ke daftar" jika dibuka dari card modal

---

## Struktur Folder

```
Challenge Session/
├── app.py                      # Entry point — PySide6 GUI
├── generate_dashboard.py       # CLI alternative
├── run.bat                     # Double-click untuk jalankan GUI
├── core/
│   ├── __init__.py
│   ├── parser_challenge.py     # Parser Excel → project records
│   └── builder.py              # Aggregasi + context builder
├── output/
│   ├── dashboard_template.html # (placeholder, tidak dipakai)
│   └── dashboard_CS_*.html     # Generated outputs (gitignored)
├── dashboard.html              # Base dashboard template
├── BRI_Design_System_v5.html   # Reference design system
├── MASTER_CONTEXT.md           # Master context untuk AI & developer
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Kolom Excel yang Digunakan

| Kolom Excel | Index (0-based) | Nama | Keterangan |
|---|---|---|---|
| U | 20 | ID RKA TI 2026 | Primary identifier |
| V/W/X | 21/22/23 | Nama Proyek | Awal / Rev / Akhir |
| Y | 24 | Total Project Cost (Awal) | Baseline TPC |
| Z | 25 | Kebutuhan 1 Tahun (Awal) | Baseline kebutuhan |
| AA | 26 | Nominal Switching | +/- switching |
| **AB** | **27** | **Alokasi Update** | **ISG allocation (for delta)** |
| AE | 30 | TPC Revisi | Revised TPC |
| **AF** | **31** | **Kebutuhan 1 Thn Revisi** | **INF request (for delta)** |
| AH | 33 | Selisih | Gap vs minimum ISG |
| AL–AW | 37–48 | Realisasi Jan–Des | Monthly realization |
| BV–CG | 73–84 | Prognosa Jan–Des | Monthly forecast |

**Delta Kebutuhan = col AF − col AB** (Kebutuhan INF − Alokasi ISG)

---

## Keamanan & DLP

- File Excel dibaca **lokal** oleh Python — tidak pernah di-upload ke browser
- Dashboard output = file HTML statis offline — tidak ada koneksi internet saat dibuka
- Tidak ada data yang dikirim ke luar mesin pengguna

---

## Tech Stack

- Python 3.11+ (openpyxl)
- PySide6 (desktop GUI)
- HTML + Vanilla JS (ECharts 5.5.x via CDN)
- BRI Design System v5
