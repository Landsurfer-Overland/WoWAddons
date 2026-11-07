#!/usr/bin/env python3
"""Inventory every production definition; no game APIs are simulated as success.

Uses the existing Lua 5.1 development dependency. A standalone Lua interpreter
can export the same metadata when lupa is unavailable; it does not validate the
client. --check detects stale audit coverage after catalog changes.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = "1.60.1.70862"
CLIENT_COMMIT = "9dc84f0d3bbae1768ac3405b3716000bd93eda06"
DEFAULT = ROOT / "docs/research/client-70862-achievement-audit.json"
BOOTSTRAP = r'''
unpack=unpack or table.unpack
ns={}; SlashCmdList={}; UISpecialFrames={}; tinsert=table.insert
function CreateFrame()
    return {SetScript=function() end,RegisterEvent=function() end,
        RegisterUnitEvent=function() end,Hide=function() end}
end
C_Timer={After=function() end,NewTicker=function() return {} end}
time=function() return 1 end
GetTime=function() return 0 end
UnitLevel=function() return 1 end
UnitFactionGroup=function() return "Alliance" end
UnitName=function() return "Audit","Character" end
GetRealmName=function() return "Audit realm" end
UnitGUID=function() return "Player-AUDIT" end
'''
COLLECT = r'''
local function quote(s)
    return '"'..s:gsub('[%z\1-\31\\"]',function(c)
        if c=='"' then return '\\"' elseif c=='\\' then return '\\\\' end
        return string.format('\\u%04x',string.byte(c))
    end)..'"'
end
local function json(value)
    if type(value)=='string' then return quote(value) end
    if type(value)=='number' or type(value)=='boolean' then return tostring(value) end
    if type(value)~='table' then return 'null' end
    local entries={}
    if #value>0 then
        for i=1,#value do entries[#entries+1]=json(value[i]) end
        return '['..table.concat(entries,',')..']'
    end
    for k,v in pairs(value) do entries[#entries+1]=quote(tostring(k))..':'..json(v) end
    table.sort(entries)
    return '{'..table.concat(entries,',')..'}'
end
local categories={}
for key,sections in pairs(ns.LAR.CATEGORY_SECTIONS) do
    for _,section in ipairs(sections) do
        for _,a in ipairs(section.list) do categories[a.key]={category=key,section=section.title} end
    end
end
local out={}
for _,a in ipairs(ns.LAR.ALL) do
    local category=categories[a.key] or {}
    local info=debug.getinfo(a.progress,'S')
    local facts={}
    for i=1,64 do
        local name,value=debug.getupvalue(a.progress,i)
        if not name then break end
        if name=='n' or name=='stat' or name=='factions' or name=='items' or name=='spells' or name=='skill' then facts[name]=value end
        if name=='e' and type(value)=='table' then facts.nativeIDs=value.ids end
    end
    out[#out+1]={key=a.key,title=a.name,description=a.desc or '',category=category.category,
        section=category.section,referenceID=a.id,native=a.native==true,unsupported=a.unsupported==true,
        unsupportedReason=a.unsupportedReason,series=a.series,skill=a.skill,class=a.class,faction=a.faction,
        points=a.pts,dungeon=a.dungeon,facts=facts,criteriaList=a.list,
        dynamicCriteria=type(a.dynamicList)=='function',observedItems=type(a.seen)=='function',
        definition={file=info.source:gsub('^@',''),firstLine=info.linedefined,lastLine=info.lastlinedefined}}
end
return json(out)
'''
FILES = ("AlphaUI.lua", "Data.lua", "DataQuests.lua", "DataProfDungeons.lua",
         "DataExtra.lua", "MoneyTracking.lua", "LegacyAchievementsReforged.lua")

# These describe evidence units and refresh paths, not proof that every authored
# item/quest/statistic ID still exists in this build's game-data tables.
FAMILIES = {
    "level": (["UnitLevel"], ["PLAYER_LEVEL_UP"], "Current character level", "none"),
    "riding": (["C_SkillInfo.GetSkillLineInfoByID", "IsPlayerSpell", "C_SpellBook.IsSpellKnown", "GetSkillLineInfo"],
               ["SKILL_LINES_CHANGED", "SPELLS_CHANGED"], "Current skill/spells; observed rank history", "Legacy spell IDs require live content checks"),
    "money": (["GetStatistic", "GetAchievementInfo", "GetMoney"], ["CHAT_MSG_MONEY", "QUEST_TURNED_IN", "PLAYER_MONEY"],
              "Verified native coin-unit total, else observed ledger", "Fallback ledger covers tracking period only"),
    "collection": (["C_Container.GetContainerNumSlots", "C_Container.GetContainerItemID", "C_Item.GetItemInfoInstant", "GetInventoryItemID"],
                   ["BAG_UPDATE_DELAYED", "PLAYER_EQUIPMENT_CHANGED", "COMPANION_LEARNED"], "Character bag/equipment observations", "Account journals deliberately excluded; historical bag-only items can be missed"),
    "quests": (["GetStatistic", "C_QuestLog.GetAllCompletedQuestIDs", "C_QuestLog.IsQuestFlaggedCompleted"],
               ["QUEST_TURNED_IN"], "Native totals or exact completed quest flags", "Unique flags approximate quest totals when statistic is unavailable"),
    "loremaster": (["C_QuestLog.GetAllCompletedQuestIDs", "QuestDB.Exists", "QuestDB.Get"], ["QUEST_TURNED_IN"],
                   "Completed flags classified through optional QuestieDB", "Legacy quest roster/continent thresholds need content verification"),
    "exploration": (["C_Map.GetMapInfo", "C_Map.GetPlayerMapPosition", "C_MapExplorationInfo.GetExploredMapTextures", "C_MapExplorationInfo.GetExploredAreaIDsAtPosition"],
                    ["MAP_EXPLORATION_UPDATED", "ZONE_CHANGED", "ZONE_CHANGED_NEW_AREA"], "Character-bound observed discoveries; personal matching native completion can recover", "Legacy overlay roster must match current maps; remote shared maps do not prove character history"),
    "skills": (["C_SkillInfo.GetSkillLineInfoByID", "GetSkillLineInfo", "GetProfessionInfo"], ["SKILL_LINES_CHANGED", "LEARNED_SPELL_IN_SKILL_LINE"],
               "Current rank or previously observed highest rank", "Previously dropped professions cannot be reconstructed without exact native evidence"),
    "recipes": (["GetStatistic"], ["NEW_RECIPE_LEARNED", "TRADE_SKILL_LIST_UPDATE"], "Native cooking recipe statistic 1745", "Statistic identity/unit requires live verification; profession view/filter counts are not substituted"),
    "fishing": (["GetStatistic", "IsFishingLoot", "GetLootSlotLink", "GetLootSourceInfo"], ["LOOT_OPENED", "LOOT_CLOSED", "CRITERIA_UPDATE"],
                "Native statistics plus observed fishing windows", "Existing skill-minus-one floor and window/item units are approximate; retained, not newly verified"),
    "quickfish": (["QuickFishDB.log", "QuickFishDB.rares"], ["LOOT_CLOSED"], "Optional dependency's existing catch log", "Dependency log is account-wide; not a native per-character lifetime counter"),
    "dungeons": (["GetStatistic", "GetAchievementInfo", "GetAchievementNumCriteria", "GetAchievementCriteriaInfo", "UnitIsDead", "UnitGUID"],
                 ["CRITERIA_UPDATE", "CRITERIA_COMPLETE", "CRITERIA_EARNED", "ENCOUNTER_END", "BOSS_KILL", "UPDATE_INSTANCE_INFO"],
                 "Personal native criteria/statistics, then confirmed observed kills", "Named single-boss dungeon completion can infer final-boss defeat; no multi-boss blanket credit; legacy head-quest fallback remains approximate"),
    "reputation": (["C_Reputation.GetFactionDataByID", "GetFactionInfoByID"], ["UPDATE_FACTION"], "Current reputation or observed maximum", "Authored faction IDs, caps and account-wide reputation require live checks"),
    "pvp-statistics": (["GetStatistic", "GetPVPLifetimeStats"], ["PLAYER_PVP_KILLS_CHANGED", "UPDATE_BATTLEFIELD_SCORE", "UPDATE_BATTLEFIELD_STATISTIC"],
                       "Native PvP statistics", "Legacy statistic IDs/units require live verification"),
    "pvp-observed": (["GetBattlefieldScore", "GetBattlefieldWinner", "GetBattlefieldInstanceRunTime", "UnitIsDead", "UnitIsEnemy"],
                     ["UPDATE_BATTLEFIELD_SCORE", "CHAT_MSG_TEXT_EMOTE"], "Observed match/target behavior", "No pre-installation history; scoreboard timing and surnames need live checks"),
    "ownership": (["C_Item.GetItemCount", "IsEquippedItem", "IsPlayerSpell", "C_SpellBook.IsSpellKnown"], ["BAG_UPDATE_DELAYED", "SPELLS_CHANGED"],
                  "Current item or known spell; recorded ownership", "Ownership can infer acquisition source; class-mount spell does not prove a specific quest path"),
    "observed": (["UnitName", "UnitIsDead", "GetItemInfo", "GetLootRollItemInfo", "UnitPosition"],
                 ["PLAYER_TARGET_CHANGED", "CHAT_MSG_TEXT_EMOTE", "ITEM_TEXT_READY", "BAG_UPDATE_DELAYED", "FALL_LANDED"],
                 "Addon observations since tracking began", "No durable pre-installation record verified; actual event/API depends on the listed objective"),
    "native": (["GetAchievementInfo", "GetAchievementNumCriteria", "GetAchievementCriteriaInfo"],
               ["ACHIEVEMENT_EARNED", "CRITERIA_UPDATE", "CRITERIA_COMPLETE", "CRITERIA_EARNED"],
               "Native achievement completion/progress", "Native adapter preserves character/account attribution; legacy imported rows are excluded from combined custom catalog"),
}
FAMILIES.update({
    "emotes": (["UnitExists", "UnitName", "UnitIsPlayer", "DoEmote", "C_ChatInfo.PerformEmote"],
               ["CHAT_MSG_TEXT_EMOTE"], "Observed /love target", "English target/emote names and secure hooks; no historical emote log"),
    "observed-kills": (["UnitGUID", "UnitName", "UnitIsDead", "UnitIsTapDenied", "UnitClassification"],
                       ["PLAYER_TARGET_CHANGED", "UNIT_HEALTH", "PLAYER_REGEN_ENABLED"],
                       "Confirmed observed target death", "Combat fields can be restricted; a disappearing living target no longer counts"),
    "books": (["ItemTextGetItem"], ["ITEM_TEXT_BEGIN"], "Observed opened book title", "English title roster; books read before tracking cannot be recovered"),
    "consumables": (["C_Container.GetContainerItemInfo", "C_Item.GetItemInfoInstant", "C_Item.GetItemSpell", "C_Item.GetItemNameByID", "CursorHasItem"],
                    ["BAG_UPDATE_DELAYED"], "Observed single-item bag decrease outside merchant/mail/trade/bank/auction", "Consumption is inferred; deletion or other bag changes can resemble eating; English food/drink classification"),
    "loot-rolls": (["GetItemInfo"], ["CHAT_MSG_LOOT"], "Observed localized loot-roll result text", "Pattern/name attribution and item quality need live locale/surname tests; no historical roll log"),
    "fall": (["UnitPosition", "UnitIsDeadOrGhost", "IsFalling"], ["FALL_LANDED"], "Measured, versioned character fall", "Requires readable position and survival samples; no old fall history"),
})


def export_catalog():
    load = "\n".join("assert(loadfile(%s))('LegacyAchievementsReforged',ns)" % json.dumps(str(ROOT / "LegacyAchievementsReforged" / p)) for p in FILES)
    program = BOOTSTRAP + load + "\nlocal function collect()\n" + COLLECT + "\nend\nreturn collect()"
    try:
        from lupa.lua51 import LuaRuntime
    except ImportError:
        runtime = next((shutil.which(p) for p in ("lua5.1", "luajit", "lua", "texlua") if shutil.which(p)), None)
        if runtime is None:
            raise SystemExit("Install requirements-dev.txt or provide a standalone Lua interpreter")
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "audit.lua"
            script.write_text("local function run()\n" + program + "\nend\nio.write(run())\n")
            result = subprocess.run([runtime, str(script)], check=True, text=True, capture_output=True)
            raw = result.stdout
    else:
        raw = LuaRuntime(unpack_returned_tuples=True).execute(program)
    return json.loads(raw)


def family(row):
    if row["native"]: return "native"
    if row.get("dungeon"): return "dungeons"
    key, section = row["key"], row.get("section")
    if row["category"] == "exploration": return "exploration"
    if row["category"] == "feats": return "ownership"
    if row["category"] == "reputation" or section == "BATTLEGROUND REPUTATION": return "reputation"
    if section == "LEVELS": return "level"
    if section == "RIDING": return "riding"
    if section == "MONEY": return "money"
    if section == "COLLECTIONS": return "collection"
    if key == "critters": return "emotes"
    if key == "books": return "books"
    if key == "fall": return "fall"
    if key == "pests" or key.startswith("rare") and section == "RARE ENEMIES": return "observed-kills"
    if section == "FOOD & DRINK": return "consumables"
    if section == "LOOT ROLLS": return "loot-rolls"
    if section == "LOREMASTER": return "loremaster"
    if row["category"] == "quests": return "quests"
    if section == "QUICK FISH": return "quickfish"
    if row.get("series") == "recipes": return "recipes"
    if section == "FISHING" and not row.get("skill"): return "fishing"
    if row["category"] == "professions": return "skills"
    if row["category"] == "pvp":
        return "pvp-observed" if key in ("grimReaper", "wreckingBall", "wsgFast", "abFast", "avFast", "hugDead") else "pvp-statistics"
    return "observed"


def audit():
    rows = export_catalog()
    for row in rows:
        row["definition"]["file"] = str(Path(row["definition"]["file"]).relative_to(ROOT))
        group = family(row)
        row.update(family=group, validation="source-reviewed; in-game payload/content verification pending",
                   personalNativeFallback=bool(row.get("referenceID") and not row["native"] and not row["unsupported"]))
    rows.sort(key=lambda r: r["key"])
    return {"schemaVersion": 1, "reviewDate": "2026-11-07", "clientBuild": BUILD, "clientSourceCommit": CLIENT_COMMIT,
            "scope": "Every production definition, including hidden/unsupported definitions and legacy native imports",
            "limits": "Source/API-contract audit; no live character or game-data database was accessible. An API declaration does not verify a content ID or historical coverage.",
            "evidencePolicies": {name: dict(apis=values[0], refreshEvents=["PLAYER_LOGIN", *values[1]],
                                           historicalCoverage=values[2], assumptions=values[3])
                                 for name, values in sorted(FAMILIES.items())},
            "nativeFallbackPolicy": "Only matching reference ID AND normalized title AND wasEarnedByMe=true. Dungeon fallback separately checks personal Spelunker criteria; named single-boss dungeon completion is an explicit objective inference.",
            "total": len(rows), "custom": sum(not r["native"] for r in rows),
            "nativeImports": sum(r["native"] for r in rows), "families": dict(sorted(Counter(r["family"] for r in rows).items())),
            "achievements": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = audit()
    if args.check:
        if not args.output.exists() or json.loads(args.output.read_text()) != result:
            raise SystemExit("Achievement audit is stale; regenerate with tools/audit_achievement_apis.py")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Audited {result['total']} definitions: {result['custom']} custom, {result['nativeImports']} native imports")


if __name__ == "__main__":
    main()
