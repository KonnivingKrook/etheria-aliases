embed
<drac2>
args = [a.lower() for a in &ARGS&]
cb = combat()

party = ""
mon = ""
mode = "player"
details = ("details" in args) or ("det" in args) or ("d" in args)
show_help = ("help" in args) or ("?" in args)

title = "Initiative Health Summary"
description = "Let's see how we're doing!"


if ("all" in args) or ("a" in args):
    mode = "showAll"
elif ("m" in args) or ("mon" in args) or ("monster" in args):
    mode = "monster"

# Help mode
if show_help:
    title = "Health Alias Help"
    description = (
        "**Usage**\n"
        "`!health` ... party health\n"
        "`!health m` ... monster health\n"
        "`!health all` ... both\n"
        "`!health d` ... show effects and resists (party only)\n"
        "`!health all d` ... both with details (party only)\n"
    )

# No initiative mode (story)
elif cb is None:
    title = "No Initiative"
    description = (
        "You start to take stock of bruises and breathing...\n"
        "But there is no turn order to anchor it. No initiative to read.\n"
        "For now, the moment is yours.\n\n"
        "Start initiative, then try `!health` again."
    )

# Normal mode
else:
    def fmt_resistance_list(res_list):
        if not res_list:
            return ""
        out = ""
        first = True
        for r in res_list:
            if not first:
                out += ", "
            out += r.dtype
            first = False
        return out

    def fmt_effect_list(eff_list):
        if not eff_list:
            return ""
        out = ""
        first = True
        for e in eff_list:
            if not first:
                out += ", "
            out += e.name
            first = False
        return out

    def detailed_block(c):
        immune = fmt_resistance_list(c.resistances.immune)
        resist = fmt_resistance_list(c.resistances.resist)
        effect = fmt_effect_list(c.effects)

        out = f"**{c.name}**:\n"
        out += f"> {c.hp_str()}\n"
        if effect:
            out += f"> Effects: {effect}\n"
        if immune:
            out += f"> Immunities: {immune}\n"
        if resist:
            out += f"> Resistances: {resist}\n"
        return out

    def simple_block(c):
        return f"**{c.name}**: {c.hp_str()}\n"

    for c in cb.combatants:
        if c.hp is None:
            continue

        pBlock = detailed_block(c) if details else simple_block(c)
        mBlock = simple_block(c)  # Monsters should never have details

        if c.monster_name is None:
            party += pBlock
        else:
            mon += mBlock
</drac2>
-title "{{title}}"
-desc "{{description}}"
{{ ('-f "Party|' + party + '"') if (cb is not None) and (not show_help) and mode in ["player","showAll"] and party else '' }}
{{ ('-f "Monsters|' + mon + '"') if (cb is not None) and (not show_help) and mode in ["monster","showAll"] and mon else '' }}
-footer "!health ? | @konnivingkrook#0"
