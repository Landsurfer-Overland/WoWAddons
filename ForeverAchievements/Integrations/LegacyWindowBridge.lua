-- Reversible presentation only. Native pages retain their original parents,
-- descendants, scripts, page-selection contract, and progression controls.
local _, ns = ...
local R = ns.LegacyReadOnly
local B = {}
B.__index = B
ns.LegacyWindowBridge = B
function B.Blocked(frame)
    if not frame then return true end
    for _, method in ipairs({ "IsForbidden", "IsProtected" }) do
        local r = R.Method(frame, method)
        if not r or r[1] == true then return true end
    end
    return false
end
local function invoke(object, method, ...)
    local fn = R.Field(object, method)
    assert(type(fn) == "function", "Missing presentation method: " .. method)
    return fn(object, ...)
end
local function shown(object)
    local r = R.Method(object, "IsShown")
    assert(r and type(r[1]) == "boolean", "Unavailable presentation visibility")
    return r[1]
end
local function visibility(object, value) invoke(object, value and "Show" or "Hide") end
local function objects(root, method, maximum)
    local r = R.Method(root, method)
    assert(r and r.n <= maximum, "Unsupported native presentation collection")
    local list = {}
    for i = 1, r.n do
        local object = r[i]
        assert(object, "Unavailable native presentation object")
        list[#list + 1] = { object = object, shown = shown(object) }
    end
    return list
end
local function geometry(frame)
    assert(not B.Blocked(frame), "Native page is protected or forbidden")
    local n = R.Method(frame, "GetNumPoints")
    n = n and R.Number(n[1])
    assert(n and n >= 0 and n <= 8, "Unsupported native page anchors")
    local data = { frame = frame, points = {}, shown = shown(frame), decorations = {} }
    for i = 1, n do
        local point = R.Method(frame, "GetPoint", i)
        assert(point and point.n >= 1, "Unavailable native page anchor")
        data.points[i] = point
    end
    for _, field in ipairs({ "Width", "Height", "Scale", "FrameLevel" }) do
        local value = R.Method(frame, "Get" .. field)
        data[field] = value and R.Number(value[1])
        assert(data[field], "Unavailable native page " .. field)
    end
    local strata = R.Method(frame, "GetFrameStrata")
    data.FrameStrata = strata and R.Text(strata[1])
    assert(data.Width > 0 and data.Height > 0 and data.Scale > 0 and data.FrameStrata,
        "Unsupported native page dimensions")
    for _, key in ipairs({ "Background", "VerticalDivider" }) do
        local object = R.Field(frame, key)
        if object then data.decorations[#data.decorations + 1] = { object = object, shown = shown(object) } end
    end
    return data
end
function B.New(root)
    assert(not B.Blocked(root), "Native Legacy frame is protected or forbidden")
    local self = setmetatable({ root = root, pages = {} }, B)
    for _, key in ipairs({ "ChallengesPage", "RewardTrackPage", "TreePage" }) do
        local frame = R.Field(root, key)
        local parent = R.Method(frame, "GetParent")
        assert(parent and parent[1] == root and not B.Blocked(frame), "Incompatible native page: " .. key)
        self[key] = frame
    end
    -- Snapshot everything before the first mutation, including both native pages.
    self.regions = objects(root, "GetRegions", 64)
    self.children = objects(root, "GetChildren", 64)
    self.pages[1], self.pages[3] = geometry(self.RewardTrackPage), geometry(self.TreePage)
    local mouse = R.Method(root, "IsMouseEnabled")
    assert(mouse and type(mouse[1]) == "boolean", "Unavailable native mouse state")
    self.mouse = mouse[1]
    assert(type(R.Field(EventRegistry, "TriggerEvent")) == "function", "Native page selection unavailable")
    return self
end
function B:Check()
    assert(not B.Blocked(self.root), "Native Legacy frame became protected or forbidden")
    for _, item in ipairs(self.children) do
        assert(not B.Blocked(item.object), "Native child became protected or forbidden")
    end
    for _, data in pairs(self.pages) do
        assert(not B.Blocked(data.frame), "Native page became protected or forbidden")
        for _, item in ipairs(data.decorations) do
            if R.Field(item.object, "IsProtected") then
                assert(not B.Blocked(item.object), "Native decoration became protected or forbidden")
            end
        end
    end
end
function B:Select(id)
    if R.Field(self.root, "currentPage") ~= id then
        invoke(EventRegistry, "TriggerEvent", "Legacy.SelectPage", id)
    end
    assert(R.Field(self.root, "currentPage") == id, "Native page selection did not complete")
end
function B:Suppress(mounted)
    self:Check()
    self.active = true -- failures after this point must attempt restoration
    invoke(self.root, "EnableMouse", false)
    for _, item in ipairs(self.regions) do visibility(item.object, false) end
    for _, item in ipairs(self.children) do
        if item.object ~= mounted then visibility(item.object, false) end
    end
end
function B:Mount(view, host)
    local id = view == "rewards" and 1 or view == "trees" and 3 or 2
    local data = self.pages[id]
    self:Check()
    self.active = true
    self:Select(id)
    self:Suppress(data and data.frame)
    if not data then return end
    local targetScale = R.Method(host, "GetEffectiveScale")
    local rootScale = R.Method(self.root, "GetEffectiveScale")
    targetScale, rootScale = targetScale and R.Number(targetScale[1]), rootScale and R.Number(rootScale[1])
    assert(targetScale and rootScale and rootScale > 0, "Unavailable native page effective scale")
    local scale = math.min(1, host:GetWidth() / data.Width, host:GetHeight() / data.Height) * targetScale / rootScale
    assert(scale > 0, "Native page content area is unavailable")
    local page = data.frame
    invoke(page, "ClearAllPoints")
    invoke(page, "SetSize", data.Width, data.Height)
    invoke(page, "SetScale", scale)
    invoke(page, "SetPoint", "CENTER", host, "CENTER", 0, 0)
    invoke(page, "SetFrameStrata", host:GetFrameStrata())
    invoke(page, "SetFrameLevel", host:GetFrameLevel() + 10)
    for _, item in ipairs(data.decorations) do visibility(item.object, false) end
    visibility(page, true)
end
function B:Restore()
    if not self.active then return true end
    -- Preflight before replaying state. A rejected restore keeps the working
    -- replacement visible until restoration is legal, avoiding a blank UI.
    local ok, err = pcall(function() self:Check() end)
    if not ok then return false, err end
    local errors = {}
    local function attempt(fn)
        local success, reason = pcall(fn)
        if not success then errors[#errors + 1] = tostring(reason) end
    end
    for _, data in pairs(self.pages) do
        attempt(function()
            local page = data.frame
            invoke(page, "ClearAllPoints")
            invoke(page, "SetSize", data.Width, data.Height)
            invoke(page, "SetScale", data.Scale)
            invoke(page, "SetFrameStrata", data.FrameStrata)
            invoke(page, "SetFrameLevel", data.FrameLevel)
            for _, point in ipairs(data.points) do invoke(page, "SetPoint", unpack(point, 1, point.n)) end
        end)
        for _, item in ipairs(data.decorations) do attempt(function() visibility(item.object, item.shown) end) end
    end
    for _, item in ipairs(self.regions) do attempt(function() visibility(item.object, item.shown) end) end
    local id = R.Number(R.Field(self.root, "currentPage"))
    for _, item in ipairs(self.children) do
        local value = item.shown
        -- Native selection made during this session remains authoritative.
        if id == 1 or id == 2 or id == 3 then
            if item.object == self.RewardTrackPage then value = id == 1
            elseif item.object == self.ChallengesPage then value = id == 2
            elseif item.object == self.TreePage then value = id == 3 end
        end
        attempt(function() visibility(item.object, value) end)
    end
    attempt(function() invoke(self.root, "EnableMouse", self.mouse) end)
    if #errors > 0 then return false, table.concat(errors, "; ") end
    self.active = false
    return true
end
