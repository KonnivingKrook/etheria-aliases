# CooldownLib
# Stores cooldowns as expiry epoch seconds in one cvar dict:
# { "key": expiry_epoch_seconds }

COOLDOWNLIB_VERSION = "1.0"
DEFAULT_CVAR = "cooldowns"

ch = character()

def Cooldowns(cvar=DEFAULT_CVAR, *, user_mode=True):
    store = {}
    state = {"error": False, "cvar": cvar}

    def _now():
        return int(float(time()))

    def _load():
        nonlocal store
        if not user_mode:
            store = {}
            return
        raw = ch.get_cvar(cvar, "{}")
        try:
            data = load_yaml(raw)
            store = data if typeof(data) == "SafeDict" else {}
        except:
            store = {}
            state["error"] = True

    def prune(now=None):
        now = _now() if now is None else int(now)
        removed = 0
        for k in list(store.keys()):
            try:
                if int(store[k]) <= now:
                    store.pop(k, None)
                    removed += 1
            except:
                store.pop(k, None)
                removed += 1
        return removed

    def get_expiry(key):
        key = str(key)
        if key not in store:
            return None
        try:
            return int(store[key])
        except:
            return None

    def remaining(key, now=None):
        now = _now() if now is None else int(now)
        exp = get_expiry(key)
        if not exp:
            return 0
        return max(0, exp - now)

    def ready(key, now=None):
        return remaining(key, now=now) == 0

    def set(key, seconds, now=None):
        now = _now() if now is None else int(now)
        key = str(key)
        seconds = max(0, int(seconds))
        exp = now + seconds
        store[key] = exp
        return exp

    def clear(key):
        return store.pop(str(key), None) is not None

    def save(error=False):
        if not user_mode or error or state["error"]:
            return -1
        prune()
        ch.set_cvar(cvar, dump_json(store))
        return 1

    # Discord timestamp helpers
    def ts(expiry, *, style="R"):
        expiry = int(expiry)
        return f"<t:{expiry}:{style}>"

    def format_window(expiry, now=None):
        # Matches your style:
        # - under 91 seconds: raw seconds
        # - under 1 day: relative timestamp
        # - otherwise: date + time
        now = _now() if now is None else int(now)
        expiry = int(expiry)
        delta = max(0, expiry - now)

        if delta < 91:
            return f"in {delta} seconds"
        if delta <= 86400:
            return ts(expiry, style="R")
        return f"on {ts(expiry, style='D')} at {ts(expiry, style='T')}"

    # Single-key gate
    def gate(key, seconds, *, now=None, set_on_pass=True):
        now = _now() if now is None else int(now)
        key = str(key)

        rem = remaining(key, now=now)
        exp = get_expiry(key)
        ok = rem == 0

        if ok and set_on_pass and int(seconds) > 0:
            exp = set(key, seconds, now=now)
            rem = 0

        return {
            "ok": ok,
            "key": key,
            "now": now,
            "seconds": int(seconds),
            "expiry": exp,
            "remaining": rem,
        }

    # Any-of group gate (shared cooldown family)
    def gate_any(keys, seconds, *, now=None, set_on_pass=True):
        now = _now() if now is None else int(now)
        keys = [str(k) for k in keys]

        blocked = []
        next_expiry = None

        for k in keys:
            exp = get_expiry(k)
            if exp:
                rem = max(0, int(exp) - now)
                if rem > 0:
                    blocked.append({"key": k, "expiry": int(exp), "remaining": rem})
                    if next_expiry is None or int(exp) > next_expiry:
                        next_expiry = int(exp)

        ok = len(blocked) == 0

        if ok and set_on_pass and int(seconds) > 0:
            exp = now + int(seconds)
            for k in keys:
                store[k] = exp

        return {"ok": ok, "blocked": blocked, "next_expiry": next_expiry, "now": now}

    _load()
    prune()

    # Return state + functions (dot-access friendly)
    functions = {
        "store": store,
        "prune": prune,
        "get_expiry": get_expiry,
        "remaining": remaining,
        "ready": ready,
        "set": set,
        "clear": clear,
        "save": save,
        "ts": ts,
        "format_window": format_window,
        "gate": gate,
        "gate_any": gate_any,
    }

    return state | functions
