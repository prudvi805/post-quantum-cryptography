# PS-P2 — Inventory Schema, Label Rules and Tool Interface

This file is the **official, fixed contract** for PS-P2. The development dataset in this folder
and the hidden evaluation inventory used for judging both follow it exactly.

---

## 1. Input file — `inventory_*.csv`

UTF-8 CSV with a header row. One row = one cryptographic use. Any field except `asset_id` may be blank.

| Column | Meaning | Allowed values / format |
|---|---|---|
| `asset_id` | Unique record ID | e.g. `DEV-0001` (dev) or `EVL-0001` (evaluation) |
| `asset_type` | Kind of asset | `application`, `certificate`, `library`, `network_service`, `code`, `hsm_key`, `database` |
| `service` | Business service that owns the asset | free text |
| `environment` | Deployment stage | `prod`, `staging`, `dev` |
| `primitive` | Declared cryptographic role | `key_establishment`, `digital_signature`, `public_key_encryption`, `symmetric_encryption`, `hash`, `mac`, `kdf`, `unknown` |
| `algorithm` | Algorithm, as recorded by the source system | free text (see the alias table, §3) |
| `key_size_or_parameter_set` | Key size in bits, curve name or PQC parameter set | free text |
| `usage` | What the crypto is used for | free text |
| `protocol` | Protocol context | free text, e.g. `TLS 1.3`, `SSH-2`, `IPsec/IKEv2` |
| `library`, `library_version` | Implementation | free text |
| `location` | Where it was found | `host:port`, or `file:line` for `code` records |
| `data_sensitivity` | Sensitivity of the protected data | `public`, `internal`, `confidential`, `restricted` |
| `data_retention_years` | How long the protected data must stay confidential/authentic | integer |
| `internet_exposed` | Reachable from the internet | `yes`, `no` |
| `criticality` | Business criticality | `low`, `medium`, `high`, `critical` |
| `cert_expiry` | Certificate expiry date | `YYYY-MM-DD` |
| `notes` | Free-text remarks from the source system | free text |

Blank **metadata** fields (retention, exposure, version …) are normal. They must be handled
explicitly in your risk score and must **never** be silently treated as "low risk".

---

## 2. Labels — exactly one per record

