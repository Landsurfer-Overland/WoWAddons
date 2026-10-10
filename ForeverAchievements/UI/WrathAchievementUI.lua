-- Presentation port of Blizzard_AchievementUI.lua / Shared.lua. The supplied
-- XML supplies the actual Wrath artwork/layout. Backend, global selection,
-- comparison, tracking setters and HybridScrollFrame code are not loaded.
local _, ns = ...
local U = {}
U.PRESETS = { Compact = { 768, 500 }, Standard = { 900, 620 }, Large = { 1024, 720 } }
ns.WrathAchievementUI = U
ForeverAchievementsWrathUI = U -- only our XML callbacks, never Blizzard globals
local P = ns.LegacyPresentation
local function perfBegin(name) local p = ns.LegacyPerf; return p and p.Begin and p.Begin(name) end
local function perfFinish(token) local p = ns.LegacyPerf; if p and p.Finish then p.Finish(token) end end
local function perfCount(name, count) local p = ns.LegacyPerf; if p and p.Count then p.Count(name, count) end end
local function region(self, suffix) return _G[self:GetName() .. suffix] end
local function show(object, yes)
    yes = not not yes
    if object:IsShown() ~= yes then if yes then object:Show() else object:Hide() end end
end
local function action(self, fn)
    local owner = self.owner
    if owner then owner.guard(function() fn(owner) end) end
end
local function font(parent, style, text)
    local f = parent:CreateFontString(nil, "OVERLAY", style or "GameFontNormal")
    f:SetText(text or ""); return f
end
local function bind(self, names)
    for _, suffix in ipairs(names) do self[suffix:sub(1, 1):lower() .. suffix:sub(2)] = region(self, suffix) end
end
function U.IconOnLoad(self)
    self.bling, self.texture, self.frame = region(self, "Bling"), region(self, "Texture"), region(self, "Overlay")
end
function U.ShieldOnLoad(self)
    self.icon, self.points = region(self, "Icon"), region(self, "Points")
    self:EnableMouse(true)
    self:SetScript("OnEnter", U.ShieldEnter)
    self:SetScript("OnLeave", function() if GameTooltip then GameTooltip:Hide() end end)
end
function U.CategoryOnLoad(self) bind(self, { "Label", "Background" }) end
function U.CriterionOnLoad(self)
    self.label, self.check = region(self, "Name"), region(self, "Check")
end
function U.MetaOnLoad(self) bind(self, { "Icon", "Label", "Check", "Border" }) end
function U.ProgressOnLoad(self)
    self.text = region(self, "Text")
    self:SetStatusBarColor(0, .6, 0, 1)
    self:GetStatusBarTexture():SetDrawLayer("BORDER")
end
function U.SummaryBarOnLoad(self)
    bind(self, { "Label", "Text", "Button", "FillBar" })
    self:SetStatusBarColor(0, .6, 0, 1)
end
function U.StatOnLoad(self) bind(self, { "BG", "Title", "Value", "HeaderLeft", "HeaderRight", "HeaderMiddle" }) end
function U.TabOnLoad(self)
    self.text = region(self, "Text")
    for _, suffix in ipairs({ "Left", "Middle", "Right" }) do region(self, suffix):SetVertexColor(.6, .6, .6) end
    region(self, "LeftDisabled"):SetPoint("TOPLEFT", 0, 2)
end
function U.CardOnLoad(self)
    bind(self, { "Label", "Description", "HiddenDescription", "Reward", "RewardBackground", "Icon", "Shield",
        "Objectives", "Highlight", "DateCompleted", "Tracked", "Check", "PlusMinus", "Background", "Glow", "TitleBackground" })
    self:SetBackdrop({ edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 16, insets = { left = 4, right = 4, top = 4, bottom = 4 } })
    self.dateCompleted:ClearAllPoints()
    self.dateCompleted:SetPoint("TOP", self.shield, "BOTTOM", -3, 6)
    self.dateCompleted:SetWidth(78)
    self.description:SetWidth(330); self.hiddenDescription:SetWidth(330)
    self.description:SetHeight(36)
    self.objectives:ClearAllPoints()
    self.objectives:SetPoint("TOPLEFT", self, "TOPLEFT", 78, -72)
    self.objectives:SetSize(340, 1)
    self.criteriaPool, self.progressPool, self.metaPool = {}, {}, {}
    self.scopeText = font(self.objectives, "GameFontNormalSmall")
    self.scopeText:SetPoint("TOPLEFT", 0, 0); self.scopeText:SetHeight(18); self.scopeText:Hide()
    self.completionText = font(self.objectives, "GameFontNormalSmall")
    self.completionText:SetPoint("TOPLEFT", 0, -22); self.completionText:SetHeight(18); self.completionText:Hide()
end
-- Original AchievementButton_Saturate / Desaturate colors and texture slices.
local function saturate(card, completed)
    local icon = card.icon
    card.titleBackground:SetTexCoord(0, .9765625, completed and 0 or .34375, completed and .3125 or .65625)
    card.background:SetTexture("Interface\\AchievementFrame\\UI-Achievement-Parchment-Horizontal" .. (completed and "" or "-Desaturated"))
    if completed then
        card.glow:SetVertexColor(1, 1, 1); icon.bling:SetVertexColor(1, 1, 1)
        icon.frame:SetVertexColor(1, 1, 1); icon.texture:SetVertexColor(1, 1, 1)
        card.shield.icon:SetTexCoord(0, .5, 0, .5); card.shield.points:SetTextColor(1, 1, 1)
        card.reward:SetTextColor(1, .82, 0); card.label:SetTextColor(1, 1, 1)
        card.description:SetTextColor(0, 0, 0); card.description:SetShadowOffset(0, 0)
        card:SetBackdropBorderColor(.7, .15, .05)
    else
        card.glow:SetVertexColor(.22, .17, .13); icon.bling:SetVertexColor(.6, .6, .6)
        icon.frame:SetVertexColor(.75, .75, .75); icon.texture:SetVertexColor(.55, .55, .55)
        card.shield.icon:SetTexCoord(.5, 1, 0, .5); card.shield.points:SetTextColor(.65, .65, .65)
        card.reward:SetTextColor(.8, .8, .8); card.label:SetTextColor(.65, .65, .65)
        card.description:SetTextColor(1, 1, 1); card.description:SetShadowOffset(1, -1)
        card:SetBackdropBorderColor(.5, .5, .5)
    end
    card.saturated = completed
end
local function pool(owner, key, index, kind, parent, template)
    local entries = owner[key]
    if not entries[index] then
        entries[index] = CreateFrame(kind, parent:GetName() .. key .. index, parent, template)
        perfCount("UI.PooledFramesCreated")
    end
    local f = entries[index]; f:ClearAllPoints(); return f
