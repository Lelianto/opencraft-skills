# AI-assisted Product Development Skills

Boilerplate lintas-agent untuk membawa produk web dari ide hingga release dengan workflow yang konsisten, dapat diaudit, dan tidak terikat framework tertentu.

Paket ini mengikuti format terbuka Agent Skills: setiap skill memiliki `SKILL.md`, metadata pemicu yang ringkas, serta referensi yang dimuat hanya saat dibutuhkan. Sumber kanonis berada di `skills/`; jangan mengedit hasil instalasi di folder agent.

## Skill map

| Skill | Gunakan untuk |
|---|---|
| `analyze-product` | Menganalisis problem, user, evidence, opportunity, dan kelayakan |
| `shape-product` | Mengubah hasil analisis menjadi scope MVP yang tajam |
| `write-product-prd` | Membuat PRD build-ready dan traceable |
| `design-product-experience` | Mendesain flow, state, accessibility, dan responsive UX |
| `design-web-system` | Mendesain boundary, contract, data, security, dan operasi |
| `threat-model-platform` | Memetakan threat, control, verification, dan residual risk |
| `plan-product-delivery` | Mengubah spesifikasi menjadi vertical slices dan bounded tasks |
| `execute-product-task` | Menjalankan satu task dengan traceability dan evidence |
| `develop-with-tests` | Mengembangkan behavior melalui red-green-refactor |
| `build-web-feature` | Membangun platform dan vertical slice lengkap, termasuk web responsif |
| `debug-platform` | Mendiagnosis root cause sebelum melakukan perbaikan |
| `review-product-change` | Review dua tahap: spec compliance dan code quality |
| `test-platform` | E2E, role/permission, security, privacy, dan data integrity testing |
| `verify-web-product` | Independent QA, accessibility, dan release gates |
| `prepare-deployment` | Build artifact, migration, observability, rollout, dan rollback |
| `ship-web-product` | Mengorkestrasi seluruh alur analysis-to-deployment |

## Quick start

Validasi sumber skill:

```bash
python3 scripts/validate.py
python3 scripts/evaluate.py
python3 scripts/generate_lock.py --check
```

Instal ke project yang sedang aktif:

```bash
python3 scripts/install.py --target all --project /path/to/project --with-project-files
```

Target yang tersedia:

- `agents` → `.agents/skills` (format portable/open standard)
- `claude` → `.claude/skills`
- `codex` → `.codex/skills`
- `cursor` → `.cursor/skills`
- `github` → `.github/skills`
- `all` → seluruh target di atas

Default instalasi menggunakan salinan agar bekerja di macOS, Linux, dan Windows. Gunakan `--mode link` untuk symlink pada environment yang mendukungnya. Installer tidak menimpa skill yang sudah ada kecuali `--force` diberikan.

Installer memverifikasi checksum sumber terhadap `skills.lock.json` sebelum menyalin, lalu menulis `.ai-skills-install.json` sebagai receipt versi, source, mode, target, dan daftar skill. Opsi `--with-project-files` juga menginisialisasi `AGENTS.md`, `PROJECT_CONTEXT.md`, dan kontrak artifact `.product/` tanpa menimpa file yang sudah ada.

Salin [templates/AGENTS.md](templates/AGENTS.md) ke root produk sebagai instruksi agent-neutral. Untuk Claude Code, [templates/CLAUDE.md](templates/CLAUDE.md) cukup mengimpor file tersebut. Isi [templates/PROJECT_CONTEXT.md](templates/PROJECT_CONTEXT.md) dengan fakta produk yang tidak dapat disimpulkan dari kode.

## Contoh prompt

```text
Use $ship-web-product to build an MVP for a team expense approval app.
```

Alur yang akan diikuti:

```text
Product analysis -> scope -> PRD -> experience -> architecture -> threat model
-> vertical slices/tasks -> tested implementation -> independent review
-> responsive/E2E/security/data validation -> deployment readiness
-> production deployment only after explicit approval -> production feedback
```

```text
Use $shape-product to narrow this feature request into a one-week vertical slice.
```

```text
Use $verify-web-product to review this release candidate. Do not fix anything yet.
```

```text
Use $prepare-deployment to create a go/no-go assessment and rollback plan. Do not deploy yet.
```

## Prinsip standardisasi

- Satu sumber skill, banyak adapter client.
- `name` dan `description` menjadi kontrak discovery lintas-agent.
- Instruksi inti singkat; detail bersifat progressive disclosure di `references/`.
- Perintah dan konvensi repository mengalahkan default generik.
- Agent membedakan fakta, asumsi, keputusan, dan bukti.
- Klaim selesai harus disertai verifikasi; aksi produksi tetap membutuhkan otorisasi eksplisit.
- Artifact `.product/` menjaga intent dan evidence lintas-agent dan lintas-sesi.
- ID `REQ`, `EXP`, `ARCH`, `TASK`, `THREAT`, `CTRL`, `TEST`, dan `RISK` menjaga traceability.
- Setiap skill mempunyai fixture trigger/non-trigger dan assertion untuk evaluasi.
- Checksum lockfile dan installation receipt menjaga provenance distribusi.

## Delivery modes

- `greenfield-product`: produk baru yang ditujukan menjadi sistem durable.
- `brownfield-feature`: perubahan terukur pada produk yang sudah berjalan.
- `prototype`: eksperimen berbatas waktu untuk menguji hipotesis.
- `production-hardening`: menutup gap kualitas dan operasional sistem yang sudah ada.
- `incident-fix`: containment, root cause, minimal fix, verification, dan prevention follow-up.

## Menambah atau mengubah skill

1. Edit sumber kanonis di `skills/`.
2. Tambahkan atau perbarui fixture di `evals/cases.json`.
3. Jalankan validator dan evaluasi.
4. Regenerasi checksum dengan `python3 scripts/generate_lock.py`.
5. Jalankan `python3 scripts/generate_lock.py --check` sebelum commit.

Spesifikasi dasar: [Agent Skills](https://agentskills.io/specification). Dukungan direktori dapat berubah antar-versi client; gunakan target native client dan target `agents` bila ingin kompatibilitas maksimum.
