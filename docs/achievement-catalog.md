# Legacy Achievements Reforged — Achievement Catalog

Build: **0.5.1-alpha-alert-test6** · Branch: `achievement-alerts-test`.
Source snapshot: [`2965262`](https://github.com/Landsurfer-Overland/WoWAddons/commit/29652626c5e39b7ddfc37a141c57a173f71d9fcd).

Extracted from the initialized production definitions, including generated achievement tiers. Descriptions and point values below are the authored definitions, not a character’s completion or verified point total.

The core contains **322 records: 263 custom definitions and 59 retained native imports**. Of the custom definitions, **256 are supported** and **7 are disabled**. Faction, class and QuickFish requirements can reduce the list visible to a particular character.

The native appendix lists all **68 bundled Legacy references**, including the 59 retained imports and 9 references excluded from the old import list. The unified presentation reads its actual native Legacy catalog, criteria and Legacy Point rewards from the running client. That live catalog can contain additional records; the appendix is not a complete export of the client database. The old imports’ synthetic 10-point values are not used here as native rewards.

## Custom category counts

| Category | Supported | Disabled | Total definitions |
| --- | ---: | ---: | ---: |
| General | 29 | 0 | 29 |
| Quests | 12 | 6 | 18 |
| Exploration | 47 | 0 | 47 |
| Professions | 38 | 0 | 38 |
| Dungeons & Raids | 43 | 0 | 43 |
| Reputation | 35 | 0 | 35 |
| PvP | 39 | 1 | 40 |
| Feats of Strength | 13 | 0 | 13 |
| **Total** | **256** | **7** | **263** |

## Supported custom achievements

Points are character achievement points. The ID column contains the definition’s reference ID; the key identifies the addon record. A dash means no reference ID is stored. The Legacy Point Achievements navigation section is a filtered native view, not an additional custom achievement set.

### General

#### Levels

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Level 10 | `lvl10` | 6 | 10 | Reach level 10. | — |
| Level 20 | `lvl20` | 7 | 10 | Reach level 20. | — |
| Level 30 | `lvl30` | 8 | 10 | Reach level 30. | — |
| Level 40 | `lvl40` | 9 | 10 | Reach level 40. | — |
| Level 50 | `lvl50` | 10 | 10 | Reach level 50. | — |
| Level 60 | `lvl60` | 11 | 10 | Reach level 60. | — |

#### Riding

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Giddy Up! | `riding75` | 891 | 10 | Learn the apprentice riding skill. | — |
| Fast and Furious | `riding150` | 889 | 10 | Learn the journeyman riding skill (epic mounts). | — |

#### Money

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Got My Mind On My Money | `gold100` | 1176 | 10 | Loot 5g. | — |
| Got My Mind On My Money | `gold1000` | 1177 | 10 | Loot 25g. | — |
| Got My Mind On My Money | `gold5000` | 1178 | 10 | Loot 100g. | — |
| The Bread Winner | `breadwinner` | 1182 | 10 | Earn 100g from quest rewards. | — |

#### Collections

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Can I Keep Him? | `pet1` | 1017 | 10 | Obtain a companion pet. | — |
| Plenty of Pets | `pet15` | 15 | 10 | Collect 15 unique companion pets. | — |
| Stable Keeper | `mount10` | 2141 | 10 | Obtain 10 mounts. | — |
| Represent | `tabard` | 621 | 10 | Equip a tabard. | — |

#### Around Azeroth

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Going Down? | `fall` | 964 | 10 | Fall 65 yards without dying. | — |
| To All The Squirrels I've Loved Before | `critters` | 1206 | 10 | Show the critters of Azeroth how much you /love them. | — |
| Pest Control | `pests` | 2556 | 10 | Slay the following pests. | — |
| Well Read | `books` | 1244 | 10 | Read the books listed below. | — |

#### Food & Drink

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| It's Happy Hour Somewhere | `drinks` | 1833 | 10 | Drink 25 different types of beverages. | — |
| Tastes Like Chicken | `foods` | 1832 | 10 | Sample 50 different kinds of Azeroth's delectable dishes. | — |

#### Loot Rolls

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Greedy | `greedy` | 558 | 10 | Win a greed roll on a superior or better item by rolling 100. | — |
| Needy | `needy` | 559 | 10 | Win a need roll on a superior or better item by rolling 100. | — |

#### Rare Enemies

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Something Rare | `rare1` | — | 10 | Slay 1 different rare enemies. | — |
| Rare Hunter | `rare10` | — | 10 | Slay 10 different rare enemies. | — |
| Seasoned Rare Hunter | `rare25` | — | 10 | Slay 25 different rare enemies. | — |
| Rare Collector | `rare50` | — | 10 | Slay 50 different rare enemies. | — |
| Rarely Seen, Always Slain | `rare100` | — | 10 | Slay 100 different rare enemies. | — |

### Quests

#### Quests Completed

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| 50 Quests Completed | `q50` | 503 | 10 | Complete 50 quests. | — |
| 100 Quests Completed | `q100` | 504 | 10 | Complete 100 quests. | — |
| 250 Quests Completed | `q250` | 505 | 10 | Complete 250 quests. | — |
| 500 Quests Completed | `q500` | 506 | 10 | Complete 500 quests. | — |
| 1000 Quests Completed | `q1000` | 507 | 10 | Complete 1000 quests. | — |
| 1500 Quests Completed | `q1500` | 508 | 10 | Complete 1500 quests. | — |
| 2000 Quests Completed | `q2000` | 32 | 10 | Complete 2000 quests. | — |
| 3000 Quests Completed | `q3000` | 978 | 50 | Complete 3000 quests. | — |

#### Quest Lines

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| The Green Hills of Stranglethorn | `greenhills` | 940 | 10 | Complete all of Hemet Nesingwary quests in Stranglethorn Vale. | — |

#### Loremaster

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Loremaster of Eastern Kingdoms | `loreEK` | 1676 | 10 | Complete quests in Eastern Kingdoms (counted with QuestieDB). | — |
| Loremaster of Kalimdor | `loreKal` | 1678 | 10 | Complete quests in Kalimdor (counted with QuestieDB). | — |
| The Loremaster | `loremaster` | 1681 | 10 | Complete Loremaster of Eastern Kingdoms and Loremaster of Kalimdor. | — |

### Exploration

#### Azeroth

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Explore Eastern Kingdoms | `exploreEK` | 42 | 25 | Explore the regions of Eastern Kingdoms. | — |
| Explore Kalimdor | `exploreKal` | 43 | 25 | Explore the regions of Kalimdor. | — |
| Explore Azeroth | `worldexplorer` | 46 | 50 | Explore Eastern Kingdoms and Kalimdor. | — |

#### Eastern Kingdoms

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Explore Elwynn Forest | `explore776` | 776 | 10 | Explore Elwynn Forest, revealing the covered areas of the world map. | — |
| Explore Dun Morogh | `explore627` | 627 | 10 | Explore Dun Morogh, revealing the covered areas of the world map. | — |
| Explore Tirisfal Glades | `explore768` | 768 | 10 | Explore Tirisfal Glades, revealing the covered areas of the world map. | — |
| Explore Loch Modan | `explore779` | 779 | 10 | Explore Loch Modan, revealing the covered areas of the world map. | — |
| Explore Westfall | `explore802` | 802 | 10 | Explore Westfall, revealing the covered areas of the world map. | — |
| Explore Wetlands | `explore841` | 841 | 10 | Explore Wetlands, revealing the covered areas of the world map. | — |
| Explore Silverpine Forest | `explore769` | 769 | 10 | Explore Silverpine Forest, revealing the covered areas of the world map. | — |
| Explore Redridge Mountains | `explore780` | 780 | 10 | Explore Redridge Mountains, revealing the covered areas of the world map. | — |
| Explore Duskwood | `explore778` | 778 | 10 | Explore Duskwood, revealing the covered areas of the world map. | — |
| Explore Hillsbrad Foothills | `explore772` | 772 | 10 | Explore Hillsbrad Foothills, revealing the covered areas of the world map. | — |
| Explore Swamp of Sorrows | `explore782` | 782 | 10 | Explore Swamp of Sorrows, revealing the covered areas of the world map. | — |
| Explore Badlands | `explore765` | 765 | 10 | Explore Badlands, revealing the covered areas of the world map. | — |
| Explore Stranglethorn Vale | `explore781` | 781 | 10 | Explore Stranglethorn Vale, revealing the covered areas of the world map. | — |
| Explore Alterac Mountains | `explore760` | 760 | 10 | Explore Alterac Mountains, revealing the covered areas of the world map. | — |
| Explore Arathi Highlands | `explore761` | 761 | 10 | Explore Arathi Highlands, revealing the covered areas of the world map. | — |
| Explore The Hinterlands | `explore773` | 773 | 10 | Explore The Hinterlands, revealing the covered areas of the world map. | — |
| Explore Searing Gorge | `explore774` | 774 | 10 | Explore Searing Gorge, revealing the covered areas of the world map. | — |
| Explore Blasted Lands | `explore766` | 766 | 10 | Explore Blasted Lands, revealing the covered areas of the world map. | — |
| Explore Burning Steppes | `explore775` | 775 | 10 | Explore Burning Steppes, revealing the covered areas of the world map. | — |
| Explore Deadwind Pass | `explore777` | 777 | 10 | Explore Deadwind Pass, revealing the covered areas of the world map. | — |
| Explore Western Plaguelands | `explore770` | 770 | 10 | Explore Western Plaguelands, revealing the covered areas of the world map. | — |
| Explore Eastern Plaguelands | `explore771` | 771 | 10 | Explore Eastern Plaguelands, revealing the covered areas of the world map. | — |
| Explore Riverglades | `exploreRiverglades` | — | 10 | Explore Riverglades, revealing the covered areas of the world map. | — |

#### Kalimdor

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Explore Durotar | `explore728` | 728 | 10 | Explore Durotar, revealing the covered areas of the world map. | — |
| Explore Mulgore | `explore736` | 736 | 10 | Explore Mulgore, revealing the covered areas of the world map. | — |
| Explore Teldrassil | `explore842` | 842 | 10 | Explore Teldrassil, revealing the covered areas of the world map. | — |
| Explore The Barrens | `explore750` | 750 | 10 | Explore The Barrens, revealing the covered areas of the world map. | — |
| Explore Darkshore | `explore844` | 844 | 10 | Explore Darkshore, revealing the covered areas of the world map. | — |
| Explore Ashenvale | `explore845` | 845 | 10 | Explore Ashenvale, revealing the covered areas of the world map. | — |
| Explore Thousand Needles | `explore846` | 846 | 10 | Explore Thousand Needles, revealing the covered areas of the world map. | — |
| Explore Stonetalon Mountains | `explore847` | 847 | 10 | Explore Stonetalon Mountains, revealing the covered areas of the world map. | — |
| Explore Desolace | `explore848` | 848 | 10 | Explore Desolace, revealing the covered areas of the world map. | — |
| Explore Dustwallow Marsh | `explore850` | 850 | 10 | Explore Dustwallow Marsh, revealing the covered areas of the world map. | — |
| Explore Feralas | `explore849` | 849 | 10 | Explore Feralas, revealing the covered areas of the world map. | — |
| Explore Tanaris Desert | `explore851` | 851 | 10 | Explore Tanaris Desert, revealing the covered areas of the world map. | — |
| Explore Azshara | `explore852` | 852 | 10 | Explore Azshara, revealing the covered areas of the world map. | — |
| Explore Felwood | `explore853` | 853 | 10 | Explore Felwood, revealing the covered areas of the world map. | — |
| Explore Un'Goro Crater | `explore854` | 854 | 10 | Explore Un'Goro Crater, revealing the covered areas of the world map. | — |
| Explore Moonglade | `explore855` | 855 | 10 | Explore Moonglade, revealing the covered areas of the world map. | — |
| Explore Silithus | `explore856` | 856 | 10 | Explore Silithus, revealing the covered areas of the world map. | — |
| Explore Winterspring | `explore857` | 857 | 10 | Explore Winterspring, revealing the covered areas of the world map. | — |
| Explore Shen'dralas | `exploreShendralas` | — | 10 | Explore Shen'dralas, revealing the covered areas of the world map. | — |
| Explore Mount Hyjal | `exploreHyjal` | — | 10 | Explore Mount Hyjal, revealing the covered areas of the world map. | — |

#### Zephras Isle

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Explore Zephras Isle | `exploreZephras` | — | 10 | Explore Zephras Isle, revealing the covered areas of the world map. | — |

### Professions

#### Professions

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Professional Apprentice | `prof75` | — | 10 | Reach 75 in a profession. | — |
| Professional Journeyman | `prof150` | 116 | 10 | Reach 150 in a profession. | — |
| Professional Expert | `prof225` | 731 | 10 | Reach 225 in a profession. | — |
| Professional Artisan | `prof300` | 732 | 10 | Reach 300 in a profession. | — |
| Working Day and Night | `dayandnight` | 735 | 10 | Become an Artisan (300) in two professions. | — |
| Skills to Pay the Bills | `paythebills` | 730 | 10 | Become an Artisan (300) in fishing, first aid and cooking. | — |

#### Cooking

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Apprentice Cook | `cook75` | — | 10 | Become an Apprentice Cook. | — |
| Journeyman Cook | `cook150` | 121 | 10 | Become a Journeyman Cook. | — |
| Expert Cook | `cook225` | 122 | 10 | Become an Expert Cook. | — |
| Artisan Cook | `cook300` | 123 | 10 | Become an Artisan Cook. | — |
| Lunch Lady | `recipes25` | 1795 | 10 | Learn 25 cooking recipes. | — |
| Short Order Cook | `recipes50` | 1796 | 10 | Learn 50 cooking recipes. | — |
| Chef de Partie | `recipes75` | 1797 | 10 | Learn 75 cooking recipes. | — |

#### Fishing

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Apprentice Fisherman | `fish75` | — | 10 | Become an Apprentice Fisherman. | — |
| Journeyman Fisherman | `fish150` | 126 | 10 | Become a Journeyman Fisherman. | — |
| Expert Fisherman | `fish225` | 127 | 10 | Become an Expert Fisherman. | — |
| Artisan Fisherman | `fish300` | 128 | 10 | Become an Artisan Fisherman. | — |
| 25 Fish | `fished25` | 1556 | 10 | Fish up 25 items. | — |
| 50 Fish | `fished50` | 1557 | 10 | Fish up 50 items. | — |
| 100 Fish | `fished100` | 1558 | 10 | Fish up 100 items. | — |
| 250 Fish | `fished250` | 1559 | 10 | Fish up 250 items. | — |
| 500 Fish | `fished500` | 1560 | 10 | Fish up 500 items. | — |
| 1000 Fish | `fished1000` | 1561 | 10 | Fish up 1000 items. | — |
| The Old Gnome and the Sea | `oldgnome` | 153 | 10 | Successfully fish from a school. | — |
| The Fishing Diplomat | `diplomat` | 150 | 10 | Fish something up in Orgrimmar and Stormwind. | — |
| Master Angler of Azeroth | `masterangler` | 306 | 20 | Win the Booty Bay fishing contest. | — |
| One That Didn't Get Away | `rarefish` | 878 | 10 | Catch one of the rare fish in the list below. | — |

#### Quick Fish

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Wandering Angler | `qfzones5` | — | 10 | Fish something up in 5 zones (Quick Fish catch log). | Requires QuickFish |
| Travelling Angler | `qfzones10` | — | 10 | Fish something up in 10 zones (Quick Fish catch log). | Requires QuickFish |
| Angler of Azeroth | `qfzones20` | — | 10 | Fish something up in 20 zones (Quick Fish catch log). | Requires QuickFish |
| Lucky Strike | `qfrares1` | — | 10 | Fish up an uncommon or better item (Quick Fish rare finds). | Requires QuickFish |
| Treasure Angler | `qfrares10` | — | 10 | Fish up 10 uncommon or better items (Quick Fish rare finds). | Requires QuickFish |
| Mixed Bag | `qfkinds15` | — | 10 | Fish up 15 different items (Quick Fish catch log). | Requires QuickFish |
| Fish of Every Kind | `qfkinds30` | — | 10 | Fish up 30 different items (Quick Fish catch log). | Requires QuickFish |

#### First Aid

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Apprentice in First Aid | `aid75` | — | 10 | Become an Apprentice in first aid. | — |
| Journeyman in First Aid | `aid150` | 131 | 10 | Become a Journeyman in first aid. | — |
| Expert in First Aid | `aid225` | 132 | 10 | Become an Expert in first aid. | — |
| Artisan in First Aid | `aid300` | 133 | 10 | Become an Artisan in first aid. | — |

### Dungeons & Raids

#### Dungeons

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Ragefire Chasm | `dungeon629` | 629 | 10 | Defeat Taragaman the Hungerer. | — |
| Deadmines | `dungeon628` | 628 | 10 | Defeat Edwin VanCleef. | — |
| Wailing Caverns | `dungeon630` | 630 | 10 | Defeat Mutanus the Devourer. | — |
| Shadowfang Keep | `dungeon631` | 631 | 10 | Defeat Archmage Arugal. | — |
| Blackfathom Deeps | `dungeon632` | 632 | 10 | Defeat Aku'mai. | — |
| Stormwind Stockade | `dungeon633` | 633 | 10 | Defeat Bazil Thredd. | — |
| Razorfen Kraul | `dungeon635` | 635 | 10 | Defeat Charlga Razorflank. | — |
| Gnomeregan | `dungeon634` | 634 | 10 | Defeat Mekgineer Thermaplugg. | — |
| Razorfen Downs | `dungeon636` | 636 | 10 | Defeat Amnennar the Coldbringer. | — |
| Scarlet Monastery | `dungeon637` | 637 | 10 | Defeat the Scarlet Crusade within the Scarlet Monastery. | — |
| Uldaman | `dungeon638` | 638 | 10 | Defeat Archaedas. | — |
| Zul'Farrak | `dungeon639` | 639 | 10 | Defeat Chief Ukorz Sandscalp. | — |
| Maraudon | `dungeon640` | 640 | 10 | Defeat Princess Theradras. | — |
| Sunken Temple | `dungeon641` | 641 | 10 | Defeat Shade of Eranikus. | — |
| Blackrock Depths | `dungeon642` | 642 | 10 | Defeat Emperor Dagran Thaurissan. | — |
| Lower Blackrock Spire | `dungeon643` | 643 | 10 | Defeat Overlord Wyrmthalak. | — |
| Upper Blackrock Spire | `dungeon1307` | 1307 | 10 | Defeat General Drakkisath. | — |
| King of Dire Maul | `dungeon644` | 644 | 10 | Defeat each wing of Dire Maul. | — |
| Scholomance | `dungeon645` | 645 | 10 | Defeat the leaders of Scholomance. | — |
| Stratholme | `dungeon646` | 646 | 10 | Defeat the evil masterminds inhabiting Stratholme. | — |

#### Forever Dungeons

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| The Hall of Thanes | `dungeonThanes` | — | 10 | Defeat Durgen Dirgehammer. | — |
| Ruins of Lordaeron | `dungeonLordaeron` | — | 10 | Defeat Rath'mael. | — |
| Excavation Site: Wetlands | `dungeonExcavation` | — | 10 | Defeat the Relic Guardian. | — |
| City of Dalaran | `dungeonDalaran` | — | 10 | Defeat the Shade of the Archmage. | — |
| The Drowned City | `dungeonDrowned` | — | 10 | Defeat the master of The Drowned City. | — |
| Krol'dok Stronghold | `dungeonKroldok` | — | 10 | Defeat the master of Krol'dok Stronghold. | — |
| Alcaz Prison | `dungeonAlcaz` | — | 10 | Defeat Blazeroar. | — |
| Blackmaw Hold | `dungeonBlackmaw` | — | 10 | Defeat the master of Blackmaw Hold. | — |
| The Shaper's Terrace | `dungeonShaper` | — | 10 | Defeat Nanaya. | — |

#### Raids

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Onyxia's Lair | `onyxia60` | 684 | 10 | Defeat Onyxia. | — |
| Zul'Gurub | `dungeon688` | 688 | 10 | Defeat Hakkar. | — |
| Ruins of Ahn'Qiraj | `dungeon689` | 689 | 10 | Defeat Ossirian the Unscarred. | — |
| Molten Core | `dungeon686` | 686 | 10 | Defeat Ragnaros. | — |
| Blackwing Lair | `dungeon685` | 685 | 10 | Defeat Nefarian. | — |
| Temple of Ahn'Qiraj | `dungeon687` | 687 | 10 | Defeat C'Thun. | — |
| Naxxramas | `naxx40` | — | 10 | Defeat Kel'Thuzad. | — |

#### World Bosses

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Azuregos | `wbAzuregos` | — | 10 | Defeat Azuregos in Azshara. | — |
| Lord Kazzak | `wbKazzak` | — | 10 | Defeat Lord Kazzak. | — |
| Ysondre | `wbYsondre` | — | 10 | Defeat Ysondre, a Dragon of Nightmare. | — |
| Lethon | `wbLethon` | — | 10 | Defeat Lethon, a Dragon of Nightmare. | — |
| Emeriss | `wbEmeriss` | — | 10 | Defeat Emeriss, a Dragon of Nightmare. | — |
| Taerar | `wbTaerar` | — | 10 | Defeat Taerar, a Dragon of Nightmare. | — |
| Nightmare's End | `wbNightmare` | — | 25 | Defeat the four Dragons of Nightmare. | — |

### Reputation

#### Exalted

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Somebody Likes Me | `ex1` | 522 | 10 | Raise a reputation to Exalted. | — |
| 5 Exalted Reputations | `ex5` | 523 | 10 | Raise 5 reputations to Exalted. | — |
| 10 Exalted Reputations | `ex10` | 524 | 10 | Raise 10 reputations to Exalted. | — |
| 15 Exalted Reputations | `ex15` | 521 | 10 | Raise 15 reputations to Exalted. | — |
| 20 Exalted Reputations | `ex20` | 520 | 10 | Raise 20 reputations to Exalted. | — |
| 25 Exalted Reputations | `ex25` | 519 | 10 | Raise 25 reputations to Exalted. | — |
| 30 Exalted Reputations | `ex30` | 518 | 10 | Raise 30 reputations to Exalted. | — |

#### Home Cities

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Ambassador of the Alliance | `ambAlliance` | 948 | 10 | Earn exalted reputation with the Alliance home cities. | Alliance only |
| Ambassador of the Horde | `ambHorde` | 762 | 10 | Earn exalted reputation with the Horde home cities. | Horde only |

#### Classic Factions

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| They Love Me In That Tunnel | `repTimbermaw` | 944 | 15 | Earn exalted status with Timbermaw Hold. | — |
| The Argent Dawn | `repArgent` | 946 | 15 | Earn exalted status with the Argent Dawn. | — |
| Guardian of Cenarius | `repCenarius` | 953 | 25 | Earn exalted status with the Cenarion Circle. | — |
| Hydraxian Waterlords | `repHydraxian` | 955 | 10 | Earn exalted status with the Hydraxian Waterlords. | — |
| Brood of Nozdormu | `repBrood` | 956 | 10 | Earn exalted status with the Brood of Nozdormu. | — |
| Hero of the Zandalar Tribe | `repZandalar` | 957 | 10 | Earn exalted status with the Zandalar Tribe. | — |
| Thorium Brotherhood | `repThorium` | — | 10 | Earn exalted status with the Thorium Brotherhood. | — |
| Shen'dralar | `repShendralar` | — | 10 | Earn exalted status with the Shen'dralar. | — |
| Wintersaber Trainers | `repWintersaber` | — | 10 | Earn exalted status with the Wintersaber Trainers. | Alliance only |
| Darkmoon Faire | `repDarkmoon` | — | 10 | Earn exalted status with the Darkmoon Faire. | — |
| Insane in the Membrane | `insane` | 2336 | 10 | Honored with the Bloodsail Buccaneers, and Exalted with Booty Bay, Everlook, Gadgetzan, Ratchet, Ravenholdt and the Darkmoon Faire. | — |

#### Forever Factions

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Azeroth Commerce Authority | `rep2586` | — | 10 | Earn exalted status with Azeroth Commerce Authority. | — |
| Durotar Supply and Logistics | `rep2587` | — | 10 | Earn exalted status with Durotar Supply and Logistics. | — |
| Emerald Wardens | `rep2641` | — | 10 | Earn exalted status with Emerald Wardens. | — |
| Cenarion Scouts | `rep2719` | — | 10 | Earn exalted status with Cenarion Scouts. | — |
| Kirin Tor | `rep2740` | — | 10 | Earn exalted status with Kirin Tor. | — |
| Barkskin Burrow | `rep2747` | — | 10 | Earn exalted status with Barkskin Burrow. | — |
| Nightclaw Druids | `rep2758` | — | 10 | Earn exalted status with Nightclaw Druids. | — |
| Guardians of Hyjal | `rep2765` | — | 10 | Earn exalted status with Guardians of Hyjal. | — |
| Windshapers | `rep2778` | — | 10 | Earn exalted status with Windshapers. | — |
| High Order | `rep2779` | — | 10 | Earn exalted status with High Order. | — |
| Bolder'ok Clan | `rep2782` | — | 10 | Earn exalted status with Bolder'ok Clan. | — |
| Earthen Ring | `rep2787` | — | 10 | Earn exalted status with Earthen Ring. | — |
| The Watchers | `rep2819` | — | 10 | Earn exalted status with The Watchers. | — |
| Brotherhood of the Horse | `rep2826` | — | 10 | Earn exalted status with Brotherhood of the Horse. | — |
| Powderfuse | `rep2827` | — | 10 | Earn exalted status with Powderfuse. | — |

### PvP

#### Honorable Kills

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| An Honorable Kill | `hk1` | 238 | 10 | Achieve an honorable kill. | — |
| 100 Honorable Kills | `hk100` | 513 | 10 | Get 100 honorable kills. | — |
| 500 Honorable Kills | `hk500` | 515 | 10 | Get 500 honorable kills. | — |
| 1000 Honorable Kills | `hk1000` | 516 | 10 | Get 1000 honorable kills. | — |
| 5000 Honorable Kills | `hk5000` | 512 | 10 | Get 5000 honorable kills. | — |
| 10000 Honorable Kills | `hk10000` | 509 | 10 | Get 10000 honorable kills. | — |
| 25000 Honorable Kills | `hk25000` | 239 | 10 | Get 25000 honorable kills. | — |
| 50000 Honorable Kills | `hk50000` | 869 | 10 | Get 50000 honorable kills. | — |
| 100000 Honorable Kills | `hk100000` | 870 | 10 | Get 100000 honorable kills. | — |

#### Battlegrounds

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Warsong Gulch Victory | `wsgWin` | 166 | 10 | Win Warsong Gulch. | — |
| Warsong Gulch Veteran | `wsgVet` | 167 | 10 | Complete 100 victories in Warsong Gulch. | — |
| Arathi Basin Victory | `abWin` | 154 | 10 | Win Arathi Basin. | — |
| Arathi Basin Veteran | `abVet` | 155 | 10 | Complete 100 victories in Arathi Basin. | — |
| Alterac Valley Victory | `avWin` | 218 | 10 | Win Alterac Valley. | — |
| Alterac Valley Veteran | `avVet` | 219 | 10 | Complete 100 victories in Alterac Valley. | — |
| Darkspear Islands Victory | `diWin` | — | 10 | Win Darkspear Islands. | — |
| Darkspear Islands Veteran | `diVet` | — | 10 | Complete 100 victories in Darkspear Islands. | — |
| Battlemaster | `battlemaster` | 230 | 50 | Win Warsong Gulch, Arathi Basin, Alterac Valley and Darkspear Islands. | — |

#### In The Battle

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Capture the Flag | `captureFlag` | 199 | 10 | Personally carry and capture the flag in Warsong Gulch. | — |
| Persistent Defender | `persistent` | 200 | 10 | Return 50 flags as a defender in Warsong Gulch. | — |
| Tower Defense | `towerDefense` | 222 | 10 | Defend 50 towers in Alterac Valley. | — |
| The Grim Reaper | `grimReaper` | 229 | 10 | Get 30 honorable kills in a single battle in any battleground. | — |
| Wrecking Ball | `wreckingBall` | 231 | 10 | Get 20 killing blows without dying in a single battle in any battleground. | — |
| Warsong Expedience | `wsgFast` | 201 | 10 | Win Warsong Gulch in under 7 minutes. | — |
| Let's Get This Done | `abFast` | 159 | 10 | Win Arathi Basin in 6 minutes. | — |
| The Alterac Blitz | `avFast` | 226 | 20 | Win Alterac Valley in 6 minutes. | — |

#### Battleground Reputation

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Hero of the Frostwolf Clan | `repFrostwolf` | 708 | 10 | Gain exalted reputation with the Frostwolf Clan. | Horde only |
| Hero of the Stormpike Guard | `repStormpike` | 709 | 10 | Gain exalted reputation with the Stormpike Guard. | Alliance only |
| The Defiler | `repDefilers` | 710 | 10 | Gain exalted reputation with The Defilers. | Horde only |
| Knight of Arathor | `repArathor` | 711 | 10 | Gain exalted reputation with The League of Arathor. | Alliance only |
| Warsong Outrider | `repOutriders` | 712 | 10 | Gain exalted reputation with the Warsong Outriders. | Horde only |
| Silverwing Sentinel | `repSilverwing` | 713 | 10 | Gain exalted reputation with the Silverwing Sentinels. | Alliance only |
| Darkspear Raider | `repRaiders` | — | 10 | Gain exalted reputation with the Darkspear Raiders. | Horde only |
| Theramore Expeditionary | `repTheramore` | — | 10 | Gain exalted reputation with the Theramore Expeditionary Force. | Alliance only |
| The Conqueror | `conqueror` | 714 | 20 | Exalted with the Frostwolf Clan, The Defilers and the Warsong Outriders. | Horde only |
| The Justicar | `justicar` | 907 | 20 | Exalted with the Stormpike Guard, The League of Arathor and the Silverwing Sentinels. | Alliance only |

#### World PvP

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Duel-icious | `duel` | 1157 | 10 | Win a duel against another player. | — |
| Make Love, Not Warcraft | `hugDead` | 247 | 10 | Emote /hug on a dead enemy before they release corpse. | — |
| For The Horde! | `forHorde` | 619 | 20 | Slay the leaders of the Alliance. | Horde only |

### Feats of Strength

#### Legendary

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Thunderfury, Blessed Blade of the Windseeker | `thunderfury` | 428 | 0 | Wielder of Thunderfury, Blessed Blade of the Windseeker. | — |
| Sulfuras, Hand of Ragnaros | `sulfuras` | 429 | 0 | Wielder of Sulfuras, Hand of Ragnaros. | — |
| Atiesh, Greatstaff of the Guardian | `atiesh` | 425 | 0 | Wielder of Atiesh, Greatstaff of the Guardian. | — |

#### Mounts

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Deathcharger's Reins | `deathcharger` | 729 | 0 | Obtain the Deathcharger's Reins from Baron Rivendare in Stratholme. | — |
| Swift Zulian Tiger | `zulianTiger` | 880 | 0 | Obtain the Swift Zulian Tiger from High Priest Thekal in Zul'Gurub. | — |
| Swift Razzashi Raptor | `razzashi` | 881 | 0 | Obtain the Swift Razzashi Raptor from Bloodlord Mandokir in Zul'Gurub. | — |
| Winterspring Frostsaber | `frostsaber` | 3356 | 0 | Obtain a Winterspring Frostsaber. | — |
| Dreadsteed of Xoroth | `dreadsteed` | 2357 | 0 | Completed the Dreadsteed of Xoroth warlock quest. | Warlock only |
| Charger | `charger` | 2358 | 0 | Completed the paladin quest to obtain a Charger. | Paladin only |
| Why? Because It's Red | `redQiraji` | 424 | 0 | Obtain a Red Qiraji Resonating Crystal. | — |

#### Titles & Rare Finds

| Achievement | Key | Reference ID | Points | Description | Availability |
| --- | --- | ---: | ---: | --- | --- |
| Scarab Lord | `scarabLord` | 416 | 0 | Opened the gates of Ahn'Qiraj. | — |
| Avast Ye, Admiral! | `admiral` | 871 | 0 | Obtain the Bloodsail Admiral's Hat. | — |
| The Fifth Element | `fifthElement` | 2496 | 0 | Obtain an Aqual Quintessence. | — |

## Disabled custom records

These definitions and saved keys remain in the source for compatibility. They are not available as active achievements.

| Achievement | Key | Reference ID | Points | Description | Disabled reason |
| --- | --- | ---: | ---: | --- | --- |
| 5 Daily Quests Complete | `d5` | 973 | 10 | Complete 5 daily quests. | Daily quests are unavailable in this Forever project. |
| 50 Daily Quests Complete | `d50` | 974 | 10 | Complete 50 daily quests. | Daily quests are unavailable in this Forever project. |
| 200 Daily Quests Complete | `d200` | 975 | 10 | Complete 200 daily quests. | Daily quests are unavailable in this Forever project. |
| 500 Daily Quests Complete | `d500` | 976 | 10 | Complete 500 daily quests. | Daily quests are unavailable in this Forever project. |
| 1000 Daily Quests Complete | `d1000` | 977 | 10 | Complete 1000 daily quests. | Daily quests are unavailable in this Forever project. |
| A Simple Re-Quest | `request` | 31 | 10 | Complete a daily quest every day for five consecutive days. | Daily quests are unavailable in this Forever project. |
| For The Alliance! | `forAlliance` | 614 | 20 | Slay the leaders of the Horde. | For the Alliance! (custom ID 614) is unobtainable with the available Forever mechanics. |

## Bundled native Legacy references

IDs on the same row are stored aliases for one reference, not separate achievement counts. Descriptions are bundled reference text; the client supplies the current descriptions, criteria, completion and rewards. No Legacy Point reward is inferred from the name or description.

### Native: Classes

| Achievement | Native ID aliases | Group | Description |
| --- | --- | --- | --- |
| Novice Druid | `61502`, `63972` | Druid | Reach level 25 for the first time on a Druid. |
| Experienced Druid | `63973`, `61503` | Druid | Reach level 45 for the first time on a Druid. |
| Master Druid | `63974`, `61504` | Druid | Reach level 60 for the first time on a Druid. |
| Novice Hunter | `61989`, `63975` | Hunter | Reach level 25 for the first time on a Hunter. |
| Experienced Hunter | `63976`, `61992` | Hunter | Reach level 45 for the first time on a Hunter. |
| Master Hunter | `63977`, `61993` | Hunter | Reach level 60 for the first time on a Hunter. |
| Novice Mage | `61994`, `63978` | Mage | Reach level 25 for the first time on a Mage. |
| Experienced Mage | `63979`, `61995` | Mage | Reach level 45 for the first time on a Mage. |
| Master Mage | `63980`, `61996` | Mage | Reach level 60 for the first time on a Mage. |
| Novice Paladin | `61997`, `63981` | Paladin | Reach level 25 for the first time on a Paladin. |
| Experienced Paladin | `63982`, `61998` | Paladin | Reach level 45 for the first time on a Paladin. |
| Master Paladin | `63983`, `61999` | Paladin | Reach level 60 for the first time on a Paladin. |
| Novice Priest | `62000`, `63984` | Priest | Reach level 25 for the first time on a Priest. |
| Experienced Priest | `63985`, `62001` | Priest | Reach level 45 for the first time on a Priest. |
| Master Priest | `63986`, `62002` | Priest | Reach level 60 for the first time on a Priest. |
| Novice Rogue | `63987`, `62003` | Rogue | Reach level 25 for the first time on a Rogue. |
| Experienced Rogue | `62004`, `63988` | Rogue | Reach level 45 for the first time on a Rogue. |
| Master Rogue | `63989`, `62005` | Rogue | Reach level 60 for the first time on a Rogue. |
| Novice Shaman | `62006`, `63990` | Shaman | Reach level 25 for the first time on a Shaman. |
| Experienced Shaman | `63991`, `62007` | Shaman | Reach level 45 for the first time on a Shaman. |
| Master Shaman | `63992`, `62008` | Shaman | Reach level 60 for the first time on a Shaman. |
| Novice Warlock | `62009`, `63993` | Warlock | Reach level 25 for the first time on a Warlock. |
| Experienced Warlock | `63994`, `62010` | Warlock | Reach level 45 for the first time on a Warlock. |
| Master Warlock | `63995`, `62011` | Warlock | Reach level 60 for the first time on a Warlock. |
| Novice Warrior | `61499`, `63969` | Warrior | Reach level 25 for the first time on a Warrior. |
| Experienced Warrior | `63970`, `61500` | Warrior | Reach level 45 for the first time on a Warrior. |
| Master Warrior | `63971`, `61501` | Warrior | Reach level 60 for the first time on a Warrior. |

### Native: Tradeskills

| Achievement | Native ID aliases | Group | Description |
| --- | --- | --- | --- |
| Journeyman Alchemist | `62012`, `63996` | Alchemy | Reach 150 skill in Alchemy for the first time. |
| Expert Alchemist | `63997`, `62013` | Alchemy | Reach 225 skill in Alchemy for the first time. |
| Artisan Alchemist | `63998`, `62014` | Alchemy | Reach 300 skill in Alchemy for the first time. |
| Journeyman Blacksmith | `63999`, `62015` | Blacksmithing | Reach 150 skill in Blacksmithing for the first time. |
| Expert Blacksmith | `62016`, `64000` | Blacksmithing | Reach 225 skill in Blacksmithing for the first time. |
| Artisan Blacksmith | `64001`, `62017` | Blacksmithing | Reach 300 skill in Blacksmithing for the first time. |
| Journeyman Enchanter | `62018`, `64002` | Enchanting | Reach 150 skill in Enchanting for the first time. |
| Expert Enchanter | `64003`, `62019` | Enchanting | Reach 225 skill in Enchanting for the first time. |
| Artisan Enchanter | `64004`, `62020` | Enchanting | Reach 300 skill in Enchanting for the first time. |
| Journeyman Engineer | `64005`, `62021` | Engineering | Reach 150 skill in Engineering for the first time. |
| Expert Engineer | `62022`, `64006` | Engineering | Reach 225 skill in Engineering for the first time. |
| Artisan Engineer | `64007`, `62023` | Engineering | Reach 300 skill in Engineering for the first time. |
| Journeyman Leatherworker | `62024`, `64008` | Leatherworking | Reach 150 skill in Leatherworking for the first time. |
| Expert Leatherworker | `64009`, `62025` | Leatherworking | Reach 225 skill in Leatherworking for the first time. |
| Artisan Leatherworker | `64010`, `62026` | Leatherworking | Reach 300 skill in Leatherworking for the first time. |
| Journeyman Tailor | `62028`, `64011` | Tailoring | Reach 150 skill in Tailoring for the first time. |
| Expert Tailor | `64012`, `62029` | Tailoring | Reach 225 skill in Tailoring for the first time. |
| Artisan Tailor | `64013`, `62030` | Tailoring | Reach 300 skill in Tailoring for the first time. |

### Native: Dungeons

| Achievement | Native ID aliases | Group | Description |
| --- | --- | --- | --- |
| Novice Spelunker | `62031`, `64016` | Dungeons | Complete the following dungeons. |
| Experienced Spelunker | `64017`, `62032` | Dungeons | Complete the following dungeons. |
| Master Spelunker | `64018`, `62033` | Dungeons | Complete the following dungeons. |

### Native: Raids

| Achievement | Native ID aliases | Group | Description |
| --- | --- | --- | --- |
| Conqueror of the Wilds | `62034`, `64019` | Raids | Defeat the following encounters in Hyjal Summit. |
| Conqueror of the Deeps | `64020`, `62035` | Raids | Defeat the following encounters in the Barrow Deeps. |
| Conqueror of the Lair | `64030`, `684` | Raids | Defeat Onyxia. |

### Native: Player Vs. Player

| Achievement | Native ID aliases | Group | Description |
| --- | --- | --- | --- |
| Rank 3 | `62041`, `64021` | Ranks | Reach the rank of Sergeant in the Player vs. Player Honor System. |
| Rank 7 | `62042`, `64022` | Ranks | Reach the rank of Knight-Lieutenant or Blood Guard in the Player vs. Player Honor System. |
| Rank 10 | `62043`, `64023` | Ranks | Reach the rank of Lieutenant-Commander or Champion in the Player vs. Player Honor System. |
| Rank 13 | `64024`, `62044` | Ranks | Reach the rank of Field Marshal or Warlord in the Player vs. Player Honor System. |
| Rank 14 | `64025`, `62045` | Ranks | Reach the rank of Grand Marshal or High Warlord in the Player vs. Player Honor System. |
| Master of Alterac Valley | `62046`, `64026` | Reputations | Reach exalted reputation with the Frostwolf Clan or Stormpike Guard. |
| Master of Arathi Basin | `62047`, `64027` | Reputations | Reach exalted reputation with the Defilers or League of Arathor. |
| Master of Warsong Gulch | `64028`, `62048` | Reputations | Reach exalted reputation with the Warsong Outriders or Silverwing Sentinels. |
| Master of Darkspear Islands | `64029`, `62049` | Reputations | Reach exalted reputation with the Darkspear Raiders or Theramore Expeditionary Force. |
| Field of Honor: Week 4 | `63340`, `64031` | Season Journey | Complete Week 4 of the Field of Honor Journey. |
| Field of Honor: Week 7 | `64032`, `63341` | Season Journey | Complete Week 7 of the Field of Honor Journey. |
| Field of Honor: Week 10 | `64033`, `63342` | Season Journey | Complete Week 10 of the Field of Honor Journey. |

### Native: Adventure

| Achievement | Native ID aliases | Group | Description |
| --- | --- | --- | --- |
| Lord Valthalak Laid to Rest | `64014`, `62054` | Adventure | Complete the questline beginning with An Earnest Proposition, and ending with Saving the Best for Last. |
| Explorer | `64015`, `62382` | Adventure | Have a character with the Explore Azeroth achievement. |
| Explore Azeroth | `62053` | Explorer | Complete the zone map for all existing zones in Eastern Kingdoms and Kalimdor on a single character. |
| Explore Eastern Kingdoms | `62353` | Explorer | Complete the maps of Eastern Kingdoms on a single character: |
| Explore Kalimdor | `62355` | Explorer | Complete the maps of Kalimdor on a single character: |

## Source files

- `LegacyAchievementsReforged/LegacyAchievementsReforged.lua`: generated custom definitions, authored sections, availability and retained imports.
- `LegacyAchievementsReforged/Data.lua`, `DataQuests.lua`, `DataProfDungeons.lua`, `DataExtra.lua`: supporting data and bundled native references.
- `LegacyAchievementsReforged/Integrations/CustomAdapter.lua`: custom presentation filtering.
- `LegacyAchievementsReforged/Integrations/LegacyAdapter.lua`: live native Legacy catalog and reward reads.

This export does not execute progress evaluators, award achievements, or modify addon saves.
