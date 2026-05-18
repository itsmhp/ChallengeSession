# MASTER CONTEXT — Challenge Session Dashboard v2.0

**Proyek:** Challenge Session Dashboard — Analisis Revisi RKA TI 2026  
**Tim:** PMO Infrastruktur (PIN) — IT Directorate, PT Bank Rakyat Indonesia  
**Versi Dokumen:** 2.0 (diperbarui 2026-05-18)  
**Repository:** https://github.com/itsmhp/ChallengeSession  
**Tujuan Dokumen:** Master context untuk AI assistant & developer. Baca seluruh dokumen ini sebelum menulis satu baris kode pun.

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
> "Bagaimana ringkasan hasil Challenge Session? Proyek mana yang bertambah/berkurang alokasi, berapa total switching, dan bagaimana perbandingan antara yang diminta INF vs yang dialokasikan ISG?"

### Tujuan Aplikasi
1. Membaca file Challenge Session Excel secara **lokal** (DLP-safe)
2. Memproses dan mengekstrak 200+ proyek dari struktur multi-header
3. Menghasilkan **dashboard HTML interaktif** dengan analisis perubahan lengkap
4. Menampilkan delta TPC, delta kebutuhan (INF vs ISG), switching flow, scope changes
5. Mendukung drill-down ke detail per proyek via drawer

---

## 2. ARSITEKTUR APLIKASI

### Stack Teknologi

| Komponen | Teknologi | Versi |
|---|---|---|
| Runtime | Python | 3.11+ |
| GUI | PySide6 | 6.8+ |
| Excel Reader | openpyxl | 3.1+ |
| Charts | ECharts (CDN) | 5.5.0 |
| Output | Single-file HTML | self-contained |

### Struktur Folder
```
Challenge Session/
├── app.py                      # PySide6 desktop GUI launcher
├── generate_dashboard.py       # CLI alternative
├── run.bat                     # Double-click launcher (Windows)
├── core/
│   ├── __init__.py
│   ├── parser_challenge.py     # Parser Excel → ProjectRow records
│   └── builder.py              # Aggregasi + context dict builder
├── output/
│   ├── dashboard_template.html # (placeholder, tidak dipakai aktif)
│   └── dashboard_CS_*.html     # Generated outputs (gitignored)
├── dashboard.html              # Base dashboard template (single-file HTML)
├── BRI_Design_System_v5.html   # Reference design system
├── MASTER_CONTEXT.md           # This document
├── README.md
├── requirements.txt
└── .gitignore
```

### Alur Data
```
┌─────────────────────────────────────────────┐
│         USER INPUT (1 Excel file)            │
│  Challenge Session.xlsx                      │
│  (Sheet pertama, ~1250 rows × 101 cols)      │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  parser_challenge.py    │
          │  • openpyxl read_only   │
          │  • Detect project rows  │
          │  • Merge continuation   │
          │  • Compute deltas       │
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
          ┌────────────────────────────────────┐
          │  dashboard.html + inject JSON data  │
          │  via window.__autoRender hook       │
          └────────────┬───────────────────────┘
                       │
                       ▼
          output/dashboard_CS_YYYYMMDD_HHMMSS.html
```

### Cara Kerja Injection (DLP-safe)
`app.py` dan `generate_dashboard.py` membaca `dashboard.html`, lalu inject data JSON ke dalam HTML sebelum `</body>`:

```python
inject_script = f"""
<script>
(function() {{
  window.__INJECTED_DATA__ = {{
    projects: {projects_json},
    cutoff_month: {cutoff},
    ...
  }};
}})();
</script>
<script>
document.addEventListener('DOMContentLoaded', function() {{
  if (window.__autoRender) window.__autoRender(window.__INJECTED_DATA__);
}});
</script>
"""
```

`dashboard.html` sudah punya `window.__autoRender` built-in yang menerima data ini dan langsung render dashboard tanpa perlu upload file di browser.

---

