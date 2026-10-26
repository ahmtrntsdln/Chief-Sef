# Chief-Sef
Machine learning-powered software-hardware security engine

> Türkçe: [README.tr.md](README.tr.md)

> The development story and the reasoning behind each decision are in
> [GELISIM_SURECI.md](GELISIM_SURECI.md) (in Turkish).

## About Şef-Chief

This repository contains the initial version (prototype) of Şef-Chief, a machine learning-powered software and hardware security engine.

AI-Assisted Development: Developed with the support of Large Language Models (LLMs). The core project concept and direction belong entirely to me, while the coding phase was fully handled by Claude and Gemini.

Project Milestone: This serves as a functional prototype and represents a personal milestone as both my first-ever project and my first AI-supported venture.

---

# The Şef Project

An AI-assisted cybersecurity engine built around hardware isolation.

## Phase 1: Proof of Concept - "Customs Officer" (Gümrük Memuru)

First goal: a simple static analysis layer that measures the Shannon entropy
of files and tells normal files apart from encrypted/packed (potentially
suspicious) ones.

- `gumruk_memuru/entropy.py` -> Entropy calculation module
- `gumruk_memuru/sef_sabitler.py` -> Shared measurement constants (KARA_LISTE
  (suspicious API list), magic signatures, ordinal pattern, CLR directory
  names). The malicious and benign sides must be produced by the same
  measurement; with the constants in one place, one side cannot change while
  the other stays stale.
- `gumruk_memuru/sef_ayarlar.py` -> Machine-specific paths and data file names.
  Kept separate from the measurement constants: changing a path changes no
  number, changing a constant requires regenerating all data.
- `gumruk_memuru/Chief_1.2.py` -> Full static analysis engine (magic bytes, per-section entropy, IAT/API)
- `gumruk_memuru/ember_zararli_cikar.py`, `ember_zararsiz_cikar.py` -> Extracting real data from EMBER
- `gumruk_memuru/toplu_tarama.py` -> Scanning the files on this machine (external validation set)
- `gumruk_memuru/rf_egit_gercek.py` -> Training, external validation and "sneaky sample" tests;
  saves the main model as `model.pkl` (not in the repo: the same model is
  reproduced in ~10 s, and a pickle is tied to the scikit-learn version)
- `gumruk_memuru/tahmin_et.py` -> Single-file prediction with the native model
  (see "Native model" below): `python tahmin_et.py <file>`. Features come from
  `gumruk_memuru/ozellik_cikar.py`, the same module the external validation
  uses; the model is only loaded if its SHA-256 matches the checked-in
  metadata (`gumruk_memuru/model_native_meta.json`). For .NET files a score
  below the threshold is reported as BELIRSIZ (uncertain, needs review), never
  as benign, because the native model misses many .NET malware samples (see
  ".NET is still a weak spot" below); above the threshold a .NET EXE is
  OLASI ZARARLI (possibly malicious). Invalid scores (NaN, infinite, outside
  [0, 1]) are BELIRSIZ for every file. Exit codes: 0 = clean (zararsiz),
  1 = error, 2 = BELIRSIZ, 3 = ZARARLI, 4 = OLASI ZARARLI; only 0 means clean.
- `gumruk_memuru/toplu_tahmin.py` -> The same prediction for a folder or several files:
  `python toplu_tahmin.py <folder> [--liste]`. Prints separate counts for clean,
  BELIRSIZ, ZARARLI, OLASI ZARARLI, not a PE file, and error; BELIRSIZ is not
  counted as an error. File names are only printed with `--liste`, never written.
  Exit code = the worst result: any ZARARLI 3, else OLASI ZARARLI 4, else
  BELIRSIZ 2, else error 1, all clean 0. Non-PE files do not raise it; a missing
  path, or no PE file classified at all (empty folder, wrong path, only .txt),
  gives a warning and 1, so a typo never reports "all clean".
- `gumruk_memuru/model_karsilastir.py` -> RF vs LightGBM and calibration comparison

Setup: `pip install -r requirements.txt` (`requirements-experimental.txt` for
the model comparison). If your data folders differ, edit
`gumruk_memuru/sef_ayarlar.py`.

