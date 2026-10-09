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
- `gumruk_memuru/tahmin_et.py` -> Single-file prediction: `python tahmin_et.py <file>`.
  Features are extracted with the same code used in the external validation,
  so the 3.5% false-alarm measurement also applies to this script.
- `gumruk_memuru/model_karsilastir.py` -> RF vs LightGBM and calibration comparison

Setup: `pip install -r requirements.txt` (`requirements-experimental.txt` for
the model comparison). If your data folders differ, edit
`gumruk_memuru/sef_ayarlar.py`.

Tests: `pip install -r requirements-dev.txt`, then from the repo root
`python -m pytest tests`. `tests/test_olcum_tutarliligi.py` checks that the
malicious side (EMBER JSON) and the benign side (pefile) turn the same file
into the same numbers. In this project the most expensive bugs were not model
errors but measurement differences: when the two sides are measured
differently, the model learns the measurement difference instead of
maliciousness.

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
7. [ ] (Phase 2) Linux system-call monitoring with eBPF
8. [ ] (Phase 3) NPU / TEE hardware isolation