| Label | Meaning |
|---|---|
| `QUANTUM_VULNERABLE` | Uses a classical public-key mechanism (breakable by Shor's algorithm) with no PQC component |
| `QUANTUM_RESISTANT` | Uses a post-quantum public-key mechanism only |
| `HYBRID` | Combines a classical and a post-quantum public-key mechanism |
| `SYMMETRIC_OR_HASH` | Symmetric cipher, MAC, KDF or hash considered adequate today (not Shor-exposed) |
| `LEGACY_BROKEN` | Symmetric/hash algorithm that is already classically broken or deprecated |
| `UNKNOWN` | Cannot be classified safely → **requires human review** |

### Labelling rules (applied in this order)

1. **UNKNOWN first.** Label `UNKNOWN` if the `algorithm` is blank, `unknown`, `vendor default`,
   `vendor-managed`, `proprietary` or otherwise unidentifiable, **or** if the crypto fields contradict each other.
   Contradictions include:
   - a hash or symmetric algorithm declared as `digital_signature` / `key_establishment` (e.g. `SHA-256` used for "release signing", `AES-256` for "contract signing");
   - a public-key algorithm declared as `hash` / `symmetric_encryption`;
   - a parameter set that is impossible for the algorithm (e.g. `ML-KEM` with `2048`, `AES` with `2048`, `ML-DSA-65` with `ML-KEM-768`).
2. **HYBRID** if the record contains both a classical public-key component and a PQC component (e.g. `X25519MLKEM768`).
3. **QUANTUM_VULNERABLE** if the record contains any classical public-key component — RSA, DSA, DH/FFDH/MODP, ECDH/ECDHE, ECDSA, EdDSA/Ed25519/Ed448, X25519/X448, ECC named curves. This applies **regardless of key size** (RSA-4096 is still vulnerable) and also covers cipher-suite strings and `SHA256withRSA`-style signature names.
   A weak classical key such as RSA-1024 is still labelled `QUANTUM_VULNERABLE`; mention the extra classical weakness in your recommendation.
4. **QUANTUM_RESISTANT** for ML-KEM, ML-DSA, SLH-DSA, FN-DSA/Falcon, LMS, XMSS, HQC, including pre-standard names (Kyber, Dilithium, SPHINCS+). Pre-standard versions should get an "upgrade to the FIPS version" recommendation.
5. **LEGACY_BROKEN** for MD5, SHA-1, DES, 3DES/TDEA, RC4.
6. **SYMMETRIC_OR_HASH** for AES (any mode, 128/192/256), ChaCha20-Poly1305, SHA-2 family, SHA-3 family, HMAC-SHA2, HKDF, PBKDF2, scrypt, Argon2.

> `SHA-256` on its own is **never** a public-key signature or key-establishment scheme.

---

## 3. Alias table (spellings that occur in the dev and evaluation inventories)

| Family | Spellings you must recognise |
|---|---|
| RSA | `RSA`, `rsaEncryption`, `RSA-OAEP`, `RS256`, `RSASHA256`, `SHA256withRSA`, `sha256WithRSAEncryption` |
| ECC / ECDH / ECDSA | `ECDHE P-256`, `ECDH secp256r1`, `prime256v1 ECDHE`, `ECDH P-384`, `secp384r1`, `ECDSA`, `ES256`, `ECDSAP256SHA256`, `ecdsa-with-SHA384` |
| Edwards / Montgomery | `X25519`, `Curve25519`, `Ed25519`, `EdDSA` (`Ed448`) |
| Finite-field DH / DSA | `DH group 14`, `MODP-2048`, `FFDHE2048`, `DSA` |
| TLS cipher suites | `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`, `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256`, `ECDHE-RSA-AES256-GCM-SHA384` (OpenSSL style) |
| PQC | `ML-KEM`, `ML-DSA`, `ML-DSA-65`, `SLH-DSA`, `FN-DSA`, `LMS`, `XMSS`, `Kyber768`, `Dilithium3`, `SPHINCS+-SHA2-128s` |
| Hybrid | `X25519MLKEM768`, `X25519+ML-KEM-768`, `SecP256r1MLKEM768`, `P-256+ML-KEM-768`, `ECDSA-P256+ML-DSA-44`, `X25519Kyber768Draft00` |
| Symmetric / hash | `AES-256-GCM`, `AES-256`, `aes256-gcm`, `AES-128-GCM`, `ChaCha20-Poly1305`, `SHA-256`, `SHA256`, `sha-256`, `SHA-384`, `SHA-512`, `SHA3-256`, `HMAC-SHA256`, `HKDF-SHA256`, `PBKDF2-HMAC-SHA256`, `scrypt`, `Argon2id` |
| Legacy broken | `MD5`, `md5`, `SHA-1`, `SHA1`, `3DES`, `TDEA`, `DES-EDE3-CBC`, `DES`, `RC4` |
| Unidentifiable | blank, `unknown`, `vendor default`, `vendor-managed`, `proprietary`, `custom XOR scheme`, bare `AES` with an impossible key size |

---

## 4. Output file your tool must produce — `predictions.csv`

| Column | Required | Description |
|---|---|---|
| `asset_id` | yes | Same IDs as the input, one row per input row |
| `predicted_label` | yes | One of the six labels in §2 |
| `priority_score` | yes | Number from 0 to 100 (higher = migrate sooner). `UNKNOWN` records must get a review priority, not 0 |
| `priority_rank` | yes | 1 = most urgent. Ties allowed |
| `recommended_action` | yes | e.g. `Replace RSA-2048 TLS cert with ML-DSA-65 (or hybrid) cert`, `Manual review: algorithm not recorded` |
| `migration_wave` | yes | `1`, `2`, `3` or `review` |
| `depends_on` | no | `asset_id`s that must migrate first (e.g. an internal CA before the certificates it issues) |
| `rationale` | yes | Short text listing the inputs that drove the score (e.g. `QV; internet_exposed=yes; retention=10y; criticality=critical`) |

A template is included as `predictions_template.csv`.

---

## 5. Mandatory command-line interface (used by judges on the hidden inventory)

```
python run_inventory.py --input <inventory.csv> --output <predictions.csv>
```

- Must run **offline** (no internet, no paid APIs, no cloud LLM calls during the judged run).
- Must finish within **5 minutes** for 1,000 records on Platform A.
- Must not need any file other than the input CSV and your repository.
- Must accept an inventory **with no label file**. The hidden inventory has the same columns as `inventory_dev.csv`.

Judges run your command on the hidden inventory and then run `evaluate.py` from this kit. You can run the
same evaluation on the development set:

```
python run_inventory.py --input inventory_dev.csv --output predictions_dev.csv
python evaluate.py --pred predictions_dev.csv --labels inventory_dev_labels.csv
```

---

## 6. How classification is scored

`evaluate.py` reports accuracy, per-class precision/recall/F1, **macro-F1** (the headline number), the confusion
matrix, and two safety checks:

- **Unsafe-unknown count:** true `UNKNOWN` records predicted `SYMMETRIC_OR_HASH` or `QUANTUM_RESISTANT` (i.e. silently assumed safe).
- **Hash-as-public-key count:** true `SYMMETRIC_OR_HASH` / `LEGACY_BROKEN` records predicted as a public-key label.

Missing or invalid predictions count as wrong. Priority and migration quality are **not** scored automatically.
Judges score them separately from classification, because more than one migration order can be defensible.
