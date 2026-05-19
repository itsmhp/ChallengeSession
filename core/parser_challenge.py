"""
parser_challenge.py
-------------------
Parse the "Challenge Session" Excel workbook (revisi window RKA TI).

The workbook contains a single sheet (typically named "Sheet3") with:
- Rows 1-14: summary totals and legends
- Row 8-11: multi-row merged headers
- Row 15-16: repeated header block
- Row 18+ : data rows (one project per row, with continuation rows for extra
            notes/switching entries)

Column layout is fixed (verified from the source file). All indices below are
0-based as returned by openpyxl `sheet.iter_rows` with `values_only=True`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable

import openpyxl


# ---------------------------------------------------------------------------
# Column map — fixed layout in the Challenge Session template
# ---------------------------------------------------------------------------

COL = {
    # New 135-column format — sheet "INF" (verified 2026-05-19)
    "no": 1,
    "parent_child": 2,
    "planned": 3,
    "nota_dinas": 4,           # Nomor Nota Dinas (unplanned)
    "kanpus": 5,               # UPA/Kanpus
    "ho_ro": 6,                # HO/RO
    "group": 7,                # Group (INF)
    "dept": 8,                 # DEPT
    "tim": 9,                  # Tim
    # SK RKA TI 2026 awal (col K-N)
    "jenis_anggaran_awal": 10,
    "nama_gl_awal": 11,
    "asset_class_awal": 12,
    "id_ac_awal": 13,
    # SK RKA TI 2026 revisi (col O-R)
    "jenis_anggaran_rev": 14,
    "nama_gl_rev": 15,
    "asset_class_rev": 16,
    "id_ac_rev": 17,
    "id_rka_2025": 18,         # ID RKA TI 2025
    "kode_nomor": 19,          # Kode Nomor
    "id_rka_2026": 20,         # ID RKA TI 2026 — col U
    "nama_proyek_awal": 21,    # Nama Proyek (Awal) — col V
    "nama_proyek_rev": 22,     # Nama Proyek (Rev) — col W
    "nama_proyek_akhir": 23,   # Nama Proyek (Akhir/CS) — col X
    "tpc_awal": 24,            # Total Project Cost awal — col Y
    "kebutuhan_1thn": 25,      # Kebutuhan 1 Tahun awal — col Z
    "nominal_switching": 26,   # Nominal Switching — col AA
    "alokasi_update": 27,      # Alokasi Update (ISG) — col AB ← KEY
    "ip_switching": 28,        # IP Switching/Link — col AC
    "keterangan_switching": 29,# Keterangan switching — col AD
    "tpc_revisi": 30,          # TPC Revisi — col AE
    "kebutuhan_1thn_rev": 31,  # Kebutuhan 1 Thn Revisi (INF) — col AF ← KEY
    "nominal_min_alokasi": 32, # Nominal Min Alokasi — col AG
    "selisih_alokasi": 33,     # Selisih — col AH
    "keterangan_revisi": 34,   # Keterangan Revisi — col AI
    # Cols AJ-AQ: various metadata
    "status_pengadaan": 69,    # Status Pengadaan — col BR
    "update_progress": 70,     # Update Progress / Catatan — col BS
    # Prognosa per tahun (col BX-CF) — not monthly, skip
    # Realisasi bulanan non-kumulatif — col DD-DO (idx 107-118)
    "real_jan": 107, "real_feb": 108, "real_mar": 109, "real_apr": 110,
    "real_mei": 111, "real_jun": 112, "real_jul": 113, "real_agst": 114,
    "real_sep": 115, "real_okt": 116, "real_nov": 117, "real_des": 118,
    "real_total": 119,         # Total Realisasi — col DP
    "real_selisih": 120,       # Selisih Realisasi — col DQ
    # Prognosa kumulatif — col DR-EC (idx 121-132)
    "prog_kum_jan": 121, "prog_kum_feb": 122, "prog_kum_mar": 123, "prog_kum_apr": 124,
    "prog_kum_mei": 125, "prog_kum_jun": 126, "prog_kum_jul": 127, "prog_kum_agst": 128,
    "prog_kum_sep": 129, "prog_kum_okt": 130, "prog_kum_nov": 131, "prog_kum_des": 132,
    "prog_kum_selisih": 133,
    # Prognosa non-kumulatif — not available in this format, use kum diffs
    "prog_jan": 107, "prog_feb": 108, "prog_mar": 109, "prog_apr": 110,
    "prog_mei": 111, "prog_jun": 112, "prog_jul": 113, "prog_agst": 114,
    "prog_sep": 115, "prog_okt": 116, "prog_nov": 117, "prog_des": 118,
    "prog_total": 119,
    "prog_selisih": 120,
    # SPK
    "nomor_spk": 100,          # Nomor SPK — col CW
    "nama_spk": 101,           # Nama SPK — col CX
    "nominal_spk": 102,        # Nominal SPK — col CY
    "spk_mulai": 103,          # Mulai SPK — col CZ
    "spk_selesai": 104,        # Selesai SPK — col DA
    "principle": 105,          # Principle — col DB
    "bp": 106,                 # BP — col DC
    # Meta
    "kategori": 95,            # Kategori Pengadaan — col CR
    "klasifikasi": 96,         # Klasifikasi — col CS
    "rutin": 97,               # Rutin — col CT
    "baru": 98,                # Baru/Sisa Bayar — col CU
}

REAL_COLS = [COL[f"real_{m}"] for m in ("jan", "feb", "mar", "apr", "mei", "jun",
                                         "jul", "agst", "sep", "okt", "nov", "des")]
PROG_COLS = REAL_COLS  # Use realisasi cols as proxy for prognosa (not available separately)
PROG_KUM_COLS = [COL[f"prog_kum_{m}"] for m in ("jan", "feb", "mar", "apr", "mei", "jun",
                                                  "jul", "agst", "sep", "okt", "nov", "des")]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
          "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
MONTHS_FULL = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
               "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

DATA_START_ROW = 11  # 0-indexed; first project at row 12 (idx 11)
SUMMARY_ROW = 10     # Summary totals row


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _num(value: Any) -> float:
    """Coerce to float; return 0.0 on failure or None."""
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value) if value == value else 0.0  # NaN guard
    text = str(value).strip()
    if not text or text in {"-", "—"}:
        return 0.0
    # Indonesian / common numeric formats: strip spaces, handle parentheses
    text = text.replace("Rp", "").replace(" ", "")
    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    text = text.lstrip("-").strip("()")
    # Keep digits, dot, comma
    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return 0.0
    # If both separators present, assume dot=thousand, comma=decimal
    if "." in cleaned and "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        # Assume comma decimal
        cleaned = cleaned.replace(",", ".")
    else:
        # Dot may be thousand separator if more than 1 or followed by 3 digits
        if cleaned.count(".") > 1 or (cleaned.count(".") == 1 and len(cleaned.split(".")[1]) == 3):
            cleaned = cleaned.replace(".", "")
    try:
        result = float(cleaned)
        return -result if negative else result
    except ValueError:
        return 0.0


def _text(value: Any) -> str:
    """Return stripped string or empty."""
    if value is None:
        return ""
    return str(value).strip()


_RKA_ID_RE = re.compile(r"^\d{4}-[A-Z]+-[A-Z]\.\d", re.IGNORECASE)


def _is_valid_id(idrka: str) -> bool:
    return bool(idrka) and bool(_RKA_ID_RE.match(idrka))


def _normalize_status(raw: str) -> str:
    s = raw.lower()
    if not s:
        return "Tidak diketahui"
    if "lunas" in s or "selesai" in s:
        return "Selesai (Lunas)"
    if "batal" in s or "drop" in s or "dibatalkan" in s:
        return "Batal"
    if "ditunda" in s or "hold" in s:
        return "Ditunda"
    if "pembayaran" in s:
        return "Pembayaran"
    if "spk" in s:
        return "SPK Terbit"
    if "ip terbit" in s:
        return "IP Terbit"
    if "pengadaan" in s:
        return "Pengadaan"
    if "belum" in s:
        return "Belum Mulai"
    if "tbc" in s:
        return "TBC"
    # Catch SPK numbers mistakenly in status column
    if s.startswith("4") and len(s) > 10:
        return "SPK Terbit"
    return raw or "Tidak diketahui"


def _classify_change(planned: str, nominal_switching: float, status: str) -> str:
    """Category for the 'Perubahan' grouping."""
    if nominal_switching > 0:
        return "Bertambah"
    if nominal_switching < 0:
        return "Berkurang"
    status_l = (status or "").lower()
    if "batal" in status_l or "drop" in status_l:
        return "Batal"
    if "ditunda" in status_l or "hold" in status_l:
        return "Ditunda"
    if (planned or "").lower() == "unplanned":
        return "Baru (Unplanned)"
    return "Tidak berubah"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SwitchingLog:
    ip: str = ""
    desc: str = ""


@dataclass
class ProjectRow:
    # Identifiers
    no: str = ""
    parent_child: str = ""
    planned: str = ""
    nota_dinas: str = ""
    kanpus: str = ""
    ho_ro: str = ""
    group: str = ""
    dept: str = ""
    tim: str = ""
    # Asset & IDs
    jenis_anggaran: str = ""
    nama_gl: str = ""
    asset_class: str = ""
    id_asset: str = ""
    id_rka_2025: str = ""
    kode_nomor: str = ""
    id_rka_ti: str = ""
    # Names
    name: str = ""
    name_awal: str = ""
    name_rev: str = ""
    # Nominal
    tpc_awal: float = 0.0
    tpc_revisi: float = 0.0
    kebutuhan_1thn: float = 0.0
    kebutuhan_1thn_rev: float = 0.0
    nominal_switching: float = 0.0
    alokasi_update: float = 0.0
    nominal_min_alokasi: float = 0.0
    selisih_alokasi: float = 0.0
    # Text fields
    keterangan_revisi: str = ""
    update_progress: str = ""
    catatan: str = ""
    # Bulanan
    real: list = field(default_factory=lambda: [0.0] * 12)
    real_total: float = 0.0
    prog: list = field(default_factory=lambda: [0.0] * 12)
    prog_total: float = 0.0
    prog_kum: list = field(default_factory=lambda: [0.0] * 12)
    # Klasifikasi
    si_rbb: str = ""
    jps: str = ""
    program_kerja: str = ""
    nama_aplikasi: str = ""
    grp_aplikasi: str = ""
    fungsi_tim: str = ""
    mulai: str = ""
    selesai: str = ""
    kategori: str = ""
    klasifikasi: str = ""
    rutin: str = ""
    baru: str = ""
    status: str = ""
    status_raw: str = ""
    nomor_spk: str = ""
    nama_spk: str = ""
    nominal_spk: float = 0.0
    spk_mulai: str = ""
    spk_selesai: str = ""
    principle: str = ""
    bp: str = ""
    # Derived — change detection
    switching_log: list = field(default_factory=list)
    change_type: str = ""
    serapan_pct: float = 0.0
    source_row: int = 0
    # Delta fields (revision tracking)
    tpc_delta: float = 0.0          # tpc_revisi - tpc_awal
    keb_delta: float = 0.0          # kebutuhan_1thn_rev - kebutuhan_1thn
    has_tpc_change: bool = False
    has_keb_change: bool = False
    has_name_change: bool = False
    has_switching: bool = False
    has_selisih: bool = False
    is_new_unplanned: bool = False   # Unplanned + no baseline

    def to_dict(self) -> dict:
        d = asdict(self)
        # dataclasses serialise nested dataclasses fine, but SwitchingLog is dataclass-of-dict already
        return d


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_challenge_session(xlsx_path: str | Path) -> dict:
    """
    Parse the Challenge Session workbook.

    Returns a dict:
        {
            "sheet_name": str,
            "cutoff_month": int (0..11),
            "summary_totals": { ... excel summary row values ... },
            "projects": [ProjectRow dicts...]
        }
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"File not found: {xlsx_path}")

    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
    # Find the data sheet — prefer "INF", fallback to first sheet
    sheet_name = wb.sheetnames[0]
    for sname in wb.sheetnames:
        if sname.strip().upper() == "INF":
            sheet_name = sname
            break
    ws = wb[sheet_name]

    # Collect rows into list of tuples indexed 0..N
    rows: list[tuple] = []
    for r in ws.iter_rows(values_only=True):
        rows.append(r)

    # Summary totals from SUMMARY_ROW (0-indexed 14)
    summary = {}
    if len(rows) > SUMMARY_ROW:
        srow = rows[SUMMARY_ROW] or ()
        def _g(idx): return srow[idx] if idx < len(srow) else None
        summary = {
            "tpc_awal":            _num(_g(COL["tpc_awal"])),
            "kebutuhan_1thn":      _num(_g(COL["kebutuhan_1thn"])),
            "nominal_switching":   _num(_g(COL["nominal_switching"])),
            "alokasi_update":      _num(_g(COL["alokasi_update"])),
            "tpc_revisi":          _num(_g(COL["tpc_revisi"])),
            "kebutuhan_1thn_rev":  _num(_g(COL["kebutuhan_1thn_rev"])),
            "nominal_min_alokasi": _num(_g(COL["nominal_min_alokasi"])),
            "selisih_alokasi":     _num(_g(COL["selisih_alokasi"])),
            "real_total":          _num(_g(COL["real_total"])),
        }

    projects: list[dict] = []
    current: ProjectRow | None = None

    for i in range(DATA_START_ROW, len(rows)):
        raw = rows[i]
        if raw is None:
            continue

        def g(idx):
            return raw[idx] if idx is not None and idx < len(raw) else None

        name = _text(g(COL["nama_proyek_rev"])) or _text(g(COL["nama_proyek_awal"]))
        id_rka = _text(g(COL["id_rka_2026"]))
        pc = _text(g(COL["parent_child"]))
        plan = _text(g(COL["planned"]))

        id_valid = _is_valid_id(id_rka)
        name_valid = bool(name) and name != "-" and len(name) > 3
        has_marker = pc in {"Parent", "Child"} or plan in {"Planned", "Unplanned"}

        is_project = id_valid or (name_valid and has_marker)

        if is_project:
            current = _project_from_row(raw, i)
            projects.append(current.to_dict())
        elif current is not None:
            # continuation — merge extra narrative
            ket = _text(g(COL["keterangan_switching"]))
            ip = _text(g(COL["ip_switching"]))
            catatan = _text(g(COL["update_progress"]))
            ket_rev = _text(g(COL["keterangan_revisi"]))
            if ket:
                current.switching_log.append(asdict(SwitchingLog(ip=ip, desc=ket)))
                # also sync back onto the dict we stored
                projects[-1]["switching_log"] = current.switching_log
            if catatan and catatan not in projects[-1]["catatan"]:
                joined = projects[-1]["catatan"] + ("\n" if projects[-1]["catatan"] else "") + catatan
                projects[-1]["catatan"] = joined
            if ket_rev and ket_rev not in projects[-1]["keterangan_revisi"]:
                joined = projects[-1]["keterangan_revisi"] + ("\n" if projects[-1]["keterangan_revisi"] else "") + ket_rev
                projects[-1]["keterangan_revisi"] = joined

    wb.close()

    cutoff = _detect_cutoff(projects)

    return {
        "sheet_name": sheet_name,
        "cutoff_month": cutoff,
        "summary_totals": summary,
        "projects": projects,
    }


