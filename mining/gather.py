embed
<drac2>
ch = character()
data = load_json(get_gvar("c2535af3-0e34-44dc-9412-c1d72c9a70f6"))
using(
    cdlib="cc413a98-489e-49f9-aac2-907993761792"
)

cd = cdlib.Cooldowns()
# Cooldown in seconds
# TODO: Bump to 3000 after testing
cooldown = 5

FOOTER = "!mining help, list | @konnivingkrook#0"
thumb = f' -thumb "{ch.image}"' if ch.image else ""

nodes = data.get("nodes", [])
tiers = data.get("tiers", {})
tier_aliases = data.get("tier_aliases", {})

args = [a.lower() for a in &ARGS&]
cmd = args[0] if args else ""

use_adv = "adv" in args
use_dis = "dis" in args
use_guidance = ("guidance" in args) or ("g" in args)
found_node = False

acceptable_tools = ["Mason's Tools"]
def quote(s):
    return (s or "").replace("\"", "'")

def build(title, desc_lines=None, fields=None):
    desc = "\n".join(desc_lines or [])
    out = [
        f'-title "{quote(title)}"',
        f'-desc "{quote(desc)}"',
        f'-footer "{FOOTER}"',
    ]
    if thumb:
        out.append(thumb)
    for n, v in (fields or []):
        if v:
            out.append(f'-f "{quote(n)}|{quote(v)}"')
    return " ".join(out)

# ---- help / list ----
if cmd in ["help", "list", "?"]:
    tier_names = ", ".join(tiers.keys()) if tiers else "none"

    by_tier = {}
    for n in nodes:
        t = (n.get("tier") or "unknown").lower()
        by_tier.setdefault(t, []).append(n.get("id") or "unknown")

    lines = []
    lines.append("**Mining**")
    lines.append("Mine a random node (weighted by rarity), optionally filtering by tier.")
    lines.append("")
    lines.append("**Usage**")
    lines.append("- `!mining`")
    lines.append(f"- `!mining <tier>` where tier is one of: `{tier_names}`")
    lines.append("- Optional: add `adv` or `dis`")
    lines.append("- Optional: add `guidance`")
    lines.append("")
    lines.append("**Tiers**")

    tier_list = list(by_tier.keys())
    tier_list.sort()

    for t in tier_list:
        id_list = list(by_tier[t])
        id_list.sort()
        ids = ", ".join(id_list)
        dc_val = tiers.get(t, {}).get("dc", "?")
        lines.append(f"- **{t}** (DC {dc_val}): {ids}")

    title = "Mining Help" if cmd != "list" else "Mining List"
    return build(title, lines, [])

# ---- Cooldown Ready? ----
gate = cd.gate("mining", cooldown, set_on_pass=False)
if not gate["ok"]:
    title = "Mining"
    lines = []
    lines.append(f"Available: {cd.ts(gate['expiry'], 'R')} ")
    return build(title, lines, [])

cd.set_timer("mining", cooldown)
cd.save()

# ---- tier or all ----
tier = tier_aliases.get(cmd, cmd)
mode = "tier" if tier in tiers else "all"

pool = nodes if mode == "all" else [n for n in nodes if (n.get("tier") or "").lower() == tier]
if not pool:
    mode = "all"
    pool = nodes

weights = [int(n.get("rarity", 1)) for n in pool]
node = randchoices(pool, weights=weights)[0]

# Flat DC from tier table
node_tier = (node.get("tier") or "crude").lower()
dc_val = int(tiers.get(node_tier, {}).get("dc"))
dc = vroll(str(dc_val))

# Roll Nature first (find the node)
nat = ch.skills.nature
nat_expr = ""

if use_adv and not use_dis:
    nat_expr = nat.d20(base_adv=True)
elif use_dis and not use_adv:
    nat_expr = nat.d20(base_adv=False)
else:
    nat_expr = nat.d20()

nat_expr += ("+1d4[guidance]" if use_guidance else "")
nat_check = vroll(nat_expr)

found_node = nat_check.total >= dc.total

# Prepare outputs
points = 0
point_str = ""
extract_check = ""  # set later
extract_name = ""   # set later
desc_lines = []

