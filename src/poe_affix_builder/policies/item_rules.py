from __future__ import annotations


def domain_for_category(category: str) -> str:
    if category == "Tablet":
        return "tablet"
    if category == "Relics":
        return "sanctum_relic"
    if category == "Flasks":
        return "flask"
    if category == "Jewels":
        return "misc"
    if category == "Waystones":
        return "area"
    return "item"


def _armour_subtag_from_slug(slug: str) -> str | None:
    if "_dex_int" in slug:
        return "dex_int_armour"
    if "_str_dex" in slug:
        return "str_dex_armour"
    if "_str_int" in slug:
        return "str_int_armour"
    if slug.endswith("_dex"):
        return "dex_armour"
    if slug.endswith("_int"):
        return "int_armour"
    if slug.endswith("_str"):
        return "str_armour"
    return None


def spawn_tags_for_slug(slug: str) -> list[str]:
    direct = {
        "Amulets": ["amulet"],
        "Belts": ["belt"],
        "Rings": ["ring"],
        "Quivers": ["quiver"],
        "Bows": ["bow"],
        "Crossbows": ["crossbow"],
        "Wands": ["wand"],
        "Sceptres": ["sceptre"],
        "Staves": ["staff"],
        "Quarterstaves": ["staff", "warstaff"],
        "Flails": ["flail"],
        "Daggers": ["dagger"],
        "Claws": ["claw"],
        "Spears": ["spear"],
        "Traps": ["trap"],
        "Talismans": ["talisman"],
        "Bucklers": ["shield"],
        "One_Hand_Axes": ["weapon", "one_hand_weapon", "axe"],
        "One_Hand_Maces": ["weapon", "one_hand_weapon", "mace"],
        "One_Hand_Swords": ["weapon", "one_hand_weapon", "sword"],
        "Two_Hand_Axes": ["weapon", "two_hand_weapon", "axe"],
        "Two_Hand_Maces": ["weapon", "two_hand_weapon", "mace"],
        "Two_Hand_Swords": ["weapon", "two_hand_weapon", "sword"],
        "Life_Flasks": ["life_flask"],
        "Mana_Flasks": ["mana_flask"],
        "Charms": ["utility_flask"],
        "Waystones_low_tier": ["low_tier_map"],
        "Waystones_mid_tier": ["mid_tier_map"],
        "Waystones_top_tier": ["top_tier_map"],
        "Precursor_Tablet": [],
        "Abyss_Precursor_Tablet": ["tower_augment_abyss"],
        "Breach_Precursor_Tablet": ["tower_augment_breach"],
        "Delirium_Precursor_Tablet": ["tower_augment_delirium"],
        "Expedition_Precursor_Tablet": ["tower_augment_expedition"],
        "Overseer_Precursor_Tablet": ["tower_augment_map_boss"],
        "Ritual_Precursor_Tablet": ["tower_augment_ritual"],
        "Amphora_Relic": ["medium_sanctum_relic"],
        "Tapestry_Relic": ["medium_sanctum_relic"],
        "Seal_Relic": ["small_sanctum_relic"],
        "Urn_Relic": ["small_sanctum_relic"],
        "Coffer_Relic": ["large_sanctum_relic"],
        "Incense_Relic": ["large_sanctum_relic"],
        "Vase_Relic": ["large_sanctum_relic"],
        "Ruby": ["strjewel"],
        "Sapphire": ["intjewel"],
        "Emerald": ["dexjewel"],
        "Time-Lost_Ruby": ["strjewel", "radius_jewel"],
        "Time-Lost_Sapphire": ["intjewel", "radius_jewel"],
        "Time-Lost_Emerald": ["dexjewel", "radius_jewel"],
    }
    if slug in direct:
        return direct[slug]

    if slug.startswith("Body_Armours"):
        tags = ["body_armour"]
        sub = _armour_subtag_from_slug(slug)
        if sub:
            tags.append(sub)
        return tags

    if slug.startswith("Boots"):
        tags = ["boots"]
        sub = _armour_subtag_from_slug(slug)
        if sub:
            tags.append(sub)
        return tags

    if slug.startswith("Gloves"):
        tags = ["gloves"]
        sub = _armour_subtag_from_slug(slug)
        if sub:
            tags.append(sub)
        return tags

    if slug.startswith("Helmets"):
        tags = ["helmet"]
        sub = _armour_subtag_from_slug(slug)
        if sub:
            tags.append(sub)
        return tags

    if slug.startswith("Shields"):
        tags = ["shield"]
        sub = _armour_subtag_from_slug(slug)
        if sub:
            tags.append(sub)
        return tags

    return []
