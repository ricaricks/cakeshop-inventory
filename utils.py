import threading

_root = None


def set_root(r):
    global _root
    _root = r


def run_bg(fn, *args, callback=None):
    def worker():
        try:
            result = fn(*args)
        except Exception as e:
            result = {"_error": str(e)}
        if callback and _root:
            _root.after(0, lambda: callback(result))
    threading.Thread(target=worker, daemon=True).start()


def extract_list(data, *keys):
    inner = data.get("data")
    if isinstance(inner, list):
        return inner
    if isinstance(inner, dict):
        for k in keys:
            if k in inner:
                return inner[k]
    return []