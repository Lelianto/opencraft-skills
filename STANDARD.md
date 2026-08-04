# Standard v1

## Contract

Setiap skill wajib:

1. berada di `skills/<name>/SKILL.md`;
2. memakai nama lowercase kebab-case, maksimal 64 karakter, dan sama dengan nama direktori;
3. memiliki hanya `name` dan `description` pada frontmatter portable;
4. menjelaskan kapabilitas dan kondisi pemicu di `description`;
5. memakai kalimat imperatif dan workflow yang dapat diverifikasi;
6. tetap di bawah 500 baris; pindahkan detail ke `references/` satu tingkat dari root skill;
7. tidak menduplikasi aturan yang seharusnya hidup di instruksi repository;
8. tidak mengasumsikan framework, package manager, provider, atau izin eksternal;
9. menyatakan output atau definition of done;
10. tidak mengklaim keberhasilan tanpa bukti.
11. memiliki eval trigger positif, negatif, ambigu, dan assertion yang dapat ditinjau;
12. mencantumkan dependency atau authorization boundary bila workflow membutuhkannya.

`agents/openai.yaml` adalah metadata UI opsional untuk Codex/OpenAI. Client lain boleh mengabaikannya. Ekstensi khusus client tidak boleh mengubah makna workflow portable.

## Instruction precedence

Saat aturan bertentangan, agent mengikuti urutan berikut:

1. system, policy, dan permission client;
2. permintaan pengguna terbaru;
3. instruksi repository (`AGENTS.md`, `CLAUDE.md`, atau ekuivalen);
4. skill yang aktif;
5. referensi dan baseline generik.

## Lifecycle

1. Edit hanya sumber di `skills/`.
2. Jalankan `python3 scripts/validate.py`.
3. Uji trigger positif, trigger negatif, dan satu tugas realistis.
4. Instal ulang dengan `scripts/install.py --force` hanya setelah meninjau target.
5. Version-control sumber dan template; perlakukan folder hasil instalasi sebagai generated output bila berada di repo yang sama.
6. Regenerasi `skills.lock.json` dan jalankan evaluasi sebelum release.

## Artifact and traceability contract

- Gunakan `.product/` untuk intent, decisions, dan evidence yang harus bertahan lintas-agent atau sesi.
- Gunakan ID stabil `REQ`, `EXP`, `ARCH`, `TASK`, `THREAT`, `CTRL`, `TEST`, dan `RISK`.
- Setiap must-have requirement harus terhubung ke implementation task dan test/release evidence.
- Production findings memperbarui artifact terkait; jangan membiarkan specification menjadi snapshot usang.
- Pilih delivery mode: `greenfield-product`, `brownfield-feature`, `prototype`, `production-hardening`, atau `incident-fix`.

## Trigger evaluation

Untuk setiap skill, pertahankan sekurangnya:

- tiga prompt yang harus memicu;
- dua prompt berdekatan yang tidak seharusnya memicu;
- satu prompt ambigu;
- satu tugas end-to-end untuk memeriksa kepatuhan workflow dan kualitas output.

Revisi `description` bila discovery gagal. Revisi body bila discovery benar tetapi eksekusi menyimpang.
