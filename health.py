embed
<drac2>
# !health
# Initiative HP summary for party and monsters.

args = [a.lower() for a in &ARGS&]
cb = combat()
ch = character()

FOOTER = "!health ? | @konnivingkrook#0"
thumb = f' -thumb "{ch.image}"' if ch.image else ''

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def q(s):
    return (s or "").replace("\"", "'")

def build(title, desc_lines=None, fields=None):
    desc = "\n".join(desc_lines or [])
    out = [
        f'-title "{q(title)}"',
        f'-desc "{q(desc)}"',
        f'-footer "{FOOTER}"',
    ]
    if thumb:
        out.append(thumb)
    for n, v in (fields or []):
        if v:
            out.append(f'-f "{q(n)}|{q(v)}"')
    return " ".join(out)

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------

show_help = ("help" in args) or ("?" in args)
details = ("details" in args) or ("det" in args) or ("d" in args)

mode = "party"  # party|monsters|all
if ("all" in args) or ("a" in args):
    mode = "all"
elif ("m" in args) or ("mon" in args) or ("monster" in args):
    mode = "monsters"

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

if show_help:
    return build(
        "Health Help",
        [
            "**Usage**",
            "- `!health`",
            "- `!health m`",
            "- `!health all`",
            "- `!health d`",
            "",
            "**What it does**",
            "- Shows current HP for combatants in initiative.",
            "- `d` adds effects and resistances for party only.",
            "",
            "**Notes**",
            "- Requires an active initiative.",
        ],
    )

# ---------------------------------------------------------------------------
# No initiative
# ---------------------------------------------------------------------------

if cb is None:
    return build(
        "No Initiative",
        [
            "You take stock of bruises and breathing...",
            "But there is no turn order to anchor it.",
            "",
            "Start initiative, then try `!health` again.",
        ],
    )

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def join_dtypes(res_list):
    return ", ".join([r.dtype for r in (res_list or [])])

def join_effects(eff_list):
    return ", ".join([e.name for e in (eff_list or [])])

def party_block(c):
    if not details:
        return f"**{c.name}**: {c.hp_str()}"

    lines = [f"**{c.name}**:", f"> {c.hp_str()}"]

    eff = join_effects(c.effects)
    imm = join_dtypes(c.resistances.immune)
    res = join_dtypes(c.resistances.resist)

    if eff:
        lines.append(f"> Effects: {eff}")
    if imm:
        lines.append(f"> Immunities: {imm}")
    if res:
        lines.append(f"> Resistances: {res}")

    return "\n".join(lines)

def monster_block(c):
    return f"**{c.name}**: {c.hp_str()}"

party_lines = []
monster_lines = []

for c in cb.combatants:
    if c.hp is None:
        continue
    if c.monster_name is None:
        party_lines.append(party_block(c))
    else:
        monster_lines.append(monster_block(c))

party_text = "\n".join(party_lines)
monster_text = "\n".join(monster_lines)

fields = []
if mode in ["party", "all"]:
    fields.append(("Party", party_text or "None"))
if mode in ["monsters", "all"]:
    fields.append(("Monsters", monster_text or "None"))

return build(
    "Initiative Health Summary",
    ["Let's see how we're doing!"],
    fields,
)
</drac2>
