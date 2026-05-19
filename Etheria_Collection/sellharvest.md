# **sellharvest – Harvest Sale Utility**
A utility command that converts a character’s gathered **Forage**, **Meat**, **Fish**, and **Marine** bag contents into gold based on a shared pricing table.

This alias complements survival-style systems (foraging, hunting, fishing) where characters accumulate materials in BagLib-managed bags.

---

## **Command Summary**

### **Primary Commands**
| Command | Description |
|--------|-------------|
| `!sellharvest` | Executes a full sale: removes priced items and adds gold to the coin purse. |
| `!sellharvest check` | Preview mode: calculates values but makes **no changes**. |
| `!sellharvest help` | Shows user-friendly help text. |

---

## **Behavior Overview**
- Reads the following BagLib bags:
  - `"Forage"`
  - `"Meat"`
  - `"Fish"`
  - ~~`"Marine"`~~ For some reason, all of the marine items were being placed into `" Meat"` by the !survival alias
- Each quantity is assumed to represent **1 pound**.
- Cross-references items with a shared pricing GVAR.
- All priced items are valued & summed.
- During a normal sale:
  - Bag items are removed.
  - Gold is added to the character.
  - Only **whole GP** are awarded (copper is discarded).

---

## **Pricing System**

Prices are stored in this GVAR:

```
5f3a0cfc-3232-40b7-809f-3e8bb250acc7
```

The structure contains two components:

```json
{
  "groups": {
    "berries": 100,
    "mushrooms": 50,
    "deer": 100,
    ...
  },
  "species": {
    "Forage": {
      "Berries": "berries",
      "Mushrooms": "mushrooms"
    },
    "Meat": {
      "Deer": "deer",
      "Rabbit": "rabbit"
    },
    "Fish": {
      "Bass": "bass"
    },
    "Marine": {
      "Cod": "cod"
    }
  }
}
```

### **How pricing works**
1. For each bag, the alias matches the item name against the `species` mapping.  
2. That mapping points to a pricing group key (e.g., `"berries"`).  
3. The group key looks up a CP-per-pound rate in `groups`.  
4. Value in CP = `quantity × cp_per_lb`.  
5. CP is converted to GP:
   - Only whole GP are awarded.  
   - Remainder CP is ignored intentionally.

### **Unknown or missing prices**
Items missing from the GVAR appear under:

**Unpriced items (not sold)**

These remain untouched in the bags.

---

## **BagLib Integration Details**

This alias uses BagLib (`5f1ffcbf-3f59-4396-b402-1ca0f02d6bbb`) to handle all inventory operations safely:

- `LoadedBags()` loads the character’s current BagLib structure.
- `bags.internal_bag_data` is used to *read* bag contents.
- `bags.modify_item(item=..., quantity=-qty, bag_name=...)` removes sold items.
- `bags.modify_coins("gp", amount)` adds GP to the character.
- `bags.save_bags()` persists final changes during a sale.

BagLib ensures:
- Validation and safety of edits  
- Bag reordering and structure integrity  
- Compatibility with other BagLib-based aliases  

---

## **Execution Modes**

### **1. Sale Mode (default)**  
Triggered by:
```
!sellharvest
```

Performs:
- Full valuation
- Removal of sold items
- Gold payout  
- Summary report including per-bag breakdown and unpriced items

### **2. Check Mode**
Triggered by:
```
!sellharvest check
```

Performs:
- Full valuation  
- No mutation (no coins added, no items removed)  
- Output labeled clearly as a *check*  
- Useful for verifying inventory value or spotting missing price entries  
