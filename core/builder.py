"""
builder.py
----------
Build the Jinja2 rendering context from parsed projects.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Iterable

from .parser_challenge import MONTHS, MONTHS_FULL


STATUS_COLORS = {
    "Selesai (Lunas)": "success",
    "Pembayaran": "info",
    "SPK Terbit": "primary",
    "IP Terbit": "primary",
    "Pengadaan": "accent",
    "Belum Mulai": "warning",
    "Batal": "danger",
    "Ditunda": "warning",
    "TBC": "neutral",
    "Tidak diketahui": "neutral",
}


def _rp_short(n: float) -> str:
    if not n or n != n:
        return "Rp 0"
    absn = abs(n)
    sign = "-" if n < 0 else ""
    if absn >= 1e12:
        return f"Rp {sign}{absn/1e12:.2f} T"
    if absn >= 1e9:
        return f"Rp {sign}{absn/1e9:.2f} M"
    if absn >= 1e6:
        return f"Rp {sign}{absn/1e6:.1f} Jt"
    if absn >= 1e3:
        return f"Rp {sign}{absn/1e3:.0f} Rb"
    return f"Rp {sign}{absn:.0f}"


def build_context(parsed: dict, *, source_file: str = "", period_label: str = "") -> dict:
    """
    Produce the full context dict for the Jinja2 template.
    """
    projects = parsed["projects"]
    cutoff_month = parsed["cutoff_month"]
    sheet_name = parsed["sheet_name"]
    summary_totals = parsed.get("summary_totals", {})

    agg = _aggregate(projects)

    # KPI derived values
    ytd_realisasi = sum(agg["real_monthly"][: cutoff_month + 1])
    total_alokasi = agg["total_kebutuhan_1thn_rev"] or summary_totals.get("kebutuhan_1thn_rev", 0.0)
    serapan_pct = (ytd_realisasi / total_alokasi * 100.0) if total_alokasi > 0 else 0.0
    sisa = total_alokasi - ytd_realisasi

    # Change analysis
    bertambah = sorted(
        [p for p in projects if p["nominal_switching"] > 0],
        key=lambda p: -p["nominal_switching"],
    )
    berkurang = sorted(
        [p for p in projects if p["nominal_switching"] < 0],
        key=lambda p: p["nominal_switching"],
    )
    unplanned = [p for p in projects if (p.get("planned") or "").lower() == "unplanned"]
    batal = [p for p in projects if p["status"] == "Batal"]
    ditunda = [p for p in projects if p["status"] == "Ditunda"]

    total_switch_in = sum(p["nominal_switching"] for p in bertambah)
    total_switch_out = abs(sum(p["nominal_switching"] for p in berkurang))

    # Switching pairs for sankey/flow
    switching_pairs = _extract_switching_pairs(projects)

    # Multi-year CJE0 estimation from text
    year_totals, year_entries = _extract_year_estimations(projects)
    if 2026 not in year_totals:
        year_totals[2026] = total_alokasi

    # Dropdown / filter sources
    statuses = sorted({p["status"] for p in projects if p.get("status")})
    depts = sorted({p["dept"] for p in projects if p.get("dept")})
    kategoris = sorted({p["kategori"] for p in projects if p.get("kategori")})
    asset_classes = sorted({p["asset_class"] for p in projects if p.get("asset_class")})

    context = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB"),
        "source_file": source_file,
        "period_label": period_label or f"Cut-off {MONTHS_FULL[cutoff_month]}",
        "sheet_name": sheet_name,
        "cutoff_month": cutoff_month,
        "cutoff_month_label": MONTHS_FULL[cutoff_month],

        "totals": {
            "projects": len(projects),
            "alokasi": total_alokasi,
            "alokasi_short": _rp_short(total_alokasi),
            "kebutuhan_awal": agg["total_kebutuhan_1thn"],
            "kebutuhan_awal_short": _rp_short(agg["total_kebutuhan_1thn"]),
            "realisasi_ytd": ytd_realisasi,
            "realisasi_ytd_short": _rp_short(ytd_realisasi),
            "prognosa": agg["total_prognosa"],
            "prognosa_short": _rp_short(agg["total_prognosa"]),
            "serapan_pct": serapan_pct,
            "sisa": sisa,
            "sisa_short": _rp_short(sisa),
            "switch_in": total_switch_in,
            "switch_in_short": _rp_short(total_switch_in),
            "switch_out": total_switch_out,
            "switch_out_short": _rp_short(total_switch_out),
            "switch_net": total_switch_in - total_switch_out,
            "tpc_awal": agg["total_tpc_awal"],
            "tpc_revisi": agg["total_tpc_revisi"],
            "tpc_delta": agg["total_tpc_revisi"] - agg["total_tpc_awal"],
            "bertambah_count": len(bertambah),
            "berkurang_count": len(berkurang),
            "unplanned_count": len(unplanned),
            "unplanned_total": sum(p["alokasi_update"] for p in unplanned),
            "unplanned_total_short": _rp_short(sum(p["alokasi_update"] for p in unplanned)),
            "batal_count": len(batal),
            "ditunda_count": len(ditunda),
        },

        "distribution": {
            "by_status": agg["by_status"],
            "by_dept": agg["by_dept"],
            "by_kategori": agg["by_kategori"],
            "by_klasifikasi": agg["by_klasifikasi"],
            "by_rutin": agg["by_rutin"],
            "by_planned": agg["by_planned"],
            "by_asset": agg["by_asset"],
            "by_gl": agg["by_gl"],
        },

        "monthly": {
            "labels": MONTHS,
            "realisasi": agg["real_monthly"],
            "realisasi_kum": _cumulative(agg["real_monthly"]),
            "prognosa": agg["prog_monthly"],
            "prognosa_kum": agg["prog_kum_monthly"],
        },

        # By-value aggregations (for bar charts)
        "by_dept_value": _top_n(agg["dept_alokasi"], 10),
        "by_gl_value": _sorted_dict_values(agg["gl_alokasi"]),
        "by_asset_value": _sorted_dict_values(agg["asset_alokasi"]),

        # Heatmap data: dept × month
        "heatmap": _build_heatmap(projects),

        # Top lists for quick panels
        "top_projects": sorted(projects, key=lambda p: -p["alokasi_update"])[:15],
        "bertambah": bertambah,
        "berkurang": berkurang,
        "unplanned": unplanned,
        "batal_ditunda": batal + ditunda,

        "switching_pairs": switching_pairs,
        "year_totals": year_totals,
        "year_entries": year_entries,

        # Change detection aggregates
        "revision": {
            "total_with_changes": sum(1 for p in projects if p.get("has_tpc_change") or p.get("has_keb_change") or p.get("has_name_change") or p.get("has_switching")),
            "tpc_changed": sum(1 for p in projects if p.get("has_tpc_change")),
            "keb_changed": sum(1 for p in projects if p.get("has_keb_change")),
            "name_changed": sum(1 for p in projects if p.get("has_name_change")),
            "has_switching": sum(1 for p in projects if p.get("has_switching")),
            "has_selisih": sum(1 for p in projects if p.get("has_selisih")),
            "new_unplanned": sum(1 for p in projects if p.get("is_new_unplanned")),
            "total_tpc_delta": sum(p.get("tpc_delta", 0) for p in projects),
            "total_keb_delta": sum(p.get("keb_delta", 0) for p in projects),
            "total_selisih": sum(p.get("selisih_alokasi", 0) for p in projects),
            "tpc_increased": sorted([p for p in projects if p.get("tpc_delta", 0) > 0], key=lambda p: -p["tpc_delta"])[:15],
            "tpc_decreased": sorted([p for p in projects if p.get("tpc_delta", 0) < 0], key=lambda p: p["tpc_delta"])[:15],
            "name_changes": [p for p in projects if p.get("has_name_change")][:20],
            "biggest_selisih": sorted([p for p in projects if p.get("selisih_alokasi", 0) != 0], key=lambda p: -abs(p["selisih_alokasi"]))[:15],
        },

        "projects": projects,

        "filters": {
            "statuses": statuses,
            "depts": depts,
            "kategoris": kategoris,
            "asset_classes": asset_classes,
        },

        "status_colors": STATUS_COLORS,
    }

    # Pre-serialize JSON payloads for embedding in HTML
    context["json_projects"] = _safe_json(projects)
    context["json_monthly"] = _safe_json(context["monthly"])
    context["json_distribution"] = _safe_json(context["distribution"])
    context["json_heatmap"] = _safe_json(context["heatmap"])
    context["json_switching_pairs"] = _safe_json(switching_pairs)
    context["json_year_totals"] = _safe_json(year_totals)
    context["json_year_entries"] = _safe_json(year_entries)
    context["json_totals"] = _safe_json(context["totals"])
    context["json_revision"] = _safe_json(context["revision"])
    context["json_by_dept_value"] = _safe_json(context["by_dept_value"])
    context["json_by_gl_value"] = _safe_json(context["by_gl_value"])
    context["json_by_asset_value"] = _safe_json(context["by_asset_value"])
    context["json_status_colors"] = _safe_json(STATUS_COLORS)

    return context


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _aggregate(projects: list[dict]) -> dict:
    total_alokasi = 0.0
    total_kebutuhan_1thn = 0.0
    total_kebutuhan_1thn_rev = 0.0
    total_prognosa = 0.0
    total_tpc_awal = 0.0
    total_tpc_revisi = 0.0

    real_monthly = [0.0] * 12
    prog_monthly = [0.0] * 12
    prog_kum_monthly = [0.0] * 12

    by_status: dict[str, int] = defaultdict(int)
    by_dept: dict[str, int] = defaultdict(int)
    by_kategori: dict[str, int] = defaultdict(int)
    by_klasifikasi: dict[str, int] = defaultdict(int)
    by_rutin: dict[str, int] = defaultdict(int)
    by_planned: dict[str, int] = defaultdict(int)
    by_asset: dict[str, int] = defaultdict(int)
    by_gl: dict[str, int] = defaultdict(int)

    dept_alokasi: dict[str, float] = defaultdict(float)
    gl_alokasi: dict[str, float] = defaultdict(float)
    asset_alokasi: dict[str, float] = defaultdict(float)

    for p in projects:
        total_alokasi += p["alokasi_update"]
        total_kebutuhan_1thn += p["kebutuhan_1thn"]
        total_kebutuhan_1thn_rev += p["kebutuhan_1thn_rev"]
        total_prognosa += p["prog_total"]
        total_tpc_awal += p["tpc_awal"]
        total_tpc_revisi += p["tpc_revisi"]

        for i, v in enumerate(p["real"]):
            real_monthly[i] += v
        for i, v in enumerate(p["prog"]):
            prog_monthly[i] += v
        for i, v in enumerate(p["prog_kum"]):
            prog_kum_monthly[i] += v

        by_status[p["status"] or "(lainnya)"] += 1
        by_dept[p["dept"] or "(lainnya)"] += 1
        by_kategori[p["kategori"] or "(lainnya)"] += 1
        by_klasifikasi[p["klasifikasi"] or "(lainnya)"] += 1
        by_rutin[p["rutin"] or "(lainnya)"] += 1
        by_planned[p["planned"] or "(lainnya)"] += 1
        by_asset[p["asset_class"] or "(lainnya)"] += 1
        by_gl[p["nama_gl"] or "(lainnya)"] += 1

        dept_alokasi[p["dept"] or "(lainnya)"] += p["alokasi_update"]
        gl_alokasi[p["nama_gl"] or "(lainnya)"] += p["alokasi_update"]
        asset_alokasi[p["asset_class"] or "(lainnya)"] += p["alokasi_update"]

    return {
        "total_alokasi": total_alokasi,
        "total_kebutuhan_1thn": total_kebutuhan_1thn,
        "total_kebutuhan_1thn_rev": total_kebutuhan_1thn_rev,
        "total_prognosa": total_prognosa,
        "total_tpc_awal": total_tpc_awal,
        "total_tpc_revisi": total_tpc_revisi,
        "real_monthly": real_monthly,
        "prog_monthly": prog_monthly,
        "prog_kum_monthly": prog_kum_monthly,
        "by_status": dict(by_status),
        "by_dept": dict(by_dept),
        "by_kategori": dict(by_kategori),
        "by_klasifikasi": dict(by_klasifikasi),
        "by_rutin": dict(by_rutin),
        "by_planned": dict(by_planned),
        "by_asset": dict(by_asset),
        "by_gl": dict(by_gl),
        "dept_alokasi": dict(dept_alokasi),
        "gl_alokasi": dict(gl_alokasi),
        "asset_alokasi": dict(asset_alokasi),
    }


def _cumulative(series: list[float]) -> list[float]:
    out = []
    acc = 0.0
    for v in series:
        acc += v
        out.append(acc)
    return out


def _top_n(d: dict, n: int) -> list[list]:
    items = sorted(d.items(), key=lambda kv: -kv[1])[:n]
    return [[k, v] for k, v in items]


def _sorted_dict_values(d: dict) -> list[list]:
    items = sorted(d.items(), key=lambda kv: -kv[1])
    return [[k, v] for k, v in items]


def _build_heatmap(projects: list[dict]) -> dict:
    dept_map: dict[str, list[float]] = {}
    for p in projects:
        d = p.get("dept") or "(lainnya)"
        if d not in dept_map:
            dept_map[d] = [0.0] * 12
        for i, v in enumerate(p["real"]):
            dept_map[d][i] += v
    # Keep only depts with any realization
    depts = [d for d, vals in dept_map.items() if any(v > 0 for v in vals)]
    depts.sort()
    data = []
    for i, d in enumerate(depts):
        for m in range(12):
            data.append([m, i, dept_map[d][m]])
    return {"depts": depts, "months": MONTHS, "data": data}


# ---------------------------------------------------------------------------
# Switching parse (from keterangan text)
# ---------------------------------------------------------------------------

_SW_RE = re.compile(
    r"(Bertambah|Berkurang)[^.]*?Rp\s*([\d.,]+)[^()]*\(([^)]+)\)",
    re.IGNORECASE,
)


def _extract_switching_pairs(projects: list[dict]) -> list[dict]:
    id_map = {p["id_rka_ti"]: p for p in projects if p.get("id_rka_ti")}

    pairs: dict[tuple[str, str], float] = {}

    for p in projects:
        for log in p.get("switching_log", []):
            desc = log.get("desc", "") if isinstance(log, dict) else ""
            if not desc:
                continue
            m = _SW_RE.search(desc)
            if not m:
                continue
            direction = m.group(1).lower()
            raw_amt = m.group(2).replace(".", "").replace(",", ".")
            try:
                amount = float(raw_amt)
            except ValueError:
                continue
            if not amount:
                continue

            other_id_raw = m.group(3).strip()
            # Try to match trailing RKA id inside parens
            other_id = other_id_raw
            other = id_map.get(other_id)
            if other is None:
                # Sometimes "2026 XXX INF 2026-INF-X.YY.ZZ" format
                for key in id_map:
                    if key and key in other_id_raw:
                        other = id_map[key]
                        break
            other_name = other["name"] if other else other_id_raw

            if direction.startswith("bertambah"):
                src, tgt = other_name, p["name"]
            else:
                src, tgt = p["name"], other_name

            key = (src, tgt)
            if key in pairs:
                pairs[key] = max(pairs[key], amount)
            else:
                pairs[key] = amount

    result = [{"source": s, "target": t, "value": v} for (s, t), v in pairs.items() if v > 0]
    result.sort(key=lambda x: -x["value"])
    return result[:30]


# ---------------------------------------------------------------------------
# Multi-year estimation from text
# ---------------------------------------------------------------------------

_YEAR_RE = re.compile(r"tahun\s*(20\d\d)\s*:?\s*Rp\s*([\d.,]+)", re.IGNORECASE)


def _extract_year_estimations(projects: list[dict]) -> tuple[dict, dict]:
    year_totals: dict[int, float] = {}
    year_entries: dict[int, list[dict]] = {}

    for p in projects:
        blobs = [p.get("keterangan_revisi") or "", p.get("catatan") or ""]
        for log in p.get("switching_log", []):
            if isinstance(log, dict):
                blobs.append(log.get("desc", ""))
        text = "\n".join(blobs)
        for m in _YEAR_RE.finditer(text):
            try:
                year = int(m.group(1))
                raw = m.group(2).replace(".", "").replace(",", ".")
                amt = float(raw)
            except (ValueError, TypeError):
                continue
            if not amt:
                continue
            year_totals[year] = year_totals.get(year, 0.0) + amt
            year_entries.setdefault(year, []).append({
                "id_rka_ti": p.get("id_rka_ti", ""),
                "name": p.get("name", ""),
                "dept": p.get("dept", ""),
                "amount": amt,
            })
    for y in year_entries:
        year_entries[y].sort(key=lambda e: -e["amount"])
    return year_totals, year_entries


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------

def _safe_json(obj) -> str:
    """Serialize to JSON safe for HTML embedding (</script>-proof)."""
    def default(o):
        try:
            return float(o)
        except Exception:
            return str(o)
    text = json.dumps(obj, ensure_ascii=False, default=default)
    # Escape anything that could break out of <script>
    text = text.replace("</", "<\\/")
    text = text.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return text