Windows: the 260-character path limit can break `pip install` (scikit-learn
ships deeply nested test files). A failed install can leave a half-installed
package behind: in a clean-clone check, `pytest` still passed but
`import sklearn` failed (`sklearn.utils` missing). Create the virtual
environment under a short path (e.g. `C:\venvs\sef`) or enable long path
support (`LongPathsEnabled` = 1, needs admin). Afterwards check with
`python -c "import sklearn.ensemble"`.

Tests: `pip install -r requirements-dev.txt`, then from the repo root
`python -m pytest tests`. `tests/test_olcum_tutarliligi.py` checks that the
malicious side (EMBER JSON) and the benign side (pefile) turn the same file
into the same numbers. In this project the most expensive bugs were not model
errors but measurement differences: when the two sides are measured
differently, the model learns the measurement difference instead of
maliciousness. `tests/test_esik_sinir.py` + `tests/esik_sinir.c` are a
boundary-value regression test for the threshold comparison, written ahead
of Phase 2 (see the roadmap); the C part is skipped when no gcc/clang is
installed.

## Phase 1 Results

Model: Random Forest, 5 features (size, zero-byte ratio, mean section
entropy, total APIs, suspicious APIs). Training: 5,700 malicious + 5,700
benign real PE files from EMBER 2018.

| Measurement | Result |
|---|---|
| EMBER test accuracy: same period (80/20 within November 2018) | 90.1% |
| EMBER test accuracy: temporal split (train Jan-Oct -> test Nov-Dec) | 83.8% (AUC 0.920) |
| False alarms / missed malware within EMBER (same period) | 8.1% / 11.7% |
| False alarms on 5,700 real benign PE files from this machine (never seen in training) | 3.5% |
| Most important features | Toplam_API 0.30, Boyut 0.25, Entropi 0.24, Sifir orani 0.18 |
| Known limitation | Nearly blind to .NET malware: 93% of recent (2024) .NET malware is missed (see CLAUDE.md) |

The realistic number is the temporal one: when training and test data come
from the same month, the same campaigns appear on both sides and the score
becomes artificially easy (90.1% -> 83.8%). Details and experimental fixes
(.NET specialist model, string features): CLAUDE.md (in Turkish).

90% is deliberately a more trustworthy result than 99%: the earlier 99.9%
(synthetic data) and 97% (benign data from a single machine) results showed
that the model was learning the difference between data sources, not
malicious behavior. Details: [GELISIM_SURECI.md](GELISIM_SURECI.md).

Model comparison (5-fold CV): Random Forest (AUC 0.963) beats untuned
LightGBM (0.952). This result is specific to 5 features; the comparison will
be repeated as the feature count grows.

## Native model (EMBER2024, October 2026)

The Phase 1 model, trained on 2018 data, collapses on 2024 files (AUC 0.663).
Its replacement is trained on EMBER2024 Win32/Win64 with 86 features (5 basic +
80 string features + DLL flag): Random Forest, 483,224 training files sampled
50/50 *within* each file type, because in the data set most benign files are
DLLs and very few malicious ones are, and a model can otherwise learn "DLL ⇒
benign". The decision criteria were written down and committed before any
result was seen (`gumruk_memuru/sonuclar/`).

Thresholds were chosen on held-out training weeks 48-51 (1% false alarms per
file type); the test weeks 52-63 (959,738 files) were measured once with
those fixed thresholds:

| File type | Missed malware | False alarms on EMBER2024 benign files |
|---|---|---|
| EXE | 17.7% | 0.83% |
| DLL | 19.5% | 1.43% |

Overall test AUC 0.9865. On 5,635 real benign files from this machine: false
alarms 0.25% (EXE) and 0.21% (DLL).

How to read these numbers:
- **50% of the test files are malicious.** EMBER2024 is sampled 50/50 per
  week; in real use malware is far rarer, so the real probability behind a
  given score is lower and the real share of alarms that are false is higher.
