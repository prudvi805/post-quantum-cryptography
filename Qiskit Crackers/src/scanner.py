"""Scans Python code for quantum-vulnerable public-key crypto (RSA, DSA, DH, ECC)
and suggests a NIST post-quantum replacement for each hit:

  ML-KEM (FIPS 203) for key exchange / encryption
  ML-DSA (FIPS 204) for signatures

Two ways of finding things:
  1. AST: resolve import aliases, then check whether a call lands in a known crypto module
  2. Pattern: JWT-style algorithm names (RS256, ES384, ...) sitting in string literals
"""
import ast
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

REPLACEMENTS = {
    "signature": "ML-DSA-65 (FIPS 204)",
    "key_establishment": "ML-KEM-768 (FIPS 203)",
    "unknown": "ML-KEM-768 (FIPS 203) if used for encryption or key exchange; "
               "ML-DSA-65 (FIPS 204) if used for signing",
}

# module path -> crypto family
LIBRARY_MODULES = {
    # pyca/cryptography
    "cryptography.hazmat.primitives.asymmetric.rsa": "RSA",
    "cryptography.hazmat.primitives.asymmetric.dsa": "DSA",
    "cryptography.hazmat.primitives.asymmetric.dh": "DH",
    "cryptography.hazmat.primitives.asymmetric.ec": "ECC",
    "cryptography.hazmat.primitives.asymmetric.x25519": "ECC",
    "cryptography.hazmat.primitives.asymmetric.x448": "ECC",
    "cryptography.hazmat.primitives.asymmetric.ed25519": "ECC",
    "cryptography.hazmat.primitives.asymmetric.ed448": "ECC",
    # other libs
    "rsa": "RSA",
    "ecdsa": "ECC",
    "nacl.public": "ECC",
    "nacl.signing": "ECC",
}

# pycryptodome installs as Crypto, pycryptodomex as Cryptodome
for root_pkg in ("Crypto", "Cryptodome"):
    for name in ("RSA", "DSA", "DH", "ECC"):
        LIBRARY_MODULES[f"{root_pkg}.PublicKey.{name}"] = name

# longest first so a more specific module wins over a shorter one
PREFIXES = sorted(LIBRARY_MODULES, key=len, reverse=True)

KEYGEN_RE = re.compile(r"generate|newkeys|keygen|construct", re.IGNORECASE)
SIGNATURE_RE = re.compile(
    r"\b(sign|signing|signer|signature|verify|verifier|pss|pkcs1_v1_5|ecdsa|ed25519|ed448"
    r"|signingkey|verifykey|dsa)\b",
    re.IGNORECASE,
)
KEX_RE = re.compile(
    r"\b(dh|diffie|ecdh|x25519|x448|exchange|derive|encrypt|decrypt|oaep|box)\b",
    re.IGNORECASE,
)
JWT_ALG_RE = re.compile(r"RS256|RS384|RS512|PS256|PS384|PS512|ES256|ES384|ES512|EdDSA")

SEVERITY_RANK = {"HIGH": 2, "MEDIUM": 1}
SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", ".tox", "site-packages"}


@dataclass
class Finding:
    file: str
    line: int
    family: str      # RSA, DSA, DH or ECC
    matched: str     # the call as written, or the algorithm string
    layer: str       # "ast" or "pattern"
    usage: str       # signature, key_establishment or unknown
    severity: str    # HIGH = key generation, MEDIUM = anything else
    replacement: str
    snippet: str


@dataclass
class ScanReport:
    root: str
    files_scanned: int
    lines_scanned: int
    elapsed_s: float
    findings: list = field(default_factory=list)
    parse_errors: list = field(default_factory=list)


def dotted_name(node):
    """a.b.c -> ["a", "b", "c"]. Returns None for anything that isn't a plain dotted name."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    parts.reverse()
    return parts


def collect_aliases(tree):
    """Map each name bound by an import to the full dotted path it refers to."""
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.asname:
                    aliases[item.asname] = item.name
                else:
                    top = item.name.split(".")[0]
                    aliases[top] = top
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for item in node.names:
                if item.name == "*":
                    continue
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
    return aliases


def resolve(parts, aliases):
    # Only names that came from an import count. This keeps us from flagging a local
    # variable that happens to be called "rsa" or "dh".
    first = parts[0]
    if first not in aliases:
        return None
    return ".".join([aliases[first]] + parts[1:])


def family_for(full_name):
    for prefix in PREFIXES:
        if full_name == prefix or full_name.startswith(prefix + "."):
            return LIBRARY_MODULES[prefix]
    return None


def guess_usage(full_name, line):
    if SIGNATURE_RE.search(full_name) or SIGNATURE_RE.search(line):
        return "signature"
    if KEX_RE.search(full_name) or KEX_RE.search(line):
        return "key_establishment"
    return "unknown"


def scan_source(source, filename="<string>"):
    """Scan one string of Python source. Raises SyntaxError if it doesn't parse."""
    tree = ast.parse(source, filename=filename)
    lines = source.splitlines()
    aliases = collect_aliases(tree)

    # one finding per (line, family); if there are several, keep the most severe
    found = {}

    def line_text(n):
        if 0 < n <= len(lines):
            return lines[n - 1]
        return ""

    def record(lineno, family, matched, layer, usage, severity):
        new = Finding(filename, lineno, family, matched, layer, usage, severity,
                      REPLACEMENTS[usage], line_text(lineno).strip()[:160])
        old = found.get((lineno, family))
        if old is None or SEVERITY_RANK[severity] > SEVERITY_RANK[old.severity]:
            found[(lineno, family)] = new

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            parts = dotted_name(node.func)
            if not parts:
                continue
            full_name = resolve(parts, aliases)
            if not full_name:
                continue
            family = family_for(full_name)
            if family is None:
                continue

            func = full_name.rsplit(".", 1)[-1]
            severity = "HIGH" if KEYGEN_RE.search(func) else "MEDIUM"
            usage = guess_usage(full_name, line_text(node.lineno))
            record(node.lineno, family, ".".join(parts), "ast", usage, severity)

        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if JWT_ALG_RE.fullmatch(node.value):
                family = "RSA" if node.value.startswith(("RS", "PS")) else "ECC"
                record(node.lineno, family, node.value, "pattern", "signature", "MEDIUM")

    return sorted(found.values(), key=lambda f: (f.line, f.family))


def iter_python_files(root):
    root = Path(root)
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*.py")):
        folders = path.relative_to(root).parts[:-1]
        if any(part in SKIP_DIRS for part in folders):
            continue
        yield path


def scan_path(root):
    """Scan a file or a whole directory. Paths in the findings are relative to root."""
    root = Path(root)
    start = time.perf_counter()
    findings = []
    parse_errors = []
    n_files = 0
    n_lines = 0

    for path in iter_python_files(root):
        rel = path.name if root.is_file() else path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        n_files += 1
        n_lines += text.count("\n") + 1
        try:
            findings.extend(scan_source(text, rel))
        except (SyntaxError, ValueError) as err:
            parse_errors.append(f"{rel}: {type(err).__name__}")

    elapsed = round(time.perf_counter() - start, 4)
    return ScanReport(str(root), n_files, n_lines, elapsed, findings, parse_errors)