end
local function hidePool(entries) for _, f in ipairs(entries) do f:Hide() end end
local function clampScroll(scrollFrame, child, requested)
    local value = math.max(0, math.min(requested or scrollFrame:GetVerticalScroll(), math.max(0, child:GetHeight() - scrollFrame:GetHeight())))
    local changed = value ~= scrollFrame:GetVerticalScroll()
    if changed then scrollFrame:SetVerticalScroll(value) end
    return changed
end
local function resetScroll(self)
    self.suppressScroll = true; self.contentScroll:SetVerticalScroll(0); self.suppressScroll = false
end
local function colors(label, completed, parentDone)
    if parentDone then label:SetTextColor(0, 0, 0)
    elseif completed then label:SetTextColor(0, 1, 0) else label:SetTextColor(.65, .65, .65) end
end
function U.CardClick(self)
    action(self, function(owner)
        -- Lua's "condition and nil or key" always returns key. Clear the
        -- expanded entry explicitly; linked navigation is a separate state.
        local key = self.record.key
        if owner.selected == key then owner.selected = nil else owner.selected = key end
        if owner.focus and owner.focus.key ~= key then owner.focus = nil end
        owner:Render()
    end)
end
function U.CardEnter(self) if self.record then self.highlight:Show() end end
function U.CardLeave(self) if not self.selected then self.highlight:Hide() end end
local function completionDetail(row)
    -- Adapters verify character identity and completion provenance. This view
    -- displays their result without deriving an earner from source or scope.
    if type(row.completionDetail) == "string" and row.completionDetail ~= "" then return row.completionDetail end
    if row.completed == nil then return "Completion unavailable" end
end
function U.ShieldEnter(self)
    local row, tooltip = self:GetParent().record, GameTooltip
    if not row or not tooltip then return end
    tooltip:SetOwner(self, "ANCHOR_RIGHT")
    local titles = { legacy = "Legacy Points", character = "Character Achievement Points", none = "No point reward", unknown = "Point system unavailable" }
    tooltip:SetText(titles[row.pointType] or (row.source == "legacy" and "Legacy Points" or "Character Achievement Points"))
    local points = row.pointValue
    if points == nil and row.pointType == nil then points = row.points end
    tooltip:AddLine(points == nil and "Point value unavailable" or tostring(points), 1, 1, 1)
    tooltip:AddLine((row.sourceType == "native_legacy" or row.source == "legacy") and "Source: Native Legacy Challenge" or "Source: Character Achievement", .7, .7, .7)
    local scopes = { character = "Character", account = "Account", unknown = "Unknown" }
    tooltip:AddLine("Scope: " .. (scopes[row.scopeType] or row.scope or "Unknown"), 1, .82, 0)
    if row.achievementType == "feat_of_strength" then tooltip:AddLine("Feat of Strength", 1, .82, 0)
    elseif row.achievementType == "unknown" then tooltip:AddLine("Achievement classification unavailable", .7, .7, .7) end
    local detail = completionDetail(row)
    if detail then tooltip:AddLine(detail, .7, .7, .7, true) end
    tooltip:Show()
end
function U.CategoryClick(self)
    action(self, function(owner)
        local cat = self.category
        if self.navigation == "statistics" then owner.statisticsCategory = cat.key
        else owner.category, owner.focus, owner.selected = cat.key, nil, nil end
        resetScroll(owner); owner:Render()
    end)
end
function U.CategoryExpand(self)
    action(self, function(owner)
        local row = self:GetParent()
        local expanded = row.navigation == "statistics" and owner.statisticsExpanded or owner.expanded
        expanded[row.category.key] = not expanded[row.category.key]
        owner.navigationVersion = (owner.navigationVersion or 0) + 1
        owner:Render()
    end)
end
function U.TrackClick(self)
    action(self, function(owner)
        ns.CustomAchievementAdapter.Track(self:GetParent().record)
        owner.onRefresh()
    end)
end
function U.MetaClick(self)
    action(self, function(owner)
        local row = P.Resolve(owner.model, self.link)
        if row then
            owner.focus, owner.selected, owner.tab = row, row.key, "achievements"
            resetScroll(owner); owner:Render()
        end
    end)
end
function U.SummaryClick(self)
    action(self, function(owner)
        owner.category, owner.focus, owner.selected = self.categoryKey, nil, nil
        owner.expanded[self.categoryKey] = true
        resetScroll(owner); owner:Render()
    end)
end
function U.TabClick(self)
    action(self, function(owner)
        owner:SetTab(self.view, true)
    end)
end
function U.CloseClick(self)
    action(self, function(owner) if owner.callbacks.onClose then owner.callbacks.onClose() end end)
end
local function scroll(parent, name, width, height, x, y)
    local s = CreateFrame("ScrollFrame", name, parent, "UIPanelScrollFrameTemplate")
    s:SetSize(width, height); s:SetPoint("TOPLEFT", x, y)
    local child = CreateFrame("Frame", name .. "Child", s)
    child:SetSize(width, height); s:SetScrollChild(child)
    return s, child
