-- Custom money observations use copper only. Native Legacy requirements and
-- the alpha's historical `money`/`done` fields are never rewritten here.
local _, ns = ...
local M = {}
ns.MoneyTracking = M
local MAX_COPPER, MAX_TEXT = 1000000000000, 2048
local defaults = { gold100 = 50000, gold1000 = 250000, gold5000 = 1000000, breadwinner = 1000000 }
local lootKeys = { "gold100", "gold1000", "gold5000" }
local sourceIDs = { loot = 333, quest = 326 }
local sourceNames = { loot = "Gold looted", quest = "Gold from quest rewards" }
local factors = { gold = 10000, silver = 100, copper = 1 }
local snapshot
local eventIDs = setmetatable({}, { __mode = "k" })

local function safe(value)
    if type(value) == "nil" then return true end
    if type(issecretvalue) ~= "function" then return true end
    local ok, hidden = pcall(issecretvalue, value)
    return ok and not hidden
end
local function integer(value)
    return safe(value) and type(value) == "number" and value == value and value >= 0
        and value <= MAX_COPPER and value % 1 == 0 and value or nil
end
local function text(value)
    return safe(value) and type(value) == "string" and #value <= MAX_TEXT and value or nil
end
local function call(fn, ...)
    if type(fn) ~= "function" then return nil end
    local ok, a, b = pcall(fn, ...)
    if ok then return a, b end
end
local function scope(db)
    if type(db) ~= "table" or not safe(db) then return false end
    if ns.FA and type(ns.FA.CharacterScope) == "function" then
        local matches, identity = call(ns.FA.CharacterScope, db)
        return safe(matches) and matches == true, identity
    end
    return true
end
local function config()
    local account = ForeverAchievementsDB
    local c = type(account) == "table" and safe(account) and account.moneyConfig
    return type(c) == "table" and safe(c) and c or {}
end
function M.Threshold(key)
    local c = config().thresholds
    if type(c) ~= "table" or not safe(c) then return defaults[key] end
    if key == "breadwinner" then return integer(c[key]) and c[key] > 0 and c[key] or defaults[key] end
    local previous, values = 0, {}
    for _, k in ipairs(lootKeys) do
        local candidate = c[k]
        if not safe(candidate) then return defaults[key] end
        local v = candidate == nil and defaults[k] or integer(candidate)
        if not v or v <= previous then return defaults[key] end
        previous, values[k] = v, v
    end
    return values[key]
end
function M.Configure(key, copper)
    copper = integer(copper)
    if not defaults[key] or not copper or copper <= 0 then return false, "Use a known custom key and positive integer copper." end
    local values = {}
    for _, k in ipairs(lootKeys) do values[k] = k == key and copper or M.Threshold(k) end
    if values.gold100 >= values.gold1000 or values.gold1000 >= values.gold5000 then
        return false, "Loot thresholds must increase from gold100 to gold1000 to gold5000."
    end
    if type(ForeverAchievementsDB) == "nil" then ForeverAchievementsDB = {} end
    if type(ForeverAchievementsDB) ~= "table" or not safe(ForeverAchievementsDB) then return false, "Settings unavailable." end
    if not safe(ForeverAchievementsDB.moneyConfig) or ForeverAchievementsDB.moneyConfig ~= nil
        and type(ForeverAchievementsDB.moneyConfig) ~= "table" then
        return false, "Existing money settings are malformed; nothing was overwritten."
    end
    ForeverAchievementsDB.moneyConfig = ForeverAchievementsDB.moneyConfig or {}
    local c = ForeverAchievementsDB.moneyConfig
    if not safe(c.thresholds) or c.thresholds ~= nil and type(c.thresholds) ~= "table" then return false, "Existing thresholds are malformed." end
    c.thresholds = c.thresholds or {}
    c.thresholds[key] = copper
    return true
