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

chosen = find_node(nodes, want) if want else None
fallback = False
if want and not chosen:
    fallback = True
chosen = chosen or pick_weighted(nodes)

check = vroll(ch.skills.athletics.d20())
dc = vroll(chosen.get("dc") or "10")
passed = check.total >= dc.total

desc = chosen.get("found") or ""
if fallback:
    desc = f"_Couldn't find `{want}`. Mining a random node instead._\n\n" + desc

desc += f"\n\n**Athletics:** {check.total} vs **DC:** {dc.total}\n\n"
desc += (chosen.get("pass") if passed else chosen.get("fail")) or ""
</drac2>
-title "Mining"
-desc "{{desc}}"
-f "Athletics Roll|{{check}}"
-f "DC Roll|{{dc}}"
