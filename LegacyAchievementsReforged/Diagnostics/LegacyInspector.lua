-- Manual, read-only Legacy UI diagnostic. No LAR dependency, hooks, timers,
-- SavedVariables, native setters, achievement queries, or network calls.
local _, ns = ...
local Inspector = {}
ns.LegacyInspector = Inspector
Inspector.Config = {
    maxDepth = 4, maxObjects = 80, maxOutputChars = 60000,
    maxFields = 24, maxEntries = 20, maxGlobalMatches = 100,
    maxGlobalScan = 30000,
}

local previousSnapshot
local SCRIPT_NAMES = { "OnEvent", "OnShow", "OnHide", "OnUpdate", "OnClick", "OnMouseDown" }
local READ_METHODS = {
    GetObjectType = true, GetName = true, GetParent = true, GetChildren = true,
    GetRegions = true, GetScript = true, IsForbidden = true,
    GetDataProvider = true, GetCollection = true, GetSize = true, GetElementData = true,
}

local function Secret(value)
    local test = rawget(_G, "issecretvalue")
    if type(test) == "function" then
        local ok, restricted = pcall(test, value)
        return not ok or restricted == true
    end
    return false
end

local function Kind(value)
    if Secret(value) then return "restricted" end
    return type(value)
end

local function Scalar(value)
    local kind = Kind(value)
    if kind == "restricted" then return "<restricted>" end
    if kind == "string" then
        local text = value:sub(1, 240):gsub("[%c]", " ")
        return text .. (#value > 240 and "..." or "")
    end
    if kind == "number" or kind == "boolean" then return tostring(value) end
    if kind == "nil" then return "unavailable" end
    return "<" .. kind .. ">" -- Never invoke an object's __tostring.
end

-- Read direct fields / table-valued inheritance without executing __index.
-- Only native WoW wrappers may use a function-valued index for known getters.
local function Read(object, key)
    local kind = Kind(object)
    if kind == "table" then
        local value = rawget(object, key)
        if Secret(value) then return nil, "restricted" end
        if value ~= nil then return value end
        local ok, mt = pcall(getmetatable, object)
        if ok and Kind(mt) == "table" then
            local index = rawget(mt, "__index")
            if Kind(index) == "table" then
                value = rawget(index, key)
                if Secret(value) then return nil, "restricted" end
                return value
            end
        end
        if not READ_METHODS[key] or Kind(rawget(object, 0)) ~= "userdata" then return nil end
    elseif kind ~= "userdata" or not READ_METHODS[key] then
        return nil
    end
    local ok, value = pcall(function() return object[key] end)
    if not ok then return nil, "inaccessible" end
    if Secret(value) then return nil, "restricted" end
    return value
end

local function Pack(...) return { n = select("#", ...), ... } end

local function Call(object, name, ...)
    local method, reason = Read(object, name)
    if Kind(method) ~= "function" then return nil, reason or "unsupported" end
    local result = Pack(pcall(method, object, ...))
    if not result[1] then return nil, "getter failed" end
    return result
end

local function First(object, name)
    local result, reason = Call(object, name)
    if not result then return nil, reason end
    if Secret(result[2]) then return nil, "restricted" end
    return result[2]
end

local function Forbidden(object)
    local check = Read(object, "IsForbidden")
    if Kind(check) ~= "function" then return false end
    local result = Call(object, "IsForbidden")
    return not result or Secret(result[2]) or result[2] == true
end

local function Combat()
    local check = rawget(_G, "InCombatLockdown")
    if Kind(check) ~= "function" then return false end
    local ok, value = pcall(check)
    return not ok or Secret(value) or value == true
end

local function Limit(key, default, minimum, maximum)
    local value = rawget(Inspector.Config, key)
    if Kind(value) ~= "number" or value ~= value then value = default end
    return math.floor(math.max(minimum, math.min(maximum, value)))
end

local function DataKey(key)
    if Kind(key) ~= "string" then return false end
    local lower = key:lower()
    return lower:find("id") or lower:find("name") or lower:find("desc") or
        lower:find("categor") or lower:find("progress") or lower:find("point") or
        lower:find("reward") or lower:find("complet") or lower:find("claim") or
        lower:find("account") or lower:find("character") or lower:find("milestone") or
        lower:find("threshold") or lower:find("data") or lower:find("collection") or lower:find("element")
end

local function Keys(object, maximum)
    local keys, key, scanned = {}, nil, 0
    while scanned < 256 do
        local ok, nextKey, value = pcall(next, object, key)
        if not ok or Secret(nextKey) or nextKey == nil then break end
        key, scanned = nextKey, scanned + 1
        local kind = Kind(key)
        if kind == "string" or kind == "number" then
            keys[#keys + 1] = { key = key, value = value,
                rank = Kind(value) == "function" and 2 or (DataKey(key) and 0 or 1) }
        end
    end
    table.sort(keys, function(a, b)
        if a.rank ~= b.rank then return a.rank < b.rank end
        if Kind(a.key) == "number" and Kind(b.key) == "number" then return a.key < b.key end
        return Scalar(a.key) < Scalar(b.key)
    end)
    local limited = #keys > maximum or scanned == 256
    while #keys > maximum do table.remove(keys) end
    return keys, limited
end

local function Inspect()
    local state = {
        depth = Limit("maxDepth", 4, 0, 4), objects = Limit("maxObjects", 80, 1, 160),
        fields = Limit("maxFields", 24, 1, 64), entries = Limit("maxEntries", 20, 1, 100),
        outputLimit = Limit("maxOutputChars", 60000, 256, 120000),
        lines = {}, chars = 0, detailChars = 0, stopped = false, count = 0,
        counted = {}, dumped = {}, frames = {}, names = {}, limits = {}, origins = {}, methods = {},
        evidence = { challenge = {}, reward = {} },
    }
    local function line(text, detailed)
        if state.stopped then return end
        if detailed then
            if state.detailChars + #text + 1 > state.outputLimit * 0.45 then
                state.limits.output = true
                return
            end
            state.detailChars = state.detailChars + #text + 1
        end
        if state.chars + #text + 1 > state.outputLimit - 32 then
            state.lines[#state.lines + 1] = "[OUTPUT TRUNCATED: size limit]"
            state.stopped = true
            return
        end
        state.lines[#state.lines + 1] = text
        state.chars = state.chars + #text + 1
    end
    local function reserve(object)
        if state.counted[object] then return true end
        if state.count >= state.objects or state.stopped then
            state.limits.objects = true
            return false
        end
        state.counted[object] = true
        state.count = state.count + 1
        return true
    end
    local function frameLike(object)
        local kind = Kind(object)
        if kind ~= "table" and kind ~= "userdata" then return false end
        if state.frames[object] then return true end
        if kind == "table" and Kind(rawget(object, 0)) == "userdata" then return true end
        return Kind(Read(object, "GetObjectType")) == "function" and
            Kind(Read(object, "GetChildren")) == "function" and
            Kind(Read(object, "GetParent")) == "function"
    end
    local function evidence(context, label, key, value)
        if not state.evidence[context] or not DataKey(key) then return end
        local kind = Kind(value)
        if kind ~= "string" and kind ~= "number" and kind ~= "boolean" then return end
        local out = state.evidence[context]
        if #out < 24 then out[#out + 1] = Scalar(label .. "." .. Scalar(key)) .. " = " .. Scalar(value) end
    end
    local dump
    dump = function(object, label, depth, context, nested)
        if Kind(object) ~= "table" or rawequal(object, _G) or state.dumped[object] then return end
        if depth > state.depth then state.limits.depth = true; return end
        if not reserve(object) then return end
        state.dumped[object] = true
        local keys, limited = Keys(object, state.fields)
        if limited then state.limits.fields = true end
        local records = 0
        for _, item in ipairs(keys) do
            if state.stopped then break end
            local key, value = item.key, item.value
            if Kind(key) == "number" and Kind(value) == "table" then
                records = records + 1
                if records > state.entries then state.limits.entries = true; break end
            end
            local kind = Kind(value)
            local path = label .. "." .. Scalar(key)
            line("  " .. Scalar(path) .. " = " .. Scalar(value), true)
            if kind == "function" then
                if context then state.methods[#state.methods + 1] = { value = value, path = path }
                else state.origins[value] = path end
            end
            evidence(context, label, key, value)
            -- Recurse only into data-like fields and numeric records of an
            -- explicitly sampled data table. Frame references never recurse here.
            -- Provider collections are sampled exactly once below, under the
            -- entry budget, rather than through the general frame field dump.
            local deferred = (key == "dataProvider" and context ~= "reward") or
                (key == "collection" and rawequal(object, state.challengeProvider))
            if nested and kind == "table" and not deferred and not frameLike(value) and
                (DataKey(key) or Kind(key) == "number" or
                (Kind(key) == "string" and key:find("Mixin"))) then
                dump(value, path, depth + 1, context, true)
            end
        end
    end

    line("=== LEGACY ACHIEVEMENTS REFORGED INSPECTOR ===")
    line("")
    line("CLIENT")
    local build = rawget(_G, "GetBuildInfo")
    if Kind(build) == "function" then
        local result = Pack(pcall(build))
        if result[1] then
            line("Build: " .. Scalar(result[2]) .. " / " .. Scalar(result[3]) .. " / " .. Scalar(result[4]))
            line("Interface: " .. Scalar(result[5]))
        else line("Build / Interface: unavailable (GetBuildInfo failed)") end
    else line("Build / Interface: unavailable") end
    line("Project: " .. Scalar(rawget(_G, "WOW_PROJECT_ID")))
    line("Lua: " .. Scalar(rawget(_G, "_VERSION")))
    line("Budgets: depth=" .. state.depth .. " objects=" .. state.objects .. " entries=" .. state.entries)
    if Combat() then
        for _, heading in ipairs({ "FRAMES", "NAMESPACES", "CHALLENGE DATA", "REWARD TRACK" }) do
            line(""); line(heading); line("Unavailable: inspection deferred during combat.")
        end
        line(""); line("LIMITATIONS"); line("Leave combat before running the inspector.")
        line(""); line("RECOMMENDED INTEGRATION POINTS"); line("Unavailable until a safe inspection completes.")
        return table.concat(state.lines, "\n")
    end

    -- Raw namespace discovery: bounded key scan, no unknown function calls,
    -- no metatable enumeration, and no traversal of matching unrelated frames.
    local globals, key, scanned = {}, nil, 0
    local matchLimit = Limit("maxGlobalMatches", 100, 1, 200)
    local scanLimit = Limit("maxGlobalScan", 30000, 100, 50000)
    while scanned < scanLimit and #globals < matchLimit do
        local ok, nextKey, value = pcall(next, _G, key)
        if not ok or Secret(nextKey) or nextKey == nil then break end
        key, scanned = nextKey, scanned + 1
        if Kind(key) == "string" then
            local lower = key:lower()
            if lower:find("legacy") or lower:find("challenge") or lower:find("achievement") or lower:find("rewardtrack") then
                globals[#globals + 1] = { name = key, value = value }
            end
        end
    end
    if scanned == scanLimit or #globals == matchLimit then state.limits.globals = true end
    table.sort(globals, function(a, b) return a.name < b.name end)

    line(""); line("FRAMES")
    local root = rawget(_G, "LegacySystemFrame")
    -- Reserve the requested paths before generic expansion. A candidate's
    -- native parent getter must confirm each direct descendant relationship.
    local priority = {}
    local function prime(object, label, depth)
        if frameLike(object) and depth <= state.depth and reserve(object) then
            priority[#priority + 1] = { object = object, label = label, depth = depth }
            return object
        end
    end
    local function child(parent, key, depth)
        if not parent or depth > state.depth then return nil end
        local candidate = Read(parent, key)
        if not frameLike(candidate) or Forbidden(candidate) or not reserve(candidate) then return nil end
        if not rawequal(First(candidate, "GetParent"), parent) then return nil end
        return prime(candidate, "LegacySystemFrame." .. (key == "DetailPane" and "ChallengesPage.DetailPane" or
            key == "ScrollBox" and "ChallengesPage.DetailPane.ScrollBox" or key), depth)
    end
    if prime(root, "LegacySystemFrame", 0) and not Forbidden(root) then
        local cp = child(root, "ChallengesPage", 1)
        local dp = child(cp, "DetailPane", 2)
        local sb = child(dp, "ScrollBox", 3)
        child(root, "RewardTrackPage", 1)
        if sb then
            local provider = First(sb, "GetDataProvider")
            if provider == nil then provider = Read(sb, "dataProvider") end
            if (Kind(provider) == "table" or Kind(provider) == "userdata") and reserve(provider) then
                state.challengeProvider = provider
                state.providerCount = First(provider, "GetSize")
                local collection = First(provider, "GetCollection")
                if Kind(collection) ~= "table" then collection = Read(provider, "collection") end
                if Kind(collection) == "table" and reserve(collection) then
                    state.challengeCollection = collection
                    local cursor
                    for _ = 1, state.entries do
                        local ok, nextKey, value = pcall(next, collection, cursor)
                        if not ok or Secret(nextKey) or nextKey == nil then break end
                        cursor = nextKey
                        if Kind(value) == "table" and not reserve(value) then break end
                    end
                end
            end
        end
    end
    local walk
    walk = function(object, label, depth, expand)
        if Kind(object) ~= "table" and Kind(object) ~= "userdata" then return end
        if depth > state.depth then state.limits.depth = true; return end
        if not reserve(object) then return end
        local record = state.frames[object]
        if record then
            if not expand or record.expanded then return end
            record.expanded = true
            label = record.label
            local children = record.children
            if not children then return end
            if depth >= state.depth and children.n > 1 then state.limits.depth = true; return end
            for i = 2, math.min(children.n, 257) do
                if state.count >= state.objects or state.stopped then state.limits.objects = true; break end
                local descendant = children[i]
                if Kind(descendant) == "table" or Kind(descendant) == "userdata" then
                    walk(descendant, label .. ".child[" .. (i - 1) .. "]", depth + 1, true)
                end
            end
            if children.n > 257 then state.limits.fields = true end
            return
        end
        state.frames[object] = { label = label, depth = depth }
        if Forbidden(object) then line(label .. ": forbidden / inaccessible; skipped", true); return end
        local name = First(object, "GetName")
        if Kind(name) == "string" then
            label = name
            state.frames[object].label = name
        end
        local objectType = First(object, "GetObjectType")
        local parent = First(object, "GetParent")
        local parentName = parent and not Forbidden(parent) and First(parent, "GetName")
        line(Scalar(label) .. ": FOUND; type=" .. Scalar(objectType) .. "; name=" .. Scalar(name) .. "; parent=" .. Scalar(parentName), true)
        if Kind(name) == "string" then state.names[name] = object end
        local context = label:lower():find("reward") and "reward" or "challenge"
        dump(object, label, 0, context, true)
        local element = First(object, "GetElementData")
        if Kind(element) == "table" then dump(element, label .. ".GetElementData()", 0, context, true) end
        for _, script in ipairs(SCRIPT_NAMES) do
            local result = Call(object, "GetScript", script)
            if result and Kind(result[2]) == "function" then line("  Script " .. script .. ": function present (not invoked)", true) end
        end
        line("  Registered events: unavailable (no verified safe enumeration; no registration probes)", true)
        local regions = Call(object, "GetRegions")
        if regions then
            for i = 2, math.min(regions.n, state.fields + 1) do
                local region = regions[i]
                if (Kind(region) == "table" or Kind(region) == "userdata") and reserve(region) and not Forbidden(region) then
                    local regionName = First(region, "GetName")
                    if Kind(regionName) == "string" then
                        line("  Named region: " .. Scalar(regionName) .. "; type=" .. Scalar(First(region, "GetObjectType")), true)
                    end
                end
            end
            if regions.n - 1 > state.fields then state.limits.fields = true end
        else line("  Regions: unavailable", true) end
        local children = Call(object, "GetChildren")
        if not children then line("  Children: unavailable", true); return end
        line("  Immediate child count: " .. (children.n - 1), true)
        state.frames[object].children = children
        if expand then walk(object, label, depth, true) end
    end
    if Kind(root) == "table" or Kind(root) == "userdata" then
        for _, item in ipairs(priority) do walk(item.object, item.label, item.depth, false) end
        walk(root, "LegacySystemFrame", 0, true)
    else line("LegacySystemFrame: NOT FOUND. Open the native Legacy Challenges window before inspecting.") end

    local function target(parts)
        local current = root
        for _, part in ipairs(parts) do current = Read(current, part) end
        if current and state.frames[current] and not Forbidden(current) then return current end
        local full = "LegacySystemFrame." .. table.concat(parts, ".")
        local compact = "LegacySystemFrame" .. table.concat(parts, "")
        current = state.names[full] or state.names[compact]
        if current and not Forbidden(current) then return current end
        return nil
    end
    local page = target({ "ChallengesPage" })
    local detail = target({ "ChallengesPage", "DetailPane" })
    local box = target({ "ChallengesPage", "DetailPane", "ScrollBox" })
    local rewards = target({ "RewardTrackPage" })
    for _, item in ipairs({ { "ChallengesPage", page }, { "DetailPane", detail }, { "ScrollBox", box }, { "RewardTrackPage", rewards } }) do
        line(item[1] .. ": " .. (item[2] and "FOUND (descendant verified)" or "NOT FOUND / unavailable in bounded snapshot"))
    end

    line(""); line("NAMESPACES")
    line("C_Legacy: " .. (Kind(rawget(_G, "C_Legacy")) ~= "nil" and "FOUND" or "NOT FOUND"))
    line("C_AchievementInfo: " .. (Kind(rawget(_G, "C_AchievementInfo")) ~= "nil" and "FOUND" or "NOT FOUND"))
    for _, item in ipairs(globals) do
        local kind = Kind(item.value)
        local class = kind == "function" and "Function" or (kind == "table" and "Table" or "Other")
        if frameLike(item.value) then class = "Frame" end
        line(Scalar(item.name) .. ": " .. class, true)
        if class == "Table" then dump(item.value, item.name, 0, nil, false) end
    end
    for _, method in ipairs(state.methods) do
        local origin = state.origins[method.value]
        if origin then
            line("  Legacy method " .. Scalar(method.path) .. " shares function identity with " ..
                Scalar(origin) .. " (mixin attachment unverified)", true)
        end
    end

    line(""); line("CHALLENGE DATA")
    local provider, reason
    if box then
        provider = state.challengeProvider
        if provider == nil then provider, reason = First(box, "GetDataProvider") end
        if provider == nil then provider = Read(box, "dataProvider") end
    end
    line("Data provider: " .. Scalar(provider) .. (reason and " (" .. reason .. ")" or ""))
    local count, collection
    if (Kind(provider) == "table" or Kind(provider) == "userdata") and reserve(provider) then
        state.challengeProvider = provider
        dump(provider, "ScrollBox.dataProvider", 0, "challenge", true)
        count = state.providerCount
        collection = state.challengeCollection
        if count == nil then count = First(provider, "GetSize") end
        if collection == nil then collection = First(provider, "GetCollection") end
        if Kind(collection) ~= "table" then collection = Read(provider, "collection") end
        line("Readable APIs: GetSize=" .. Kind(Read(provider, "GetSize")) .. "; GetCollection=" .. Kind(Read(provider, "GetCollection")) ..
            "; Enumerate=" .. Kind(Read(provider, "Enumerate")) .. " (iterator not invoked)")
    end
    if Kind(count) ~= "number" or count < 0 or count ~= count then count = nil end
    line("Entry count: " .. Scalar(count) .. " (provider-reported; may describe only the selected category)")
    local sampled, fingerprint = 0, {}
    if Kind(collection) == "table" and reserve(collection) then
        local cursor
        while sampled < state.entries and not state.stopped do
            local ok, nextKey, value = pcall(next, collection, cursor)
            if not ok or Secret(nextKey) or nextKey == nil then break end
            cursor, sampled = nextKey, sampled + 1
            line("  Sample entry [" .. Scalar(cursor) .. "]: " .. Scalar(value), true)
            if Kind(value) == "table" and reserve(value) then
                dump(value, "provider.entry[" .. Scalar(cursor) .. "]", 0, "challenge", true)
                local id = Read(value, "challengeID")
                if id == nil then id = Read(value, "id") end
                if Kind(id) == "number" or Kind(id) == "string" then
                    fingerprint[#fingerprint + 1] = Scalar(id)
                end
            end
        end
        if sampled == state.entries then state.limits.entries = true end
    else line("Readable collection: unavailable; unknown provider functions were not invoked.") end
    table.sort(fingerprint)
    local signature = table.concat(fingerprint, ",")
    line("Sampled entries: " .. sampled)
    line("Readable IDs / names / descriptions / categories / progress / completion / points / scope: observed candidate fields below; semantics unverified.")
    for _, finding in ipairs(state.evidence.challenge) do line("  " .. finding) end
    if #state.evidence.challenge == 0 then line("  Unavailable in accessible populated fields.") end
    if previousSnapshot and box then
        local providerChange = "unavailable"
        if provider ~= nil and previousSnapshot.provider ~= nil then
            providerChange = rawequal(provider, previousSnapshot.provider) and "unchanged" or "changed"
        end
        local idChange = "unavailable (no readable IDs to compare)"
        if #fingerprint > 0 and (previousSnapshot.idCount or 0) > 0 then
            idChange = signature == previousSnapshot.signature and "unchanged" or "changed"
        end
        line("Manual snapshot comparison: provider " .. providerChange .. "; sampled IDs " .. idChange .. ".")
    else line("Manual snapshot comparison: no prior ScrollBox snapshot.") end
    line("Category selection: NOT VERIFIED. Change categories yourself and rerun; snapshot differences alone do not establish their cause.")
    if box then previousSnapshot = { provider = provider, signature = signature, idCount = #fingerprint } end

    line(""); line("REWARD TRACK")
    line("Current points / next milestone / thresholds / reward IDs / descriptions / claimed state: observed candidate fields; semantics unverified.")
    for _, finding in ipairs(state.evidence.reward) do line("  " .. finding) end
    if not rewards or #state.evidence.reward == 0 then line("Unavailable in accessible populated reward fields. Open the native reward track yourself, then rerun.") end

    line(""); line("LIMITATIONS")
    line("Inspected objects: " .. state.count .. " / " .. state.objects .. "; global keys scanned: " .. scanned)
    for _, budget in ipairs({ "objects", "depth", "fields", "entries", "globals", "output" }) do
        if state.limits[budget] then line("Partial output: " .. budget .. " budget reached.") end
    end
    line("Only direct Legacy descendants and bounded passive data samples are read. Unrelated UI frames are not traversed.")
    line("ScrollBox elements may be recycled; visible rows and provider samples need not cover all challenges.")
    line("Hidden/unloaded pages, forbidden objects, restricted values and unsupported getters may make data unavailable.")
    line("Registered events, original mixin attachment, field semantics and account/character scope may be unavailable.")
    line("No unknown functions/iterators, event callbacks, hooks, selectors, scrolling, native setters or reward claims are invoked.")
    line("The diagnostic never transmits data. Sharing requires you to copy the report manually.")

    line(""); line("RECOMMENDED INTEGRATION POINTS")
    if box and (Kind(provider) == "table" or Kind(provider) == "userdata") and Kind(collection) == "table" then
        line("CONFIRMED: a Legacy descendant ScrollBox exposes a provider and readable collection in this snapshot.")
        line("HYPOTHESIS: its records may support a read-only achievement adapter after IDs, scope and field meanings are verified.")
    else line("No readable challenge integration point confirmed. Open Challenges and inspect again.") end
    if rewards and #state.evidence.reward > 0 then
        line("CONFIRMED: populated reward-related fields are accessible; their meaning still needs validation.")
        line("HYPOTHESIS: a separate read-only reward adapter could preserve the existing native reward page.")
    end
    line("Namespace/method presence alone does not prove a safe API. Native Legacy integration is not implemented.")
    return table.concat(state.lines, "\n")
end

function Inspector.Inspect()
    local ok, report = pcall(Inspect)
    if ok then return report end
    local failure = "=== LEGACY ACHIEVEMENTS REFORGED INSPECTOR ===\n\nLIMITATIONS\nInspection stopped safely: " .. Scalar(report)
    return failure:sub(1, Limit("maxOutputChars", 60000, 256, 120000))
end

local window, edit, scroll
local function SetResults(text)
    edit:SetText(text)
    -- Account for wrapping as well as newlines. Use native text height when
    -- exposed, with a conservative width-based estimate on older clients.
    local columns = math.max(20, math.floor((edit:GetWidth() - 8) / 8))
    local lines = 0
    for row in (text .. "\n"):gmatch("(.-)\n") do
        lines = lines + math.max(1, math.ceil(#row / columns))
    end
    local height = math.max(350, lines * 14 + 20)
    local getter = edit.GetTextHeight
    if type(getter) == "function" then
        local ok, measured = pcall(getter, edit)
        if ok and Kind(measured) == "number" then height = math.max(height, measured + 20) end
    end
    edit:SetHeight(height)
    if type(scroll.UpdateScrollChildRect) == "function" then scroll:UpdateScrollChildRect() end
    scroll:SetVerticalScroll(0)
    edit:SetCursorPosition(0)
    edit:ClearFocus()
end

local function ShowWindow()
    if Combat() then
        local chat = rawget(_G, "DEFAULT_CHAT_FRAME")
        if chat and chat.AddMessage then chat:AddMessage("Legacy Inspector: leave combat before opening or running the diagnostic.") end
        return
    end
    if not window then
        window = CreateFrame("Frame", "LegacyAchievementsReforgedInspectorWindow", UIParent)
        window:SetSize(780, 560)
        window:SetPoint("CENTER")
        window:SetFrameStrata("DIALOG")
        window:SetClampedToScreen(true)
        window:EnableMouse(true)
        window:SetMovable(true)
        window:RegisterForDrag("LeftButton")
        window:SetScript("OnDragStart", window.StartMoving)
        window:SetScript("OnDragStop", window.StopMovingOrSizing)
        local background = window:CreateTexture(nil, "BACKGROUND")
        background:SetAllPoints()
        background:SetColorTexture(0.04, 0.04, 0.04, 0.98)
        local title = window:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
        title:SetPoint("TOPLEFT", 18, -16)
        title:SetText("Legacy Achievements Reforged Inspector")
        local help = window:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
        help:SetPoint("TOPLEFT", 18, -42)
        help:SetText("Open native Challenges first. Run Inspection. Click the report, then Ctrl+A and Ctrl+C to copy.")
        scroll = CreateFrame("ScrollFrame", nil, window, "UIPanelScrollFrameTemplate")
        scroll:SetPoint("TOPLEFT", 18, -70)
        scroll:SetPoint("BOTTOMRIGHT", -38, 56)
        edit = CreateFrame("EditBox", nil, scroll)
        edit:SetMultiLine(true)
        edit:SetAutoFocus(false)
        edit:SetFont("Fonts\\FRIZQT__.TTF", 11, "")
        edit:SetTextInsets(4, 4, 4, 4)
        edit:SetWidth(714)
        edit:SetHeight(350)
        edit:SetMaxLetters(120000)
        edit:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
        scroll:SetScrollChild(edit)
        local function button(label, x, action)
            local b = CreateFrame("Button", nil, window, "UIPanelButtonTemplate")
            b:SetSize(145, 26)
            b:SetPoint("BOTTOMLEFT", x, 16)
            b:SetText(label)
            b:SetScript("OnClick", action)
        end
        button("Run Inspection", 18, function() SetResults(Inspector.Inspect()) end)
        button("Clear Results", 175, function() SetResults("") end)
        button("Close", 600, function() edit:ClearFocus(); window:Hide() end)
        window:SetScript("OnHide", function() edit:ClearFocus() end)
        if type(UISpecialFrames) == "table" then table.insert(UISpecialFrames, "LegacyAchievementsReforgedInspectorWindow") end
        SetResults("Open the native Legacy Challenges window, then click Run Inspection.\nSwitch categories yourself and rerun to compare snapshots.\nOpen the native reward track and rerun to inspect its populated fields.\n\nReports stay in memory; click here and use Ctrl+A / Ctrl+C to share them manually.")
    end
    window:Show()
end

SLASH_LARLEGACYINSPECTOR1 = "/legacyinspect"
SlashCmdList.LARLEGACYINSPECTOR = ShowWindow