end
function U.Create(cover, guard, refresh, callbacks)
    local self = { guard = guard, onRefresh = refresh, category = "summary", tab = "achievements", filter = "All", search = "",
        expanded = {}, statisticsExpanded = {}, statisticsCategory = "stats:summary", scrollOffsets = {}, sidebarOffsets = {},
        categories = {}, cards = {}, bars = {}, stats = {}, headings = {}, callbacks = callbacks or {} }
    self.root = CreateFrame("Frame", "FAWrathAchievementFrame", cover, "FAWrathWindowTemplate")
    self.root:SetSize(900, 620)
    self.root:SetPoint("TOP", cover, "TOP", 0, -72)
    self.contentBackground = self.root:CreateTexture(nil, "BACKGROUND")
    self.contentBackground:SetPoint("TOPLEFT", 219, -23); self.contentBackground:SetPoint("BOTTOMRIGHT", -25, 23)
    self.contentBackground:SetTexture("Interface\\AchievementFrame\\UI-Achievement-AchievementBackground")
    self.contentBackground:SetTexCoord(0, 1, 0, .5)
    self.nativeHost = CreateFrame("Frame", "FAWrathNativePageHost", self.root)
    self.nativeHost:SetSize(718, 454)
    self.nativeHost:SetPoint("TOPLEFT", 25, -23); self.nativeHost:SetPoint("BOTTOMRIGHT", -25, 23)
    if type(self.nativeHost.SetClipsChildren) == "function" then self.nativeHost:SetClipsChildren(true) end
    self.nativeHost:EnableMouse(true); self.nativeHost:Hide()
    self.nativeBackground = self.nativeHost:CreateTexture(nil, "BACKGROUND")
    self.nativeBackground:SetAllPoints(self.nativeHost)
    self.nativeBackground:SetTexture("Interface\\AchievementFrame\\UI-Achievement-AchievementBackground")
    self.nativeBackground:SetTexCoord(0, 1, 0, .5)
    local header, close = region(self.root, "Header"), region(self.root, "CloseButton")
    -- Native content sits above the parchment. Keep the original close button
    -- above that subtree at the small corner where their hit rectangles meet.
    close:SetFrameLevel(self.nativeHost:GetFrameLevel() + 50)
    header:RegisterForDrag("LeftButton")
    header:SetScript("OnDragStart", function() guard(function()
        cover:StartMoving(); if self.callbacks.onDragStart then self.callbacks.onDragStart() end
    end) end)
    header:SetScript("OnDragStop", function() guard(function()
        cover:StopMovingOrSizing(); if self.callbacks.onPositionSave then self.callbacks.onPositionSave(cover) end
    end) end)
    close.owner = self
    self.categoryScroll, self.categoryChild = scroll(self.root, "FAWrathCategoryScroll", 169, 442, 28, -27)
    self.contentScroll, self.contentChild = scroll(self.root, "FAWrathContentScroll", 496, 402, 234, -69)
    self.measureFont = font(self.contentChild, "FAWrathAchievementDescriptionFont"); self.measureFont:Hide()
    self.contentScroll:HookScript("OnVerticalScroll", function()
        if self.rendering or self.scrollRendering or self.suppressScroll or not self.model then return end
        self.scrollRendering = true
        guard(function() self:Render("scroll") end)
        self.scrollRendering = false
    end)
    self.notice = font(self.root, "GameFontNormalSmall")
    self.notice:SetPoint("TOPLEFT", 238, -47); self.notice:SetWidth(491); self.notice:SetHeight(24)
    self.notice:SetJustifyH("LEFT")
    self.searchBox = CreateFrame("EditBox", "FAWrathSearch", self.root, "InputBoxTemplate")
    self.searchBox:SetSize(250, 24)
    self.searchBox:SetAutoFocus(false); self.searchBox:SetMaxLetters(100)
    self.searchBox:SetScript("OnEscapePressed", function(box) box:ClearFocus() end)
    self.searchBox:SetScript("OnTextChanged", function(box, userInput)
        if self.suppressSearchChange then return end
        guard(function()
            self.search = box:GetText() or ""; self.focus = nil
            show(self.searchHint, self.search == ""); show(self.searchClear, self.search ~= "" or self.filter ~= "All")
            perfCount("UI.SearchRequests")
            resetScroll(self)
            if userInput and C_Timer and C_Timer.After then
                if self.searchQueued then return end
                self.searchQueued = true
                self.searchQueueVersion = (self.searchQueueVersion or 0) + 1
                local version = self.searchQueueVersion
                C_Timer.After(.12, function() guard(function()
                    if not self.searchQueued or self.searchQueueVersion ~= version then return end
                    self.searchQueued = false; self:Render("search")
                end) end)
            else self.searchQueued = false; self:Render("search") end
        end)
    end)
    self.searchBox:SetScript("OnEnterPressed", function(box) box:ClearFocus() end)
    self.searchHint = font(self.searchBox, "GameFontDisableSmall", "Search achievements...")
    self.searchHint:SetPoint("LEFT", 2, 0); self.searchHint:SetJustifyH("LEFT")
    self.searchIcon = self.searchBox:CreateTexture(nil, "OVERLAY")
    self.searchIcon:SetTexture("Interface\\Common\\UI-Searchbox-Icon")
    self.searchIcon:SetSize(16, 16); self.searchIcon:SetPoint("RIGHT", self.searchBox, "LEFT", -5, 0)
    self.searchBox:SetScript("OnEnter", function(box)
        if not GameTooltip then return end
        GameTooltip:SetOwner(box, "ANCHOR_TOP")
        GameTooltip:SetText("Search achievements")
        GameTooltip:AddLine("Titles, descriptions, categories, and loaded criteria.", 1, 1, 1, true)
        GameTooltip:Show()
    end)
    self.searchBox:SetScript("OnLeave", function() if GameTooltip then GameTooltip:Hide() end end)
    self.searchClear = CreateFrame("Button", "FAWrathSearchClear", self.root)
    self.searchClear:SetSize(20, 20)
    self.searchClear.label = font(self.searchClear, "GameFontNormal", "×")
    self.searchClear.label:SetPoint("CENTER")
    self.searchClear:SetScript("OnClick", function() guard(function()
        self.search, self.filter, self.focus = "", "All", nil
        self.searchQueued, self.suppressSearchChange = false, true
        self.searchBox:SetText(""); self.suppressSearchChange = false; self.filterButton.label:SetText("All")
        self.searchBox:ClearFocus(); resetScroll(self); self:Render()
    end) end)
    self.filterButton = CreateFrame("Button", "FAWrathFilter", self.root, "FAWrathCategoryTemplate")
    self.filterButton:SetSize(155, 24); self.filterButton:SetPoint("TOPRIGHT", -28, -25)
    self.filterButton.label:SetWidth(145); self.filterButton.label:SetFontObject(GameFontNormalSmall)
    self.filterButton.label:SetText("All")
    self.filterButton:SetScript("OnClick", function()
        guard(function()
            local filters = { "All", "Completed", "Incomplete", "Character Achievements", "Legacy Challenges" }
            local current = 1
            for i, value in ipairs(filters) do if value == self.filter then current = i; break end end
            self.filter = filters[current % #filters + 1]
            self.filterButton.label:SetText(self.filter); self.focus = nil
            resetScroll(self); self:Render()
        end)
    end)
    self.tabs = {}
    local tabDefinitions = {
        { "achievements", "Achievements", 142 }, { "rewards", "Legacy Rewards", 151 },
        { "trees", "Legacy Trees", 135 }, { "statistics", "Statistics", 123 },
    }
    local x = 11
    for i, definition in ipairs(tabDefinitions) do
        local view, label, width = unpack(definition)
        local tab = CreateFrame("Button", "FAWrathTab" .. i, self.root, "FAWrathTabTemplate")
        tab:SetPoint("TOPLEFT", self.root, "BOTTOMLEFT", x, 0)
        tab:SetSize(width, 32); tab:SetText(label)
        for _, suffix in ipairs({ "Middle", "MiddleDisabled" }) do region(tab, suffix):SetWidth(width - 39) end
        tab.owner, tab.view = self, view; self.tabs[i] = tab
        x = x + width - 5
    end
    self.nativePoints = region(self.root, "HeaderLegacyPoints")
    region(self.root, "HeaderLegacyShield"):SetVertexColor(.63, .79, 1)
    self.sizeButton = CreateFrame("Button", "FAWrathSizePreset", self.root, "FAWrathCategoryTemplate")
    self.sizeButton:SetSize(110, 24); self.sizeButton:SetPoint("TOPRIGHT", self.root, "BOTTOMRIGHT", -25, -15)
    self.sizeButton.label:SetText("Standard")
    self.sizeButton:SetScript("OnClick", function() guard(function()
        if self.callbacks.onSizePresetCycle then self.callbacks.onSizePresetCycle() end
    end) end)
    -- Explicit method table keeps our controller out of Blizzard globals.
    for _, name in ipairs({ "Fit", "Layout", "SetTab", "SetModel", "Render", "QueueRender", "CancelPending", "RenderCategories", "RenderCard", "MeasureCard", "RenderList", "RenderStatistics", "Heading", "SummaryBar" }) do self[name] = U[name] end
    self:Layout(900, 620)
    return self
end
function U.Fit(self, page, suppressRender)
    local width, height = page:GetWidth(), page:GetHeight()
    assert(width > 0 and height > 0, "Legacy presentation host has no layout yet")
    self.root:SetScale(1)
    self:Layout(width, height - 140, suppressRender)
    self.root:ClearAllPoints()
    -- Offsets use the scaled child's coordinate space.
    self.root:SetPoint("TOP", page, "TOP", 0, -72)
end
function U.Layout(self, width, height, suppressRender)
    assert(width >= 768 and height >= 500, "Wrath window requires at least Compact logical dimensions")
    if self.width == width and self.height == height then return end
    local token = perfBegin("UI.Resize")
    self.sidebarSignature, self.listPlan, self.measureCache, self.renderState = nil, nil, nil, nil
    self.width, self.height = width, height
    self.root:SetSize(width, height)
    self.sidebarWidth = width >= 900 and 220 or 195
    self.contentLeft = self.sidebarWidth + 39
    self.contentWidth = width - self.contentLeft - 38
    self.contentHeight = height - 98
    self.categoryHeight = height - 58
    self.nativeHost:SetSize(width - 50, height - 46)
    self.categoryScroll:SetSize(self.sidebarWidth - 26, self.categoryHeight)
    self.categoryChild:SetWidth(self.sidebarWidth - 26)
    region(self.root, "CategoriesBG"):SetWidth(self.sidebarWidth)
    local watermark = region(self.root, "WaterMark")
    watermark:SetWidth(self.sidebarWidth); watermark:SetTexCoord(0, self.sidebarWidth / 256, 0, 1)
    for _, suffix in ipairs({ "MetalBorderLeft", "MetalBorderRight" }) do region(self.root, suffix):SetHeight(height - 64) end
    for _, suffix in ipairs({ "MetalBorderTop", "MetalBorderBottom" }) do region(self.root, suffix):SetWidth(width - 56) end
    local header = region(self.root, "Header")
    header:ClearAllPoints(); header:SetPoint("BOTTOM", self.root, "TOP", 0, -39)
    -- The ornate roof and corner ornaments retain their original pixel size.
    -- Only plain border strips and the parchment centers grow with the panes.
    self.searchBox:ClearAllPoints(); self.searchBox:SetPoint("TOPRIGHT", self.root, "TOPRIGHT", -217, -25)
    self.searchBox:SetWidth(math.min(290, self.contentWidth - 200))
    self.searchHint:SetWidth(self.searchBox:GetWidth() - 8)
    self.searchClear:ClearAllPoints(); self.searchClear:SetPoint("LEFT", self.searchBox, "RIGHT", 4, 0)
    self.filterButton:SetSize(155, 24)
    self.notice:ClearAllPoints(); self.notice:SetPoint("TOPLEFT", self.contentLeft + 4, -47)
    self.notice:SetWidth(self.contentWidth - 8)
    self.layoutName = "Standard"
    for name, preset in pairs(U.PRESETS) do if preset[1] == width and preset[2] == height then self.layoutName = name; break end end
    self.sizeButton.label:SetText(self.layoutName)
    if self.model and not suppressRender then self:Render() end
    perfFinish(token)
end
function U.SetTab(self, view, notify)
    if view ~= "achievements" and view ~= "rewards" and view ~= "trees" and view ~= "statistics" then return end
    local token = perfBegin("UI.TabSwitch")
    local changed = self.tab ~= view
    if changed then
        self.scrollOffsets[self.tab] = self.contentScroll:GetVerticalScroll()
        self.sidebarOffsets[self.tab] = self.categoryScroll:GetVerticalScroll()
        self.tab = view
    end
    local handled = notify and self.callbacks.onTab and self.callbacks.onTab(view) == true
    if not handled then self:Render() end
    if changed then
        clampScroll(self.contentScroll, self.contentChild, self.scrollOffsets[view] or 0)
        clampScroll(self.categoryScroll, self.categoryChild, self.sidebarOffsets[view] or 0)
    end
    perfFinish(token)
end
function U.SetModel(self, model)
    self.model = model
    self.modelGeneration = (self.modelGeneration or 0) + 1
    self.sidebarSignature, self.listPlan, self.measureCache, self.renderState, self.statisticsPlan = nil, nil, nil, nil, nil
    if P.CategoryKey then self.category = P.CategoryKey(model, self.category) or "summary" end
    if not model.byCategory[self.category] then self.category = "summary" end
    if self.focus then self.focus = P.Resolve(model, self.focus.key) end
    region(self.root, "HeaderPoints"):SetText(model.custom.points ~= nil and tostring(model.custom.points) or "Unavailable")
    self.nativePoints:SetText(model.native.points ~= nil and tostring(model.native.points) or "Unavailable")
    self.statisticsCatalog = nil
    self:Render()
end
function U.RenderCategories(self)
    local statistics = self.tab == "statistics"
    local catalog = statistics and self.statisticsCatalog or self.model
    local expanded = statistics and self.statisticsExpanded or self.expanded
    local selected = statistics and self.statisticsCategory or self.category
    local keys = {}
    for key, value in pairs(expanded) do if value then keys[#keys + 1] = key end end
    table.sort(keys)
    local signature = table.concat({ self.tab, selected, tostring(self.modelGeneration), tostring(self.width), tostring(self.height), table.concat(keys, ",") }, "|")
    if self.sidebarSignature == signature then return end
    self.sidebarSignature = signature
    local token = perfBegin("UI.CategoryRender")
    hidePool(self.categories)
    local count, y = 0, 0
    local function visit(cat, depth)
        count = count + 1
        local b = pool(self, "categories", count, "Button", self.categoryChild, "FAWrathCategoryTemplate")
        if not b.selection then
            b.selection = b:CreateTexture(nil, "ARTWORK")
            b.selection:SetTexture("Interface\\AchievementFrame\\UI-Achievement-Category-Highlight")
            b.selection:SetTexCoord(0, .6640625, 0, 1); b.selection:SetDrawLayer("BACKGROUND", 1)
            b.selection:SetAllPoints(b)
            b.connector = b:CreateTexture(nil, "ARTWORK")
            b.connector:SetColorTexture(.55, .4, .2, .55)
            b.connector:SetSize(7, 1); b.connector:SetPoint("LEFT", -10, 0)
            b.expandButton = CreateFrame("Button", b:GetName() .. "Expand", b)
            b.expandButton:SetSize(16, 20); b.expandButton:SetPoint("LEFT", 3, 0)
            b.expandButton.label = font(b.expandButton, "GameFontNormalSmall")
            b.expandButton.label:SetPoint("CENTER")
            b.expandButton:SetScript("OnClick", U.CategoryExpand)
        end
        local indent = math.min(depth, 3) * 14
        local height = depth == 0 and 26 or 23
        b:SetSize(self.categoryScroll:GetWidth() - indent - 5, height)
        b:SetPoint("TOPLEFT", indent, -y)
        b.owner, b.category, b.depth = self, cat, depth
        b.navigation = statistics and "statistics" or "achievements"
        b.expandButton.owner = self
        b.label:ClearAllPoints(); b.label:SetPoint("LEFT", 21, 0)
        b.label:SetWidth(b:GetWidth() - 25); b.label:SetWordWrap(false)
        b.label:SetFontObject(depth == 0 and GameFontNormal or GameFontNormalSmall)
        b.label:SetText(cat.name)
        b.label:SetTextColor(depth == 0 and 1 or .88, depth == 0 and .82 or .72, depth == 0 and 0 or .35)
        b.background:SetAllPoints(b); b.background:SetVertexColor(depth == 0 and .65 or .4, depth == 0 and .55 or .36, .3, .9)
        show(b.selection, selected == cat.key); show(b.connector, depth > 0)
        local hasChildren = #(cat.children or {}) > 0
        show(b.expandButton, hasChildren)
        b.expandButton.label:SetText(expanded[cat.key] and "−" or "+")
        b:Show()
        y = y + height + (depth == 0 and 3 or 1)
        if expanded[cat.key] then for _, child in ipairs(cat.children) do visit(child, depth + 1) end end
    end
    for _, cat in ipairs(catalog and catalog.roots or {}) do visit(cat, 0) end
    self.categoryChild:SetHeight(math.max(self.categoryHeight, y))
    clampScroll(self.categoryScroll, self.categoryChild)
    perfFinish(token)
end
function U.Heading(self, text, y)
    self.headingIndex = self.headingIndex + 1
    local h = self.headings[self.headingIndex]
    if not h then h = font(self.contentChild, "GameFontNormalLarge"); self.headings[self.headingIndex] = h end
    h:ClearAllPoints(); h:SetPoint("TOP", self.contentChild, "TOP", 0, -y); h:SetText(text); h:Show()
    return y + 30
end
function U.SummaryBar(self, key, label, y, column, summary)
    self.barIndex = self.barIndex + 1
    local b = pool(self, "bars", self.barIndex, "StatusBar", self.contentChild, "FAWrathSummaryBarTemplate")
    local width = column and (self.contentWidth - 48) / 2 or self.contentWidth - 30
    b:SetSize(width, 21); b:SetPoint("TOPLEFT", 15 + (column or 0) * (width + 18), -y)
    local done, total, unknown
    if summary then done, total, unknown = summary.completed, summary.total, summary.unknown or 0
    else done, total, unknown = P.Count(self.model, key) end
    b.label:SetWidth(math.max(80, width - 145)); b.label:SetWordWrap(false)
    b.text:SetWidth(142)
    local count = done .. "/" .. total
    if summary and summary.available == false then count = "Unavailable"
    elseif summary and summary.partial then count = count .. " shown" end
    if unknown > 0 then count = count .. " (" .. unknown .. " unknown)" end
    b.label:SetText(label); b.text:SetText(count)
    b:SetMinMaxValues(0, math.max(total, 1)); b:SetValue(done)
    -- Unknown records do not become zero-percent claims. Keep the count, and
    -- use an empty bar only for the observed completed portion of this catalog.
    b.fillBar:ClearAllPoints(); b.fillBar:SetAllPoints(b)
    b.button.owner, b.button.categoryKey = self, key
    b:Show(); return y + 34
end
function U.RenderCard(self, row, index, y)
    local c = pool(self, "cards", index, "Button", self.contentChild, "FAWrathCardTemplate")
    local width = self.contentWidth - 6
    local textWidth = width - 160
    local selected = self.selected == row.key
    if self.scrollPass and c.record == row and c.selected == selected and c:GetWidth() == width
        and c.modelGeneration == self.modelGeneration and c.criteriaVersion == self.model.criteriaVersion then
        c:SetPoint("TOPLEFT", 0, -y); c:Show(); return y + c:GetHeight() + 4
    end
    c:SetWidth(width); c:SetPoint("TOPLEFT", 0, -y)
    c.owner, c.record, c.selected = self, row, self.selected == row.key
    c.tracked.owner = self
    c.label:SetWidth(width - 180); c.label:SetText(row.name)
    c.description:SetWidth(textWidth); c.hiddenDescription:SetWidth(textWidth)
    c.objectives:SetWidth(textWidth)
    c.icon.texture:SetTexture(row.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
    local pointValue = row.pointValue
    if pointValue == nil and row.pointType == nil then pointValue = row.points end
    local feat = row.achievementType == "feat_of_strength"
    c.shield.points:SetText(feat and row.pointType == "none" and "" or pointValue == nil and "?" or tostring(pointValue))
    if type(c.shield.points.SetFontObject) == "function" then
        c.shield.points:SetFontObject(pointValue and pointValue > 100 and GameFontHighlight or FAWrathAchievementPointsFont)
    end
    c.shield.icon:SetTexture("Interface\\AchievementFrame\\UI-Achievement-Shields" .. (feat and "-NoPoints" or ""))
    c.description:SetText(row.description); c.hiddenDescription:SetText(row.description)
    c.description:SetHeight(c.selected and math.max(36, c.hiddenDescription:GetStringHeight()) or 36)
    c.dateCompleted:SetText(row.date or ""); show(c.dateCompleted, row.completed and row.date)
    local reward = row.reward or ""
    c.reward:SetText(reward)
    -- The date occupies the shield column. Keep reward lettering within the
    -- description column while retaining the original full-width reward band.
    c.reward:SetWidth(textWidth); c.reward:SetHeight(20)
    show(c.reward, reward ~= ""); show(c.rewardBackground, reward ~= "")
    saturate(c, row.completed == true)
    -- A restrained blue bronze tint and gold number identify native Legacy
    -- awards while preserving the original Wrath shield and laurel artwork.
    if row.pointType == "legacy" or row.pointType == nil and row.source == "legacy" then
        c.shield.icon:SetVertexColor(row.completed == true and .63 or .45, row.completed == true and .79 or .56, row.completed == true and 1 or .75)
        c.shield.points:SetTextColor(1, .82, .2)
    else c.shield.icon:SetVertexColor(1, 1, 1) end
    show(c.highlight, c.selected)
    show(c.check, row.tracked)
    show(c.tracked, row.source == "custom" and not row.completed and (c.selected or row.tracked))
    c.tracked:SetChecked(row.tracked == true)
    -- Every card can expand a long description or report unavailable criteria.
    c.plusMinus:Show()
    c.plusMinus:SetTexCoord(row.completed and 0 or .5, row.completed and .5 or 1, c.selected and .25 or 0, c.selected and .5 or .25)
    hidePool(c.criteriaPool); hidePool(c.progressPool); hidePool(c.metaPool)
    c.scopeText:Hide(); c.completionText:Hide()
    local height, cy = 84, 0
    if c.selected then
        local data = P.Criteria(row)
        local descHeight = c.description:GetHeight()
        c.objectives:ClearAllPoints(); c.objectives:SetPoint("TOPLEFT", 78, -36 - descHeight)
        local scopes = { character = "Character", account = "Account", unknown = "Unknown" }
        c.scopeText:SetWidth(textWidth)
        c.scopeText:SetText("Scope: " .. (scopes[row.scopeType] or row.scope or "Unknown"))
        c.scopeText:SetTextColor(row.completed and .3 or .7, row.completed and .22 or .7, row.completed and .12 or .7)
        c.scopeText:Show(); cy = 22
        local detail = completionDetail(row)
        if detail then
            c.completionText:SetWidth(textWidth); c.completionText:SetText(detail)
            c.completionText:SetTextColor(row.completed and .3 or .7, row.completed and .22 or .7, row.completed and .12 or .7)
            c.completionText:Show(); cy = cy + 22
        end
        local texts, bars, metas = 0, 0, 0
        local omitted = false
        for criterionIndex, item in ipairs(data.items) do
            if criterionIndex > 256 then omitted = true; break end
            local f
            if item.link then
                metas = metas + 1
                f = pool(c, "metaPool", metas, "Button", c.objectives, "FAWrathMetaTemplate")
                local target = P.Resolve(self.model, item.link)
                f.owner, f.link = self, item.link
                f.icon:SetTexture(target and target.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
                f.label:SetText(item.name); f.label:SetWidth(textWidth - 54)
                show(f.check, item.completed); colors(f.label, item.completed, row.completed)
                f:SetSize(textWidth, 30)
            elseif item.current and item.required and item.required > 1 and item.current >= 0 then
                bars = bars + 1
                f = pool(c, "progressPool", bars, "StatusBar", c.objectives, "FAWrathProgressTemplate")
                f:SetSize(textWidth - 2, 14); f:SetMinMaxValues(0, item.required); f:SetValue(item.current)
                f.text:SetText(item.name .. ": " .. (item.quantityText or (item.current .. " / " .. item.required)))
                f.text:SetWidth(textWidth - 7)
            else
                texts = texts + 1
                f = pool(c, "criteriaPool", texts, "Frame", c.objectives, "FAWrathCriterionTemplate")
                f:SetSize(textWidth, 18); f.label:SetWidth(textWidth - 32)
                local unavailable = item.completed == nil and " (completion unavailable)"
                    or item.required and item.required > 1 and item.current == nil and " (progress unavailable)" or ""
                f.label:SetText(item.name .. unavailable)
                show(f.check, item.completed); colors(f.label, item.completed, row.completed)
            end
            f:SetPoint("TOPLEFT", 0, -cy); f:Show()
            cy = cy + math.max(23, f:GetHeight() + 4)
        end
        if not data.available or not data.complete or omitted then
            texts = texts + 1
            local f = pool(c, "criteriaPool", texts, "Frame", c.objectives, "FAWrathCriterionTemplate")
            f:SetPoint("TOPLEFT", 0, -cy); f:SetSize(textWidth, 20)
            f.label:SetWidth(textWidth - 12); f.label:SetText(data.available and "Some criteria unavailable or omitted." or "Criteria / progress unavailable.")
            f.label:SetTextColor(.65, .65, .65); f.check:Hide(); f:Show(); cy = cy + 24
        end
        height = math.max(110, 36 + descHeight + cy + 32)
    end
    c.objectives:SetHeight(math.max(cy, 1))
    c:SetHeight(height)
    -- Original Collapse/Expand parchment and glow texture calculations.
    c.background:SetTexCoord(0, 1, math.max(0, 1 - height / 256), 1)
    c.glow:SetTexCoord(0, 1, 0, (height + (c.selected and 5 or 0)) / 128)
    c.modelGeneration, c.criteriaVersion = self.modelGeneration, self.model.criteriaVersion
    c:Show(); return y + height + 4
end
function U.MeasureCard(self, row)
    local cache = self.measureCache
    if cache and cache.row == row and cache.generation == self.modelGeneration and cache.width == self.contentWidth
        and cache.description == row.description and cache.detail == completionDetail(row)
        and cache.criteriaVersion == self.model.criteriaVersion then return cache.advance end
    local data = P.Criteria(row)
    self.measureFont:SetWidth(self.contentWidth - 166); self.measureFont:SetText(row.description or "")
    local descHeight = math.max(36, self.measureFont:GetStringHeight())
    local cy, omitted = completionDetail(row) and 44 or 22, false
    for index, item in ipairs(data.items or {}) do
        if index > 256 then omitted = true; break end
        cy = cy + (item.link and 34 or 23)
    end
    if not data.available or not data.complete or omitted then cy = cy + 24 end
    local advance = math.max(110, 36 + descHeight + cy + 32) + 4
    self.measureCache = { row = row, generation = self.modelGeneration, width = self.contentWidth,
        description = row.description, detail = completionDetail(row), criteriaVersion = self.model.criteriaVersion, advance = advance }
    return advance
end
function U.RenderList(self, y)
    local token = perfBegin("UI.ListRender")
    local plan = self.scrollPass and self.listPlan
    if not plan then
        local searchToken = self.search ~= "" and perfBegin("UI.Search")
        local rows = P.Rows(self.model, self.category, self.search, self.filter)
        perfFinish(searchToken)
        plan = { rows = rows, y = y }
        if self.selected then
            for index, row in ipairs(rows) do
                if row.key == self.selected then
                    plan.selectedIndex, plan.delta = index, self:MeasureCard(row) - 88; break
                end
            end
        end
        plan.delta = plan.delta or 0
        self.listPlan = plan
    end
    y = plan.y
    local rows, count = plan.rows, #plan.rows
    local finish = y + count * 88 + plan.delta
    self.contentChild:SetHeight(math.max(finish + 12, self.contentScroll:GetHeight()))
    clampScroll(self.contentScroll, self.contentChild)
    local offset = self.contentScroll:GetVerticalScroll()
    local lower, upper = offset - 88, offset + self.contentScroll:GetHeight() + 88
    local function rowStart(index)
        return y + (index - 1) * 88 + (plan.selectedIndex and index > plan.selectedIndex and plan.delta or 0)
    end
    local lo, hi, first = 1, count, count + 1
    while lo <= hi do
        local mid = math.floor((lo + hi) / 2)
        local bottom = rowStart(mid) + 88 + (mid == plan.selectedIndex and plan.delta or 0)
        if bottom >= lower then first, hi = mid, mid - 1 else lo = mid + 1 end
    end
    lo, hi = first, count
    local last = first - 1
    while lo <= hi do
        local mid = math.floor((lo + hi) / 2)
        if rowStart(mid) <= upper then last, lo = mid, mid + 1 else hi = mid - 1 end
    end
    -- Slot one is reserved for the expanded card. Its criterion widgets do
    -- not accumulate across every ordinary card as the viewport moves.
    local index = plan.selectedIndex and 1 or 0
    for position = first, last do
        local row = rows[position]
        if position == plan.selectedIndex then self:RenderCard(row, 1, rowStart(position))
        else index = index + 1; self:RenderCard(row, index, rowStart(position)) end
    end
    if count == 0 then finish = self:Heading("No matching achievements", y) end
    perfFinish(token)
    return finish
end
function U.RenderStatistics(self, y)
    local catalog = self.statisticsCatalog
    local token = perfBegin("UI.StatisticsRender")
    local plan = self.scrollPass and self.statisticsPlan
    if not plan then
        local selectedRows = ns.StatisticsAdapter.Rows(catalog, self.statisticsCategory)
        local rows, groups, items = {}, {}, {}
        for _, row in ipairs(selectedRows) do
            groups[row.category] = groups[row.category] or {}
            groups[row.category][#groups[row.category] + 1] = row
        end
        local function visit(category)
            for _, row in ipairs(groups[category.key] or {}) do rows[#rows + 1] = row end
            for _, child in ipairs(category.children or {}) do visit(child) end
        end
        for _, category in ipairs(catalog.roots) do visit(category) end
        local previous, stripe = nil, 0
        for _, row in ipairs(rows) do
            if previous ~= row.category then
                local category = catalog.byCategory[row.category]
                items[#items + 1] = { header = true, label = category and category.name or row.section }
                previous = row.category
            end
            stripe = stripe + 1; items[#items + 1] = { label = row.name, record = row, stripe = stripe }
        end
        plan = { items = items, y = y }; self.statisticsPlan = plan
    end
    local base = plan.y
    self.contentChild:SetHeight(math.max(base + #plan.items * 26 + 12, self.contentScroll:GetHeight()))
    clampScroll(self.contentScroll, self.contentChild)
    local index, stripe = 0, 0
    local offset, viewport = self.contentScroll:GetVerticalScroll(), self.contentScroll:GetHeight()
    local function statRow(header, label, record)
        if y + 26 >= offset - 26 and y <= offset + viewport + 26 then
            index = index + 1
            local f = pool(self, "stats", index, "Button", self.contentChild, "FAWrathStatTemplate")
            f:SetSize(self.contentWidth - 6, 24); f:SetPoint("TOPLEFT", 0, -y)
            f.record, f.isHeader = record, header
            show(f.headerLeft, header); show(f.headerRight, header); show(f.headerMiddle, header)
            show(f.title, header); show(f.text, not header); show(f.value, not header); show(f.bG, not header)
            f.title:SetText(header and label or ""); f.title:SetWidth(self.contentWidth - 20)
            f:SetText(header and "" or label); f.text:SetWidth(self.contentWidth - 155)
            f.value:SetWidth(140); f.value:SetWordWrap(false)
            f.value:SetText(record and record.value or "")
            f.value:SetTextColor(record and record.available and 1 or .65, record and record.available and 1 or .65, record and record.available and 1 or .65)
            if not header then
                local odd = stripe % 2 == 1
                f.bG:SetTexCoord(0, 1, odd and .1875 or .375, odd and .3671875 or .5390625)
                f.bG:SetBlendMode(odd and "BLEND" or "ADD"); f.bG:SetAlpha(odd and 1 or .5)
            end
            f:Show()
        end
        y = y + 26
    end
    local first = math.max(1, math.floor((offset - 26 - base) / 26) + 1)
    local last = math.min(#plan.items, math.floor((offset + viewport + 26 - base) / 26) + 1)
    y = base + (first - 1) * 26
    for position = first, last do
        local item = plan.items[position]
        stripe = item.stripe or 0; statRow(item.header, item.label, item.record)
    end
    local finish = base + #plan.items * 26
    if #plan.items == 0 then finish = self:Heading("No available statistics in this category", base) end
    perfFinish(token)
    return finish
end
local function recentDay(row)
    if row.dateSort then return row.dateSort end
    if row.timestamp and date then
        local ok, day = pcall(date, "%Y%m%d", row.timestamp)
        if ok then return tonumber(day) end
    end
    -- Completion strings are presentation data. Parse only an explicit date;
    -- never invent a native timestamp for sorting an undated completion.
    local month, day, year = tostring(row.date or ""):match("^(%d+)/(%d+)/(%d+)$")
    if month then
        month, day, year = tonumber(month), tonumber(day), tonumber(year)
        if year < 100 then year = year + 2000 end
        return year * 10000 + month * 100 + day
    end
end
local function mergedRecent(summary)
    local rows, seen = {}, {}
    for _, source in ipairs({ summary.custom, summary.native }) do
        for _, row in ipairs(source.recent or {}) do
            if not seen[row.key] then rows[#rows + 1], seen[row.key] = row, true end
        end
    end
    table.sort(rows, function(a, b)
        local da, db = recentDay(a), recentDay(b)
        if da and db and da ~= db then return da > db end
        if da ~= nil and db == nil then return true end
        if db ~= nil and da == nil then return false end
        if a.timestamp and b.timestamp and a.timestamp ~= b.timestamp then return a.timestamp > b.timestamp end
        return a.key < b.key
    end)
    return rows
end
local stateFields = { "model", "generation", "tab", "category", "statisticsCategory", "selected", "focus", "search", "filter", "width", "height", "criteriaVersion", "navigationVersion" }
local function renderState(self)
    return { model = self.model, generation = self.modelGeneration, tab = self.tab, category = self.category,
        statisticsCategory = self.statisticsCategory, selected = self.selected, focus = self.focus,
        search = self.search, filter = self.filter, width = self.width, height = self.height,
        criteriaVersion = self.model.criteriaVersion, navigationVersion = self.navigationVersion }
end
local function sameState(a, b)
    if not a then return false end
    for _, key in ipairs(stateFields) do if a[key] ~= b[key] then return false end end
    return true
end
function U.QueueRender(self, reason)
    self.pendingRender = reason ~= "scroll" and "full" or self.pendingRender or "scroll"
    if self.renderQueued then return end
    assert(C_Timer and type(C_Timer.After) == "function", "Deferred UI refresh is unavailable")
    self.renderQueued = true
    self.renderQueueVersion = (self.renderQueueVersion or 0) + 1
    local version = self.renderQueueVersion
    C_Timer.After(0, function()
        if not self.renderQueued or self.renderQueueVersion ~= version then return end
        local pending = self.pendingRender
        self.renderQueued, self.pendingRender = false, nil
        if pending then self.guard(function() self:Render(pending) end) end
    end)
end
function U.CancelPending(self)
    self.searchQueueVersion = (self.searchQueueVersion or 0) + 1
    self.renderQueueVersion = (self.renderQueueVersion or 0) + 1
    self.workCancelVersion = (self.workCancelVersion or 0) + 1
    self.searchQueued, self.renderQueued, self.pendingRender = false, false, nil
end
function U.Render(self, reason)
    if not self.model then return end
    if self.rendering then
        perfCount("UI.RenderReentrant")
        -- Setters may fire callbacks while the same presentation is already
        -- being drawn. Replaying that unchanged request each next frame would
        -- create an endless deferred cycle. A changed query/model/selection
        -- remains queued and receives its own pass after the active one.
        if sameState(self.activeRenderState, renderState(self)) then perfCount("UI.RenderRedundant"); return end
        self.pendingRender = reason ~= "scroll" and "full" or self.pendingRender or "scroll"
        return
    end
    -- A direct full refresh already consumes the newest query and any queued
    -- presentation request. Older timer callbacks become harmless; new work
    -- requested during this pass receives a fresh generation.
    if reason ~= "scroll" then
        self.searchQueueVersion = (self.searchQueueVersion or 0) + 1
        self.renderQueueVersion = (self.renderQueueVersion or 0) + 1
        self.searchQueued, self.renderQueued, self.pendingRender = false, false, nil
    end
    local cancelVersion = self.workCancelVersion
    local token = perfBegin(reason == "scroll" and "UI.ScrollRender" or "UI.Render")
    self.rendering, self.activeRenderState = true, renderState(self)
    local ok, err = pcall(U.RenderPass, self, reason)
    self.rendering, self.scrollPass, self.activeRenderState = false, false, nil
    perfFinish(token)
    if not ok then
        U.CancelPending(self)
        error(err, 0)
    end
    self.renderState = renderState(self)
    if self.workCancelVersion ~= cancelVersion then self.pendingRender = nil
    elseif self.pendingRender then self:QueueRender(self.pendingRender) end
end
function U.RenderPass(self, reason)
    self.scrollPass = reason == "scroll" and sameState(self.renderState, renderState(self))
    if self.scrollPass then
        if self.renderMode == "list" and self.listPlan and #self.listPlan.rows > 0 then
            hidePool(self.cards); self:RenderList(self.listPlan.y)
        elseif self.renderMode == "statistics" and self.statisticsPlan and #self.statisticsPlan.items > 0 then
            hidePool(self.stats); self:RenderStatistics(self.statisticsPlan.y)
        end
        -- Static Summary, linked cards, headings, sidebar and outer artwork
        -- already belong to the ScrollFrame. Scrolling needs no rebuild.
        return
    end
    hidePool(self.cards); hidePool(self.bars); hidePool(self.stats); hidePool(self.headings)
    self.headingIndex, self.barIndex = 0, 0
    local achievements = self.tab == "achievements"
    local nativePage = self.tab == "rewards" or self.tab == "trees"
    local sidebar = achievements or self.tab == "statistics"
    if self.tab == "statistics" then
        self.statisticsCatalog = self.statisticsCatalog or ns.StatisticsAdapter.Catalog()
        if not self.statisticsCatalog.byCategory[self.statisticsCategory] then self.statisticsCategory = "stats:summary" end
    end
    if sidebar then self:RenderCategories() end
    self.notice:SetText(self.model.native.notice or "")
    show(self.notice, achievements and self.model.native.notice ~= nil)
    show(self.searchHint, achievements and self.search == "")
    show(self.searchBox, achievements); show(self.filterButton, achievements); show(self.searchIcon, achievements)
    show(self.searchClear, achievements and (self.search ~= "" or self.filter ~= "All"))
    show(self.categoryScroll, sidebar); show(self.contentScroll, not nativePage)
    show(self.nativeHost, nativePage)
    show(self.contentBackground, not nativePage)
    self.nativeBackground:Hide()
    show(region(self.root, "CategoriesBG"), sidebar)
    show(region(self.root, "WaterMark"), sidebar)
    self.contentBackground:ClearAllPoints()
    self.contentBackground:SetPoint("TOPLEFT", sidebar and self.sidebarWidth + 25 or 25, -23)
    self.contentBackground:SetPoint("BOTTOMRIGHT", -25, 23)
    self.contentScroll:ClearAllPoints()
    self.contentScroll:SetPoint("TOPLEFT", self.contentLeft, achievements and -69 or -33)
    self.contentScroll:SetSize(self.contentWidth, achievements and self.contentHeight or self.height - 62)
    self.contentChild:SetWidth(self.contentWidth)
    for _, tab in ipairs(self.tabs) do
        local selected = tab.view == self.tab
        for _, suffix in ipairs({ "Left", "Middle", "Right" }) do
            show(region(tab, suffix), not selected); show(region(tab, suffix .. "Disabled"), selected)
        end
    end
    local y, index = 4, 0
    if nativePage then
        -- The controller mounts the original Forever page. This renderer owns
        -- its surrounding Wrath artwork and tabs, never reward/tree behavior.
        self.renderMode = "native"
        return
    elseif self.tab == "statistics" then
        self.renderMode = "statistics"
        y = self:RenderStatistics(y)
    elseif self.focus then
        self.renderMode = "focus"
        y = self:Heading("Linked Achievement", y)
        y = self:RenderCard(self.focus, 1, y)
    elseif self.category == "summary" and self.search == "" and self.filter == "All" then
        self.renderMode = "summary"
        local summaryToken = perfBegin("UI.SummaryRender")
        local summary = P.Summary(self.model)
        y = self:Heading("Progress Overview", y)
        y = self:SummaryBar("custom", "Custom Achievements Earned", y, nil, summary.custom)
        y = self:SummaryBar("legacy", "Native Legacy Challenges Earned", y, nil, summary.native)
        y = self:Heading("Recent Achievements", y + 8)
        local recent = mergedRecent(summary)
        local selectedRecent
        for i = 1, math.min(6, #recent) do if recent[i].key == self.selected then selectedRecent = true; break end end
        -- Summary shares the same expanded-card slot as category lists.
        -- Opening different recent records must not leave objective pools on
        -- each ordinary card in addition to the active expanded card.
        index = selectedRecent and 1 or 0
        for i = 1, math.min(6, #recent) do
            if recent[i].key == self.selected then y = self:RenderCard(recent[i], 1, y)
            else index = index + 1; y = self:RenderCard(recent[i], index, y) end
        end
        if #recent == 0 then y = self:Heading("No recorded completions yet", y) end
        y = self:Heading("Category Progress Overview", y + 12)
        -- Wide original summary bars accommodate merged category names and
        -- explicit unknown counts without colliding with the value label.
        for _, cat in ipairs(summary.categories) do
            y = self:SummaryBar(cat.key, cat.name, y, nil, cat)
        end
        perfFinish(summaryToken)
    else
        self.renderMode = "list"
        y = self:Heading(self.model.byCategory[self.category].name, y)
        y = self:RenderList(y)
    end
    self.contentChild:SetHeight(math.max(y + 12, self.contentScroll:GetHeight()))
    self.contentScroll:UpdateScrollChildRect()
    clampScroll(self.contentScroll, self.contentChild)
end
