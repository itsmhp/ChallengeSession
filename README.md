# Challenge Session Dashboard

**Dashboard Analisis Revisi Anggaran RKA TI 2026 — PMO Infrastruktur, IT Directorate BRI**

Status: aktif diperbarui (sinkron per 2026-05-13)

## Deskripsi

Aplikasi desktop yang memproses file Excel "Challenge Session" (window revisi pengadaan RKA TI) dan menghasilkan dashboard HTML interaktif untuk analisis:
- **Switching flow** antar proyek (bertambah/berkurang alokasi)
- **Status pengadaan** seluruh proyek INF Group
- **Realisasi vs Prognosa** bulanan dan kumulatif
- **Proyeksi multi-tahun** (CJE0) berdasarkan estimasi termin pembayaran
- **Proyek baru (unplanned)**, yang dibatalkan, dan yang ditunda

## Cara Install

```bash
pip install -r requirements.txt
```

Dependensi utama:
- openpyxl
- jinja2
- PySide6

## Cara Menjalankan

```bash
python app.py
```

1. Klik tombol **Pilih File** dan pilih file Challenge Session Excel (.xlsx)
2. Klik **Process & Generate Dashboard**
3. Dashboard otomatis terbuka di browser

Alternatif (tanpa GUI):

```bash
python generate_dashboard.py "Challenge Session.xlsx"
```

## Output

File HTML dashboard interaktif di folder `output/`, dengan format nama: `dashboard_CS_YYYYMMDD_HHMMSS.html`

Alias file terbaru:
- `output/dashboard_latest.html`

Dashboard meliputi:
- **Overview**: KPI utama (alokasi revisi, realisasi YTD, switching flow, sisa, prognosa), chart realisasi vs prognosa, distribusi status, breakdown per DEPT
- **Perubahan**: Highlight revisi — proyek bertambah/berkurang alokasi, unplanned baru, batal/ditunda
- **Pengadaan**: Tabel lengkap sortable & filterable dengan detail per proyek
- **RKA TI**: Realisasi vs prognosa bulanan, Sankey switching flow, heatmap DEPT × bulan, top proyek
- **CJE0**: Proyeksi cashout multi-tahun (2026–2030+) dari estimasi termin pembayaran

## Struktur Folder

```
Challenge Session/
├── app.py                          # Entry point — PySide6 GUI
├── generate_dashboard.py           # Generator dashboard via CLI
├── core/
│   ├── __init__.py
│   ├── parser_challenge.py         # Parser Challenge Session Excel → records
│   └── builder.py                  # Aggregasi & context builder untuk Jinja2
├── output/
│   ├── dashboard_template.html     # Jinja2 template dashboard
│   └── dashboard_CS_*.html         # Generated output files (gitignored)
├── BRI_Design_System_v5.html       # Reference: BRI Design System spec
├── MASTER_CONTEXT.md               # Master context untuk AI & developer
├── requirements.txt
├── .gitignore
└── README.md
```

## Tech Stack

- Python 3.11+ (openpyxl, jinja2)
- PySide6 (desktop GUI)
- HTML + Vanilla JS (ECharts 5.5.x)
- BRI Design System v5

## Keamanan & DLP

- File Excel dibaca **lokal** oleh Python — tidak pernah di-upload ke browser atau server
- Dashboard output adalah file HTML statis offline — tidak ada koneksi internet saat dibuka
- Tidak ada data yang dikirim ke luar mesin pengguna

## Catatan Penting

- File input: `Challenge Session.xlsx` (format window revisi pengadaan dari ISG)
- Sheet yang diproses: sheet pertama (biasanya "Sheet3")
- Struktur kolom fixed — sesuai template Challenge Session ISG
- Kolom alokasi utama: `Kebutuhan 1 Tahun Revisi` (col 31) sebagai angka final pasca-Challenge Session
- Kolom switching: `Nominal Switching` (col 26) — positif = bertambah, negatif = berkurang
