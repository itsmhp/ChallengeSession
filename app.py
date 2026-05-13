"""
Challenge Session Dashboard — PySide6 Desktop GUI
==================================================
Entry point: python app.py

Reads the Challenge Session Excel file locally (no browser upload — DLP safe),
processes it, and generates an interactive HTML dashboard.
"""

import sys
import os
import webbrowser
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QProgressBar, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPalette

from core.parser_challenge import parse_challenge_session
from core.builder import build_context

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_TITLE = "Challenge Session Dashboard"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "PMO Infrastruktur · IT Directorate BRI"

BRI_BLUE = "#00529C"
BRI_BLUE_DARK = "#003F7A"
BRI_ORANGE = "#F37021"
BRI_BG = "#F0F4F8"
BRI_CARD = "#FFFFFF"
BRI_BORDER = "#E2ECF4"
BRI_TEXT = "#0D1F35"
BRI_TEXT2 = "#435770"
BRI_TEXT3 = "#8FA5BE"

OUTPUT_DIR = Path(__file__).parent / "output"
TEMPLATE_PATH = OUTPUT_DIR / "dashboard_template.html"


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class ProcessWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            self.progress.emit(10, "Membaca file Excel…")
            parsed = parse_challenge_session(self.filepath)

            self.progress.emit(40, f"Ditemukan {len(parsed['projects'])} proyek. Menghitung aggregasi…")
            context = build_context(
                parsed,
                source_file=Path(self.filepath).name,
            )

            self.progress.emit(70, "Rendering dashboard HTML…")
            output_path = self._render_dashboard(context)

            self.progress.emit(100, "Selesai!")
            self.finished.emit(str(output_path))

        except Exception as e:
            self.error.emit(str(e))

    def _render_dashboard(self, context: dict) -> Path:
        """
        Inject parsed data into the existing dashboard.html.
        Strategy: Read dashboard.html, replace the file-upload/parsing section
        with pre-loaded data, so it renders immediately without user interaction.
        """
        import json

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Read the base dashboard HTML
        base_html_path = Path(__file__).parent / "dashboard.html"
        if not base_html_path.exists():
            raise FileNotFoundError(f"Base dashboard.html not found at {base_html_path}")

        html = base_html_path.read_text(encoding="utf-8")

        # Build the injection script that auto-loads data
        projects_json = context["json_projects"]
        totals_json = context["json_totals"]
        cutoff = context["cutoff_month"]
        source = context.get("source_file", "")
        period = context.get("period_label", "")

        inject_script = f"""
<script>
// === AUTO-INJECTED BY app.py — data pre-loaded, skip file upload ===
(function() {{
  var _injectedData = {{
    projects: {projects_json},
    cutoff_month: {cutoff},
    source_file: "{source}",
    period_label: "{period}"
  }};
  window.__INJECTED_DATA__ = _injectedData;
}})();
</script>
"""

        # Also inject an auto-start script that triggers processing after page load
        auto_start = """
<script>
// Auto-start: if injected data exists, skip upload and render directly
document.addEventListener('DOMContentLoaded', function() {
  if (!window.__INJECTED_DATA__) return;
  var data = window.__INJECTED_DATA__;

  // Simulate what processBtn click does, but with pre-parsed data
  // We need to wait for the IIFE to set up state
  setTimeout(function() {
    // Access the state object via a hook we'll add
    if (window.__autoRender) window.__autoRender(data);
  }, 100);
});
</script>
"""

        # Insert injection before closing </body>
        html = html.replace("</body>", inject_script + auto_start + "</body>")

        # Add the __autoRender hook inside the main IIFE
        # Insert just before the closing })(); of the IIFE
        hook_code = """

// === AUTO-RENDER HOOK (injected by app.py) ===
window.__autoRender = function(data) {
  // Parse projects same way as processBtn handler
  state.rows = data.projects.map(function(p, idx) {
    // Convert Python dict format to match JS expected format
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
    // Getter-like computed
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
        # Insert hook before the IIFE closing
        html = html.replace("})(); // IIFE end", hook_code + "})(); // IIFE end")

        # Hide the landing page by default when data is injected
        html = html.replace(
            '<main class="landing" id="landing">',
            '<main class="landing hidden" id="landing">'
        )
        # Show topbar by default
        html = html.replace(
            '<header class="topbar" id="topbar" style="display:none;">',
            '<header class="topbar" id="topbar">'
        )
        # Show dashboard by default
        html = html.replace(
            '<main class="main hidden" id="dashboard">',
            '<main class="main" id="dashboard">'
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dashboard_CS_{timestamp}.html"
        output_path = OUTPUT_DIR / filename
        output_path.write_text(html, encoding="utf-8")

        # Create latest alias
        latest = OUTPUT_DIR / "dashboard_latest.html"
        latest.write_text(html, encoding="utf-8")

        return output_path


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.setMinimumSize(680, 480)
        self.setStyleSheet(f"""
            QMainWindow {{ background: {BRI_BG}; }}
        """)

        self.filepath = ""
        self.output_path = ""
        self.worker = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BRI_BLUE_DARK}, stop:1 {BRI_BLUE});
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        logo = QLabel("CS")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"""
            QLabel {{
                background: rgba(255,255,255,0.15);
                color: white;
                font-size: 13px;
                font-weight: 800;
                border-radius: 8px;
            }}
        """)
        h_layout.addWidget(logo)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_lbl = QLabel(APP_TITLE)
        title_lbl.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        subtitle_lbl = QLabel(APP_SUBTITLE)
        subtitle_lbl.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px;")
        title_block.addWidget(title_lbl)
        title_block.addWidget(subtitle_lbl)
        h_layout.addLayout(title_block)
        h_layout.addStretch()

        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px;")
        h_layout.addWidget(ver_lbl)

        layout.addWidget(header)

        # Body card
        body = QWidget()
        body.setStyleSheet(f"""
            QWidget {{
                background: {BRI_BG};
            }}
        """)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(32, 28, 32, 28)
        body_layout.setSpacing(20)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BRI_CARD};
                border: 1px solid {BRI_BORDER};
                border-radius: 16px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        # Section: File input
        sec_title = QLabel("📁 Input File")
        sec_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {BRI_TEXT}; border: none;")
        card_layout.addWidget(sec_title)

        sec_desc = QLabel("Pilih file Challenge Session Excel (.xlsx). File dibaca lokal — tidak dikirim ke server.")
        sec_desc.setStyleSheet(f"font-size: 12px; color: {BRI_TEXT2}; border: none;")
        sec_desc.setWordWrap(True)
        card_layout.addWidget(sec_desc)

        # File row
        file_row = QHBoxLayout()
        file_row.setSpacing(10)

        badge = QLabel("1")
        badge.setFixedSize(26, 26)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background: {BRI_BLUE};
                color: white;
                font-size: 12px;
                font-weight: 700;
                border-radius: 13px;
                border: none;
            }}
        """)
        file_row.addWidget(badge)

        self.file_label = QLabel("Belum ada file dipilih")
        self.file_label.setStyleSheet(f"""
            QLabel {{
                background: {BRI_BG};
                border: 1px solid {BRI_BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 12px;
                color: {BRI_TEXT2};
            }}
        """)
        self.file_label.setMinimumHeight(40)
        file_row.addWidget(self.file_label, 1)

        browse_btn = QPushButton("Pilih File")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BRI_BG};
                border: 1px solid {BRI_BORDER};
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 12px;
                font-weight: 600;
                color: {BRI_TEXT};
            }}
            QPushButton:hover {{
                background: {BRI_BORDER};
                border-color: {BRI_BLUE};
                color: {BRI_BLUE};
            }}
        """)
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)

        card_layout.addLayout(file_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {BRI_BORDER}; border: none; max-height: 1px;")
        card_layout.addWidget(sep)

        # Process button
        self.process_btn = QPushButton("▶  Process & Generate Dashboard")
        self.process_btn.setCursor(Qt.PointingHandCursor)
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumHeight(48)
        self.process_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BRI_BLUE}, stop:1 {BRI_BLUE_DARK});
                color: white;
                font-size: 14px;
                font-weight: 700;
                border-radius: 10px;
                border: none;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BRI_BLUE_DARK}, stop:1 #002D58);
            }}
            QPushButton:disabled {{
                background: {BRI_BORDER};
                color: {BRI_TEXT3};
            }}
        """)
        self.process_btn.clicked.connect(self._process)
        card_layout.addWidget(self.process_btn)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {BRI_BG};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {BRI_ORANGE};
                border-radius: 3px;
            }}
        """)
        card_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 11px; color: {BRI_TEXT3}; border: none;")
        self.status_label.setVisible(False)
        card_layout.addWidget(self.status_label)

        # Open button (hidden until done)
        self.open_btn = QPushButton("🌐  Buka Dashboard")
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.setVisible(False)
        self.open_btn.setMinimumHeight(44)
        self.open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BRI_ORANGE};
                color: white;
                font-size: 13px;
                font-weight: 700;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background: #D85A10;
            }}
        """)
        self.open_btn.clicked.connect(self._open_dashboard)
        card_layout.addWidget(self.open_btn)

        body_layout.addWidget(card)

        # Footer
        footer = QLabel("© 2026 PT Bank Rakyat Indonesia — PMO Infrastruktur, IT Directorate")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"font-size: 10px; color: {BRI_TEXT3};")
        body_layout.addWidget(footer)

        layout.addWidget(body, 1)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih file Challenge Session Excel",
            "",
            "Excel Files (*.xlsx *.xls *.xlsm);;All Files (*)",
        )
        if path:
            self.filepath = path
            self.file_label.setText(Path(path).name)
            self.file_label.setStyleSheet(f"""
                QLabel {{
                    background: {BRI_BG};
                    border: 1px solid {BRI_BLUE};
                    border-radius: 8px;
                    padding: 10px 14px;
                    font-size: 12px;
                    color: {BRI_TEXT};
                    font-weight: 500;
                }}
            """)
            self.process_btn.setEnabled(True)
            self.open_btn.setVisible(False)

    def _process(self):
        if not self.filepath:
            return

        if not TEMPLATE_PATH.exists():
            QMessageBox.critical(
                self, "Template Tidak Ditemukan",
                f"File template tidak ditemukan:\n{TEMPLATE_PATH}\n\n"
                "Pastikan file output/dashboard_template.html ada."
            )
            return

        self.process_btn.setEnabled(False)
        self.open_btn.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Memulai…")
        self.status_label.setStyleSheet(f"font-size: 11px; color: {BRI_ORANGE}; border: none;")

        self.worker = ProcessWorker(self.filepath)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_finished(self, output_path: str):
        self.output_path = output_path
        self.progress_bar.setValue(100)
        self.status_label.setText(f"✓ Dashboard berhasil dibuat: {Path(output_path).name}")
        self.status_label.setStyleSheet(f"font-size: 11px; color: #15803D; border: none; font-weight: 600;")
        self.process_btn.setEnabled(True)
        self.open_btn.setVisible(True)

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✗ Error: {msg}")
        self.status_label.setStyleSheet(f"font-size: 11px; color: #DC2626; border: none;")
        self.process_btn.setEnabled(True)

    def _open_dashboard(self):
        if self.output_path and Path(self.output_path).exists():
            webbrowser.open(Path(self.output_path).as_uri())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Inter", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