## 3. SKEMA DATA & STRUKTUR EXCEL

### File Input
**Nama:** `Challenge Session.xlsx`  
**Sheet:** Sheet pertama (biasanya "Sheet3" atau "Sheet1")  
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

| Index | Excel Col | Nama Kolom | Variabel Internal | Keterangan |
|---|---|---|---|---|
| 20 | U | ID RKA TI 2026 | `id_rka_ti` | Primary identifier |
| 21 | V | Nama Proyek (Awal) | `name_awal` | Sebelum revisi |
| 22 | W | Nama Proyek (Rev) | `name_rev` | Setelah revisi |
| 23 | X | Nama Proyek (Akhir) | `name` | Final Challenge Session |
| 24 | Y | Total Project Cost (Awal) | `tpc_awal` | Baseline TPC |
| 25 | Z | Kebutuhan 1 Tahun (Awal) | `kebutuhan_1thn` | Baseline kebutuhan |
| 26 | AA | Nominal Switching | `nominal_switching` | +/- switching |
| **27** | **AB** | **Alokasi Update** | **`alokasi_update`** | **ISG allocation — dipakai untuk delta keb** |
| 30 | AE | TPC Revisi | `tpc_revisi` | Revised TPC |
| **31** | **AF** | **Kebutuhan 1 Thn Revisi** | **`kebutuhan_1thn_rev`** | **INF request — dipakai untuk delta keb** |
| 32 | AG | Nominal Min Alokasi | `nominal_min_alokasi` | Minimum ISG |
| 33 | AH | Selisih | `selisih_alokasi` | Gap vs minimum ISG |
| 35 | AJ | Update Progress | `update_progress` | Status terkini |
| 36 | AK | Catatan | `catatan` | Catatan tambahan |
| 37–48 | AL–AW | Realisasi Jan–Des | `real_jan`..`real_des` | Realisasi bulanan |
| 49 | AX | Total Realisasi | `real_total` | Sum Jan–Des |
| 65 | BN | Status Pengadaan | `status_pengadaan` | Status aktual |
| 71 | BT | Principle | `principle` | Vendor prinsipal |
| 72 | BU | BP | `bp` | Business Partner |
| 73–84 | BV–CG | Prognosa Jan–Des | `prog_jan`..`prog_des` | Prognosa non-kumulatif |
| 87–98 | CJ–CU | Prognosa Kumulatif | `prog_kum_jan`..`prog_kum_des` | Prognosa kumulatif |

### Deteksi Baris Proyek
```python
id_valid = re.match(r"^\d{4}-[A-Z]+-[A-Z]\.\d", id_rka)
name_valid = name and name != "-" and len(name) > 3
has_marker = pc in {"Parent","Child"} or plan in {"Planned","Unplanned"}
is_project = id_valid or (name_valid and has_marker)
```

Baris lain = continuation row → merge ke proyek sebelumnya.

---

## 4. BUSINESS LOGIC & RULES

### 4.1 Alokasi Primary (untuk display)
```python
alokasi = kebutuhan_1thn_rev (col AF) or alokasi_update (col AB)
```

### 4.2 Delta TPC
```python
tpc_delta = tpc_revisi - tpc_awal  # jika keduanya > 0
```

### 4.3 Delta Kebutuhan — KRITIS
```
keb_delta = kebutuhan_1thn_rev (col AF) - alokasi_update (col AB)
```
- **Positif (+)** = INF minta lebih dari yang sudah di-alokasikan ISG → perlu negosiasi
- **Negatif (−)** = Alokasi ISG sudah lebih dari cukup untuk kebutuhan INF
- Kondisi: tampilkan delta jika salah satu nilai != 0 (bukan hanya jika keduanya > 0)
- **JANGAN** gunakan nominal_switching untuk delta kebutuhan

### 4.4 Switching Classification
```python
if nominal_switching > 0:  → "Bertambah"
if nominal_switching < 0:  → "Berkurang"
if planned == "Unplanned": → "Baru (Unplanned)"
if status contains "batal": → "Batal"
```

