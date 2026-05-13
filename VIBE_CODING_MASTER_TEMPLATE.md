# Vibe Coding Master Template
## VSCode GitHub Copilot — Token-Efficient Workflow

---

# BAGIAN 1 — PRINSIP HEMAT TOKEN

## Aturan Emas

1. **Satu chat = satu task**. Jangan campurkan "bikin auth" dan "bikin dashboard"
   dalam satu sesi. Context yang membengkak = token yang terbuang.

2. **File beats description**. Daripada mendeskripsikan struktur kode ke AI,
   gunakan `#file:src/components/Button.tsx` agar AI baca langsung.

3. **Buat SPEC.md sebelum mulai coding**. AI tidak perlu "menemukan" konteks
   di setiap sesi — tinggal baca satu file.

4. **Pakai model yang tepat untuk task yang tepat** (lihat Bagian 2).

5. **Clear chat setelah setiap task selesai**. Context lama = token terbuang
   di prompt berikutnya.

6. **Jangan tanya, instruksikan**. "Buatkan komponen login form" lebih hemat
   dari "Menurut kamu bagaimana cara terbaik membuat login form di React?"

---

# BAGIAN 2 — PANDUAN PEMILIHAN MODEL

## Tabel Referensi Cepat

| Task | Model Terbaik | Multiplier | Alasan |
|------|--------------|------------|--------|
| Eksplorasi file / baca codebase | GPT-4.1 | 0x (GRATIS) | Cukup pintar, gratis |
| Boilerplate / CRUD sederhana | GPT-5 mini | 0x (GRATIS) | Cepat, gratis |
| Fix bug sederhana | GPT-4.1 | 0x (GRATIS) | Tidak perlu overkill |
| Tulis unit test | GPT-5 mini | 0x (GRATIS) | Repetitif, gratis |
| Coding fitur standar | Claude Sonnet 4.6 | 1x | Terbaik untuk coding sehari-hari |
| Coding + context library besar | Claude Sonnet 4.6 + Context7 | 1x | Akurat, hemat revisi |
| Debugging kompleks | Claude Sonnet 4.6 + Seq.Thinking | 1x | Analisis mendalam |
| Arsitektur sistem baru | Claude Opus 4.6 | 3x | Gunakan HANYA untuk planning |
| Refactor skala besar | GPT-5.2-Codex | 1x | Context 400K, ideal untuk banyak file |
| Multi-file editing | GPT-5.2-Codex | 1x | Context window terbesar (400K) |

## Strategi Kunci: "Pakai yang Gratis Dulu"

GPT-4.1, GPT-4o, dan GPT-5 mini adalah 0x multiplier = tidak memotong kuota.
Gunakan ini untuk semua task yang tidak butuh reasoning mendalam.
Simpan Sonnet 4.6 untuk logic kompleks. Opus 4.6 HANYA untuk planning awal.

---

# BAGIAN 3 — FILE WAJIB SEBELUM MULAI CODING

## Struktur Folder yang Harus Ada

```
project-kamu/
├── .github/
│   └── copilot-instructions.md    ← Dibaca Copilot otomatis setiap sesi
├── .vscode/
│   └── mcp.json                   ← Konfigurasi semua MCP agent
├── docs/
│   └── SPEC.md                    ← Blueprint project (buat sebelum coding)
└── src/
```

---

# BAGIAN 4 — TEMPLATE: SPEC.md

> Buat file ini SEBELUM prompt coding pertama.
> Copy template ini, isi bagian yang bertanda [GANTI], hapus yang tidak relevan.

```markdown
# Project Spec: [NAMA PROJECT]

## Overview
[1-2 kalimat: apa yang dibangun dan untuk siapa]

## Tech Stack
- Framework: [Next.js 15 App Router / React / Vue / Express / dll]
- Language: [TypeScript / JavaScript]
- Database: [Supabase / PostgreSQL / SQLite / MongoDB]
- Auth: [Supabase Auth / Clerk / NextAuth]
- Styling: [Tailwind CSS / shadcn/ui / MUI]
- Deployment: [Vercel / Railway / VPS]

## Struktur Folder
src/
├── app/              # Next.js pages & layouts
├── components/
│   ├── ui/           # Komponen generik (Button, Input, Modal)
│   └── features/     # Komponen spesifik fitur
├── actions/          # Server actions
├── lib/              # Utilities & config
└── types/            # TypeScript types

## Fitur yang Dibangun
- [ ] [Fitur 1]
- [ ] [Fitur 2]
- [ ] [Fitur 3]

## Batasan & Aturan Kode
- [Contoh: Semua fetch data harus lewat Server Component]
- [Contoh: Jangan pakai useEffect untuk data fetching]
- [Contoh: Semua form harus pakai Server Action]
- [Contoh: Warna utama: #00529C, accent: #F37021]

## Environment Variables yang Dipakai
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
[tambah sesuai kebutuhan]

## Yang TIDAK Boleh Dilakukan AI
- Jangan pakai pages/ router (pakai app/ router)
- Jangan hardcode warna, selalu pakai CSS variable atau Tailwind class
- Jangan taruh logic di page.tsx, pisahkan ke komponen
- Jangan pakai `any` di TypeScript
```

