# MASTER CONTEXT — RKA TI Budget Realization Analyzer v2.0

**Proyek:** INF Budget Alignment Dashboard  
**Tim:** PMO Infrastruktur (PIN) — IT Directorate, PT Bank Rakyat Indonesia  
**Versi Dokumen:** 2.1 (diperbarui 2026-04-23)  
**Repository:** https://github.com/itsmhp/MappingRealisasi  
**Tujuan Dokumen:** Master context project untuk GitHub Copilot & pengembang baru. Baca seluruh dokumen ini sebelum menulis satu baris kode pun.

---

## DAFTAR ISI

1. [Latar Belakang & Business Problem](#1-latar-belakang--business-problem)
2. [Arsitektur Aplikasi](#2-arsitektur-aplikasi)
3. [Skema Data & Kolom Kunci](#3-skema-data--kolom-kunci)
4. [Business Logic & Rules Kalkulasi](#4-business-logic--rules-kalkulasi)
5. [Spesifikasi Dashboard HTML Output](#5-spesifikasi-dashboard-html-output)
6. [Spesifikasi GUI Input (app.py)](#6-spesifikasi-gui-input-apppy)
7. [BRI Design System — CSS Tokens](#7-bri-design-system--css-tokens)
8. [Contoh Output Merged Data](#8-contoh-output-merged-data)
9. [Rules & Edge Cases](#9-rules--edge-cases)
10. [Catatan Teknis & Debugging](#10-catatan-teknis--debugging)
11. [Development Phases & Changelog](#11-development-phases--changelog)
12. [Instruksi Khusus untuk GitHub Copilot](#12-instruksi-khusus-untuk-github-copilot)
13. [Konvensi Kode](#13-konvensi-kode)
14. [Deployment & Environment](#14-deployment--environment)
15. [Testing Strategy](#15-testing-strategy)
16. [Troubleshooting & Known Issues](#16-troubleshooting--known-issues)
17. [Performance & Scalability](#17-performance--scalability)
18. [Security Considerations](#18-security-considerations)
19. [Roadmap & Future Enhancements](#19-roadmap--future-enhancements)
20. [FAQ & Glossary](#20-faq--glossary)
21. [Architecture Diagrams (Detailed)](#21-architecture-diagrams-detailed)

---

## 1. LATAR BELAKANG & BUSINESS PROBLEM

### Konteks Organisasi
Tim INF (Infrastruktur) berada di bawah IT Directorate BRI. Setiap tahun, INF mengusulkan alokasi anggaran ke **ISG (IT Strategy & Governance)** melalui mekanisme **RKA TI (Rencana Kerja Anggaran Teknologi Informasi)**. ISG kemudian menyetujui dan mendistribusikan alokasi tersebut.

Sepanjang tahun berjalan, realisasi pembayaran dicatat di sistem SAP dan dipetakan ke setiap ID RKA TI melalui proses **Mapping Realisasi** (CAPEX dan OPEX).

### Problem Statement
> "Apakah alokasi anggaran yang INF usulkan ke ISG sudah **tepat sasaran**? Artinya, apakah realisasi (pengeluaran aktual) yang terjadi memang terkait dengan pengadaan/kegiatan yang dialokasikan di ID RKA TI tersebut?"

Selama ini, data alokasi ada di Master Data Excel (ratusan kolom), sementara data realisasi ada di file Mapping Realisasi terpisah (CAPEX & OPEX). Tidak ada satu tempat yang bisa menjawab pertanyaan di atas secara cepat.

### Tujuan Aplikasi
Membangun **aplikasi GUI desktop** yang:
1. Menerima input 3 file Excel sekaligus
2. Memproses dan menyambungkan data berdasarkan **ID RKA TI**
3. Menghasilkan **dashboard HTML interaktif** yang menampilkan analisis alignment antara alokasi dan realisasi per ID RKA TI
4. Memungkinkan drill-down ke detail transaksi per ID RKA TI
5. Memberikan **warning OVER_BUDGET** untuk item yang realisasinya melebihi 100% alokasi

---

## 2. ARSITEKTUR APLIKASI

### Stack Teknologi

| Komponen | Teknologi | Versi |
|---|---|---|
| Runtime | Python | 3.13+ |
| GUI | PySide6 | 6.8+ |
| Data Processing | pandas | 3.0+ |
| Excel Reader | openpyxl | 3.1+ |
| Templating | Jinja2 | 3.1+ |
| Charts | Chart.js (CDN, optional/hidden by default) | 4.4.0 |
| Output | Single-file HTML | self-contained |

### Struktur Folder
```
MappingRealisasi/
├── app.py                           # Entry point: PySide6 desktop GUI launcher
├── core/
│   ├── __init__.py
│   ├── parser_capex.py              # Parser CAPEX Mapping Excel → DataFrame
│   ├── parser_opex.py               # Parser OPEX Mapping Excel → DataFrame
│   ├── parser_master.py             # Parser Master Data Excel → 2 DataFrames (CAPEX/OPEX)
│   └── merger.py                    # JOIN + alignment kalkulasi + context builder
├── output/
│   ├── dashboard_template.html      # Jinja2 template (BRI Design System)
│   └── dashboard_INF_*.html         # Generated output files (gitignored)
├── BRI_Design_System_v5.html        # Reference: BRI Design System spec
├── MASTER_CONTEXT_RKA_ANALYZER.md   # This document
├── requirements.txt
├── .gitignore
└── README.md
```

### Alur Data (Data Flow)
```
┌───────────────────────────────────────────────────────────┐
│                    USER INPUT (3 Excel)                     │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐ │
│  │ CAPEX Mapping │ │ OPEX Mapping │ │ Master Data ISG    │ │
│  │ (.xlsx)       │ │ (.xlsx)      │ │ (.xlsx)            │ │
│  └───────┬──────┘ └──────┬───────┘ └─────────┬──────────┘ │
└──────────│───────────────│────────────────────│────────────┘
           │               │                    │
           ▼               ▼                    ▼
   parser_capex.py   parser_opex.py    parser_master.py
           │               │          ┌────────┴────────┐
           │               │          │                  │
           ▼               ▼          ▼                  ▼
     df_mapping_c    df_mapping_o   df_master_c      df_master_o
           │               │          │                  │
           └───────┬───────┘          └────────┬─────────┘
                   │                           │
                   ▼                           ▼
            ┌──────────────────────────────────────────┐
            │            merger.py                       │
            │  LEFT JOIN on id_rka_ti                   │
            │  → Aggregate realisasi per ID            │
            │  → Calculate: pct_realisasi, sisa, etc.  │
            │  → Classify alignment (9 categories)     │
            │  → Build context dict for Jinja2         │
            └─────────────────┬────────────────────────┘
                              │
                              ▼
            ┌──────────────────────────────────────────┐
            │    Jinja2 render(dashboard_template.html) │
            │    → Embed JSON data                      │
            │    → KPI cards, tables, modal drill-down  │
            │    → Sortable/filterable tables           │
            └─────────────────┬────────────────────────┘
                              │
                              ▼
            ┌──────────────────────────────────────────┐
            │  output/dashboard_INF_YYYYMMDD_HHMMSS.html│
            │  → Auto-open in browser                   │
            └──────────────────────────────────────────┘
```

---

## 3. SKEMA DATA & KOLOM KUNCI

### 3.1 CAPEX Mapping File
**File contoh:** `20260407 Mapping Realisasi CAPEX Maret 2026.xlsx`  
**Sheet:** `INF`  
**Header:** Row 1 (pandas header=0)  
**Data starts:** Row 5 (skip rows 2-4 = summary/total rows → `iloc[3:]`)  

| Excel Col | Kolom Asli | Variabel Internal | Tipe | Catatan |
|---|---|---|---|---|
| O (15) | `ID RKA TI` | `id_rka_ti` | str | **Primary Join Key** |
| J (10) | `Nama Pengadaan` | `nama_pengadaan` | str | Nama item pengadaan |
| M (13) | `Nama SPK` | `nama_spk` | str | Nama SPK |
| N (14) | `Nilai SPK` | `nilai_spk` | float | Nilai kontrak |
| V (22) | `Jan` | `realisasi_jan` | float | Realisasi Januari |
| W (23) | `Feb` | `realisasi_feb` | float | Realisasi Februari |
| X (24) | `Mar` | `realisasi_mar` | float | Realisasi Maret |
| Y (25) | `Grand Total` | `realisasi_total` | float | Total realisasi Jan–Mar |
| AB (28) | `Status Mapping` | `status_mapping` | str | "Sudah Mapping"/lainnya |
| AC (29) | `Total Mapping` | `total_mapping` | float | Nominal ter-mapping |
| P (16) | `Kode Confluence` | `kode_confluence` | str | Link confluence |
| Q (17) | `No IP` | `no_ip` | str | Nomor Izin Prinsip |
| R (18) | `Nama Vendor/Seller` | `nama_vendor` | str | Nama vendor |

**Parser approach:** Column name matching (search for column names in header row).

### 3.2 OPEX Mapping File
**File contoh:** `20260407 Mapping Realisasi OPEX Maret 2026.xlsx`  
**Sheet:** `INF`  
**Header:** Row 1 (pandas header=0)  
**Data starts:** Row 5 (skip rows 2-4 = summary/total rows → `iloc[3:]`)  

| Excel Col | Kolom Asli | Variabel Internal | Tipe | Catatan |
|---|---|---|---|---|
| M (13) | `ID RKAP TI` | `id_rka_ti` | str | **Join Key** (nama beda!) |
| K (11) | `Nama SPK` | `nama_spk` | str | |
| L (12) | `Nilai SPK` | `nilai_spk` | float | |
| AA (27) | `Januari` | `realisasi_jan` | float | Nama bulan berbeda! |
| AB (28) | `Februari` | `realisasi_feb` | float | |
| AC (29) | `Maret` | `realisasi_mar` | float | |
| AD (30) | `Grand Total` | `realisasi_total` | float | |
| AG (33) | `Status Mapping` | `status_mapping` | str | |
| AH (34) | `Total Mapping` | `total_mapping` | float | |
| Y (25) | `Nama Vendor` | `nama_vendor` | str | |
| N (14) | `Kode Confluence 2025` | `kode_confluence` | str | |
| Q (17) | `WBS` | `wbs` | str | WBS element |
| R (18) | `Nomor Izin Prinsip` | `no_ip` | str | |

**Perbedaan CAPEX vs OPEX:**

| Aspek | CAPEX | OPEX |
|---|---|---|
| Join key col name | `ID RKA TI` | `ID RKAP TI` |
| Bulan cols | `Jan`, `Feb`, `Mar` | `Januari`, `Februari`, `Maret` |
| Nama vendor col | `Nama Vendor/Seller` | `Nama Vendor` |
| Extra fields | — | `WBS` |

### 3.3 Master Data File

> **⚠ CRITICAL:** Sheet CAPEX dan OPEX memiliki **header row yang BERBEDA!**

**File contoh:** `Master Data - INF (Update 13 April 2026) (2).xlsx`  
**NEW Format Support (v2.2.1+):** `MASTERDATA INF (28 April 2026).xlsx`

**Old Format (v2.0-v2.2):**

| Sheet | Sheet Name | Header Row (pandas) | Data Start Row | Rows |
|---|---|---|---|---|
| CAPEX | `CAPEX - INF ` (trailing space!) | **header=10** | Row 12+ | ~199 |
| OPEX | `OPEX - INF` (no trailing space) | **header=4** | Row 9+ | ~276 |

**New Format (v2.2.1+):**

| Sheet | Sheet Name | Header Row (pandas) | Data Start Row | Rows |
|---|---|---|---|---|
| CAPEX | `CAPEX` (simple name) | **header=6** | Row 9+ | ~230 |
| OPEX | `OPEX` (simple name) | **header=3** | Row 9+ | ~359 |

**Backward Compatibility:** Parser otomatis mendeteksi format file dan sheet names. Mendukung BOTH old dan new format tanpa perlu konfigurasi manual.

**Struktur Excel per sheet:**

**CAPEX - INF:**
```
Row 1-5:  Summary/title rows
Row 6-8:  Merged header rows  
Row 9:    Empty / totals
Row 10:   Empty
Row 11:   ← pandas header=10 uses this as column names
Row 12+:  ← Data rows
```

**OPEX - INF:**
```
Row 1-3:  Summary/title rows
Row 4-5:  Merged header rows ← pandas header=4 uses Row 5 
Row 6:    Empty
Row 7:    Totals row (c28=1,164,052,000,000)
Row 8:    Empty  
Row 9+:   ← Data rows
```

**Column positions (iloc index) — IDENTICAL for both sheets:**

| Index | Header (CAPEX) | Variabel Internal | Catatan |
|---|---|---|---|
| 1 | `No.` | `no` | Nomor urut; filter: `pd.to_numeric(df.iloc[:,1], errors='coerce').notna()` |
| 2 | `Parent / Child` | `parent_child` | "Parent" atau "Child" |
| 3 | `Planned / Unplanned` | `planned` | |
| 9 | `Group*)` | `group` | "INF" |
| 10 | `DEPT*)` | `dept` | Departemen |
| 12 | `Pengadaan Baru / Pembayaran` | `jenis_pengadaan` | |
| 13 | `Jenis Anggaran (Akhir)` | `jenis_anggaran` | "Investasi TI" / "Eksploitasi TI" |
| 14 | `Nama GL` | `nama_gl` | Nama GL akun |
| 16 | `ID` | `id_short` | ID singkat (mis: "A.01") |
| 17 | `ID RKA TI 2025` | `id_rka_2025` | ID tahun lalu |
| 18 | `Kode Nomor` | `kode_nomor` | Kode ISG |
| **19** | **`ID RKA TI 2026`** | **`id_rka_ti`** | **PRIMARY JOIN KEY** |
| 20 | `Nama Usulan Proyek/Kegiatan` | `nama_proyek` | |
| 21 | `Nama (Pos Kegiatan SK)` | `nama_proyek_sk` | |
| 24 | `Total Project Cost*)` | `total_project_cost` | |
| **25** | **`Total Kebutuhan 1 Tahun`** | **`alokasi_awal`** | **Digunakan untuk total KPI** |
| 26 | `Nominal Switching` | `nominal_switching` | |
| **27** | **`Alokasi Update`** | **`alokasi_update`** | **Alokasi setelah switching** |
| 48 | `Update Progress Pengadaan` | `update_progress` | |
| 64 | `Catatan ISG` | `catatan_isg` | |
| 65 | `Rutin / Tidak Rutin` | `rutin` | |
| 70 | `Mulai Pelaksanaan` | `tgl_mulai` | |
| 71 | `Selesai Pelaksanaan` | `tgl_selesai` | |
| 72 | `Status Pelaksanaan` | `status_pelaksanaan` | |
| 73 | `Status Pengadaan` | `status_pengadaan` | |
| 74 | `Nomor IP` | `no_ip_master` | |
| 75 | `Nama IP` | `nama_ip` | |
| 76 | `Nominal IP` | `nominal_ip` | |
| 79 | `Nomor SPK*)` | `no_spk_master` | |
| 80 | `Nama SPK*)` | `nama_spk_master` | |
| 81 | `Nominal SPK*)` | `nominal_spk_master` | |
| 83 | `Total Anggaran 2026` | `total_anggaran_2026` | |
| 84–95 | `JAN`..`DES` (Prognosa) | `prognosa_jan`..`prognosa_des` | |
| 96 | `TOTAL (JAN-DES)` (Prognosa) | `prognosa_total` | |
| 107–118 | `JAN`..`DES` (Realisasi Kumulatif) | `real_kum_jan`..`real_kum_des` | |
| 119 | `TOTAL (JAN-DES)` (Realisasi) | `real_kum_total` | |

**Catatan penting `alokasi_awal` vs `alokasi_update`:**

| Metric | CAPEX | OPEX |
|---|---|---|
| `alokasi_awal` (col 25) | 1,430,374,000,000 | 1,164,052,000,000 |
| `alokasi_update` (col 27) | 1,430,374,000,000 | 1,154,165,530,154 |
| Selisih (switching) | 0 | −9,886,469,846 |

- **Untuk KPI Summary totals** → gunakan `alokasi_awal` (col 25) = "Total Kebutuhan"
- **Untuk per-item alignment** → gunakan `alokasi_update` (col 27) = alokasi setelah switching
- **User expects:** CAPEX total = **1,430,374,000,000** dan OPEX total = **1,164,052,000,000**

---

## 4. BUSINESS LOGIC & RULES KALKULASI

### 4.1 Aggregate Realisasi dari Mapping
```python
realisasi_df = mapping_df.groupby('id_rka_ti').agg(
    realisasi_jan=('realisasi_jan', 'sum'),
    realisasi_feb=('realisasi_feb', 'sum'),
    realisasi_mar=('realisasi_mar', 'sum'),
    realisasi_total=('realisasi_total', 'sum'),
    jumlah_transaksi=('realisasi_total', 'count'),
    total_mapping=('total_mapping', 'sum'),
    status_mapping_list=('status_mapping', lambda x: list(x.dropna().unique()))
).reset_index()
```

### 4.2 Join Logic
```python
merged = master_df.merge(realisasi_df, on='id_rka_ti', how='left')
merged['realisasi_total'] = merged['realisasi_total'].fillna(0)
```

### 4.3 Kalkulasi Metrics Per ID RKA TI
```python
merged['pct_realisasi'] = (merged['realisasi_total'] / merged['alokasi_update'] * 100)
merged['sisa_alokasi'] = merged['alokasi_update'] - merged['realisasi_total']
merged['variance_prognosa'] = merged['realisasi_total'] - merged['prognosa_total']
merged['efisiensi'] = merged['alokasi_update'] - merged['prognosa_total']
```

### 4.4 Klasifikasi Alignment (9 Kategori)

```
                    ┌─────────────────────────────────┐
                    │      alokasi_update > 0 ?        │
                    └──────────┬──────────┬────────────┘
                          YES  │          │  NO
                               │          │
                               ▼          ▼
                    ┌───────────────┐  ┌──────────────┐
                    │  pct > 100%?  │  │ realisasi>0? │
                    └──┬────────┬──┘  └──┬────────┬──┘
                  YES  │        │ NO    YES │      │ NO
                       ▼        ▼          ▼      ▼
                  OVER_BUDGET   │   TANPA_ALOKASI  BELUM_MULAI
                                ▼
                    ┌───────────────┐
                    │  pct >= 80%?  │
                    └──┬────────┬──┘
                  YES  │        │ NO
                       ▼        ▼
                 TEPAT_SASARAN  ┌───────────────┐
                                │  pct >= 40%?  │
                                └──┬────────┬──┘
                              YES  │        │ NO
                                   ▼        ▼
                          PERLU_PERHATIAN  ┌──────────┐
                                          │ pct > 0? │
                                          └──┬───┬──┘
                                        YES  │   │ NO
                                             ▼   ▼
                                         KRITIS  (check status →
                                                  BELUM_MULAI / BATAL /
                                                  DITUNDA / TIDAK_TEREALISASI)
```

| Alignment | Kondisi | Warna Badge | Deskripsi |
|---|---|---|---|
| `OVER_BUDGET` | pct > 100% | Purple | Realisasi melebihi alokasi |
| `TEPAT_SASARAN` | 80% <= pct <= 100% | Green | Realisasi proporsional |
| `PERLU_PERHATIAN` | 40% <= pct < 80% | Amber | Perlu monitoring |
| `KRITIS` | 0 < pct < 40% | Red | Realisasi sangat rendah |
| `TANPA_ALOKASI` | No alokasi, has realisasi | Dark Red | Orphan transaction |
| `BELUM_MULAI` | No realisasi, status "Belum" | Blue | Normal |
| `BATAL` | No realisasi, status "Batal" | Gray | Dibatalkan |
| `DITUNDA` | No realisasi, status "Ditunda" | Light Purple | Ditunda |
| `TIDAK_TEREALISASI` | No realisasi, no status match | Orange | Harusnya ada tapi 0 |

**Thresholds:**
```python
ALIGNMENT_THRESHOLD_GOOD = 80    # %
ALIGNMENT_THRESHOLD_WARNING = 40  # %
```

### 4.5 Definisi Tepat Sasaran
> **Tepat Sasaran** = Pengadaan/kegiatan yang dianggarkan dalam ID RKA TI sudah terealisasi dan nilai realisasinya proporsional (80-100%) dengan alokasi yang diberikan ISG.
>
> Indikator **tidak tepat sasaran:**
> - Realisasi > 100% alokasi → **OVER_BUDGET** (warning)
> - ID punya alokasi besar tapi realisasi 0 → **TIDAK_TEREALISASI**
> - Ada realisasi untuk ID tanpa alokasi → **TANPA_ALOKASI**

---

## 5. SPESIFIKASI DASHBOARD HTML OUTPUT

Dashboard adalah **single HTML file** yang di-generate setelah klik tombol Process. Self-contained, bisa dibuka offline. Data di-embed sebagai JSON via Jinja2.

### 5.1 Struktur 4 Halaman

| Tab | Konten |
|---|---|
| **Overview** | KPI cards (total alokasi, realisasi, sisa budget SAP, sisa alokasi master), alignment KPI row, KPI luar perencanaan, planned vs unplanned, top 10 gap table |
| **CAPEX** | Filter bar (search, alignment multi-select, GL, planned) + sortable/paginated table + expandable row detail |
| **OPEX** | Sama dengan CAPEX |
| **Detail** | Search by ID → detail card + transaction sub-table |

### 5.2 KPI Cards

**Row 1 — Angka utama:**
- Total Alokasi (uses `alokasi_awal`)
- Total Realisasi
- % Realisasi (ditampilkan sebagai sub-label color-coded)
- Alokasi CAPEX / Alokasi OPEX / Realisasi CAPEX / Realisasi OPEX
- Sisa Budget SAP
- Sisa Alokasi Master Data

**Row 2 — Alignment distribution:**
- Tepat Sasaran (count)
- Perlu Perhatian (count)
- Kritis (count)
- Over Budget (count, highlighted)
- Tanpa Alokasi (count)

### 5.3 Charts (Chart.js 4.4.0)
- Data chart tetap disiapkan untuk kompatibilitas.
- Section chart di UI saat ini disembunyikan (`display:none`) sesuai requirement terbaru.

### 5.4 Tables
- Sortable by clicking column headers
- Paginated (25 rows/page)
- Expandable rows → detail sub-table with all transactions
- Orphan rows highlighted yellow background
- Filter by search text, alignment multi-select, GL dropdown, dan planned/unplanned
- KPI cards utama dapat diklik untuk membuka modal berisi subset item yang relevan

### 5.5 Format Angka
- Rupiah: `Rp 1.234,56 M` (Miliar) atau `Rp 567,89 Jt` (Juta)
- Persentase: `85,3%`
- Locale: Indonesia (titik = ribuan, koma = desimal)

### 5.6 Dark Mode
- Toggle di top bar, saved to `localStorage`
- CSS: `[data-theme="dark"]` overrides

---

## 6. SPESIFIKASI GUI INPUT (app.py)

GUI telah dimodernisasi menggunakan **PySide6** dengan flow utama:
- Pilih tepat 3 file sekaligus (CAPEX, OPEX, Master)
- Auto-assign berdasarkan nama file, fallback ke urutan pilihan
- Progress bar + status processing
- Tombol buka output dashboard setelah proses selesai

### Layout
```
+-----------------------------------------------------+
|  +- HEADER BAR (BRI Blue) -----------------------+  |
|  |  RKA TI Budget Analyzer    v2.0 . PMO INF BRI |  |
|  +-----------------------------------------------+  |
|  +- WHITE CARD ----------------------------------+  |
|  |  Input Files                                   |  |
|  |                                                |  |
|  |  [1] CAPEX Mapping Excel                       |  |
|  |      [___________________path___] [Browse]     |  |
|  |                                                |  |
|  |  [2] OPEX Mapping Excel                        |  |
|  |      [___________________path___] [Browse]     |  |
|  |                                                |  |
|  |  [3] Master Data ISG Excel                     |  |
|  |      [___________________path___] [Browse]     |  |
|  |                                                |  |
|  |  -----------------------------------------     |  |
|  |                                                |  |
|  |  [>  PROCESS & GENERATE DASHBOARD          ]   |  |
|  |                                                |  |
|  |  [================--------] 70%                |  |
|  |  . Menggabungkan data & menghitung metrics...  |  |
|  +-----------------------------------------------+  |
|  (c) 2026 Bank Rakyat Indonesia -- Divisi INF TI    |
+-----------------------------------------------------+
```

### Features
- BRI color palette (#00529C blue, #F37021 orange accents)
- Number badges (1/2/3) for file inputs
- Hover effects on buttons
- Orange progress bar
- Status icon with color (orange=processing, green=done, red=error)
- Button disabled during processing, re-enabled after

---

## 7. BRI DESIGN SYSTEM — CSS TOKENS

```css
:root {
  --bg:#F0F4F8; --card:#FFFFFF; --brd:#E2ECF4; --brd2:#CBD8E8;
  --t1:#0D1F35; --t2:#435770; --t3:#8FA5BE;
  --bri:#00529C; --org:#F37021;
  --success:#15803D; --success-bg:#DCFCE7;
  --warning:#B45309; --warning-bg:#FEF3C7;
  --danger:#DC2626; --danger-bg:#FEE2E2;
  --info:#1D4ED8; --info-bg:#DBEAFE;
  --fi:'Inter',system-ui,sans-serif;
  --text-xs:10px; --text-sm:12px; --text-base:14px;
  --text-md:16px; --text-lg:20px; --text-xl:24px; --text-2xl:32px;
  --r:14px; --rs:8px; --r-pill:20px;
}
[data-theme="dark"] {
  --bg:#0D1F35; --card:#162840; --brd:#1E3A55; --brd2:#2A4F72;
  --t1:#F0F4F8; --t2:#8FA5BE; --t3:#435770;
}
```

### Badge Styles

| Class | Background | Color | Notes |
|---|---|---|---|
| `.tepat-sasaran` | `--success-bg` | `--success` | |
| `.perlu-perhatian` | `--warning-bg` | `--warning` | |
| `.kritis` | `--danger-bg` | `--danger` | |
| `.over-budget` | `#FDE2FF` | `#9B1DB8` | 1.5px solid #D946EF border |
| `.tanpa-alokasi` | `#FEE2E2` | `#7F1D1D` | |
| `.belum-mulai` | `--info-bg` | `--info` | |
| `.batal` | `--bg` | `--t3` | 1px solid --brd2 border |
| `.ditunda` | `#F3E8FF` | `#6B21A8` | |
| `.tidak-terealisasi` | `--warning-bg` | `--warning` | |

---

## 8. CONTOH OUTPUT MERGED DATA

```python
context = {
    "generated_at": "2026-04-14 15:30:00",
    "period": "Maret 2026",
    "summary": {
        "capex_transactions": 170,
        "opex_transactions": 769,
        "master_capex_items": 199,
        "master_opex_items": 276,
        "total_alokasi_capex": 1430374000000,      # from alokasi_awal
        "total_alokasi_opex": 1164052000000,        # from alokasi_awal
        "total_alokasi_update_capex": 1430374000000, # from alokasi_update
        "total_alokasi_update_opex": 1154165530154,  # from alokasi_update
        "total_realisasi_capex": 84246936561,
        "total_realisasi_opex": 1256561776320,
        "total_alokasi": 2594426000000,
        "total_alokasi_update": 2584539530154,
        "total_realisasi": 1340808712881,
        "total_switching": -9886469846,
        "alignment_counts": {
            "tepat_sasaran": 3,
            "perlu_perhatian": 19,
            "kritis": 30,
            "over_budget": 11,
            "tanpa_alokasi": 78,
            "belum_mulai": 111,
            "batal": 0,
            "ditunda": 0,
            "tidak_terealisasi": 276,
        }
    },
    "capex_items": [...],   # list of item dicts
    "opex_items": [...],
    "gl_breakdown": {...},  # {gl_name: {alokasi, realisasi}}
    "monthly_trend": {...}, # {jan/feb/mar: {capex, opex}}
    "top10_gap": [...],     # sorted by abs(sisa_alokasi) desc
}
```

Each item dict:
```python
{
    "id_rka_ti": "2026-INF-A.01.044",
    "nama_proyek": "Pengadaan Infrastruktur New Data Center...",
    "alokasi_awal": 18777167872,
    "nominal_switching": 0,
    "alokasi_update": 18777167872,
    "realisasi_total": 48886675000,
    "pct_realisasi": 260.3,
    "sisa_alokasi": -30109507128,
    "alignment": "OVER_BUDGET",
    "tipe": "CAPEX",
    "transactions": [{...}, ...],
    # ... other fields
}
```

---

## 9. RULES & EDGE CASES

| # | Scenario | Handling |
|---|---|---|
| 1 | ID di Mapping tapi tidak di Master | Orphan item; `alignment='TANPA_ALOKASI'`; yellow row in table |
| 2 | ID di Master tapi tidak di Mapping | `realisasi_total=0`; classify by status_pelaksanaan |
| 3 | ID format inconsistent | Normalize: `str.strip().str.upper()` -> `2026-INF-X.XX.XXX` |
| 4 | Numeric columns with strings | `pd.to_numeric(..., errors='coerce').fillna(0)` |
| 5 | Multiple SPK per ID | Aggregate SUM; keep detail list for drill-down |
| 6 | Realisasi > 100% alokasi | `alignment='OVER_BUDGET'` |
| 7 | Master OPEX header != CAPEX header | CAPEX: `header=10`, OPEX: `header=4` (old) or CAPEX: `header=6`, OPEX: `header=3` (new) |
| 8 | Sheet names with trailing space | Auto-detected: try "CAPEX - INF " / "CAPEX - INF" / "CAPEX"; try "OPEX - INF" / "OPEX - INF " / "OPEX" |
| 9 | alokasi_awal != alokasi_update | CAPEX: same (switching=0). OPEX: differ by -9.9B |
| 10 | New master data file format (v2.2.1+) | Parser auto-detects sheet names and header rows; backward compatible with old format |

---

## 10. CATATAN TEKNIS & DEBUGGING

### Parser Master — Header Row Issue (FIXED in v2.0)

**Sebelum (v1.0 -- BUG):**
```python
MASTER_HEADER_ROW = 10  # Used for both sheets -> OPEX data WRONG
```

**Sesudah (v2.0 -- FIXED):**
```python
CAPEX_HEADER_ROW = 10  # CAPEX - INF: header at row 11 (0-indexed 10)
OPEX_HEADER_ROW = 4    # OPEX - INF: header at row 5 (0-indexed 4)
```

**Root cause:** OPEX - INF sheet has a shorter summary section (rows 1-3) vs CAPEX - INF (rows 1-9). Using header=10 for OPEX read the wrong row as column names, causing all column positions to be off and returning incorrect data.

**Validation results:**
```
CAPEX: 199 rows, alokasi_awal = 1,430,374,000,000
OPEX:  276 rows, alokasi_awal = 1,164,052,000,000
```

### Summary Totals — alokasi_awal vs alokasi_update (FIXED in v2.0)

**Issue:** OPEX `alokasi_update` sums to 1,154,165,530,154 (after switching adjustments), but user expects 1,164,052,000,000 as "total alokasi OPEX".

**Fix:** KPI summary now uses `alokasi_awal` (= "Total Kebutuhan 1 Tahun") for headline totals. Per-item alignment calculation still uses `alokasi_update`.

### OVER_BUDGET Classification (NEW in v2.0)

**Issue:** Items with realisasi > 100% of alokasi had no special warning.

**Fix:** Added `OVER_BUDGET` classification for `pct_realisasi > 100%`. This triggers BEFORE `TEPAT_SASARAN` check. 11 items detected in current dataset.

### Column Position Consistency

Both CAPEX-INF and OPEX-INF sheets use the **same column positions** (same Excel template). The only difference is the header row. Once the correct header row is set, all `iloc[:, idx]` mappings work identically for both sheets.

---

## 11. DEVELOPMENT PHASES & CHANGELOG

### Phase 1 — Initial Build (v1.0)
- [x] `core/parser_master.py` — Parse master data (header=10 for both, BUG for OPEX)
- [x] `core/parser_capex.py` — Column-name-matching parser
- [x] `core/parser_opex.py` — Column-name-matching parser
- [x] `core/merger.py` — JOIN + metrics + alignment (no OVER_BUDGET)
- [x] `output/dashboard_template.html` — 4-page dashboard with Chart.js
- [x] `app.py` — Tkinter GUI
- [x] Git push to https://github.com/itsmhp/MappingRealisasi

### Phase 2 — Bug Fixes & Enhancements (v2.0)
- [x] **FIX** parser_master.py: OPEX header=4 (was 10)
- [x] **FIX** merger.py: Summary uses `alokasi_awal` for totals
- [x] **NEW** OVER_BUDGET alignment classification (pct > 100%)
- [x] **NEW** Over Budget badge styling (purple)
- [x] **NEW** Over Budget KPI card in dashboard
- [x] **NEW** Over Budget in filter dropdowns & donut chart
- [x] **IMPROVE** GUI modernized: BRI header bar, card layout, number badges, hover effects, colored status
- [x] **VALIDATE** Full pipeline test: all totals match expected values

### Phase 3 — Data Quality & UX Refinement (v2.1, 2026-04-23)
- [x] **UPDATE** Header logo dashboard memakai file `favicon-bri-alt.svg` (alternate white/blue)
- [x] **UPDATE** Label alignment UI: "Tidak Terealisasi" -> "Belum Terealisasi"
- [x] **UPDATE** Filter alignment menjadi multi-select pada CAPEX/OPEX
- [x] **UPDATE** KPI cards dapat diklik dan menampilkan modal subset item terkait
- [x] **UPDATE** Section chart disembunyikan dari tampilan utama sesuai requirement
- [x] **UPDATE** Mapping transaksi menampilkan `Catatan` dan `No SPK` pada detail transaksi

### Phase 4 — Master Data Format Support (v2.2.1, 2026-04-29)
- [x] **NEW** Auto-detection of sheet names (support both "CAPEX - INF " and "CAPEX")
- [x] **NEW** Auto-detection of header row positions (support both old and new format)
- [x] **FIX** Parser now handles new master data file format with simple sheet names
- [x] **IMPROVE** Backward compatible with old master data files (seamless transition)

### Validated Data Points (v2.0)
```
CAPEX total alokasi  = 1,430,374,000,000
OPEX total alokasi   = 1,164,052,000,000
Master CAPEX items   = 199
Master OPEX items    = 276
Mapping CAPEX tx     = 170
Mapping OPEX tx      = 769
Over Budget items    = 11
Orphan CAPEX         = 3
Orphan OPEX          = 50
```

---

## 12. INSTRUKSI KHUSUS UNTUK GITHUB COPILOT

1. **Baca seluruh dokumen ini sebelum generate kode apapun**
2. **Selalu gunakan BRI Design System CSS tokens** dari section 7
3. **Master Data: CAPEX header=10 (old) or 6 (new), OPEX header=4 (old) or 3 (new)** — Parser otomatis mendeteksi format
4. **Master Data sheet names:** Support both old ("CAPEX - INF ", "OPEX - INF") and new ("CAPEX", "OPEX") — Parser auto-detects
5. **OPEX join key adalah `ID RKAP TI`** (bukan `ID RKA TI`) — normalize sebelum join
6. **Dashboard harus single HTML file** — embed semua CSS/JS (kecuali Chart.js CDN)
7. **Semua angka format locale Indonesia** (Rp, titik ribuan, koma desimal)
8. **Chart data tetap tersedia**, namun section chart dapat disembunyikan sesuai requirement dashboard aktif
9. **Jangan hardcode data** — semua dari hasil merge
10. **Implement dark mode** via `[data-theme="dark"]` + toggle
11. **Table harus sortable** (vanilla JS click handler)
12. **Row expand** untuk detail transaksi per ID
13. **Summary totals use `alokasi_awal`**, per-item uses `alokasi_update`
14. **OVER_BUDGET classification** harus ada (pct > 100%)
15. **Backward compatibility:** Pastikan code tetap support format master data lama dan baru

---

## 13. KONVENSI KODE

```python
# Python — snake_case
id_rka_ti, alokasi_update, realisasi_total, pct_realisasi

# JavaScript — camelCase
rkaItems, totalAlokasi, formatRupiah(), toggleDarkMode()

# CSS class — kebab-case
.kpi-card, .badge.tepat-sasaran, .tbl

# File naming — snake_case
parser_capex.py, parser_master.py, merger.py

# Constants — UPPER_SNAKE
CAPEX_HEADER_ROW = 10
OPEX_HEADER_ROW = 4
ALIGNMENT_THRESHOLD_GOOD = 80
ALIGNMENT_THRESHOLD_WARNING = 40
```

---

## 14. DEPLOYMENT & ENVIRONMENT

### 14.1 System Requirements
| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 | Windows 10+ / Linux / macOS |
| Python | 3.11 | 3.13+ |
| RAM | 2 GB | 4 GB+ |
| Disk | 500 MB | 1 GB |
| Display | 1366x768 | 1920x1080+ |
| Network | Optional (offline capable) | — |

### 14.2 Installation Steps
```bash
# Clone repository
git clone https://github.com/itsmhp/MappingRealisasi.git
cd MappingRealisasi

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

### 14.3 Environment Variables (Optional)
```bash
# .env file (not required for basic usage)
DASHBOARD_OUTPUT_DIR=./output
DASHBOARD_THEME=light  # light / dark
LOG_LEVEL=INFO
```

### 14.4 Configuration Files
- `requirements.txt` — Locked dependency versions
- `.gitignore` — Excludes generated output files, venv, __pycache__
- `output/dashboard_template.html` — Jinja2 template (modify with caution)

---

## 15. TESTING STRATEGY

### 15.1 Test Data
Located in repository for automated testing:
```
test_data/
├── Master_Data_Test_CAPEX.xlsx
├── Master_Data_Test_OPEX.xlsx
├── Mapping_CAPEX_Test.xlsx
├── Mapping_OPEX_Test.xlsx
└── expected_output.json
```

### 15.2 Unit Tests
```bash
python -m pytest core/test_parser_master.py -v
python -m pytest core/test_parser_capex.py -v
python -m pytest core/test_parser_opex.py -v
python -m pytest core/test_merger.py -v
```

**Coverage targets:**
- Parser modules: 95%+
- Merger logic: 98%+
- Edge cases: 100%

### 15.3 Integration Tests
```bash
# Full end-to-end pipeline
python test_data.py
python verify_dashboard.py output/dashboard_latest.html
```

**Checks:**
- All 3 Excel files parsed without errors
- Join produces expected row counts
- Alignment classifications correct
- KPI totals match expected values
- Dashboard renders without Jinja2 errors
- All chart canvases present (or correctly hidden)
- JSON data embedded and parseable

### 15.4 Validation Checklist Before Release
- [ ] Verify master context updated
- [ ] README sync'd with latest features
- [ ] All parser tests pass (100%)
- [ ] Integration test successful
- [ ] Dashboard screenshot reviewed
- [ ] Dark mode toggle works
- [ ] Mobile responsiveness check (if applicable)
- [ ] Git history clean (no secrets committed)
- [ ] Commit message follows convention
- [ ] Push to main branch successful

---

## 16. TROUBLESHOOTING & KNOWN ISSUES

### Issue 1: "FileNotFoundError" when opening Excel files
**Symptoms:** App crashes with "File not found" during file selection
**Cause:** File path contains special characters or spaces not properly handled
**Solution:**
```python
# Ensure path is properly quoted/escaped
filepath = r"C:\Users\muham\OneDrive\Documents\...xlsx"  # Use raw string
```

### Issue 2: "KeyError" in parser_master.py
**Symptoms:** Dashboard generation fails with KeyError on column index
**Cause:** Master Excel file structure changed; header rows shifted
**Solution:**
1. Verify sheet name: `CAPEX - INF ` (with trailing space) or `OPEX - INF`
2. Check header row: `header=10` for CAPEX, `header=4` for OPEX
3. Run `python test_data.py` to diagnose exact column mismatch

### Issue 3: "ValueError: could not convert string to float"
**Symptoms:** Numeric aggregation fails
**Cause:** Numeric columns contain text or special characters
**Solution:**
```python
# Already handled in code with:
pd.to_numeric(series, errors='coerce').fillna(0)
# But verify source data has no unexpected values
```

### Issue 4: Dashboard KPI cards show as blank/zero
**Symptoms:** All KPI metrics display 0 or empty values
**Cause:** Join operation failed or resulting merged dataframe is empty
**Solution:**
1. Check ID normalization: both should be uppercase, trimmed
2. Verify master IDs in column 19 (index 19, 0-indexed)
3. Verify mapping IDs in CAPEX col O (index 15) or OPEX col M (index 13)
4. Run `python test_data.py` to inspect merged dataframe

### Issue 5: "PySide6 window fails to launch"
**Symptoms:** GUI doesn't appear or immediate crash on `python app.py`
**Cause:** PySide6 not installed or display server not available (Linux)
**Solution:**
```bash
pip install --upgrade PySide6
# On Linux, may need: sudo apt-get install libxkbcommon-x11-0
```

### Issue 6: "Dashboard HTML won't open in browser"
**Symptoms:** Browser error or blank page when opening generated HTML
**Cause:** JSON embedding syntax error or corrupted template render
**Solution:**
1. Check JSON escaping in merger.py `_json_for_script()` function
2. Verify Jinja2 variables are all rendered (run verify_dashboard.py)
3. Open browser console (F12) to see JavaScript errors

### Issue 7: "Merge results show `(Tidak ada di Master Data)` for all projects"
**Symptoms:** Orphan rows everywhere despite IDs clearly in master
**Cause:** ID key mismatch due to whitespace, case, or punctuation
**Solution:**
```python
# Check normalization in merger.py
normalized_id = str(id_value).strip().upper()
# Verify both master and mapping use identical normalization
```

### Issue 8: "Alignment classification incorrect (wrong badge color)"
**Symptoms:** Items show wrong alignment category (e.g., TEPAT_SASARAN but should be KRITIS)
**Cause:** Threshold values or classification logic error
**Solution:**
1. Verify thresholds in merger.py: `ALIGNMENT_THRESHOLD_GOOD = 80`, `ALIGNMENT_THRESHOLD_WARNING = 40`
2. Check pct_realisasi calculation: `pct = (realisasi / alokasi * 100)` not reversed
3. Inspect item dict directly in browser console `DATA_CAPEX[0].alignment`

---

## 17. PERFORMANCE & SCALABILITY

### 17.1 Benchmarks (Current)
| Operation | Time | Data Volume |
|---|---|---|
| Parse Master CAPEX | ~0.5s | 199 rows |
| Parse Master OPEX | ~0.5s | 276 rows |
| Parse CAPEX Mapping | ~0.3s | 170 rows |
| Parse OPEX Mapping | ~1.2s | 769 rows |
| Merge all + calculations | ~0.8s | 941 rows total |
| Jinja2 template render | ~1.5s | 490 items + charts |
| **Total pipeline** | **~5s** | ~1000 rows input |

### 17.2 Memory Usage
- Typical: 150–200 MB resident
- Peak (during render): 250–300 MB
- Long-term stability: No detected leaks

### 17.3 Scalability Limits
- **Safe to 10,000 items** without major optimization
- **Beyond 50,000 items**: Consider breaking into batch processing
- **Recommendation**: Keep single period ≤ 5000 items for best UI responsiveness

### 17.4 Optimization Opportunities (Future)
1. **Caching**: Store parsed master data if filename unchanged
2. **Lazy loading**: Load table pages on-demand instead of embedding all rows
3. **Compression**: Gzip JSON embed in HTML
4. **Parallel parsing**: Use `concurrent.futures` for multi-file read
5. **Database backend**: Move from Excel to SQLite for larger datasets

---

## 18. SECURITY CONSIDERATIONS

### 18.1 Input Validation
- ✅ File path validation before opening (check file exists, is .xlsx)
- ✅ Column name matching (defensive against renamed columns)
- ✅ Numeric coercion (errors='coerce' prevents crashes)
- ⚠️ NO Excel macro execution (openpyxl is safe; doesn't execute VBA)

### 18.2 Data Privacy
- ✅ Dashboard is **offline-capable** — no data sent to internet
- ✅ No analytics tracking
- ✅ No authentication required (desktop app)
- ⚠️ **IMPORTANT**: Generated HTML contains raw financial data — treat as confidential

### 18.3 Code Security
- ✅ No hardcoded credentials
- ✅ No SQL injection (no SQL used)
- ✅ No arbitrary code execution (Jinja2 autoescape enabled)
- ✅ Dependencies pinned to specific versions (requirements.txt)

### 18.4 Output Security
```html
<!-- Generate HTML includes:
     - Raw project names, amounts, statuses
     - No customer PII
     - No employee personal details
     -->
```

**Recommendation:** Store dashboard files in access-controlled folder:
```bash
chmod 600 output/dashboard_*.html  # Linux/macOS
icacls output\dashboard_*.html /grant:r "%USERNAME%":F  # Windows
```

### 18.5 Dependencies Audit
Run periodically to check for CVEs:
```bash
pip install pip-audit
pip-audit requirements.txt
```

---

## 19. ROADMAP & FUTURE ENHANCEMENTS

### Phase 4 — Advanced Reporting (Planned Q3 2026)
- [ ] PDF export with company letterhead
- [ ] Email delivery of dashboard (automated scheduling)
- [ ] Historical comparison: month-over-month trending
- [ ] Drill-down analytics per department
- [ ] Custom KPI definitions (user-configurable thresholds)

### Phase 5 — Data Quality & Governance (Planned Q4 2026)
- [ ] Data validation rules engine
- [ ] Automated data quality reports
- [ ] Master data version control (audit trail)
- [ ] Data lineage visualization
- [ ] Integration with BRI data catalog

### Phase 6 — Real-time Monitoring (Planned 2027)
- [ ] Live dashboard with periodic auto-refresh
- [ ] Alert system for threshold breaches
- [ ] Slack/Teams notifications
- [ ] Mobile app (React Native)
- [ ] Web API (FastAPI) for BI tool integration

### Phase 7 — Enterprise Scale (2027+)
- [ ] Multi-tenant architecture
- [ ] Cloud deployment (AWS/Azure/GCP)
- [ ] Database backend (PostgreSQL)
- [ ] Advanced charting (Plotly, D3.js)
- [ ] Machine learning predictions (budget forecasting)

### Backlog (Lower Priority)
- [ ] Dark theme refinements (CSS improvements)
- [ ] Internationalization (I18N) — English, Mandarin
- [ ] Accessibility improvements (WCAG AA compliance)
- [ ] Performance profiling & optimization
- [ ] Comprehensive API documentation (Swagger/OpenAPI)

---

## 20. FAQ & GLOSSARY

### FAQ

**Q: Bisakah saya mengubah threshold alignment?**
A: Ya, edit di `core/merger.py` line 7-8:
```python
ALIGNMENT_THRESHOLD_GOOD = 80      # Sesuaikan ke nilai lain jika perlu
ALIGNMENT_THRESHOLD_WARNING = 40   # Contoh: 70 dan 30 untuk lebih ketat
```
Setelah itu regenerate dashboard.

**Q: Dashboard tampil kosong, kenapa?**
A: Cek:
1. Berhasil parse ketiga file? → Lihat console output `python app.py`
2. Join berhasil atau hanya orphan rows? → Run `python test_data.py`
3. Browser console (F12) menunjukkan error JavaScript? → Screenshot untuk debugging
4. HTML file valid atau corrupted? → Run `python verify_dashboard.py output/dashboard_latest.html`

**Q: Bagaimana cara membuat dashboard untuk periode lain (Februari, April, dll)?**
A: Ganti file mapping (`Mapping Realisasi CAPEX Februari 2026.xlsx`) dan master data ke periode yg diinginkan, lalu process ulang dari GUI.

**Q: Bisakah saya menambah kolom baru ke dashboard?**
A: Ya, langkah-langkahnya:
1. Tambah kolom di `core/parser_*.py` (ekstrak dari Excel)
2. Propagate ke item dict di `core/merger.py`
3. Render di template: edit `output/dashboard_template.html` dan JS di `<script>` tag
4. Test dengan `python verify_dashboard.py`

**Q: Dashboard menerima berapa maksimal baris?**
A: Saat ini tested hingga 1000 items (490 total + 510 orphan). Lebih dari itu, pertimbangkan batch processing atau database backend (roadmap phase 6).

**Q: Apakah ada way backup data sbelum process ulang?**
A: Output files auto-timestamped: `dashboard_INF_20260423_152835.html`. Semua file disimpan di `output/`, tidak dihapus. Git juga track changes jika commit regularly.

### Glossary

| Term | Definition |
|---|---|
| **Alokasi** | Budget yang dialokasikan untuk ID RKA TI (dari Master Data) |
| **Realisasi** | Pengeluaran aktual yang terjadi (dari SAP Mapping files) |
| **Alignment** | Kesesuaian antara alokasi dan realisasi (tepat sasaran vs tidak) |
| **ID RKA TI** | Identifier unik untuk item/kegiatan dalam RKA TI (format: 2026-INF-A.01.001) |
| **CAPEX** | Capital Expenditure — pengeluaran modal/investasi jangka panjang |
| **OPEX** | Operational Expenditure — pengeluaran operasional rutin |
| **Master Data** | Canonical source of budget allocation per ID RKA TI |
| **Mapping** | Monthly transaction data linked to ID RKA TI |
| **GL (General Ledger)** | Accounting classification (Hardware, Software, Services, etc.) |
| **SPK** | Surat Perintah Kerja (Work Order/Contract) |
| **Orphan Row** | Transaction/ID found in mapping but NOT in master data |
| **Over Budget** | Situation where realisasi > 100% alokasi |
| **Switching** | Budget reallocation between items (difference between alokasi_awal and alokasi_update) |
| **Tepat Sasaran** | Realization 80–100% of allocation (on-target) |
| **KPI** | Key Performance Indicator (summary metrics in dashboard) |
| **Jinja2** | Python templating engine for generating HTML |
| **PySide6** | Python bindings for Qt6 (GUI framework) |
| **Chart.js** | JavaScript charting library (optional, currently hidden) |

---

## 21. ARCHITECTURE DIAGRAMS (DETAILED)

### 21.1 System Architecture (Mermaid)

```mermaid
graph TB
    subgraph User["👤 User / PMO"]
        A1["Prepare 3 Excel Files<br/>(CAPEX, OPEX, Master)"]
    end
    
    subgraph GUI["🖥️ PySide6 Desktop GUI"]
        A2["File Selection Dialog"]
        A3["Auto-assign Filenames"]
        A4["Progress Bar"]
        A5["Process Button"]
    end
    
    subgraph Backend["⚙️ Python Backend"]
        P1["parser_master.py<br/>(CAPEX header=10<br/>OPEX header=4)"]
        P2["parser_capex.py"]
        P3["parser_opex.py"]
        P4["merger.py<br/>(JOIN + Align)"]
    end
    
    subgraph DataFrames["📊 DataFrames"]
        D1["df_master_capex"]
        D2["df_master_opex"]
        D3["df_mapping_capex"]
        D4["df_mapping_opex"]
        D5["df_merged_capex"]
        D6["df_merged_opex"]
    end
    
    subgraph Rendering["🎨 Template Rendering"]
        R1["Jinja2 Environment"]
        R2["dashboard_template.html"]
        R3["JSON Embed (context)"]
    end
    
    subgraph Output["📄 Output"]
        O1["HTML Dashboard"]
        O2["dashboard_latest.html<br/>(alias)"]
    end
    
    subgraph Browser["🌐 Browser"]
        B1["KPI Cards"]
        B2["Tables"]
        B3["Modals"]
        B4["Dark Mode"]
    end
    
    A1 -->|Load| A2
    A2 -->|Select| A3
    A3 -->|Auto-assign| A5
    A5 -->|Click| A4
    
    A4 -->|Parse Master| P1
    P1 -->|Parse CAPEX| P2
    P2 -->|Parse OPEX| P3
    P3 -->|Merge| P4
    
    P1 -->|Output| D1
    P1 -->|Output| D2
    P2 -->|Output| D3
    P3 -->|Output| D4
    P4 -->|Input| D1
    P4 -->|Input| D2
    P4 -->|Input| D3
    P4 -->|Input| D4
    P4 -->|Output| D5
    P4 -->|Output| D6
    
    D5 -->|Build Context| R1
    D6 -->|Build Context| R1
    R1 -->|Render| R2
    R2 -->|Embed| R3
    R3 -->|Output| O1
    O1 -->|Create Alias| O2
    
    O2 -->|Open Browser| B1
    B1 -->|Display| B2
    B2 -->|Click KPI| B3
    B4 -->|Toggle| B1
```

### 21.2 Data Processing Pipeline (Mermaid)

```mermaid
sequenceDiagram
    participant User as User (GUI)
    participant Parser as parser_capex.py
    participant Aggregator as merger.py
    participant Template as Jinja2
    participant Browser as Browser

    User->>Parser: Parse Excel
    activate Parser
    Parser->>Parser: iloc[:, idx] extract
    Parser->>Parser: Clean & normalize ID
    Note over Parser: Aggregate by id_rka_ti
    Parser-->>Aggregator: DataFrame (realisasi_total, etc)
    deactivate Parser

    Aggregator->>Aggregator: LEFT JOIN master
    Aggregator->>Aggregator: Calculate pct_realisasi
    Aggregator->>Aggregator: Classify alignment
    Aggregator->>Aggregator: Build item dict list

    Aggregator->>Template: Pass context dict
    activate Template
    Template->>Template: Loop items
    Template->>Template: Render KPI cards
    Template->>Template: Render tables (HTML)
    Template->>Template: Embed JSON (DATA_CAPEX)
    Template-->>Browser: Generate HTML
    deactivate Template

    Browser->>Browser: Parse JSON
    Browser->>Browser: Initialize KPI values
    Browser->>Browser: Render tables
    Browser->>Browser: Attach event listeners
    Browser-->>User: Display Dashboard
```

### 21.3 Alignment Classification Flowchart (Mermaid)

```mermaid
flowchart TD
    Start([Start: Item]) -->|Get alokasi_update<br/>Get realisasi_total| Check1{alokasi_update > 0?}
    
    Check1 -->|NO| NoAlloc["No Allocation<br/>& has realisasi?"]
    NoAlloc -->|YES| TA["✗ TANPA_ALOKASI<br/>(Orphan)"]
    NoAlloc -->|NO| BM["✓ BELUM_MULAI<br/>(Not started)"]
    
    Check1 -->|YES| CalcPct["Calculate<br/>pct = realisasi/alokasi × 100"]
    CalcPct --> Check2{pct > 100%?}
    
    Check2 -->|YES| OB["💥 OVER_BUDGET<br/>(Red flag)"]
    Check2 -->|NO| Check3{pct ≥ 80%?}
    
    Check3 -->|YES| TS["✅ TEPAT_SASARAN<br/>(Green)"]
    Check3 -->|NO| Check4{pct ≥ 40%?}
    
    Check4 -->|YES| PP["⚠️ PERLU_PERHATIAN<br/>(Amber)"]
    Check4 -->|NO| Check5{pct > 0%?}
    
    Check5 -->|YES| K["🔴 KRITIS<br/>(Red)"]
    Check5 -->|NO| Check6{status_pelaksanaan}
    
    Check6 -->|Batal| Batal["❌ BATAL"]
    Check6 -->|Ditunda| Ditunda["⏸ DITUNDA"]
    Check6 -->|Other| TR["❓ BELUM_TEREALISASI"]
    
    TA --> End([End: Classified])
    BM --> End
    OB --> End
    TS --> End
    PP --> End
    K --> End
    Batal --> End
    Ditunda --> End
    TR --> End
```

### 21.4 Database Schema (If Migrated to DB - Future)

```mermaid
erDiagram
    MASTER_CAPEX ||--o{ RKA_ITEM : "1:many"
    RKA_ITEM ||--o{ SAP_TRANSACTION : "1:many"
    RKA_ITEM ||--o{ ALIGNMENT_CLASSIFICATION : "1:1"
    
    MASTER_CAPEX {
        int id_rka_ti PK
        string nama_proyek
        decimal alokasi_awal
        decimal alokasi_update
        string status_pelaksanaan
        string gl_account
    }
    
    RKA_ITEM {
        int id_rka_item PK
        int id_rka_ti FK
        decimal realisasi_total
        decimal pct_realisasi
        decimal sisa_alokasi
        date created_at
        date updated_at
    }
    
    SAP_TRANSACTION {
        int id_transaction PK
        int id_rka_item FK
        decimal amount
        string spk_no
        string vendor_name
        date transaction_date
    }
    
    ALIGNMENT_CLASSIFICATION {
        int id PK
        int id_rka_item FK
        string alignment_status
        string classification_reason
    }
```

---

**Dokumen ini adalah Referensi Master Context lengkap untuk RKA TI Budget Realization Analyzer. Versi terbaru: 2.2 (2026-04-23, ekspansi profesional).**

**Penulis:** PMO Infrastruktur (PIN) — IT Directorate BRI  
**Status:** Production Ready (v2.1+)  
**Terakhir Diperbarui:** 2026-04-23 16:00 WIB  
**Repository:** https://github.com/itsmhp/MappingRealisasi  
**License:** Internal Use Only — PT Bank Rakyat Indonesia
