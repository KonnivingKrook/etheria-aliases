embed
<drac2>
using(
    baglib = "5f1ffcbf-3f59-4396-b402-1ca0f02d6bbb"
)

# !sellharvest
# Sells (or checks) harvest bags using a shared price table.

args = [a.lower() for a in &ARGS&]
ch = character()

FOOTER = "!sellharvest ? | @konnivingkrook#0"
thumb = f' -thumb "{ch.image}"' if ch.image else ''

PRICE_GVAR = "5f3a0cfc-3232-40b7-809f-3e8bb250acc7"
CATEGORIES = ["Forage", "Meat", "Fish", "Marine"]

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
# Mode
# ---------------------------------------------------------------------------

mode = "trade"  # trade|check|help
if args:
    a0 = args[0]
    if a0 in ["help", "?"]:
        mode = "help"
    elif a0 in ["check", "dry", "c", "d"]:
        mode = "check"

check = (mode == "check")

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

if mode == "help":
    return build(
        "Sellharvest Help",
        [
            "**Usage**",
            "- `!sellharvest`",
            "- `!sellharvest check`  (or `c`)",
            "- `!sellharvest help`   (or `?`)",
            "",
            "**What it does**",
            "- Looks in the Forage, Meat, Fish, and Marine bags.",
            "- Values each item (per lb) using a shared price table.",
            "- In normal use, removes sold items and adds gp (rounded down).",
            "- In `check` mode, shows what would sell but makes no changes.",
            "",
            "**Notes**",
            "- Assumes each unit equals 1 lb.",
            f"- Prices come from GVAR `{PRICE_GVAR}`.",
        ],
    )

# ---------------------------------------------------------------------------
# Scan (no mutation)
# ---------------------------------------------------------------------------

bags = baglib.LoadedBags()
price_data = load_json(get_gvar(PRICE_GVAR))

groups = price_data.get("groups", {})
species_map = price_data.get("species", {})

sold_lines = []
unknown = {}

# Summary by bag
bag_item_counts = {}
bag_weight_counts = {}

# Transaction list for trade mode
transactions = []

total_cp = 0

for bag_name, contents in bags.internal_bag_data:
    if bag_name not in CATEGORIES:
        continue

    category_prices = species_map.get(bag_name, {})

    for item, qty in contents.items():
        group_id = category_prices.get(item)
        cp_per_lb = groups.get(group_id, 0) if group_id else 0

        if cp_per_lb <= 0:
            unknown.setdefault(bag_name, []).append(f"{item} ({qty} lb)")
            continue

        value_cp = int(qty * cp_per_lb)
        total_cp += value_cp

        sold_lines.append(f"**{bag_name}** - {item}: {qty} lb -> {value_cp / 100.0:.2f} gp")

        bag_item_counts[bag_name] = bag_item_counts.get(bag_name, 0) + 1
        bag_weight_counts[bag_name] = bag_weight_counts.get(bag_name, 0) + qty

        transactions.append({"bag": bag_name, "item": item, "qty": qty})

# ---------------------------------------------------------------------------
# Mutations (trade only)
# ---------------------------------------------------------------------------

if (mode == "trade") and total_cp > 0:
    earned_gp = total_cp // 100
    if earned_gp:
        bags.modify_coins("gp", earned_gp)

if (mode == "trade") and transactions:
    for t in transactions:
        qtty = int(t["qty"])
        if qtty > 0:
            bags.modify_item(item=t["item"], quantity=-qtty, bag_name=t["bag"])
    bags.save_bags()

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

lines = []
fields = []

if total_cp <= 0:
    title = "Nothing to Sell"
    lines.append(f"**{ch.name}** looks over their harvest bags, but finds nothing the market is buying today.")
    lines.append("")
    lines.append("No sellable harvesting goods were found in your Forage, Meat, Fish, or Marine bags.")
else:
    title = "Harvest Sale Check" if check else "Harvest Sale Complete"
    if check:
        lines.append(f"**{ch.name}** tallies what the market would pay.")
    else:
        lines.append(f"**{ch.name}** brings their latest harvest to market and settles up with the traders.")

    lines.append("")
    lines.extend(sold_lines)
    lines.append("")
    lines.append(f"**Total Value:** {total_cp / 100.0:.2f} gp")

    if bag_item_counts:
        lines.append("")
        lines.append("**Summary by Bag**")
        for bn in sorted(bag_item_counts.keys()):
            lines.append(f"- {bn}: {bag_item_counts[bn]} item(s), {bag_weight_counts[bn]} lb total")

    lines.append("")
    if check:
        lines.append("_Check only: no items were sold and no coins were added._")
    else:
        lines.append("_Your harvest bags have been updated and your coin purse now includes these earnings._")

if unknown:
    lines.append("")
    lines.append("**Unpriced items (not sold):**")
    for bn, items in unknown.items():
        lines.append(f"- **{bn}**: " + ", ".join(items))

return build(title, lines, fields)
</drac2>