---

# BAGIAN 5 — TEMPLATE: copilot-instructions.md

> Simpan di `.github/copilot-instructions.md`
> File ini dibaca otomatis Copilot di setiap sesi — tidak perlu disebut di prompt.

```markdown
# GitHub Copilot Instructions

## Project Context
Baca file `docs/SPEC.md` untuk memahami konteks lengkap project ini
sebelum memulai task apapun.

## Aturan Wajib
- Selalu gunakan `use context7` untuk task yang menyebut nama library
- Gunakan `#sequential-thinking` untuk task debugging dan arsitektur
- Jangan pernah hardcode credentials atau API key
- Selalu gunakan TypeScript strict mode
- Tambahkan error handling di setiap server action dan API call

## Cara Menambah MCP Agent Baru
Jika diminta menambahkan agent, edit `.vscode/mcp.json` dengan format:
{
  "servers": {
    "nama-agent": {
      "command": "npx",
      "args": ["-y", "nama-package-mcp"]
    }
  }
}
Ingatkan user untuk reload VSCode setelah perubahan.

## Daftar Agent & Package
- sequential-thinking → @modelcontextprotocol/server-sequential-thinking
- context7           → @upstash/context7-mcp
- filesystem         → @modelcontextprotocol/server-filesystem
- github             → @modelcontextprotocol/server-github
- playwright         → @playwright/mcp
- memory             → @modelcontextprotocol/server-memory
- fetch              → @modelcontextprotocol/server-fetch
- brave-search       → @modelcontextprotocol/server-brave-search
- sqlite             → @modelcontextprotocol/server-sqlite
- postgres           → @modelcontextprotocol/server-postgres
- supabase           → @supabase/mcp-server-supabase@latest
```

---

# BAGIAN 6 — TEMPLATE PROMPT LENGKAP

---

## PROMPT 0 — Setup Project (Gunakan: Claude Opus 4.6)

> Pakai SEKALI di awal project. Ini satu-satunya saat Opus worth it
> karena hasilnya dipakai sepanjang project.

```
Saya akan membangun aplikasi dengan spesifikasi berikut. Bantu saya
membuat fondasi project yang solid.

## Deskripsi Project
[Jelaskan aplikasi yang ingin dibangun dalam 3-5 kalimat]

## Tech Stack yang Ingin Dipakai
- [sebutkan stack, contoh: Next.js 15, Supabase, Tailwind, TypeScript]

## Target Pengguna
[Siapa yang akan pakai aplikasi ini]

## Fitur Utama (prioritas tinggi ke rendah)
1. [Fitur 1]
2. [Fitur 2]
3. [Fitur 3]

Tugas kamu:
1. Buat file `docs/SPEC.md` yang lengkap berisi: overview, tech stack,
   struktur folder yang direkomendasikan, daftar fitur, batasan kode,
   dan environment variables yang dibutuhkan
2. Buat file `.github/copilot-instructions.md` yang berisi instruksi
   untuk Copilot di sesi berikutnya
3. Buat file `.vscode/mcp.json` dengan agent-agent yang relevan untuk
   project ini. Aktifkan minimal: filesystem, sequential-thinking, context7.
   Tambahkan agent lain sesuai kebutuhan stack.
4. Buat `package.json` dan jalankan perintah init project

Setelah selesai, berikan ringkasan: apa yang sudah dibuat dan
langkah manual apa yang harus saya lakukan (install deps, isi env, dll).
```

---

## PROMPT 1 — Inisialisasi Struktur Project (Gunakan: GPT-5.2-Codex)

> Setelah SPEC.md ada. GPT-5.2-Codex punya 400K context dan gratis
> untuk task struktur yang banyak file tapi tidak butuh reasoning dalam.

```
Baca #file:docs/SPEC.md

Berdasarkan spec tersebut, buat struktur folder lengkap project ini:
1. Buat semua folder yang diperlukan
2. Buat file-file boilerplate: layout.tsx, page.tsx utama, globals.css,
   tailwind.config.ts, tsconfig.json, next.config.ts
