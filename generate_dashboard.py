"""
generate_dashboard.py
---------------------
CLI alternative to app.py — generate dashboard without GUI.

Usage:
    python generate_dashboard.py "Challenge Session.xlsx"
    python generate_dashboard.py path/to/file.xlsx
"""

import sys
import webbrowser
from pathlib import Path
from datetime import datetime

from core.parser_challenge import parse_challenge_session
from core.builder import build_context

OUTPUT_DIR = Path(__file__).parent / "output"
TEMPLATE_PATH = OUTPUT_DIR / "dashboard_template.html"


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_dashboard.py <path_to_excel>")
        print("Example: python generate_dashboard.py 'Challenge Session.xlsx'")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    if not TEMPLATE_PATH.exists():
        print(f"ERROR: Template not found: {TEMPLATE_PATH}")
        print("Make sure output/dashboard_template.html exists.")
        sys.exit(1)

    print(f"[1/3] Parsing: {filepath.name}")
    parsed = parse_challenge_session(str(filepath))
    print(f"      -> {len(parsed['projects'])} proyek ditemukan (sheet: {parsed['sheet_name']})")
    print(f"      -> Cut-off bulan: {parsed['cutoff_month'] + 1}")

    print("[2/3] Building context & aggregations…")
    context = build_context(parsed, source_file=filepath.name)
    print(f"      -> Total alokasi: Rp {context['totals']['alokasi']:,.0f}")
    print(f"      -> Total realisasi YTD: Rp {context['totals']['realisasi_ytd']:,.0f}")

    print("[3/3] Rendering dashboard HTML…")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Read base dashboard.html and inject data
    base_html = Path(__file__).parent / "dashboard.html"
    if not base_html.exists():
        print(f"ERROR: dashboard.html not found at {base_html}")
        sys.exit(1)

    html = base_html.read_text(encoding="utf-8")

    # Inject data
    import json
    projects_json = context["json_projects"]
    cutoff = context["cutoff_month"]

    inject_script = f"""
<script>
(function() {{
  window.__INJECTED_DATA__ = {{
    projects: {projects_json},
    cutoff_month: {cutoff},
    source_file: "{filepath.name}",
    period_label: "{context['period_label']}"
  }};
}})();
</script>
<script>
document.addEventListener('DOMContentLoaded', function() {{
  if (!window.__INJECTED_DATA__) return;
  setTimeout(function() {{
    if (window.__autoRender) window.__autoRender(window.__INJECTED_DATA__);
  }}, 100);
}});
</script>
"""
    html = html.replace("</body>", inject_script + "</body>")

    # Add auto-render hook (same as app.py)
    hook_code = """
window.__autoRender = function(data) {
  state.rows = data.projects.map(function(p, idx) {
    p.rowIdx = idx;
    p.real = p.real || [0,0,0,0,0,0,0,0,0,0,0,0];
    p.prog = p.prog || [0,0,0,0,0,0,0,0,0,0,0,0];
    p.progKum = p.prog_kum || [0,0,0,0,0,0,0,0,0,0,0,0];
    p.realisasi = p.real_total || 0;
    p.prognosaTotal = p.prog_total || 0;
    p.alokasiUpdate = p.alokasi_update || 0;
    p.nominalSwitching = p.nominal_switching || 0;
    p.kebutuhan1Thn = p.kebutuhan_1thn || 0;
    p.kebutuhan1ThnRev = p.kebutuhan_1thn_rev || 0;
    p.tpcAwal = p.tpc_awal || 0;
    p.tpcRevisi = p.tpc_revisi || 0;
    p.nominalMinAlokasi = p.nominal_min_alokasi || 0;
    p.selisihAlokasi = p.selisih_alokasi || 0;
    p.nominalSpk = p.nominal_spk || 0;
    p.idRka2026 = p.id_rka_ti || '';
    p.parentChild = p.parent_child || '';
    p.namaGL = p.nama_gl || '';
    p.assetClass = p.asset_class || '';
    p.idAsset = p.id_asset || '';
    p.idRka2025 = p.id_rka_2025 || '';
    p.kodeNomor = p.kode_nomor || '';
    p.nameAwal = p.name_awal || '';
    p.nameRev = p.name_rev || '';
    p.keteranganRevisi = p.keterangan_revisi || '';
    p.updateProgress = p.update_progress || '';
    p.notaDinas = p.nota_dinas || '';
    p.namaAplikasi = p.nama_aplikasi || '';
    p.grpAplikasi = p.grp_aplikasi || '';
    p.fungsiTim = p.fungsi_tim || '';
    p.siRbb = p.si_rbb || '';
    p.programKerja = p.program_kerja || '';
    p.nomorSpk = p.nomor_spk || '';
    p.namaSpk = p.nama_spk || '';
    p.spkMulai = p.spk_mulai || '';
    p.spkSelesai = p.spk_selesai || '';
    p.statusRaw = p.status_raw || '';
    p.switchingLog = (p.switching_log || []);
    p.changeType = p.change_type || 'Tidak berubah';
    p.serapanPct = p.serapan_pct || 0;
    Object.defineProperty(p, 'serapanPct', {
      get: function() { return this.alokasiUpdate > 0 ? (this.realisasi / this.alokasiUpdate * 100) : 0; },
      configurable: true
    });
    return p;
  });
  state.cutoffMonth = data.cutoff_month;
  renderDashboard();
};
"""
    html = html.replace("})(); // IIFE end", hook_code + "})(); // IIFE end")
    html = html.replace('<main class="landing" id="landing">', '<main class="landing hidden" id="landing">')
    html = html.replace('<header class="topbar" id="topbar" style="display:none;">', '<header class="topbar" id="topbar">')
    html = html.replace('<main class="main hidden" id="dashboard">', '<main class="main" id="dashboard">')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dashboard_CS_{timestamp}.html"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(html, encoding="utf-8")

    latest = OUTPUT_DIR / "dashboard_latest.html"
    latest.write_text(html, encoding="utf-8")

    print(f"\n[OK] Dashboard generated: {output_path}")
    print(f"  Alias: {latest}")

    # Auto-open
    try:
        webbrowser.open(output_path.as_uri())
        print("  -> Opened in browser")
    except Exception:
        print("  -> Open manually in browser")


if __name__ == "__main__":
    main()
