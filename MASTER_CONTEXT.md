# MASTER CONTEXT — Challenge Session Dashboard v1.0

**Proyek:** Challenge Session Dashboard — Analisis Revisi RKA TI 2026  
**Tim:** PMO Infrastruktur (PIN) — IT Directorate, PT Bank Rakyat Indonesia  
**Versi Dokumen:** 1.0 (dibuat 2026-05-13)  
**Tujuan Dokumen:** Master context project untuk AI assistant & developer. Baca seluruh dokumen ini sebelum menulis satu baris kode pun.

---

## DAFTAR ISI

1. [Latar Belakang & Business Problem](#1-latar-belakang--business-problem)
2. [Arsitektur Aplikasi](#2-arsitektur-aplikasi)
3. [Skema Data & Struktur Excel](#3-skema-data--struktur-excel)
4. [Business Logic & Rules](#4-business-logic--rules)
5. [Spesifikasi Dashboard HTML Output](#5-spesifikasi-dashboard-html-output)
6. [Spesifikasi GUI Input (app.py)](#6-spesifikasi-gui-input-apppy)
7. [BRI Design System — CSS Tokens](#7-bri-design-system--css-tokens)
8. [Contoh Data & Aggregasi](#8-contoh-data--aggregasi)
9. [Rules & Edge Cases](#9-rules--edge-cases)
10. [Catatan Teknis & Debugging](#10-catatan-teknis--debugging)
11. [Development Phases & Changelog](#11-development-phases--changelog)
12. [Instruksi Khusus untuk AI Assistant](#12-instruksi-khusus-untuk-ai-assistant)
13. [Konvensi Kode](#13-konvensi-kode)
14. [Deployment & Environment](#14-deployment--environment)
15. [Security & DLP Considerations](#15-security--dlp-considerations)

---

## 1. LATAR BELAKANG & BUSINESS PROBLEM

### Konteks Organisasi
Tim INF (Infrastruktur) berada di bawah IT Directorate BRI. Setiap tahun, INF mengusulkan alokasi anggaran ke **ISG (IT Strategy & Governance)** melalui mekanisme **RKA TI (Rencana Kerja Anggaran Teknologi Informasi)**.

Sepanjang tahun berjalan, terdapat **window revisi** yang disebut **Challenge Session** — di mana alokasi anggaran dapat di-switching antar proyek, proyek baru (unplanned) dapat ditambahkan, dan proyek yang tidak jadi dapat dibatalkan.

### Problem Statement
> "Bagaimana ringkasan hasil Challenge Session? Proyek mana yang bertambah/berkurang alokasi, berapa total switching, dan bagaimana status pengadaan terkini?"

Selama ini, data Challenge Session ada di satu file Excel besar (~1250 baris, 101 kolom) dengan struktur multi-header yang sulit dibaca langsung. Tidak ada visualisasi yang menunjukkan:
- Flow switching antar proyek (siapa donor, siapa penerima)
- Status pengadaan agregat
- Perbandingan realisasi vs prognosa
- Proyeksi cashout multi-tahun

### Tujuan Aplikasi
Membangun **aplikasi GUI desktop** yang:
1. Membaca file Challenge Session Excel secara **lokal** (DLP-safe, tidak upload ke browser/server)
2. Memproses dan mengekstrak 225+ proyek dari struktur multi-header
3. Menghasilkan **dashboard HTML interaktif** dengan 5 view analisis
4. Menampilkan switching flow (Sankey diagram), status distribusi, realisasi vs prognosa
5. Mendukung export (CSV, Excel, PNG, PDF/print)

### Success Criteria
- [ ] Parser berhasil mengekstrak semua proyek valid (225+ items)
- [ ] Total Kebutuhan 1 Tahun Revisi = Rp 2.079.764.256.894 (match header Excel)
- [ ] Switching net = 0 (in = out)
- [ ] Dashboard render tanpa error di Chrome/Edge
- [ ] Dark mode toggle berfungsi
- [ ] Semua chart interaktif (tooltip, zoom)

---

## 2. ARSITEKTUR APLIKASI

### Stack Teknologi

| Komponen | Teknologi | Versi |
|---|---|---|
| Runtime | Python | 3.11+ |
| GUI | PySide6 | 6.8+ |
| Excel Reader | openpyxl | 3.1+ |
| Templating | Jinja2 | 3.1+ |
| Charts | ECharts (CDN) | 5.5.0 |
| Output | Single-file HTML | self-contained |

### Struktur Folder
```
Challenge Session/
├── app.py                          # PySide6 desktop GUI launcher
├── generate_dashboard.py           # CLI alternative
├── core/
│   ├── __init__.py
│   ├── parser_challenge.py         # Parser Excel → ProjectRow records
│   └── builder.py                  # Aggregasi + context dict builder
├── output/
│   ├── dashboard_template.html     # Jinja2 template (BRI Design System)
│   └── dashboard_CS_*.html         # Generated outputs (gitignored)
├── BRI_Design_System_v5.html       # Reference design system
├── MASTER_CONTEXT.md               # This document
├── README.md
├── requirements.txt
└── .gitignore
```

### Alur Data
```
┌─────────────────────────────────────────────┐
│         USER INPUT (1 Excel file)            │
│  ┌───────────────────────────────────────┐  │
│  │ Challenge Session.xlsx                 │  │
│  │ (Sheet3, ~1250 rows × 101 cols)       │  │
│  └───────────────────┬───────────────────┘  │
└──────────────────────│──────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  parser_challenge.py    │
          │  • Read with openpyxl   │
          │  • Detect project rows  │
          │  • Merge continuation   │
          │  • Extract switching    │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │     builder.py          │
          │  • Aggregate totals     │
          │  • Build distributions  │
          │  • Extract switch pairs │
          │  • Parse multi-year est │
          │  • Serialize to JSON    │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  Jinja2 render          │
          │  dashboard_template.html│
          │  → Embed JSON data      │
          │  → KPI, charts, tables  │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  output/dashboard_CS_*  │
          │  → Open in browser      │
          └────────────────────────┘
```

---

## 3. SKEMA DATA & STRUKTUR EXCEL

### File Input
**Nama:** `Challenge Session.xlsx`  
**Sheet:** Sheet pertama (biasanya "Sheet3")  
**Total rows:** ~1250  
**Total cols:** 101 (A–CW)

### Struktur Header
```
Row 1-7:   Summary/legend area
Row 8-11:  Multi-row merged headers (group labels)
Row 12-13: Sub-labels
Row 14:    Summary totals row (aggregated values)
Row 15-17: Repeated header block (column names)
Row 18+:   Data rows (projects + continuation rows)
```

### Kolom Kunci (0-indexed)

| Index | Nama Kolom | Variabel Internal | Keterangan |
|---|---|---|---|
| 1 | No. | `no` | Nomor urut |
| 2 | Parent / Child | `parent_child` | "Parent" atau "Child" |
| 3 | Planned / Unplanned | `planned` | Marker tipe proyek |
| 7 | Group | `group` | Selalu "INF" |
| 8 | DEPT | `dept` | Departemen (NSQ, CDQ, DCO, dll) |
| 9 | Tim | `tim` | Tim pelaksana |
| **20** | **ID RKA TI 2026** | **`id_rka_ti`** | **Primary identifier** |
| 21 | Nama Proyek (Awal) | `name_awal` | Nama sebelum revisi |
| 22 | Nama Proyek (Rev) | `name_rev` | Nama setelah revisi |
| 23 | Nama Proyek (Akhir) | `name` | Nama final Challenge Session |
| 25 | Total Kebutuhan 1 Tahun | `kebutuhan_1thn` | Alokasi awal |
| **26** | **Nominal Switching** | **`nominal_switching`** | **+/- switching** |
| 27 | Alokasi Update | `alokasi_update` | Alokasi setelah switching |
| 28 | IP Switching/Link | `ip_switching` | Link Confluence |
| 29 | Keterangan Switching | `keterangan_switching` | Narasi switching |
| **31** | **Kebutuhan 1 Thn Revisi** | **`kebutuhan_1thn_rev`** | **Alokasi final (primary)** |
| 34 | Keterangan Revisi | `keterangan_revisi` | Estimasi multi-tahun |
| 35 | Update Progress | `update_progress` | Status terkini |
| 36 | Catatan | `catatan` | Catatan tambahan |
| 37–48 | Jan–Des (Realisasi) | `real_jan`..`real_des` | Realisasi bulanan |
| 49 | Total Realisasi | `real_total` | Sum Jan–Des |
| 61 | Kategori Pengadaan | `kategori` | Hygiene Factor/Rass, Governance, dll |
| 62 | Klasifikasi | `klasifikasi` | Run / Change / Transform |
| 63 | Rutin | `rutin` | Rutin / Tidak Rutin |
| 64 | Baru | `baru` | Baru / Sisa Bayar / Perpanjangan |
| 65 | Status Pengadaan | `status_pengadaan` | Status aktual |
| 71 | Principle | `principle` | Vendor prinsipal |
| 72 | BP | `bp` | Business Partner |
| 73–84 | Jan–Des (Prognosa) | `prog_jan`..`prog_des` | Prognosa non-kumulatif |
| 87–98 | Jan–Des (Prognosa Kum) | `prog_kum_jan`..`prog_kum_des` | Prognosa kumulatif |

### Deteksi Baris Proyek
Sebuah baris dianggap proyek baru jika:
1. `id_rka_ti` (col 20) match pattern `2026-INF-A.XX.XXX`, **ATAU**
2. Nama proyek (col 21/22/23) valid (len > 3, bukan "-") **DAN** ada marker Parent/Child atau Planned/Unplanned

Baris lain = continuation row → merge ke proyek sebelumnya (append keterangan/catatan).

### Summary Totals (Row 14, 0-indexed)
```
Col 25: Total Kebutuhan 1 Tahun    = 1,240,100,637,920
Col 26: Total Nominal Switching     = 139,614,166,736
Col 27: Total Alokasi Update        = 1,379,714,804,656
Col 31: Total Kebutuhan 1 Thn Rev   = 2,079,764,256,894  ← PRIMARY
Col 49: Total Realisasi             = 1,952,661,652,359
```

---

## 4. BUSINESS LOGIC & RULES

### 4.1 Alokasi Primary
```python
# Alokasi final per proyek = kebutuhan_1thn_rev (col 31)
# Fallback ke alokasi_update (col 27) jika col 31 kosong
alokasi = kebutuhan_1thn_rev or alokasi_update
```

### 4.2 Switching Classification
```python
if nominal_switching > 0:  → "Bertambah"
if nominal_switching < 0:  → "Berkurang"
if planned == "Unplanned": → "Baru (Unplanned)"
if status contains "batal": → "Batal"
if status contains "ditunda": → "Ditunda"
else:                       → "Tidak berubah"
```

### 4.3 Status Normalization
Raw status dari Excel dinormalisasi ke 10 kategori:
- Selesai (Lunas)
- Pembayaran
- SPK Terbit
- IP Terbit
- Pengadaan
- Belum Mulai
- Batal
- Ditunda
- TBC
- Tidak diketahui

### 4.4 Cutoff Month Detection
Auto-detect bulan terakhir yang memiliki realisasi > 0 dari agregat seluruh proyek.

### 4.5 Switching Pair Extraction
Dari kolom `keterangan_switching`, parse pattern:
```
"Bertambah, sebesar Rp X dari [Nama Proyek] (ID-RKA)"
"Berkurang, sebesar Rp X ke [Nama Proyek] (ID-RKA)"
```
Hasilkan pasangan `{source, target, value}` untuk Sankey diagram.

### 4.6 Multi-Year Estimation (CJE0)
Dari kolom `keterangan_revisi` dan `catatan`, parse pattern:
```
"Estimasi realisasi maksimum tahun XXXX: Rp YYY"
```
Aggregate per tahun untuk proyeksi cashout 2026–2030+.

---

## 5. SPESIFIKASI DASHBOARD HTML OUTPUT

### 5 View/Tab

| Tab | Konten |
|---|---|
| **Overview** | KPI cards, chart realisasi vs prognosa kumulatif, donut status, bar DEPT, pie klasifikasi/kategori/asset/rutin |
| **Perubahan** | KPI switching, list bertambah/berkurang (top 15), unplanned baru, batal/ditunda |
| **Pengadaan** | Tabel lengkap: search + 5 filter + sort + detail drawer |
| **RKA TI** | Bar realisasi vs prognosa bulanan, sunburst GL×Asset, Sankey switching, top 15 proyek, heatmap DEPT×bulan |
| **CJE0** | Bar multi-tahun, top future projects, detail expandable per tahun |

### KPI Cards (Overview)
- Alokasi Update (Revisi) — Rp 2.08 T
- Realisasi YTD — dengan % serapan
- Switching Flow — total in
- Sisa Anggaran
- Δ Total Project Cost
- Prognosa 2026

### Format Angka
- Rupiah: `Rp 1,38 T` / `Rp 241,69 M` / `Rp 847,27 Jt`
- Persentase: `67.4%`
- Locale: Indonesia (titik = ribuan, koma = desimal)

### Dark Mode
- Toggle di topbar, saved ke `localStorage`
- CSS: `html.dark` overrides

---

## 6. SPESIFIKASI GUI INPUT (app.py)

PySide6 desktop app dengan flow:
1. Pilih 1 file Excel (Challenge Session)
2. Klik Process
3. Progress bar + status
4. Tombol buka dashboard setelah selesai

### Layout
```
+-----------------------------------------------------+
|  +- HEADER BAR (BRI Blue gradient) ---------------+  |
|  |  CS  Challenge Session Dashboard    v1.0.0      |  |
|  |      PMO Infrastruktur · IT Directorate BRI     |  |
|  +-----------------------------------------------+  |
|  +- WHITE CARD ----------------------------------+  |
|  |  📁 Input File                                 |  |
|  |  Pilih file Challenge Session Excel (.xlsx)    |  |
|  |                                                |  |
|  |  [1] [___filename.xlsx___________] [Pilih File]|  |
|  |                                                |  |
|  |  ─────────────────────────────────────────     |  |
|  |                                                |  |
|  |  [▶  Process & Generate Dashboard          ]   |  |
|  |                                                |  |
|  |  [================--------] (orange bar)       |  |
|  |  Ditemukan 225 proyek. Menghitung aggregasi…   |  |
|  |                                                |  |
|  |  [🌐  Buka Dashboard]                          |  |
|  +-----------------------------------------------+  |
|  © 2026 PT Bank Rakyat Indonesia — PMO INF IT Dir    |
+-----------------------------------------------------+
```

---

## 7. BRI DESIGN SYSTEM — CSS TOKENS

```css
:root {
  --bri-blue: #00529C;
  --bri-blue-600: #003F7A;
  --bri-blue-700: #002D58;
  --bri-orange: #F37021;
  --bg: #F6F8FB;
  --card: #FFFFFF;
  --border: #E2E8F2;
  --text-1: #121B2A;
  --text-2: #42536A;
  --text-3: #8C9BB0;
  --success: #13A888;
  --warning: #E6A700;
  --danger: #D93A3A;
  --info: #3B82C4;
}
```

Font: Inter (Google Fonts), semua elemen.  
Angka: `font-variant-numeric: tabular-nums`  
Border radius: 6px (sm), 10px (md), 14px (lg), 20px (xl)

---

## 8. CONTOH DATA & AGGREGASI

### Sample Project Record
```python
{
    "id_rka_ti": "2026-INF-A.01.159",
    "name": "Pengadaan Mesin Staging IBM AS/400 Power11",
    "dept": "CDQ",
    "tim": "IDC",
    "planned": "Unplanned",
    "parent_child": "Parent",
    "kebutuhan_1thn_rev": 241689766698,
    "nominal_switching": 241689905540,
    "alokasi_update": 241689766698,
    "real_total": 241689766698,
    "prog_total": 241689905540,
    "status": "Belum Mulai",
    "change_type": "Bertambah",
    "serapan_pct": 100.0,
    "switching_log": [
        {"ip": "2026 213 INF...", "desc": "Bertambah, sebesar Rp5.685.047.339,- dari..."}
    ]
}
```

### Validated Aggregates
```
Total proyek parsed:        225
Total Kebutuhan 1 Thn Rev:  2,079,764,256,894  (match Excel header)
Switching In:               451,164,361,613
Switching Out:              451,164,361,613
Net Switching:              0
Unique IDs:                 196
Proyek tanpa ID (unplanned): 30
```

### Status Distribution
```
Belum Mulai:    104
Pembayaran:      75
Pengadaan:       13
Batal:            9
SPK Terbit:       7
IP Terbit:        6
Selesai (Lunas):  6
TBC:              1
Tidak diketahui:  4
```

### DEPT Distribution (top)
```
CDQ: 36, NSQ: 23, DCO: 23, SRO: 15, SAC: 15, SSO: 9, CMO: 7, ENO: 5
```

---

## 9. RULES & EDGE CASES

| # | Kasus | Handling |
|---|---|---|
| 1 | Proyek tanpa ID RKA (unplanned baru) | Tetap diproses; key = nama proyek |
| 2 | Continuation rows (hanya teks di col 28/29/34/36) | Merge ke proyek sebelumnya |
| 3 | Header rows (row 15-17) yang repeat | Skip — bukan data |
| 4 | Kolom numerik berisi teks/tanggal | `_num()` coerce ke 0.0 |
| 5 | Nominal switching = 0 tapi status "Batal" | Classify sebagai "Batal" bukan "Tidak berubah" |
| 6 | Multiple switching entries per proyek | Semua di-append ke `switching_log` |
| 7 | Estimasi multi-tahun di berbagai kolom | Parse dari keterangan_revisi + catatan + switching_log |
| 8 | Sheet name bervariasi | Selalu ambil sheet pertama |
| 9 | File format .xls / .xlsm | Didukung via openpyxl |
| 10 | Alokasi = 0 tapi ada realisasi | Tetap tampilkan; serapan_pct = 0 |

---

## 10. CATATAN TEKNIS & DEBUGGING

### Parser — Deteksi Baris Proyek
```python
# Baris = proyek baru jika:
id_valid = re.match(r"^\d{4}-[A-Z]+-[A-Z]\.\d", id_rka)
name_valid = name and name != "-" and len(name) > 3
has_marker = parent_child in {"Parent","Child"} or planned in {"Planned","Unplanned"}
is_project = id_valid or (name_valid and has_marker)
```

### Alokasi Column Priority
```
PRIMARY:  col 31 (kebutuhan_1thn_rev) — angka final pasca-Challenge Session
FALLBACK: col 27 (alokasi_update) — jika col 31 kosong
```

Alasan: Col 31 sum = 2.08T (match Excel header exactly). Col 27 sum = 1.43T (pre-revisi).

### Switching Pair Regex
```python
re.compile(r"(Bertambah|Berkurang)[^.]*?Rp\s*([\d.,]+)[^()]*\(([^)]+)\)", re.IGNORECASE)
```

### Multi-Year Estimation Regex
```python
re.compile(r"tahun\s*(20\d\d)\s*:?\s*Rp\s*([\d.,]+)", re.IGNORECASE)
```

---

## 11. DEVELOPMENT PHASES & CHANGELOG

### Phase 1 — Initial Build (v1.0, 2026-05-13)
- [x] `core/parser_challenge.py` — Full parser with continuation row merging
- [x] `core/builder.py` — Aggregation + context builder + JSON serialization
- [x] `app.py` — PySide6 GUI (BRI-styled)
- [x] `generate_dashboard.py` — CLI alternative
- [x] `output/dashboard_template.html` — Jinja2 template (5 views)
- [x] `README.md` — Project documentation
- [x] `MASTER_CONTEXT.md` — This document
- [x] Validated: 225 proyek, totals match Excel header

### Planned
- [ ] Export PDF dengan letterhead BRI
- [ ] Comparison antar-periode (misal Apr vs Mei)
- [ ] Alert system untuk proyek over-timeline
- [ ] Integration dengan MappingRealisasi app (shared data)

---

## 12. INSTRUKSI KHUSUS UNTUK AI ASSISTANT

1. **Baca seluruh MASTER_CONTEXT.md sebelum generate kode apapun**
2. **File Excel TIDAK BOLEH di-upload ke browser** — DLP restriction BRI
3. **Parsing harus via Python (openpyxl)** — bukan SheetJS di browser
4. **Dashboard output = single HTML file** — embed semua CSS/JS (kecuali ECharts CDN)
5. **Alokasi primary = col 31 (kebutuhan_1thn_rev)** — bukan col 27
6. **Semua angka format locale Indonesia** (Rp, titik ribuan, koma desimal)
7. **Dark mode** via `html.dark` class + toggle
8. **Table harus sortable** (vanilla JS click handler)
9. **Switching flow** harus ada Sankey diagram
10. **Multi-year CJE0** harus parse dari teks keterangan
11. **Jangan hardcode data** — semua dari hasil parse + Jinja2 inject
12. **Ikuti pola project MappingRealisasi** — PySide6 GUI, core/ folder, output/ folder

### Larangan Keras
- ❌ Jangan upload file ke browser (DLP)
- ❌ Jangan pakai pandas (terlalu heavy untuk task ini — openpyxl cukup)
- ❌ Jangan hardcode path file
- ❌ Jangan kirim data ke server/internet
- ❌ Jangan ubah struktur kolom Excel tanpa konfirmasi

---

## 13. KONVENSI KODE

```python
# Python — snake_case
id_rka_ti, nominal_switching, kebutuhan_1thn_rev, parse_challenge_session

# JavaScript — camelCase
projectData, totalAlokasi, formatRupiah(), toggleDarkMode()

# CSS class — kebab-case
.kpi-card, .chip.success, .change-item.in

# File naming — snake_case
parser_challenge.py, builder.py, generate_dashboard.py

# Constants — UPPER_SNAKE
DATA_START_ROW = 17
SUMMARY_ROW = 14
COL = {...}
```

---

## 14. DEPLOYMENT & ENVIRONMENT

### System Requirements
| Requirement | Minimum |
|---|---|
| OS | Windows 10+ |
| Python | 3.11+ |
| RAM | 2 GB |
| Disk | 200 MB |
| Display | 1366×768 |
| Network | Tidak diperlukan (offline) |

### Installation
```bash
git clone <repo>
cd "Challenge Session"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

---

## 15. SECURITY & DLP CONSIDERATIONS

### Data Loss Prevention (DLP)
- ✅ File Excel dibaca **lokal** oleh Python — TIDAK di-upload ke browser
- ✅ Dashboard output = file HTML statis — TIDAK ada koneksi internet saat dibuka
- ✅ Tidak ada data yang dikirim ke luar mesin pengguna
- ✅ ECharts CDN hanya untuk library JS (bukan data) — bisa di-bundle offline jika perlu

### Kenapa Tidak Upload di Browser?
BRI memiliki kebijakan DLP yang memblokir upload file sensitif (Excel berisi data anggaran) ke browser. Oleh karena itu:
- Parsing dilakukan oleh **Python (openpyxl)** di mesin lokal
- Data di-inject ke HTML template via **Jinja2** (server-side rendering)
- Hasil akhir = file HTML yang sudah berisi semua data (embedded JSON)
- User hanya membuka file HTML lokal di browser — tidak ada upload

### Output Security
- Generated HTML berisi data anggaran mentah — treat as **CONFIDENTIAL**
- Simpan di folder dengan akses terbatas
- Jangan commit file output ke Git (sudah di `.gitignore`)

---

**Dokumen ini adalah Referensi Master Context untuk Challenge Session Dashboard.**

**Author:** PMO Infrastruktur (PIN) — IT Directorate BRI  
**Status:** Active Development  
**Terakhir Diperbarui:** 2026-05-13  