### 4.5 Status Normalization
10 kategori: Selesai (Lunas), Pembayaran, SPK Terbit, IP Terbit, Pengadaan, Belum Mulai, Batal, Ditunda, TBC, Tidak diketahui

### 4.6 Cutoff Month Detection
Auto-detect bulan terakhir yang memiliki realisasi > 0 dari agregat seluruh proyek.

---

## 5. SPESIFIKASI DASHBOARD HTML OUTPUT

### Layout: 1 Halaman, 2 Bagian

**Bagian 1 — KPI Cards (8 card, clickable)**

| Card | Data | Warna |
|---|---|---|
| Switching In | Proyek sw > 0 | green |
| Switching Out | Proyek sw < 0 | red |
| Delta TPC | tpc_revisi - tpc_awal | green/red |
| Delta Kebutuhan vs Alokasi ISG | keb_rev(AF) - alok_update(AB) | green/red |
| Perubahan Scope/Nama | has_name_change | sky |
| Selisih vs Min ISG | selisih_alokasi | amber |
| Unplanned Baru | is_new_unplanned | orange |
| Batal / Ditunda | status Batal/Ditunda | red |

**Klik card** → card modal berisi daftar proyek → **klik proyek** → drawer detail

**Bagian 2 — Tabel Semua Proyek**

Kolom: ID RKA · Nama Proyek · DEPT · Status · Alokasi Revisi · Realisasi · Switching · Δ TPC · Δ Kebutuhan

Filter: search, status, DEPT, planned/unplanned, jenis perubahan  
Sort: semua kolom  
Klik baris → drawer detail

### UX Flow: Card Modal → Drawer
1. Klik KPI card → card modal terbuka (z-index 301)
2. Klik item di modal → modal tutup → drawer slide in (z-index 400)
3. Drawer punya tombol "← Kembali ke daftar" → tutup drawer → buka modal lagi
4. Escape: tutup drawer dulu jika terbuka, baru tutup modal

### Drawer Detail
- Delta boxes (TPC, Kebutuhan, Scope, Selisih) dengan highlight warna
- Riwayat switching (dari/ke proyek mana)
- Keterangan revisi & catatan update progress
- Vendor/principle/BP
- SPK info

### Format Angka
- Rupiah: `Rp 1,38 T` / `Rp 241,69 M` / `Rp 847,27 Jt`
- Persentase: `67.4%`
- Locale: Indonesia

### Dark Mode
- Toggle di topbar, saved ke `localStorage`
- CSS: `html.dark` overrides

---

## 6. SPESIFIKASI GUI INPUT (app.py)

PySide6 desktop app:
1. Pilih 1 file Excel (Challenge Session)
2. Klik Process & Generate Dashboard
3. Progress bar + status
4. Tombol buka dashboard setelah selesai

**run.bat** = shortcut untuk `python app.py`

---

## 7. BRI DESIGN SYSTEM — CSS TOKENS

```css
:root {
  --blue:#00529C; --blue-d:#003F7A; --blue-dd:#002D58;
  --orange:#F37021;
  --green:#13A888; --green-s:rgba(19,168,136,.12);
  --red:#D93A3A; --red-s:rgba(217,58,58,.12);
  --amber:#E6A700; --amber-s:rgba(230,167,0,.12);
  --sky:#3B82C4; --sky-s:rgba(59,130,196,.12);
  --bg:#F4F7FB; --card:#fff; --border:#E2E8F2;
  --t1:#0F1C2E; --t2:#3D5166; --t3:#8A9BB0;
}
html.dark {
  --bg:#0B1628; --card:#112240; --border:#1E3A5F;
  --t1:#E2EAF4; --t2:#8AAAC8; --t3:#4A6A8A;
}
```

Font: Inter (Google Fonts). Angka: `font-variant-numeric: tabular-nums`.

---

## 8. CONTOH DATA & AGGREGASI

