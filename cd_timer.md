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

---

## Storage Model

Cooldowns are stored in a single character cvar as a dictionary:

```
{
  "forage": 1768600123,
  "hunt": 1768600300,
  "mine:iron": 1768600500
}
```

* Keys are arbitrary strings
* Values are integer epoch timestamps
* Expired entries are pruned automatically

The default cvar name is:

```
cooldowns
```

You may override this per project.

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
  Name of the character cvar used for storage

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
cd.gate("forage", 1800)
cd.save()
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

Removes expired or invalid cooldown entries.

* Automatically called on load and save
* Returns the number of entries removed

---

### get_expiry(key)

Returns the expiry timestamp for a key, or None.

---

### remaining(key, now=None)

Returns remaining cooldown time in seconds.

Returns 0 if the cooldown is ready or missing.

---

### ready(key, now=None)

Returns True if the cooldown is ready.

---

### set(key, seconds, now=None)

Sets a cooldown.

* key is converted to string
* seconds is clamped to >= 0
* Returns the expiry timestamp

---

### clear(key)

Removes a cooldown entry.

Returns True if an entry was removed.

---

### save(error=False)

Persists cooldowns back to the character cvar.

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

### gate(key, seconds, *, now=None, set_on_pass=True)

Single-key cooldown gate.

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

* If ready, optionally sets the cooldown
* If blocked, does not modify state

---

### gate_any(keys, seconds, *, now=None, set_on_pass=True)

Shared cooldown gate.

* Blocked if any key in the list is still cooling down
* On success, all keys are set to the same expiry

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

## Design Constraints

CooldownLib intentionally:

* Uses only Avrae-safe features
* Avoids imports
* Avoids classes
* Uses a single cvar
* Does not define cooldown policy
* Does not assume alias names or command structure

All higher-level behavior belongs in the calling project.

---

## Versioning

```
COOLDOWNLIB_VERSION
```

Increment this if you ever need to migrate stored data.

---

## Intended Usage Pattern

Load once, gate actions, save once.

```
cd = Cooldowns()

r = cd.gate("some:key", duration)
if not r.ok:
    err("Blocked")

cd.save()
```

---

## Summary

CooldownLib is a foundational utility.

It tracks time.
It stays out of the way.
Everything else is your project’s responsibility.

---

If you want, next we can add a **short header comment version** of this for the top of the GVAR itself, or tailor a **project-specific mini-readme** for your gathering system.
