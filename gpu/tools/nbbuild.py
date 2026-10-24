"""Kaggle defterlerini Python kaynaklarından yazan küçük yardımcılar (gpu/tools/nb_*.py).

Defterler elle değil bu betiklerle düzenlenir: `python gpu/tools/nb_02_finetune.py` → `gpu/02_finetune.ipynb`.
"""

import json
from pathlib import Path

GPU = Path(__file__).resolve().parents[1]
METADATA = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "kaggle": {"accelerator": "gpu", "isInternetEnabled": True},
}


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


# 02 ve 03'te ortak: Ollama'nın içindeki llama-server'ı LoRA ile başlatmak. Hücrelerde „<<SERVER>>“ yerine geçer.
# Gerekenler: os, subprocess, OUT, OLLAMA_LIB, log, wait.
SERVER = '''
def server_env(gpu):
    """llama-server'ın CUDA arka ucunu bulduğu ortam: önce çalışma klasörü, olmazsa GGML_BACKEND_PATH."""
    cuda = sorted(OLLAMA_LIB.glob("cuda_v*"))
    libdir = cuda[-1] if cuda else OLLAMA_LIB
    base = {**os.environ, "CUDA_DEVICE_ORDER": "PCI_BUS_ID", "CUDA_VISIBLE_DEVICES": str(gpu),
            "LD_LIBRARY_PATH": f"{libdir}:{OLLAMA_LIB}:" + os.environ.get("LD_LIBRARY_PATH", "")}
    tried = []
    for extra in ({}, {"GGML_BACKEND_PATH": str(libdir / "libggml-cuda.so")}):
        env = {**base, **extra}
        r = subprocess.run([str(OLLAMA_LIB / "llama-server"), "--list-devices"], env=env, cwd=libdir,
                           capture_output=True, text=True, timeout=300)
        devices = [l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("CUDA")]
        if devices:
            return env, libdir, devices
        tried.append((r.stdout + r.stderr)[-800:])
    raise RuntimeError("llama-server CUDA'yı bulamadı (--list-devices):\\n" + "\\n---\\n".join(tried))

def gpu_mem_mib(gpu):
    """nvidia-smi'ye göre kullanılan GPU belleği (MiB); nvidia-smi yoksa None."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-i",
                              str(gpu)], capture_output=True, text=True).stdout
        return int(out.strip().splitlines()[0])
    except Exception:
        return None

def start_server(gpu, port, model_blob, loras, slots=1, ctx=12288, draft=None):
    """Ollama'nın içindeki llama-server; baseline'daki komutla aynı ayarlar + LoRA (istek başına ölçek)."""
    env, libdir, devices = server_env(gpu)
    before = gpu_mem_mib(gpu)
    cmd = [str(OLLAMA_LIB / "llama-server"), "--model", model_blob, "--port", str(port), "--host", "127.0.0.1",
           "--no-webui", "--offline", "-c", str(slots * ctx), "-np", str(slots), "-ngl", "999", "--flash-attn", "auto",
           "-b", "1024", "-ub", "1024"]
    if draft:
        cmd += ["--spec-type", "draft-mtp", "--spec-draft-n-max", "3", "--spec-draft-backend-sampling",
                "--spec-draft-model", draft]
    if loras:
        cmd += ["--lora", ",".join(str(p) for p in loras), "--lora-init-without-apply"]
    logfile = OUT / f"llama_server_gpu{gpu}.log"
    proc = subprocess.Popen(cmd, env=env, cwd=libdir, stdout=open(logfile, "w"), stderr=subprocess.STDOUT)
    try:
        wait(f"http://127.0.0.1:{port}/health", 900, proc, logfile.name)
    except Exception:
        log(f"llama-server başlamadı; günlüğün sonu:\\n{logfile.read_text(errors='replace')[-3000:]}")
        raise
    after = gpu_mem_mib(gpu)
    log(f"  llama-server GPU {gpu}: {(devices or ['?'])[0]} · GPU belleği {before} → {after} MiB")
    if before is not None and after is not None and after - before < 2000:     # model ~5 GB
        proc.terminate()
        log(f"Model GPU'ya yüklenmedi; günlüğün sonu:\\n{logfile.read_text(errors='replace')[-3000:]}")
        raise RuntimeError(f"llama-server modeli GPU'ya yüklemedi ({logfile.name})")
    return proc
'''


def write(name: str, cells: list[dict], target: Path | None = None) -> Path:
    path = target or GPU / name
    for c in cells:
        if any("<<SERVER>>" in line for line in c["source"]):
            text = "".join(c["source"]).replace("<<SERVER>>", SERVER.strip("\\n"))
            c["source"] = text.splitlines(keepends=True)
    nb = {"cells": cells, "metadata": METADATA, "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("yazıldı:", path, len(cells), "hücre")
    return path