if not found_node:
    desc_lines.append("You search the rock face for anything worth working...")
    desc_lines.append("")
    desc_lines.append(f"**Tier:** {node_tier} (DC {dc_val})")
    desc_lines.append("")
    desc_lines.append("You can’t find a workable node here.")
    fields = [
        ("Nature", str(nat_check)),
        ("Resources", "No resources gained.")
    ]
    return build("Mining", desc_lines, fields)


# ----- Determine prof/expertise first (before selecting extraction method) -----
# Mason's Tools prof/exp from cvars (safe defaults)
tool_prof = False
tool_exp = False

e_tools = (ch.get_cvar("eTools") or "")
p_tools = (ch.get_cvar("pTools") or "")
tool_exp_lst = [t.strip().lower() for t in e_tools.split(",").lower() if t.strip()]
tool_prof_lst = [t.strip().lower() for t in p_tools.split(",").lower() if t.strip()]

for t in acceptable_tools:
    if t in tool_exp_lst:
        tool_exp = True
    if t in tool_prof_lst:
        tool_prof = True

# Athletics proficiency/expertise (best effort)
ath = ch.skills.athletics

ath_prof = False
ath_exp = False

try:
    ath_prof = bool(ath.prof)
except "NotDefined":
    ath_prof = False

if not ath_prof:
    try:
        ath_prof = bool(ath.proficient)
    except "NotDefined":
        ath_prof = False

try:
    ath_exp = bool(ath.expert)
except "NotDefined":
    ath_exp = False

if not ath_exp:
    try:
        ath_exp = bool(ath.expertise)
    except "NotDefined":
        ath_exp = False


# ---- Choose best extraction method (Athletics vs Mason's Tools) ----
ath_tier = 2 if ath_exp else (1 if ath_prof else 0)
tool_tier = 2 if tool_exp else (1 if tool_prof else 0)

use_tools = False
if tool_tier > ath_tier:
    use_tools = True
elif tool_tier == ath_tier:
    use_tools = True if tool_tier > 0 else False


# ---- Roll extraction ----
extract_expr = ""

if not use_tools:
    extract_name = "Athletics"
    if use_adv and not use_dis:
        extract_expr = ath.d20(base_adv=True)
    elif use_dis and not use_adv:
        extract_expr = ath.d20(base_adv=False)
    else:
        extract_expr = ath.d20()
else:
    extract_name = "Mason's Tools (STR)"

    # Advantage/disadvantage core (keep simple, then add mods)
    d20_expr = "1d20"
    if use_adv and not use_dis:
        d20_expr = "2d20kh1"
    elif use_dis and not use_adv:
        d20_expr = "2d20kl1"

    # Strength mod (safe)
    str_mod = 0
    try:
        str_mod = int(ch.stats.str.mod)
    except "NotDefined":
        str_mod = 0

    # Proficiency bonus (safe)
    pb = 0
    try:
        pb = int(ch.stats.prof_bonus)
    except "NotDefined":
        pb = 0

    extract_expr = f"{d20_expr}"

    # Strength mod
    extract_expr += f"+{str_mod}[mod]"

    # Proficiency / Expertise
    if tool_exp:
        extract_expr += f"+{pb}[prof]"
        extract_expr += f"+{pb}[expert]"
    elif tool_prof:
        extract_expr += f"+{pb}[prof]"

# Guidance
extract_expr += ("+1d4[guidance]" if use_guidance else "")

extract_check = vroll(extract_expr)
extracted = extract_check.total >= dc.total

# ---- Points (output) ----
if extracted:
    points = 1
    point_str = "1 for Pickaxe"
    if use_adv and not use_dis:
        points += 1
        point_str += "\n+1 for Advantage"
    if ath_prof or tool_prof or tool_exp or ath_exp:
        points += 1
        point_str += "\n+1 for Proficiency"
    if ath_exp or tool_exp:
        points += 1
        point_str += "\n+1 for Expertise"
else:
    point_str = "No resources gained."

desc_lines.append(node.get("found") or "")
desc_lines.append("")
desc_lines.append(f"**Tier:** {node_tier} (DC {dc_val})")
desc_lines.append((node.get("pass") if extracted else node.get("fail")) or "")

fields = [
    ("Nature", str(nat_check)),
    (extract_name, str(extract_check)),
    ("Resources", f"{points}\n{point_str}" if extracted else "0\nNo resources gained.")
]

return build("Mining (Preview)", desc_lines, fields)
</drac2>