def _project_from_row(raw: tuple, row_idx: int) -> ProjectRow:
    def g(idx):
        return raw[idx] if idx is not None and idx < len(raw) else None

    name = (
        _text(g(COL["nama_proyek_rev"]))
        or _text(g(COL["nama_proyek_awal"]))
    )
    id_rka = _text(g(COL["id_rka_2026"]))

    real = [_num(g(c)) for c in REAL_COLS]
    prog = [_num(g(c)) for c in PROG_COLS]
    prog_kum = [_num(g(c)) for c in PROG_KUM_COLS]

    real_total_row = _num(g(COL["real_total"]))
    real_total = real_total_row or sum(real)
    prog_total_row = _num(g(COL["prog_total"]))
    prog_total = prog_total_row or sum(prog)

    alokasi_update_raw = _num(g(COL["alokasi_update"]))   # col K — ISG allocation
    keb_rev_raw = _num(g(COL["kebutuhan_1thn_rev"]))       # col O — INF request
    alokasi = keb_rev_raw or alokasi_update_raw

    # Status from Update Progress column (col V = idx 21)
    status_raw = _text(g(COL["update_progress"]))
    status_norm = _normalize_status(status_raw)

    switching_log: list[dict] = []
    ket = _text(g(COL["keterangan_switching"]))
    if ket:
        switching_log.append(asdict(SwitchingLog(ip=_text(g(COL["ip_switching"])), desc=ket)))

    nominal_sw = _num(g(COL["nominal_switching"]))
    planned = _text(g(COL["planned"]))

    catatan_combined = _text(g(COL["update_progress"]))  # col BS has progress/catatan text

    pr = ProjectRow(
        no=_text(g(COL["no"])),
        parent_child=_text(g(COL["parent_child"])),
        planned=planned,
        nota_dinas="",
        kanpus="",
        ho_ro="",
        group="",
        dept="",
        tim="",

        jenis_anggaran="",
        nama_gl="",
        asset_class="",
        id_asset="",

        id_rka_2025="",
        kode_nomor="",
        id_rka_ti=id_rka,

        name=name,
        name_awal=_text(g(COL["nama_proyek_awal"])),
        name_rev=_text(g(COL["nama_proyek_rev"])),

        tpc_awal=_num(g(COL["tpc_awal"])),
        tpc_revisi=_num(g(COL["tpc_revisi"])),
        kebutuhan_1thn=_num(g(COL["kebutuhan_1thn"])),
        kebutuhan_1thn_rev=keb_rev_raw,
        nominal_switching=nominal_sw,
        alokasi_update=alokasi_update_raw,
        nominal_min_alokasi=_num(g(COL["nominal_min_alokasi"])),
        selisih_alokasi=_num(g(COL["selisih_alokasi"])),

        keterangan_revisi=_text(g(COL["keterangan_revisi"])),
        update_progress=status_raw,
        catatan=catatan_combined,

        real=real,
        real_total=real_total,
        prog=prog,
        prog_total=prog_total,
        prog_kum=prog_kum,

        si_rbb="",
        jps="",
        program_kerja="",
        nama_aplikasi="",
        grp_aplikasi="",
        fungsi_tim="",

        mulai=_text(g(COL["spk_mulai"])),
        selesai=_text(g(COL["spk_selesai"])),
        kategori="",
        klasifikasi="",
        rutin="",
        baru="",
        status=status_norm,
        status_raw=status_raw,

        nomor_spk=_text(g(COL["nomor_spk"])),
        nama_spk=_text(g(COL["nama_spk"])),
        nominal_spk=_num(g(COL["nominal_spk"])),
        spk_mulai=_text(g(COL["spk_mulai"])),
        spk_selesai=_text(g(COL["spk_selesai"])),
        principle=_text(g(COL["principle"])),
        bp=_text(g(COL["bp"])),

        switching_log=switching_log,
        source_row=row_idx,
    )

    pr.change_type = _classify_change(planned, nominal_sw, status_norm)
    pr.serapan_pct = (pr.real_total / alokasi * 100.0) if alokasi > 0 else 0.0

    # Delta TPC
    pr.tpc_delta = pr.tpc_revisi - pr.tpc_awal if (pr.tpc_awal > 0 and pr.tpc_revisi > 0) else 0.0
    # Delta Kebutuhan: col O (INF) - col K (ISG)
    pr.keb_delta = (keb_rev_raw - alokasi_update_raw) if (alokasi_update_raw != 0 or keb_rev_raw != 0) else 0.0
    pr.has_tpc_change = abs(pr.tpc_delta) > 1000
    pr.has_keb_change = abs(pr.keb_delta) > 1000
    pr.has_name_change = bool(
        pr.name_awal and pr.name and pr.name_awal != "-" and pr.name != "-"
        and pr.name_awal != pr.name and len(pr.name_awal) > 3
    )
    pr.has_switching = nominal_sw != 0
    pr.has_selisih = pr.selisih_alokasi != 0
    pr.is_new_unplanned = (planned.lower() == "unplanned") and alokasi_update_raw == 0 and keb_rev_raw == 0

    return pr

    real = [_num(g(c)) for c in REAL_COLS]
    prog = [_num(g(c)) for c in PROG_COLS]
    prog_kum = [_num(g(c)) for c in PROG_KUM_COLS]

    real_total_row = _num(g(COL["real_total"]))
    real_total = real_total_row or sum(real)
    prog_total_row = _num(g(COL["prog_total"]))
    prog_total = prog_total_row or sum(prog)

    # Primary allocation: prefer revisi result (col 31), fallback to alokasi_update (col 27)
def _detect_cutoff(projects: Iterable[dict]) -> int:
    totals = [0.0] * 12
    for p in projects:
        for i, v in enumerate(p.get("real", [])):
            totals[i] += v
    last = -1
    for i in range(12):
        if totals[i] != 0:
            last = i
    if last < 0:
        # Default to current month
        import datetime as _dt
        return _dt.datetime.now().month - 1
    return last