end
function M.Format(copper)
    copper = integer(copper)
    if not copper then return "Unavailable" end
    local gold = math.floor(copper / 10000)
    local silver = math.floor(copper % 10000 / 100)
    local coin = copper % 100
    local out = {}
    if gold > 0 then out[#out + 1] = gold .. "g" end
    if silver > 0 then out[#out + 1] = silver .. "s" end
    if coin > 0 or #out == 0 then out[#out + 1] = coin .. "c" end
    return table.concat(out, " ")
end
function M.Description(key)
    local need = M.Format(M.Threshold(key))
    if key == "breadwinner" then return "Earn " .. need .. " from quest rewards." end
    return "Loot " .. need .. "."
end
local function escape(value) return (value:gsub("([%^%$%(%)%%%.%[%]%*%+%-%?])", "%%%1")) end
local function number(value)
    value = value:match("^%s*(.-)%s*$")
    if value:match("^%d+$") then return integer(tonumber(value)) end
    -- Grouping only: 1,234 / 1.234 / 1 234. Decimal currency values without
    -- explicit subunits are ambiguous and must not become copper totals.
    local sep = value:match("%d([^%d])%d")
    if not sep or sep ~= "," and sep ~= "." and sep ~= " " then return nil end
    local parts = {}
    for part in (value .. sep):gmatch("(.-)" .. escape(sep)) do parts[#parts + 1] = part end
    if #parts < 2 or #parts[1] < 1 or #parts[1] > 3 or not parts[1]:match("^%d+$") then return nil end
    for i = 2, #parts do if not parts[i]:match("^%d%d%d$") then return nil end end
    return integer(tonumber(table.concat(parts)))
end
function M.ParseCoins(value)
    value = text(value)
    if not value then return nil, "No readable money text" end
    value = value:gsub("\194\160", " "):gsub("\226\128\175", " ")
    value = value:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
    local total, count = 0, 0
    local remainder = value:gsub("(%d[%d%., ]*)%s*|T([^|]+)|t", function(raw, texture)
        local coin = texture:lower():match("ui%-(%a+)icon")
        local amount = number(raw)
        if not factors[coin] or not amount or count >= 32 then return raw .. "|T" .. texture .. "|t" end
        total, count = total + amount * factors[coin], count + 1
        return ""
    end)
    if count == 0 or remainder:match("%S") or not integer(total) then return nil, "Currency units not explicitly verified" end
    return total
end
local function formatAmount(value, fmt)
    if not fmt then return nil end
    local start, finish = fmt:find("%%[ds]")
    if not start then return nil end
    local pattern = escape(fmt:sub(1, start - 1)) .. "(%d[%d%., ]*)" .. escape(fmt:sub(finish + 1))
    return number(value:match(pattern) or "")
end
function M.ParseLoot(value)
    value = text(value)
    if not value then return nil, "Loot message unreadable" end
    value = value:gsub("\194\160", " "):gsub("\226\128\175", " ")
    if value:match("%-%s*%d") then return nil, "Negative loot amount rejected" end
    -- CHAT_MSG_MONEY can include coin textures inside the localized loot
    -- sentence. Extract only recognized currency tags, never plain numbers.
    local tags = {}
    for amount, texture in value:gmatch("(%d[%d%., ]*)%s*|T([^|]+)|t") do
        if #tags >= 32 then return nil, "Too many currency components" end
        tags[#tags + 1] = amount .. "|T" .. texture .. "|t"
    end
    if #tags > 0 then return M.ParseCoins(table.concat(tags, " ")) end
    local total, found = 0, false
    for _, coin in ipairs({ "gold", "silver", "copper" }) do
        local upper = coin:upper()
        local fmt = text(_G[upper .. "_AMOUNT"])
        local amount = formatAmount(value, fmt)
        if amount == nil then
            local word = text(_G[upper]) or ({ gold = "Gold", silver = "Silver", copper = "Copper" })[coin]
            local raw = value:match("(%d[%d%., ]*)%s*" .. escape(word))
            amount = raw and number(raw)
        end
        if amount ~= nil then total, found = total + amount * factors[coin], true end
    end
    if not found or not integer(total) then return nil, "No recognized localized currency amount" end
    return total
end
local function ledger(db, create)
    local d = db.moneyTracking
    if not safe(d) then return nil end
    if d == nil and create then
        d = { version = 1, unit = "copper", observedLootCopper = 0 }
        local _, identity = scope(db)
        if ns.FA and type(ns.FA.CharacterScope) == "function" then
            if type(identity) ~= "table" or not safe(identity) or not text(identity.key) then return nil end
            d.ownerIdentity = { key = identity.key, name = identity.name, surname = identity.surname,
                realm = identity.realm, guid = identity.guid, verified = true }
        end
        d.startedAt = integer(call(time))
        db.moneyTracking = d
    end
    if type(d) ~= "table" or not safe(d) or not safe(d.version) or not safe(d.unit)
        or d.version ~= 1 or d.unit ~= "copper"
        or not integer(d.observedLootCopper) then return nil end
    if ns.FA and type(ns.FA.CharacterScope) == "function" then
        if type(d.ownerIdentity) ~= "table" or not safe(d.ownerIdentity)
            or call(ns.FA.CharacterScope, { trackingIdentity = d.ownerIdentity }) ~= true then return nil end
    end
    return d
end
local function source(metric)
    local id = sourceIDs[metric]
    local info = type(GetAchievementInfo) == "function" and { pcall(GetAchievementInfo, id) } or {}
    local title = info[1] == true and text(info[3]) or nil
    local flags = info[1] == true and integer(info[10]) or nil
    local raw = text(call(GetStatistic, id))
    if flags == nil then
        return nil, { id = id, title = title, raw = raw, reason = "Statistic completion scope unavailable" }
    end
    local accountFlag = integer(ACHIEVEMENT_FLAGS_ACCOUNT) or 131072
    if accountFlag > 0 and flags and math.floor(flags / accountFlag) % 2 == 1 then
        return nil, { id = id, title = title, raw = raw, reason = "Account-wide statistic is not character earnings" }
    end
    local c = config().statisticNames
    local expected = type(c) == "table" and safe(c) and text(c[metric]) or sourceNames[metric]
    if not title or title:lower() ~= expected:lower() then
        return nil, { id = id, title = title, raw = raw, reason = "Lifetime statistic identity unverified" }
    end
    local copper, reason = M.ParseCoins(raw)
    return copper, { id = id, title = title, raw = raw, reason = reason, unit = copper and "copper" or nil }
end
local function read(db, metric)
    if not scope(db) then return nil, "unknown", { reason = "Current-character scope unverified" } end
    local lifetime, detail = source(metric)
    if metric == "quest" then return lifetime, lifetime ~= nil and "lifetime" or "unsupported", detail end
    local d = ledger(db, false)
    if lifetime ~= nil and (not d or lifetime >= d.observedLootCopper) then return lifetime, "lifetime", detail end
    if d then return d.observedLootCopper, "since_tracking", detail end
    return nil, "unknown", detail
end
function M.Read(db, metric)
    if metric ~= "loot" and metric ~= "quest" then return nil, "unsupported", { reason = "Unknown money metric" } end
    if snapshot and snapshot.db == db then
        local v = snapshot.values[metric]
        if not v then v = { read(db, metric) }; snapshot.values[metric] = v end
        return unpack(v, 1, 3)
    end
    return read(db, metric)
end
function M.WithSnapshot(db, fn, ...)
    local previous = snapshot
    if not previous or previous.db ~= db then snapshot = { db = db, values = {} } end
    local function pack(...) return { n = select("#", ...), ... } end
    local ok, result = pcall(function(...) return pack(fn(...)) end, ...)
    snapshot = previous
    if not ok then error(result, 0) end
    return unpack(result, 1, result.n)
end
function M.Progress(db, key)
    local need = M.Threshold(key)
    if not need then return nil, nil, "Unknown money achievement" end
    local current = M.Read(db, key == "breadwinner" and "quest" or "loot")
    -- Provenance belongs in /fa money report. Unknown earnings stay unknown;
    -- the ordinary progress label must not manufacture a zero or repeat it.
    return current and math.min(current, need), need,
        (current ~= nil and M.Format(current) or "—") .. " / " .. M.Format(need)
end
function M.Sync(db)
    if not scope(db) then return false end
    -- Initializes a clearly dated, zero-based observed ledger. Opening the UI,
    -- logging in, and synchronizing a statistic never add earnings.
    local d = ledger(db, true)
    return d ~= nil
end
function M.ObserveLoot(db, msg, lineID)
    if not scope(db) then return false end
    local copper = M.ParseLoot(msg)
    if not copper or copper <= 0 then return false end
    local d = ledger(db, true)
    if not d or not integer(d.observedLootCopper + copper) then return false end
    lineID = integer(lineID)
    if lineID and lineID > 0 then
        local seen = eventIDs[db]
        if not seen then seen = { order = {}, values = {} }; eventIDs[db] = seen end
        if seen.values[lineID] then return false end
        seen.values[lineID] = true; seen.order[#seen.order + 1] = lineID
        if #seen.order > 128 then seen.values[table.remove(seen.order, 1)] = nil end
    end
    d.observedLootCopper = d.observedLootCopper + copper
    return true
end
function M.Report(db)
    local out = { "Forever Achievements money audit: all stored thresholds and observed totals use copper (100c=1s; 10000c=1g)." }
    local legacy = type(db) == "table" and safe(db) and db.money
    out[#out + 1] = "Historical alpha money counter preserved: " .. (integer(legacy) and tostring(legacy) or "unavailable")
        .. "; excluded because previous plain-statistic units were not verified."
    for _, metric in ipairs({ "loot", "quest" }) do
        local current, mode, detail = M.Read(db, metric)
        out[#out + 1] = metric .. ": " .. M.Format(current) .. "; source=" .. mode .. "; statistic=" .. sourceIDs[metric]
            .. "; title=" .. (detail.title or "unavailable") .. "; raw=" .. (detail.raw and string.format("%q", detail.raw) or "unavailable")
            .. "; evidence=" .. (detail.reason or "Verified statistic identity and coin units")
    end
    for _, key in ipairs({ "gold100", "gold1000", "gold5000", "breadwinner" }) do
        out[#out + 1] = key .. ": " .. M.Threshold(key) .. " copper (" .. M.Format(M.Threshold(key)) .. ")"
    end
    return out
end
function M.Command(db, command)
    command = text(command) or ""
    local key, amount = command:match("^%s*threshold%s+(%w+)%s+(%d+)%s*$")
    if key then
        local ok, why = M.Configure(key, tonumber(amount))
        return { ok and ("Custom " .. key .. " threshold: " .. M.Format(tonumber(amount)) .. ". Existing completions retained.") or why }, ok
    end
    if command:match("^%s*$") or command:match("^%s*report%s*$") then return M.Report(db), false end
    return { "Usage: /fa money report; /fa money threshold <gold100|gold1000|gold5000|breadwinner> <integer copper>." }, false
end
