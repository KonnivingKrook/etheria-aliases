# CooldownLib (GVAR)

CooldownLib is a small, project-focused utility library for Avrae (Drac2) that provides reusable, persistent cooldown timers.

It is designed to live in a GVAR and be imported into aliases or other GVARs via `using(...)`.

The library tracks time only.
Policy, messaging, and grouping are left entirely to the calling project.

---

## Purpose

CooldownLib exists to:

* Replace per-alias `last_*` cvars
* Avoid hardcoded cooldown keys
* Allow unlimited cooldown timers without modifying the library
* Centralize cooldown logic in one place
* Use expiry timestamps for simple math and display
* Interoperate with external start-time cvars (e.g. `last_hunt` from a third-party alias)

---

## Storage Model

### Internal store

Cooldowns are stored in a single character cvar as a dictionary:

```
{
  "forage": 1768600123,
  "hunt": 1768600300,
  "mine:iron": 1768600500
}
```

* Keys are arbitrary strings
* Values are integer expiry epoch timestamps
* Expired entries are pruned automatically

The default cvar name is:

```
cooldowns
```

You may override this per project.

### External start-time cvars

`gate_cvar()` operates on a separate cvar that stores a **start** timestamp (not expiry), as used by aliases like `!hunt`:

```
last_hunt: 1768600000
```

This allows sharing a cooldown with external aliases without modifying them.

---

## Public Interface

The library exposes:

* A single constructor function
  `Cooldowns(...)`

* Two constants
  `COOLDOWNLIB_VERSION`
  `DEFAULT_CVAR`

Everything else is returned by the constructor.

---

## Constructor

Cooldowns(cvar=DEFAULT_CVAR, *, user_mode=True)

### Parameters

* cvar
  Name of the character cvar used for internal storage

* user_mode
  If False, disables persistence and operates in memory only

### Returns

A dictionary-like object with dot access that contains:

* Internal state
* Cooldown data
* Helper methods

Example:

```
cd = Cooldowns()
gate = cd.gate_cvar("last_hunt", 7200)
if not gate["ok"]:
    err(f"Available: {cd.ts(gate['expiry'], 'R')}")
```

---

## Returned Properties

### store

```
cd.store
```

The internal dictionary of cooldowns.

Keys are strings.
Values are expiry timestamps.

This is exposed for inspection only. Avoid mutating directly.

---

### error

```
cd.error
```

Boolean flag indicating whether a load or parse error occurred.

If True, save() will refuse to write.

---

## Core Methods

### prune(now=None)

Removes expired or invalid cooldown entries from the internal store.

* Automatically called on load and save
* Returns the number of entries removed

---

### get_expiry(key)

Returns the expiry timestamp for a key, or None.

---

### remaining(key, now=None)

Returns remaining cooldown time in seconds from the internal store.

Returns 0 if the cooldown is ready or missing.

---

### ready(key, now=None)

Returns True if the cooldown is ready.

---

### set_timer(key, seconds, now=None)

Sets a cooldown in the internal store.

* key is converted to string
* seconds is clamped to >= 0
* Returns the expiry timestamp

---

### clear(key)

Removes a cooldown entry from the internal store.

Returns True if an entry was removed.

---

### save(error=False)

Persists the internal store back to the character cvar.

* Automatically prunes expired entries
* Will not save if:

  * error=True
  * internal error flag is set
  * user_mode=False

Return values:

* 1 for success
* -1 for failure

---

## Gate Helpers

Gate helpers combine checking and setting logic but do not enforce messaging.

### gate(key, seconds, now=None, set_on_pass=True)

Single-key cooldown gate against the internal store.

Returns a result object:

```
{
  ok: bool
  key: str
  now: int
  seconds: int
  expiry: int | None
  remaining: int
}
```

Behavior:

* If ready, optionally sets the cooldown via set_timer
* If blocked, does not modify state
* Caller is responsible for calling save() afterward

---

### gate_cvar(cvar_name, seconds, now=None, set_on_pass=True)

Cooldown gate against an external start-time cvar.

Reads the cvar as a plain epoch float (start time), computes expiry as
`start + seconds`, and writes `now` back to the cvar on a passing run.

Use this when sharing a cooldown with an external alias that stores its
own timestamp (e.g. `last_hunt`).

Returns a result object:

```
{
  ok: bool
  cvar: str
  now: int
  seconds: int
  expiry: int | None
  remaining: int
}
```

Behavior:

* Does not use the internal store
* Does not require save()
* Writes directly to the character cvar on pass

Example:

```
gate = cd.gate_cvar("last_hunt", 7200)
if not gate["ok"]:
    err(f"Available: {cd.ts(gate['expiry'], 'R')}")
```

---

### gate_any(keys, seconds, now=None, set_on_pass=True)

Shared cooldown gate against the internal store.

* Blocked if any key in the list is still cooling down
* On success, all keys are set to the same expiry
* Caller is responsible for calling save() afterward

Returns:

```
{
  ok: bool
  blocked: list
  next_expiry: int | None
  now: int
}
```

---

## Time Formatting Helpers

These helpers exist for Discord-friendly output.

### ts(expiry, style="R")

Returns a Discord timestamp string.

Styles:

* R relative
* D date
* T time

---

### format_window(expiry, now=None)

Human-friendly formatting rules:

* Under 91 seconds
  in X seconds

* Under 24 hours
  Relative timestamp

* Over 24 hours
  Date and time timestamps

---

### format_remaining(seconds, now=None)

Formats a duration (in seconds from now) using the same rules as format_window.

Convenience wrapper for displaying cooldown lengths before a timer is set.

---

## Design Constraints

CooldownLib intentionally:

* Uses only Avrae-safe features
* Avoids imports
* Avoids classes
* Uses a single cvar for internal storage
* Does not define cooldown policy
* Does not assume alias names or command structure

All higher-level behavior belongs in the calling project.

---

## Versioning

```
COOLDOWNLIB_VERSION
```

Current version: 1.3

Increment this if you ever need to migrate stored data.

---

## Intended Usage Patterns

### Internal store (independent cooldowns)

```
cd = Cooldowns()

gate = cd.gate("mining", 7200)
if not gate["ok"]:
    err(f"Available: {cd.ts(gate['expiry'], 'R')}")

cd.save()
```

### External start-time cvar (shared with third-party alias)

```
cd = Cooldowns()

gate = cd.gate_cvar("last_hunt", 7200)
if not gate["ok"]:
    err(f"Available: {cd.ts(gate['expiry'], 'R')}")
```

No save() needed — gate_cvar writes directly.

---

## Summary

CooldownLib is a foundational utility.

It tracks time.
It stays out of the way.
Everything else is your project's responsibility.
