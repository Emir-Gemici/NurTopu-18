"""Python 3.6 uyum taramasi: ast + feature_version + 3.7+/3.8+ API adlari.
Salt okunur. Hedef: scripts/kamera_koprusu.py (ve ayna)."""
import ast
import re
import sys
from pathlib import Path

HEDEF = Path(r"O:\navitas\scripts\kamera_koprusu.py")
AYNA = Path(r"O:\navitas\jetson_paket\kod\kamera_koprusu.py")
kaynak = HEDEF.read_text(encoding="utf-8")
print("ayna bayt-es:", HEDEF.read_bytes() == AYNA.read_bytes())

# 1) Sozdizimi: feature_version (3.13'te en dusuk (3,7)); walrus/posonly/f'{x=}' yakalar
for fv in ((3, 7), (3, 8)):
    try:
        ast.parse(kaynak, str(HEDEF), feature_version=fv)
        print("ast.parse feature_version=%s: OK" % (fv,))
    except SyntaxError as e:
        print("ast.parse feature_version=%s: SyntaxError %s" % (fv, e))

agac = ast.parse(kaynak)

# 2) 3.7+/3.8+/3.9+ API adlari (attr ve name)
API_37 = {
    "reconfigure": "io.TextIOWrapper.reconfigure 3.7",
    "time_ns": "time.time_ns 3.7", "monotonic_ns": "3.7", "perf_counter_ns": "3.7",
    "run": "asyncio.run 3.7 (yalniz asyncio.run ise)", "capture_output": "subprocess.run(capture_output=) 3.7",
    "ThreadingHTTPServer": "3.7", "breakpoint": "3.7", "get_running_loop": "3.7",
    "fromisoformat": "3.7", "dataclass": "3.7", "contextvars": "3.7", "isqrt": "3.8",
    "prod": "math.prod 3.8", "dist": "math.dist 3.8", "cached_property": "3.8",
    "removeprefix": "3.9", "removesuffix": "3.9", "is_relative_to": "3.9",
    "Literal": "typing.Literal 3.8", "Protocol": "typing.Protocol 3.8", "Final": "3.8",
    "TypedDict": "3.8", "SupportsIndex": "3.8", "shared_memory": "3.8", "unlink": "",
    "block_on_close": "socketserver 3.7", "as_integer_ratio": "", "isascii": "str.isascii 3.7",
    "nsmallest": "", "pickle5": "", "importlib_resources": "", "resources": "importlib.resources 3.7",
    "walrus": "", "zoneinfo": "3.9", "graphlib": "3.9", "annotations": "",
    "SO_REUSEPORT": "", "create_server": "socket.create_server 3.8", "has_dualstack_ipv6": "3.8",
    "pidfd_open": "3.9", "copy_file_range": "3.8", "memfd_create": "3.8",
    "add_dll_directory": "3.8", "Path": "", "unraisablehook": "3.8",
    "getsockname": "", "sendfile": "", "send_error": "", "text": "subprocess text= 3.7",
    "start_new_session": "", "raise_signal": "signal.raise_signal 3.8",
    "valid_signals": "3.8", "pthread_kill": "", "strsignal": "3.8",
}
bulgular = []
for d in ast.walk(agac):
    if isinstance(d, ast.Attribute) and d.attr in API_37 and API_37[d.attr]:
        bulgular.append(("attr", d.attr, d.lineno, API_37[d.attr]))
    if isinstance(d, ast.Name) and d.id in API_37 and API_37[d.id]:
        bulgular.append(("name", d.id, d.lineno, API_37[d.id]))
    if isinstance(d, ast.keyword) and d.arg in ("capture_output", "text") :
        bulgular.append(("kwarg", d.arg, getattr(d.value, "lineno", "?"), "subprocess 3.7"))
    if isinstance(d, ast.BinOp) and isinstance(d.op, ast.BitOr):
        # dict | dict (3.9) — yalniz sozluk gorunumluyse
        bulgular.append(("binop|", ast.dump(d)[:60], d.lineno, "dict | dict 3.9 olabilir (elle bak)"))
    if isinstance(d, ast.JoinedStr):
        bulgular.append(("fstring", "", d.lineno, "f-string (3.6 OK; '=' belirteci 3.8)"))
    if isinstance(d, ast.NamedExpr):
        bulgular.append(("walrus", "", d.lineno, "3.8"))
    if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and getattr(d.args, "posonlyargs", []):
        bulgular.append(("posonly", d.name if hasattr(d, "name") else "lambda", d.lineno, "3.8"))
    if isinstance(d, ast.ImportFrom) and d.module == "__future__":
        bulgular.append(("future", ",".join(a.name for a in d.names), d.lineno, ""))
    if isinstance(d, ast.Import):
        for a in d.names:
            if a.name.split(".")[0] in ("dataclasses", "contextvars", "asyncio", "typing", "importlib", "zoneinfo", "graphlib"):
                bulgular.append(("import", a.name, d.lineno, "modul 3.7+ ya da tip"))
    if isinstance(d, ast.ImportFrom) and (d.module or "").split(".")[0] in ("dataclasses", "contextvars", "asyncio", "typing", "zoneinfo", "graphlib"):
        bulgular.append(("importfrom", d.module, d.lineno, "modul 3.7+ ya da tip"))
    if isinstance(d, ast.Subscript) and isinstance(d.value, ast.Name) and d.value.id in ("list", "dict", "tuple", "set", "type"):
        bulgular.append(("generic", d.value.id, d.lineno, "3.9"))
    # Thread(daemon=) 3.3 OK; Condition.wait_for 3.2 OK; print(flush=) 3.3 OK
