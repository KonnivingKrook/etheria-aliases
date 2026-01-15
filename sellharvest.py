embed
<drac2>
using(
    baglib = "5f1ffcbf-3f59-4396-b402-1ca0f02d6bbb"
)

args = &ARGS&
ch = character()
footer = '!sellharvest help | @konnivingkrook#0'

# Thumbnail from active character, if any
thumb = f' -thumb "{ch.image}"' if ch.image else ''

# ---------------------------------------------------------------------------
# MODE SELECTION: help / check / trade(default)
# ---------------------------------------------------------------------------
mode = "trade"  # default: actual sale

if args:
    first = args[0].lower()
    if first in ["help", "?"]:
        mode = "help"
    elif first in ["check", "dry", "c", "d"]:
        mode = "check"
    else:
        mode = "trade"

check = (mode == "check")

# ---------------------------------------------------------------------------
# HELP SUBCOMMAND
# ---------------------------------------------------------------------------
if mode == "help":
    title = "sellharvest – Harvest Sale Helper"

    lines = [
        f"{ch.name} can turn their gathered meat, forage, fish, and marine harvest into coin at the local market.",
        "",
        "**Usage**",
        "- `!sellharvest`       |      — Sell your harvest (removes items, adds coins).",
        "- `!sellharvest check` | c    — Check the value of your harvest (no changes).",
        "- `!sellharvest help`  | ?    — Show this help message.",
        "",
        "**What it does**",
        "- Looks in the **Forage**, **Meat**, **Fish**, and **Marine** bags.",
        "- Uses a shared price table GVAR to value each species (per pound).",
        "- In normal use (`!sellharvest`), adds the total value to your coins and removes those items.",
        "- Or you can add `check` (`!sellharvest check`), shows what *would* be sold, but makes no changes.",
        "",
        "**Notes**",
        "- Assumes each unit in those bags equals **1 pound**.",
        "- Only the four harvest bags are processed; other bags are ignored.",
        "- Prices are managed in GVAR `5f3a0cfc-3232-40b7-809f-3e8bb250acc7`."
    ]
    desc = "\n".join(lines).replace('"', "'")
    return f'-title "{title}" -desc "{desc}" -footer "{footer}"{thumb}'

# ---------------------------------------------------------------------------
# NORMAL / TRADE EXECUTION
# ---------------------------------------------------------------------------

# Load BagLib instance for current character
bags = baglib.LoadedBags()

# Categories we sell from
sell_categories = ["Forage", "Meat", "Fish", "Marine"]

# Load price data
price_data = load_json(get_gvar("5f3a0cfc-3232-40b7-809f-3e8bb250acc7"))
groups = price_data.get("groups", {})
species_map = price_data.get("species", {})

total_cp = 0
sold_lines = []
unknown = {}

# Per-bag summary tracking
bag_item_counts = {}
bag_weight_counts = {}

# We will collect all items to remove into a transaction list (for trade)
transactions = []

# ---------------------------------------------------------------------------
# PASS 1: SCAN BAGS, CALCULATE VALUES (NO MUTATION)
# ---------------------------------------------------------------------------
bag_data = bags.internal_bag_data  # BagLib's current bag list

for bag in bag_data:
    bag_name = bag[0]
    contents = bag[1]

    if bag_name not in sell_categories:
        continue

    category_prices = species_map.get(bag_name, {})

    for item, qty in contents.items():
        group_id = category_prices.get(item)

        # Log unknown items and skip
        if not group_id:
            unknown.setdefault(bag_name, []).append(f"{item} ({qty} lb)")
            continue

        # Log unknown prices and skip
        cp_per_lb = groups.get(group_id, 0)
        if cp_per_lb <= 0:
            unknown.setdefault(bag_name, []).append(f"{item} ({qty} lb)")
            continue

        value_cp = int(qty * cp_per_lb)
        total_cp += value_cp

        gp_value = value_cp / 100.0
        sold_lines.append(f"**{bag_name}** – {item}: {qty} lb → {gp_value:.2f} gp")

        # summary tracking
        bag_item_counts[bag_name] = bag_item_counts.get(bag_name, 0) + 1
        bag_weight_counts[bag_name] = bag_weight_counts.get(bag_name, 0) + qty

        # record this sale for later mutation (only used in trade mode)
        transactions.append({"bag": bag_name, "item": item, "qty": qty})

# ---------------------------------------------------------------------------
# APPLY COIN PAYOUT (TRADE ONLY)
# ---------------------------------------------------------------------------
if (mode == "trade") and total_cp > 0:
    earned_gp = total_cp // 100
    # earned_cp = total_cp % 100

    # Add earned GP to player coins
    if earned_gp:
        bags.modify_coins("gp", earned_gp)
    # Gold should round down. No copper payout
    # if earned_cp:
    #     bags.modify_coins("cp", earned_cp)

# ---------------------------------------------------------------------------
# PASS 2: APPLY ITEM REMOVAL VIA BagLib (TRADE ONLY)
# ---------------------------------------------------------------------------
if (mode == "trade") and transactions:
    for t in transactions:
        q = int(t["qty"])  # Transform quantity into type(int)
        if q > 0:
            # Remove the sold items from the bag
            bags.modify_item(
                item=t["item"],
                quantity=-q,
                bag_name=t["bag"]
            )
    bags.save_bags()

# ---------------------------------------------------------------------------
# BUILD OUTPUT EMBED
# ---------------------------------------------------------------------------
if total_cp > 0:
    total_gp = total_cp / 100.0
    check_title = "Harvest Sale Check"
    sale_title = "Harvest Sale Complete"
    title = check_title if (mode == "check") else sale_title
else:
    total_gp = 0.0
    title = "Nothing to Sell"

lines = []

if total_cp > 0:
    if check:
        lines.append(f"**{ch.name} looks over their harvest and tallies what the market would pay.**")
    else:
        lines.append(f"**{ch.name} brings their latest harvest to market and settles up with the traders.**")
else:
    lines.append(f"**{ch.name} looks over their harvest bags, but finds nothing the market is buying today.**")

lines.append("")

# Sold items or base message
if total_cp > 0:
    lines.extend(sold_lines)
    lines.append("")
    lines.append(f"**Total Value:** {total_gp:.2f} gp")
else:
    lines.append("No sellable harvesting goods were found in your Forage, Meat, Fish, or Marine bags.")

# Per-bag summary
if bag_item_counts:
    lines.append("")
    lines.append("**Summary by Bag**")
    bag_names = list(bag_item_counts.keys())
    bag_names.sort()
    for bag_name in bag_names:
        item_count = bag_item_counts[bag_name]
        weight_total = bag_weight_counts[bag_name]
        lines.append(f"- {bag_name}: {item_count} item(s), {weight_total} lb total")

# Mode note
lines.append("")
if check:
    lines.append("_Check only: no items were sold and no coins were added._")
elif (mode == "trade") and total_cp > 0:
    lines.append("_Your harvest bags have been updated and your coin purse now includes these earnings._")

# Unknown species warnings
if unknown:
    lines.append("")
    lines.append("**Unpriced items (not sold; please update the price gvar):**")
    for bag_name, items in unknown.items():
        lines.append(f"- **{bag_name}**: " + ", ".join(items))

desc = "\n".join(lines).replace('"', "'")

return f'-title "{title}" -desc "{desc}" -footer "{footer}"{thumb}'
</drac2>
