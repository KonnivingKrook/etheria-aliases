embed
<drac2>
ch = character()
data = load_json(get_gvar("0bdc0d76-6bd1-42cb-92d4-274635c6a6bd"))
nodes = data.get("nodes", [])

args = [a.lower() for a in &ARGS&]
want = args[0] if args else ""

def pick_weighted(ns):
    total = sum(int(n.get("rarity", 1)) for n in ns)
    r = randint(1, total)
    run = 0
    for n in ns:
        run += int(n.get("rarity", 1))
        if r <= run:
            return n
    return ns[-1]

def find_node(ns, key):
    key = (key or "").lower()
    for n in ns:
        if (n.get("id","") or "").lower() == key:
            return n
    return None

node = find_node(nodes, want) if want else None
fallback = bool(want and not node)
targeted = bool(want and node)  # only true if they asked for a valid specific node
node = node or pick_weighted(nodes)

check = vroll(ch.skills.athletics.d20())

# DC: apply rarity-based penalty only when targeted
base_dc_expr = node.get("dc") or "10"
rarity = int(node.get("rarity", 10))
penalty = (10 - rarity) * 2 if targeted else 0

dc_expr = f"({base_dc_expr})+{penalty}" if penalty else base_dc_expr
dc = vroll(dc_expr)

passed = check.total >= dc.total

reward_roll = None
if passed:
    reward_roll = vroll(node.get("reward") or "0")

name = node.get("name") or node.get("id") or "Unknown"

desc = node.get("found") or ""
if fallback:
    desc = f"_Couldn't find `{want}`. Mining a random node instead._\n\n" + desc

desc += f"\n\n**Node:** {name}\n**Athletics:** {check.total} vs **DC:** {dc.total}"
if penalty:
    desc += f" _(targeted penalty +{penalty})_"
desc += "\n\n" + ((node.get("pass") if passed else node.get("fail")) or "")
</drac2>
-title "Mining"
-desc "{{desc}}"
-f "Athletics Roll|{{check}}"
-f "DC Roll|{{dc}}"
-f "Reward|{{reward_roll if reward_roll else '0'}}"