print("\nAPI/sozdizimi bulgulari (%d):" % len(bulgular))
for b in bulgular:
    print("  ", b)

# 3) Metin taramalari
for desen, aciklama in [
    (r"\{[^{}]*=\}", "f-string '=' belirteci (3.8)"),
    (r"\bmath\.prod\b", "math.prod 3.8"), (r"removeprefix|removesuffix", "3.9"),
    (r"\basyncio\b", "asyncio"), (r"\btyping\b", "typing"), (r"time\.time_ns", "3.7"),
    (r"capture_output", "3.7"), (r"ThreadingHTTPServer", "3.7"),
    (r"\bkw_only\b|\bslots=True\b", "3.10 dataclass"),
    (r"\bTextIOWrapper\b|reconfigure", "3.7 reconfigure"),
    (r"\bstr\.isascii|\.isascii\(", "3.7"),
    (r"functools\.cache\b|cached_property", "3.8/3.9"),
    (r"\bmath\.isqrt\b|math\.dist\b|math\.comb\b|math\.perm\b", "3.8"),
    (r"\bsys\.unraisablehook|sys\.audit", "3.8"),
    (r"\bthreading\.excepthook|threading\.get_native_id", "3.8"),
    (r"\bTypeError\b.*positional-only", ""),
    (r"\bsocket\.create_server", "3.8"),
    (r"\bsubprocess\.run\(", "subprocess.run 3.5 OK ama text=/capture_output= 3.7"),
    (r"\.\bstem\b|\.\bis_relative_to\b", "pathlib 3.9"),
    (r"^\s*async |^\s*await ", "async (3.5 OK; 3.7 anahtar kelime)"),
]:
    for m in re.finditer(desen, kaynak, re.M):
        satir = kaynak.count("\n", 0, m.start()) + 1
        print("  METIN satir %d: %r -> %s" % (satir, m.group(0)[:60], aciklama))

# 4) socketserver/http.server 3.6 API kullanimlari — elle listele
print("\nhttp.server / socketserver kullanimlari:")
for d in ast.walk(agac):
    if isinstance(d, ast.Attribute) and d.attr in (
            "daemon_threads", "allow_reuse_address", "server_address", "serve_forever",
            "shutdown", "server_close", "wfile", "rfile", "send_response", "send_header",
            "end_headers", "address_string", "protocol_version", "server_version",
            "wait_for", "notify_all", "is_set", "reconfigure", "flush"):
        print("   satir %d .%s" % (d.lineno, d.attr))
