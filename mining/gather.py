embed
<drac2>
ch = character()
data = load_json(get_gvar("c2535af3-0e34-44dc-9412-c1d72c9a70f6"))

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
ath_check = ""  # only filled if we actually mine
desc_lines = []

if not found_node:
    desc_lines.append("You search the rock face for anything worth working...")
    desc_lines.append("")
    desc_lines.append(f"**Tier:** {node_tier} (DC {dc_val})")
    desc_lines.append("You can’t find a workable node here.")
    fields = [
        ("Nature", str(nat_check)),
        ("Resources", "No resources gained.")
    ]
    return build("Mining", desc_lines, fields)

# If we found a node, now roll Athletics (extract)
ath = ch.skills.athletics
ath_expr = ""

if use_adv and not use_dis:
    ath_expr = ath.d20(base_adv=True)
elif use_dis and not use_adv:
    ath_expr = ath.d20(base_adv=False)
else:
    ath_expr = ath.d20()

ath_expr += ("+1d4[guidance]" if use_guidance else "")
ath_check = vroll(ath_expr)


extracted = ath_check.total >= dc.total

# Mason's Tools proficiency (best effort)
tool_prof = False
tool_exp = False
prof_text = ""

tool_exp_lst = ch.get_cvar("eTools").split(',')
tool_prof_lst = ch.get_cvar("pTools").split(',')

for t in acceptable_tools:
    if t in tool_exp_lst:
        tool_exp = True
    if t in tool_prof_lst: 
        tool_prof = True


# Athletics proficiency/expertise (best effort)
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


# Check for
        
# TODO: Check for a pickaxe in inventory? or just assume?
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
    ("Athletics", str(ath_check)),
    ("Resources", f"{points}\n{point_str}" if extracted else "0\nNo resources gained.")
]

return build("Mining (Preview)", desc_lines, fields)
</drac2>