### Sample Project Record (Python dict)
```python
{
    "id_rka_ti": "2026-INF-A.01.127",
    "name": "Modernisasi Infrastructure Network & Keamanan Unit Kerja...",
    "dept": "NSQ", "tim": "SCT",
    "planned": "Planned", "parent_child": "Parent",
    "alokasi_update": 8567807170,      # col AB — ISG allocation
    "kebutuhan_1thn_rev": 109734350000, # col AF — INF request
    "keb_delta": 101166542830,          # AF - AB = +101.17M (INF minta lebih)
    "tpc_awal": 293000000000,
    "tpc_revisi": 293000000000,
    "tpc_delta": 0,
    "nominal_switching": 8567807170,
    "real_total": 8567807170,
    "status": "SPK Terbit",
    "has_keb_change": True,
    "has_tpc_change": False,
    "has_name_change": False,
    "has_switching": True,
}
```

### Validated Aggregates (v2.0)
```
Total proyek parsed:        227
Total Kebutuhan 1 Thn Rev:  2,085,607,388,894  (col AF sum)
Switching In:               451,164,361,613
Switching Out:              451,164,361,613
Net Switching:              0
keb_changed (AF != AB):     118 proyek
tpc_changed:                30 proyek
name_changed:               26 proyek
```

---

## 9. RULES & EDGE CASES

| # | Kasus | Handling |
|---|---|---|
| 1 | Proyek tanpa ID RKA (unplanned baru) | Tetap diproses; key = nama proyek |
| 2 | Continuation rows (hanya teks di col 28/29/34/36) | Merge ke proyek sebelumnya |
| 3 | Header rows (row 15-17) yang repeat | Skip — bukan data |
| 4 | Kolom numerik berisi teks/tanggal | `_num()` coerce ke 0.0 |
| 5 | keb_delta: salah satu nilai = 0 | Tetap hitung delta (bukan skip) |
| 6 | Multiple switching entries per proyek | Semua di-append ke `switching_log` |
| 7 | Sheet name bervariasi | Selalu ambil sheet pertama |
| 8 | SPK number di kolom status | Normalize ke "SPK Terbit" |
| 9 | Drawer dibuka dari card modal | Tutup modal dulu, buka drawer, tampilkan back button |
| 10 | Escape key | Tutup drawer dulu jika terbuka, baru tutup modal |

---

## 10. CATATAN TEKNIS & DEBUGGING

### Delta Kebutuhan — PALING PENTING
```
keb_delta = col AF (kebutuhan_1thn_rev) - col AB (alokasi_update)
```
- **BUKAN** dari nominal_switching
- **BUKAN** kebutuhan_1thn (col Z) vs kebutuhan_1thn_rev (col AF)
- Kondisi: `if (alok_update != 0 or keb_rev != 0)` — bukan `if (both > 0)`

### Z-index Hierarchy
```
Card Modal overlay:  z-index 300
Card Modal:          z-index 301
Drawer overlay:      z-index 399
Drawer:              z-index 400
Loading overlay:     z-index 500
```

### __autoRender Hook
`dashboard.html` punya `window.__autoRender(data)` built-in. `app.py` dan `generate_dashboard.py` cukup inject JSON data — tidak perlu inject hook lagi.

### Parser — Deteksi Baris Proyek
```python
id_valid = re.match(r"^\d{4}-[A-Z]+-[A-Z]\.\d", id_rka)
name_valid = name and name != "-" and len(name) > 3
has_marker = pc in {"Parent","Child"} or plan in {"Planned","Unplanned"}
is_project = id_valid or (name_valid and has_marker)
```

---

## 11. DEVELOPMENT PHASES & CHANGELOG

### v1.0 (2026-05-13) — Initial Build
- PySide6 GUI + CLI
- Parser Excel → 225 proyek
- Dashboard 5 tab (Overview, Perubahan, Pengadaan, RKA TI, CJE0)
- Switching flow Sankey, heatmap, multi-year CJE0