- **The DLL false-alarm rate exceeds its 1% target** (1.43%). The threshold was
  set on weeks 48-51. A likely cause is drift over time: the benign DLL
  population looks different in the test weeks (benign DLL share 64.9% in the
  training weeks, 73.4% in test). This cause was NOT measured: those shares
  are not from weeks 48-51, where the threshold was chosen, and the
  false-alarm rate *within* DLLs does not depend directly on the DLL share.
  The threshold has to be re-validated over time.
- **The local validation set is aging.** Since it was measured on 9 October,
  857 of its files have been deleted and hundreds updated on this machine.
  The 5,635 rows the measurements rely on are frozen (not in the repository;
  SHA-256 recorded in `gumruk_memuru/sonuclar/4/yerel_set.md`) instead of
  being re-scanned.
- Random Forest beat LightGBM only against *untuned* LightGBM; a tuned
  LightGBM is a separate, not-yet-run experiment.
- **.NET is still a weak spot.** Measured separately with criteria registered
  beforehand (`gumruk_memuru/sonuclar/5/`), same fixed thresholds: in the test
  weeks, .NET EXEs are missed at 33.7% (non-.NET EXEs 17.6%). On EMBER2024's
  separate .NET test set the native model misses 49.8% of malware (86.7% of
  malicious .NET DLLs) at 1.05% false alarms; the Phase 1 model missed 92.8%
  there at 0.46% false alarms. At the *same* false-alarm rate as Phase 1, the
  native model misses 59.8% (92.7% of malicious .NET DLLs). Better, not good
  enough: .NET files need the specialist model, which is not yet connected.

## Roadmap

1. [x] Entropy calculator (the first working piece)
2. [x] First Random Forest model built - 99.9% result, BUT data leakage was
       detected: the synthetic "malicious" data was generated from 5 fixed
       scenarios (random.uniform), so it is not realistic. Out-of-scenario
       "sneaky" samples slip through with 100% confidence. See
       `faz1_dogrulama.py`.
3. [x] Real feature extraction engine written (`Chief_1.2.py` - magic bytes,
       per-section entropy, IAT/API analysis with pefile). The KARA_LISTE
       substring/double-counting bug in v1.1 was fixed (list -> set, exact
       match).
4. [x] 5,700 real malicious records extracted from EMBER. EMBER's
       measurement was aligned with the pefile side (ordinal imports and
       empty sections).
5. [x] Benign data was first scanned from this machine (System32 + Program
       Files); this turned out to create source bias. Benign training data
       was also taken from EMBER, and the machine scan (533,081 files, 64,263
       PE) became the external validation set.
6. [x] Random Forest retrained on real data and validated (same period
       90.1% / temporal 83.8%, 3.5% false alarms on a real machine).
       **Phase 1 closed.**
6b. [x] Native model moved to EMBER2024 (Random Forest, 86 features,
       type-balanced training; see "Native model"). The 2018 model is kept
       under the git tag `eski-5-ozellik`.
7. [ ] (Phase 2) Linux system-call monitoring with eBPF
   - [x] Boundary-value regression test for the threshold comparison
         (`tests/test_esik_sinir.py`, `tests/esik_sinir.c`). Python has no
         integer overflow, but once the agent moves to C, a score stored in
         a narrow type wraps at 128 and bypasses `score > 100`: a suspicious
         file passes as clean. The test pins both the broken and the correct
         version (wide type + range check + fail-closed).
   - [x] Default C/C++ flags: `-Wall -Wextra -Wconversion -Wsign-conversion
         -Werror`. Making the compiler talk is the cheapest defense:
         `-Wconversion` points at the overflow line before the code ever
         runs. The test also checks that these flags warn on exactly that
         line and nowhere else.
   - [x] Verified on Windows with MinGW gcc 16.2 (October 2026): the warning
         flags produce exactly one warning, on the narrowing line; the correct
         C version passes all 7 boundary cases, the broken one misses 128 and
         255. To be re-run on Linux in Phase 2.
   - [ ] Run the C part in CI with a real compiler, so "skipped" cannot
         silently become the norm.
8. [ ] (Phase 3) NPU / TEE hardware isolation