3. Buat file `src/lib/supabase/client.ts` dan `server.ts` [sesuaikan
   dengan database yang dipakai]
4. Buat file `src/types/index.ts` dengan type dasar yang diperlukan
5. Buat file `.env.example` berisi semua environment variable

Jangan isi logic bisnis dulu — fokus ke scaffolding dan konfigurasi.
```

---

## PROMPT 2 — Desain Database / Schema (Gunakan: Claude Sonnet 4.6)

```
#sequential-thinking
Baca #file:docs/SPEC.md

Berdasarkan fitur-fitur di spec, rancang schema database yang optimal:
1. Identifikasi semua entitas dan relasinya
2. Buat SQL migration file di `supabase/migrations/001_initial_schema.sql`
3. Sertakan: tabel, relasi (foreign key), indexes, RLS policies dasar
4. Buat file `src/types/database.ts` berisi TypeScript types yang
   merepresentasikan schema tersebut

Pertimbangkan: query yang akan sering dijalankan, dan pastikan
ada index untuk kolom yang sering di-filter atau di-join.
use context7
```

---

## PROMPT 3 — Implementasi Fitur (Template, Gunakan: Claude Sonnet 4.6)

> Copy dan sesuaikan untuk setiap fitur baru.

```
Baca #file:docs/SPEC.md
Baca #file:src/types/database.ts

Implementasikan fitur: [NAMA FITUR]

Scope task ini:
- [ ] [Komponen atau file spesifik yang perlu dibuat]
- [ ] [Server action yang perlu dibuat]
- [ ] [Query database yang diperlukan]

Requirement spesifik:
- [Contoh: Form submit harus pakai Server Action, bukan API route]
- [Contoh: Tampilkan loading state saat fetch]
- [Contoh: Handle error dan tampilkan pesan yang user-friendly]

Referensi komponen yang sudah ada:
#file:src/components/ui/[komponen-relevan].tsx

Jangan buat file di luar scope di atas.
use context7
```

---

## PROMPT 4 — Debugging (Gunakan: Claude Sonnet 4.6 + Sequential Thinking)

```
#sequential-thinking

Saya mengalami bug berikut:

## Error Message
[paste error message lengkap]

## Konteks
- Ini terjadi ketika: [describe user action]
- Di file: #file:[path/ke/file/bermasalah]
- Sudah dicoba: [apa yang sudah dicoba tapi gagal]

## File Terkait
#file:[file 1]
#file:[file 2]

Analisis root cause secara sistematis, jelaskan kenapa bug ini terjadi,
lalu berikan fix yang tepat beserta penjelasan mengapa fix itu benar.
```

---

## PROMPT 5 — Refactor (Gunakan: GPT-5.2-Codex)

> GPT-5.2-Codex ideal karena context 400K bisa tampung banyak file sekaligus.

```
Baca semua file di #file:src/components/

Lakukan refactor untuk:
[pilih satu atau lebih]
- [ ] Eliminasi duplikasi logika, jadikan shared hook/util
- [ ] Perbaiki TypeScript types, hilangkan semua `any`
- [ ] Pisahkan komponen yang terlalu besar (>200 baris) jadi sub-komponen
- [ ] Standardisasi naming convention sesuai #file:docs/SPEC.md

Jangan ubah behavior atau tampilan, hanya struktur kode.
Setelah selesai, list semua file yang diubah beserta ringkasan perubahannya.
```

---

## PROMPT 6 — Tulis Unit Test (Gunakan: GPT-5 mini — GRATIS)

```
Baca #file:[path/ke/file/yang/mau/dites]

Tulis unit test untuk semua fungsi dan komponen di file tersebut.
Gunakan [Vitest / Jest] dengan [React Testing Library untuk komponen].

Coverage yang harus ada:
- Happy path (input valid, output sesuai ekspektasi)
- Edge case (input kosong, nilai ekstrem)
- Error case (input invalid, network error)

Simpan di [__tests__/nama-file.test.ts]
```

---

## PROMPT 7 — Code Review & Security Audit (Gunakan: Claude Opus 4.6)

> Gunakan sebelum deploy ke production. Opus untuk ini worth it
> karena menemukan masalah yang tidak terlihat oleh model lebih kecil.

```
#sequential-thinking

Lakukan security audit dan code review menyeluruh pada:
#file:src/actions/
#file:src/app/api/
#file:src/lib/