### v2.0 (2026-05-18) — Simplification & Delta Focus
- **Simplify**: 5 tab → 1 halaman (KPI cards + tabel)
- **NEW**: KPI cards clickable → card modal berisi daftar proyek
- **NEW**: Delta TPC (tpc_revisi - tpc_awal)
- **FIX**: Delta Kebutuhan = col AF - col AB (bukan switching)
- **FIX**: keb_delta detection: 55 → 118 proyek
- **FIX**: Drawer z-index 400 (di atas card modal 301)
- **FIX**: Klik item di modal → tutup modal → buka drawer
- **FIX**: Back button di drawer untuk kembali ke modal
- **FIX**: app.py sync dengan dashboard.html terbaru
- **CLEAN**: Hapus dead code renderProjects(), tab nav, 3 view lama

---

## 12. INSTRUKSI KHUSUS UNTUK AI ASSISTANT

1. **Baca seluruh MASTER_CONTEXT.md sebelum generate kode apapun**
2. **File Excel TIDAK BOLEH di-upload ke browser** — DLP restriction BRI
3. **Parsing harus via Python (openpyxl)** — bukan SheetJS di browser
4. **Delta Kebutuhan = col AF - col AB** — BUKAN dari switching, BUKAN col Z vs AF
5. **keb_delta condition**: `if (alok_update != 0 or keb_rev != 0)` — bukan `if (both > 0)`
6. **dashboard.html sudah punya `__autoRender`** — app.py cukup inject JSON data
7. **Z-index**: drawer (400) > card modal (301) > loading (500 — tertinggi)
8. **Drawer dari card modal**: tutup modal dulu, buka drawer, tampilkan back button
9. **Semua angka format locale Indonesia** (Rp, titik ribuan, koma desimal)
10. **Dark mode** via `html.dark` class + toggle
11. **Jangan hardcode data** — semua dari hasil parse + injection

### Larangan Keras
- ❌ Jangan upload file ke browser (DLP)
- ❌ Jangan pakai pandas (openpyxl cukup)
- ❌ Jangan hardcode path file
- ❌ Jangan kirim data ke server/internet
- ❌ Jangan inject hook baru ke dashboard.html — sudah ada `__autoRender`
- ❌ Jangan gunakan nominal_switching untuk delta kebutuhan

---

## 13. KONVENSI KODE

```python
# Python — snake_case
id_rka_ti, alokasi_update, kebutuhan_1thn_rev, keb_delta

# JavaScript — camelCase (dalam dashboard.html)
alokUpdate, kebRev, kebDelta, openCardModal(), openDrawer()

# CSS class — kebab-case
.kpi.clickable, .ci.in, .ci.out, .delta-box.up

# File naming — snake_case
parser_challenge.py, builder.py, generate_dashboard.py
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
git clone https://github.com/itsmhp/ChallengeSession.git
cd ChallengeSession
pip install -r requirements.txt
```

### Running
```
run.bat          # GUI (Windows)
python app.py    # GUI (any OS)
python generate_dashboard.py "Challenge Session.xlsx"  # CLI
```

---

## 15. SECURITY & DLP CONSIDERATIONS

### Data Loss Prevention (DLP)
- ✅ File Excel dibaca **lokal** oleh Python — TIDAK di-upload ke browser
- ✅ Dashboard output = file HTML statis — TIDAK ada koneksi internet saat dibuka
- ✅ ECharts CDN hanya untuk library JS (bukan data)
- ✅ Tidak ada data yang dikirim ke luar mesin pengguna

### Output Security
- Generated HTML berisi data anggaran mentah — treat as **CONFIDENTIAL**
- File output sudah di-gitignore (`output/dashboard_CS_*.html`)

---

**Author:** PMO Infrastruktur (PIN) — IT Directorate BRI  
**Status:** Production Ready (v2.0)  
**Terakhir Diperbarui:** 2026-05-18  
**Repository:** https://github.com/itsmhp/ChallengeSession