Periksa:
1. SQL injection vulnerability (pastikan semua query pakai parameterized)
2. Autentikasi — apakah semua endpoint yang sensitif dilindungi?
3. Authorization — apakah ada RLS bypass yang mungkin terjadi?
4. Input validation — apakah semua user input divalidasi server-side?
5. Exposed secrets — apakah ada credential yang tidak sengaja masuk kode?
6. Rate limiting — endpoint mana yang rentan abuse?
7. Error messages — apakah error message tidak leak informasi sensitif?

Untuk setiap masalah yang ditemukan:
- Sebutkan file dan baris yang bermasalah
- Jelaskan risiko spesifiknya
- Berikan fix yang konkret
```

---

## PROMPT 8 — Optimasi Performance (Gunakan: Claude Sonnet 4.6)

```
#sequential-thinking
Baca #file:docs/SPEC.md

Analisis dan optimalkan performa aplikasi ini:
#file:src/app/
#file:src/components/

Fokus pada:
1. Identifikasi komponen yang seharusnya Server Component tapi masih Client
2. Query N+1 problem di data fetching
3. Bundle size — import yang bisa dilakukan secara lazy
4. Image optimization
5. Caching strategy yang tepat (unstable_cache, revalidate)

Berikan rekomendasi terurut dari impact tertinggi ke terendah.
use context7
```

---

## PROMPT 9 — Dokumentasi (Gunakan: GPT-4.1 — GRATIS)

```
Baca semua file di #file:src/

Buat dokumentasi teknis di `docs/TECHNICAL.md` yang mencakup:
1. Cara setup project dari awal (clone → install → env → run)
2. Penjelasan struktur folder
3. Cara menambah fitur baru (step-by-step)
4. Daftar semua environment variables dan kegunaannya
5. Troubleshooting masalah umum

Tulis dalam Bahasa Indonesia, gaya penulisan jelas dan langsung.
```

---

# BAGIAN 7 — CHEAT SHEET HEMAT TOKEN

## Modifier Wajib di Setiap Prompt

| Kapan | Tambahkan | Efek |
|-------|-----------|------|
| Pakai library (React, Supabase, dll) | `use context7` | Docs terbaru, nol hallusinasi |
| Task kompleks / debugging | `#sequential-thinking` | Analisis dulu, kode kemudian |
| Referensi file spesifik | `#file:path/ke/file` | AI baca langsung, tidak perlu deskripsi |
| Semua task | `Baca #file:docs/SPEC.md` | Konteks terjaga tanpa chat panjang |

## Anti-Pattern yang Boros Token

| Hindari | Ganti dengan |
|---------|-------------|
| "Jelaskan kode ini ke saya..." | Langsung tanya yang spesifik |
| "Apa pendapat kamu tentang..." | "Rekomendasikan X atau Y untuk kasus ini: [konteks]" |
| Describe struktur folder panjang | `#file:` referensi langsung |
| Lanjut chat setelah task selesai | Clear chat, mulai sesi baru |
| Pakai Opus untuk semua task | Pakai GPT-4.1 untuk task sederhana |
| "Perbaiki semua error di project" | Satu error, satu chat |

## Urutan Model dari Terhemat ke Terkuat

```
GPT-4.1 / GPT-5 mini (0x, GRATIS)
    ↓ tidak cukup?
Grok Code Fast 1 (0.25x)
    ↓ tidak cukup?
Claude Haiku 4.5 / Gemini 3 Flash (0.33x)
    ↓ tidak cukup?
Claude Sonnet 4.6 / GPT-5.2-Codex (1x) ← sweet spot harian
    ↓ hanya untuk planning & audit
Claude Opus 4.6 (3x) ← gunakan SEJARANG-JARANGNYA
```



---

# BAGIAN 8 — MASTER CONTEXT: FILE TERPENTING DALAM PROJECT

## Kenapa SPEC.md Saja Tidak Cukup

SPEC.md hanya menjawab **"apa yang dibangun"**. Tapi Copilot butuh jauh lebih dari itu
untuk bekerja secara konsisten tanpa kamu harus jelaskan ulang setiap sesi:

| File | Menjawab | Kapan Dibaca |
|------|----------|--------------|
| `SPEC.md` | Apa yang dibangun, stack, fitur | Awal project |
| `copilot-instructions.md` | Bagaimana AI harus berperilaku | Setiap sesi otomatis |
| **`MASTER_CONTEXT.md`** | **Segalanya: kenapa, bagaimana, aturan bisnis, jebakan, diagram** | **Setiap kali task kompleks** |

MASTER_CONTEXT adalah "otak" project — satu file yang kalau Copilot baca,
dia langsung paham seutuhnya tanpa perlu kamu jelaskan apapun lagi.

## Apa yang Ada di MASTER_CONTEXT

```
docs/MASTER_CONTEXT.md
│
├── Latar belakang & business problem    ← Copilot paham konteks, bukan cuma syntax
├── Arsitektur + data flow diagram       ← Copilot tidak buat struktur yang konflik
├── Skema data & kolom kunci             ← Copilot tidak salah nama field
├── Business logic & formula kalkulasi  ← Copilot tidak tebak-tebak aturan bisnis
├── Edge cases & jebakan yang sudah ada ← Bug yang sama tidak muncul dua kali
├── Design system & CSS tokens          ← UI konsisten di setiap komponen
├── Sample input/output nyata           ← Kode langsung cocok dengan data asli
├── Instruksi khusus untuk Copilot      ← Larangan keras, pattern wajib
├── Konvensi kode                       ← Naming, struktur file, error handling
└── Mermaid diagrams (ERD, sequence,    ← Visual arsitektur yang bisa di-render
    flowchart, component map)
```

## Cara Membuat MASTER_CONTEXT dengan Copilot

Gunakan prompt ini di awal project, dengan model **Claude Opus 4.6**:

```
Saya akan membangun aplikasi berikut:

[Deskripsi project dalam 5-10 kalimat, semakin detail semakin baik]

Stack yang dipakai: [list stack]
Target pengguna: [siapa]
Data yang diolah: [jenis data, sumbernya, formatnya]
Business rules utama: [aturan kalkulasi / logika bisnis kunci]

Buatkan file `docs/MASTER_CONTEXT.md` yang komprehensif dan lengkap.
Sertakan:
1. Latar belakang dan problem statement
2. Arsitektur sistem dan alur data (ASCII art)
3. Skema data / struktur tabel dengan semua field dan tipenya
4. Business logic dan formula kalkulasi
5. Spesifikasi UI / output
6. Design tokens (warna, typography, spacing)
7. Edge cases dan validasi data
8. Instruksi khusus untuk GitHub Copilot
9. Konvensi kode (naming, struktur, error handling)
10. Deployment dan environment variables
11. Mermaid diagrams: system overview, sequence diagram, ERD, flowchart
    untuk proses bisnis utama

Tulis sedetail mungkin — file ini akan menjadi satu-satunya referensi
yang dibaca AI di setiap sesi coding. Semakin lengkap, semakin sedikit
token terbuang untuk konteks di masa depan.
```

## Cara Menggunakan MASTER_CONTEXT di Setiap Prompt

Cukup satu baris di awal prompt apapun:

```
Baca #file:docs/MASTER_CONTEXT.md

[lanjut instruksi task kamu]
```

AI langsung punya konteks penuh. Tidak perlu explain ulang stack, aturan bisnis,
naming convention, atau edge cases yang sudah pernah kamu hadapi.

## Cara Update MASTER_CONTEXT

Jangan biarkan MASTER_CONTEXT basi. Setiap kali ada perubahan besar, gunakan:

```
Baca #file:docs/MASTER_CONTEXT.md

Kami baru menambahkan [fitur/aturan baru]. Update MASTER_CONTEXT:
- Tambahkan ke bagian [nomor bagian yang relevan]: [detail perubahan]
- Update changelog di bagian 10
- Bump versi dokumen di header dari [versi lama] ke [versi baru]
- Jika ada diagram Mermaid yang perlu diperbarui, update juga
```

---

# RINGKASAN: URUTAN KERJA YANG BENAR

```
SEBELUM CODING
─────────────────────────────────────────────────────────────
1. Buat docs/MASTER_CONTEXT.md          ← Opus 4.6 (sekali, di awal)
2. Buat .vscode/mcp.json               ← Copy dari template
3. Buat .github/copilot-instructions.md ← Referensikan MASTER_CONTEXT
4. Setup filesystem MCP                 ← Aktifkan dulu sebelum yang lain
5. Aktifkan sequential-thinking + context7

SAAT CODING
─────────────────────────────────────────────────────────────
6. Setiap prompt mulai dengan:
   "Baca #file:docs/MASTER_CONTEXT.md"
7. Referensi file spesifik dengan #file:
8. Pakai model sesuai tabel di Bagian 2
9. Clear chat setelah setiap task selesai
10. Satu chat = satu task

SETELAH FITUR SELESAI
─────────────────────────────────────────────────────────────
11. Update MASTER_CONTEXT (changelog, edge case baru, dll)
12. Commit ke Git
13. Jalankan npm audit / pip-audit sebelum deploy
```

