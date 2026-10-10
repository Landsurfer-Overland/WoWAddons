-- Presentation port of Blizzard_AchievementUI.lua / Shared.lua. The supplied
-- XML supplies the actual Wrath artwork/layout. Backend, global selection,
-- comparison, tracking setters and HybridScrollFrame code are not loaded.
local _, ns = ...
local U = {}
ns.WrathAchievementUI = U
ForeverAchievementsWrathUI = U -- only our XML callbacks, never Blizzard globals
local P = ns.LegacyPresentation
local function region(self, suffix) return _G[self:GetName() .. suffix] end
local function show(object, yes) if yes then object:Show() else object:Hide() end end
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
    self.description:SetWidth(330); self.hiddenDescription:SetWidth(330)
    self.description:SetHeight(36)
    self.objectives:ClearAllPoints()
    self.objectives:SetPoint("TOPLEFT", self, "TOPLEFT", 78, -72)
    self.objectives:SetSize(340, 1)
    self.criteriaPool, self.progressPool, self.metaPool = {}, {}, {}
end
-- Original AchievementButton_Saturate / Desaturate colors and texture slices.
local function saturate(card, completed)
    local icon = card.icon
    card.titleBackground:SetTexCoord(0, .9765625, completed and 0 or .34375, completed and .3125 or .65625)
    card.background:SetTexture("Interface\\AchievementFrame\\UI-Achievement-Parchment-Horizontal" .. (completed and "" or "-Desaturated"))
    if completed then
        card.glow:SetVertexColor(1, 1, 1); icon.bling:SetVertexColor(1, 1, 1)
        icon.frame:SetVertexColor(1, 1, 1); icon.texture:SetVertexColor(1, 1, 1)
        card.shield.icon:SetTexCoord(0, .5, 0, 1); card.shield.points:SetTextColor(1, 1, 1)
        card.reward:SetTextColor(1, .82, 0); card.label:SetTextColor(1, 1, 1)
        card.description:SetTextColor(0, 0, 0); card.description:SetShadowOffset(0, 0)
        card:SetBackdropBorderColor(.7, .15, .05)
    else
        card.glow:SetVertexColor(.22, .17, .13); icon.bling:SetVertexColor(.6, .6, .6)
        icon.frame:SetVertexColor(.75, .75, .75); icon.texture:SetVertexColor(.55, .55, .55)
        card.shield.icon:SetTexCoord(.5, 1, 0, 1); card.shield.points:SetTextColor(.65, .65, .65)
        card.reward:SetTextColor(.8, .8, .8); card.label:SetTextColor(.65, .65, .65)
        card.description:SetTextColor(1, 1, 1); card.description:SetShadowOffset(1, -1)
        card:SetBackdropBorderColor(.5, .5, .5)
    end
    card.saturated = completed
end
local function pool(owner, key, index, kind, parent, template)
    local entries = owner[key]
    if not entries[index] then entries[index] = CreateFrame(kind, parent:GetName() .. key .. index, parent, template) end
    local f = entries[index]; f:ClearAllPoints(); return f
end
local function hidePool(entries) for _, f in ipairs(entries) do f:Hide() end end
local function colors(label, completed, parentDone)
    if parentDone then label:SetTextColor(0, 0, 0)
    elseif completed then label:SetTextColor(0, 1, 0) else label:SetTextColor(.65, .65, .65) end
end
function U.CardClick(self)
    action(self, function(owner)
        owner.focus = nil
        owner.selected = owner.selected == self.record.key and nil or self.record.key
        owner:Render()
    end)
end
function U.CardEnter(self) if self.record then self.highlight:Show() end end
function U.CardLeave(self) if not self.selected then self.highlight:Hide() end end
function U.CategoryClick(self)
    action(self, function(owner)
        local cat = self.category
        owner.category, owner.focus, owner.selected = cat.key, nil, nil
        if #cat.children > 0 then owner.expanded[cat.key] = not owner.expanded[cat.key] end
        owner.contentScroll:SetVerticalScroll(0); owner:Render()
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
            owner.contentScroll:SetVerticalScroll(0); owner:Render()
        end
    end)
end
function U.SummaryClick(self)
    action(self, function(owner)
        owner.category, owner.focus, owner.selected = self.categoryKey, nil, nil
        owner.expanded[self.categoryKey] = true
        owner.contentScroll:SetVerticalScroll(0); owner:Render()
    end)
end
function U.TabClick(self)
    action(self, function(owner)
        owner.tab = self.view; owner.focus = nil
        owner.contentScroll:SetVerticalScroll(0); owner:Render()
    end)
end
local function scroll(parent, name, width, height, x, y)
    local s = CreateFrame("ScrollFrame", name, parent, "UIPanelScrollFrameTemplate")
    s:SetSize(width, height); s:SetPoint("TOPLEFT", x, y)
    local child = CreateFrame("Frame", name .. "Child", s)
    child:SetSize(width, height); s:SetScrollChild(child)
    return s, child
end
function U.Create(cover, guard, refresh)
    local self = { guard = guard, onRefresh = refresh, category = "summary", tab = "achievements", filter = "All", search = "",
        expanded = { legacy = true }, categories = {}, cards = {}, bars = {}, stats = {}, headings = {} }
    self.root = CreateFrame("Frame", "FAWrathAchievementFrame", cover, "FAWrathWindowTemplate")
    self.root:SetSize(768, 500)
    self.root:SetPoint("TOP", cover, "TOP", 0, -72)
    local background = self.root:CreateTexture(nil, "BACKGROUND")
    background:SetPoint("TOPLEFT", 219, -23); background:SetPoint("BOTTOMRIGHT", -25, 23)
    background:SetTexture("Interface\\AchievementFrame\\UI-Achievement-AchievementBackground")
    self.categoryScroll, self.categoryChild = scroll(self.root, "FAWrathCategoryScroll", 169, 442, 28, -27)
    self.contentScroll, self.contentChild = scroll(self.root, "FAWrathContentScroll", 496, 402, 234, -69)
    self.contentScroll:HookScript("OnVerticalScroll", function()
        if self.rendering or self.scrollRendering or not self.model then return end
        self.scrollRendering = true
        guard(function() self:Render() end)
        self.scrollRendering = false
    end)
    self.notice = font(self.root, "GameFontNormalSmall")
    self.notice:SetPoint("TOPLEFT", 238, -47); self.notice:SetWidth(491); self.notice:SetHeight(24)
    self.notice:SetJustifyH("LEFT")
    self.searchBox = CreateFrame("EditBox", "FAWrathSearch", self.root, "InputBoxTemplate")
    self.searchBox:SetSize(250, 22); self.searchBox:SetPoint("TOPLEFT", 248, -24)
    self.searchBox:SetAutoFocus(false); self.searchBox:SetMaxLetters(100)
    self.searchBox:SetScript("OnEscapePressed", function(box) box:ClearFocus() end)
    self.searchBox:SetScript("OnTextChanged", function(box)
        guard(function() self.search = box:GetText() or ""; self.focus = nil; self.contentScroll:SetVerticalScroll(0); self:Render() end)
    end)
    self.searchBox:SetScript("OnEnterPressed", function(box) box:ClearFocus() end)
    self.searchHint = font(self.root, "GameFontNormalSmall", "Search")
    self.searchHint:SetPoint("BOTTOMLEFT", self.searchBox, "TOPLEFT", 0, 2)
    self.filterButton = CreateFrame("Button", "FAWrathFilter", self.root, "FAWrathCategoryTemplate")
    self.filterButton:SetSize(155, 24); self.filterButton:SetPoint("TOPRIGHT", -28, -23)
    self.filterButton.label:SetText("All")
    self.filterButton:SetScript("OnClick", function()
        guard(function()
            self.filter = self.filter == "All" and "Complete" or self.filter == "Complete" and "Incomplete" or "All"
            self.filterButton.label:SetText(self.filter); self.focus = nil
            self.contentScroll:SetVerticalScroll(0); self:Render()
        end)
    end)
    self.tabs = {}
    for i, view in ipairs({ "achievements", "statistics" }) do
        local tab = CreateFrame("Button", "FAWrathTab" .. i, self.root, "FAWrathTabTemplate")
        tab:SetPoint("TOPLEFT", self.root, "BOTTOMLEFT", 11 + (i - 1) * 120, 0)
        tab:SetText(i == 1 and "Achievements" or "Statistics")
        tab.owner, tab.view = self, view; self.tabs[i] = tab
    end
    self.nativePoints = font(self.root, "GameFontNormalSmall")
    self.nativePoints:SetPoint("TOPRIGHT", self.root, "TOPRIGHT", -36, 32)
    region(self.root, "HeaderTitle"):SetText("Character Achievement Points")
    -- Explicit method table keeps our controller out of Blizzard globals.
    for _, name in ipairs({ "Fit", "SetModel", "Render", "RenderCategories", "RenderCard", "Heading", "SummaryBar" }) do self[name] = U[name] end
    return self
end
function U.Fit(self, page)
    local width, height = page:GetWidth(), page:GetHeight()
    assert(width > 0 and height > 0, "Legacy Challenges page has no layout yet")
    local scale = math.min(width / 768, height / 640)
    self.root:SetScale(scale)
    self.root:ClearAllPoints()
    -- Offsets use the scaled child's coordinate space.
    self.root:SetPoint("TOP", page, "TOP", 0, -72)
end
function U.SetModel(self, model)
    self.model = model
    if not model.byCategory[self.category] then self.category = "summary" end
    if self.focus then self.focus = P.Resolve(model, self.focus.key) end
    region(self.root, "HeaderPoints"):SetText(tostring(model.custom.points))
    self.nativePoints:SetText("Legacy Points: " .. (model.native.points and tostring(model.native.points) or "Unavailable"))
    self:Render()
end
function U.RenderCategories(self)
    hidePool(self.categories)
    local count = 0
    local function visit(cat, depth)
        count = count + 1
        local b = pool(self, "categories", count, "Button", self.categoryChild, "FAWrathCategoryTemplate")
        b:SetSize(164 - math.min(depth, 3) * 8, 24)
        b:SetPoint("TOPLEFT", math.min(depth, 3) * 8, -(count - 1) * 25)
        b.owner, b.category = self, cat
        b.label:SetText((#cat.children > 0 and (self.expanded[cat.key] and "- " or "+ ") or "") .. cat.name)
        b.background:SetVertexColor(0, self.category == cat.key and .6 or 0, 0, self.category == cat.key and .65 or .9)
        b:Show()
        if self.expanded[cat.key] then for _, child in ipairs(cat.children) do visit(child, depth + 1) end end
    end
    for _, key in ipairs({ "summary", "legacy", "custom" }) do visit(self.model.byCategory[key], 0) end
    self.categoryChild:SetHeight(math.max(442, count * 25))
end
function U.Heading(self, text, y)
    self.headingIndex = self.headingIndex + 1
    local h = self.headings[self.headingIndex]
    if not h then h = font(self.contentChild, "GameFontNormalLarge"); self.headings[self.headingIndex] = h end
    h:ClearAllPoints(); h:SetPoint("TOP", self.contentChild, "TOP", 0, -y); h:SetText(text); h:Show()
    return y + 30
end
function U.SummaryBar(self, key, label, y, column)
    self.barIndex = self.barIndex + 1
    local b = pool(self, "bars", self.barIndex, "StatusBar", self.contentChild, "FAWrathSummaryBarTemplate")
    b:SetSize(column and 222 or 465, 21); b:SetPoint("TOPLEFT", 15 + (column or 0) * 244, -y)
    local done, total, unknown = P.Count(self.model, key)
    b.label:SetWidth(column and 150 or 360); b.label:SetWordWrap(false)
    b.label:SetText(label); b.text:SetText(done .. "/" .. total .. (unknown > 0 and " (? " .. unknown .. ")" or ""))
    b:SetMinMaxValues(0, math.max(total, 1)); b:SetValue(done)
    b.fillBar:ClearAllPoints(); b.fillBar:SetAllPoints(b)
    b.button.owner, b.button.categoryKey = self, key
    b:Show(); return y + 42
end
function U.RenderCard(self, row, index, y)
    local c = pool(self, "cards", index, "Button", self.contentChild, "FAWrathCardTemplate")
    c:SetWidth(490); c:SetPoint("TOPLEFT", 0, -y)
    c.owner, c.record, c.selected = self, row, self.selected == row.key
    c.tracked.owner = self
    c.label:SetWidth(310); c.label:SetText(row.name)
    c.icon.texture:SetTexture(row.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
    c.shield.points:SetText(row.points == nil and "?" or tostring(row.points))
    c.shield.icon:SetTexture("Interface\\AchievementFrame\\UI-Achievement-Shields" .. (row.points == 0 and "-NoPoints" or ""))
    c.description:SetText(row.description); c.hiddenDescription:SetText(row.description)
    c.description:SetHeight(c.selected and math.max(36, c.hiddenDescription:GetStringHeight()) or 36)
    c.dateCompleted:SetText(row.date or ""); show(c.dateCompleted, row.completed and row.date)
    local reward = row.reward or ""
    local source = row.source == "legacy" and ("Legacy Challenge · " .. row.scope) or "Character Achievement"
    if row.completed == nil then source = source .. " · Completion unavailable" end
    c.reward:SetText(source .. (reward ~= "" and (" — " .. reward) or ""))
    c.reward:SetWidth(470); c.reward:SetHeight(20)
    c.reward:Show(); c.rewardBackground:Show()
    saturate(c, row.completed == true)
    show(c.highlight, c.selected)
    show(c.check, row.tracked)
    show(c.tracked, row.source == "custom" and not row.completed and (c.selected or row.tracked))
    c.tracked:SetChecked(row.tracked == true)
    -- Every card can expand a long description or report unavailable criteria.
    c.plusMinus:Show()
    c.plusMinus:SetTexCoord(row.completed and 0 or .5, row.completed and .5 or 1, c.selected and .5 or 0, c.selected and 1 or .5)
    hidePool(c.criteriaPool); hidePool(c.progressPool); hidePool(c.metaPool)
    local height, cy = 84, 0
    if c.selected then
        local data = P.Criteria(row)
        local descHeight = c.description:GetHeight()
        c.objectives:ClearAllPoints(); c.objectives:SetPoint("TOPLEFT", 78, -36 - descHeight)
        local texts, bars, metas = 0, 0, 0
        for _, item in ipairs(data.items) do
            local f
            if item.link then
                metas = metas + 1
                f = pool(c, "metaPool", metas, "Button", c.objectives, "FAWrathMetaTemplate")
                local target = P.Resolve(self.model, item.link)
                f.owner, f.link = self, item.link
                f.icon:SetTexture(target and target.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
                f.label:SetText(item.name); f.label:SetWidth(278)
                show(f.check, item.completed); colors(f.label, item.completed, row.completed)
                f:SetSize(332, 30)
            elseif item.current and item.required and item.required > 1 and item.current >= 0 then
                bars = bars + 1
                f = pool(c, "progressPool", bars, "StatusBar", c.objectives, "FAWrathProgressTemplate")
                f:SetSize(330, 14); f:SetMinMaxValues(0, item.required); f:SetValue(item.current)
                f.text:SetText(item.name .. ": " .. (item.quantityText or (item.current .. " / " .. item.required)))
                f.text:SetWidth(325)
            else
                texts = texts + 1
                f = pool(c, "criteriaPool", texts, "Frame", c.objectives, "FAWrathCriterionTemplate")
                f:SetSize(332, 18); f.label:SetWidth(300)
                local unavailable = item.completed == nil and " (completion unavailable)"
                    or item.required and item.required > 1 and item.current == nil and " (progress unavailable)" or ""
                f.label:SetText(item.name .. unavailable)
                show(f.check, item.completed); colors(f.label, item.completed, row.completed)
            end
            f:SetPoint("TOPLEFT", 0, -cy); f:Show()
            cy = cy + math.max(23, f:GetHeight() + 4)
        end
        if not data.available or not data.complete then
            texts = texts + 1
            local f = pool(c, "criteriaPool", texts, "Frame", c.objectives, "FAWrathCriterionTemplate")
            f:SetPoint("TOPLEFT", 0, -cy); f:SetSize(332, 20)
            f.label:SetWidth(320); f.label:SetText(data.available and "Some criteria unavailable or omitted." or "Criteria / progress unavailable.")
            f.label:SetTextColor(.65, .65, .65); f.check:Hide(); f:Show(); cy = cy + 24
        end
        height = math.max(110, 36 + descHeight + cy + 32)
    end
    c.objectives:SetHeight(math.max(cy, 1))
    c:SetHeight(height)
    -- Original Collapse/Expand parchment and glow texture calculations.
    c.background:SetTexCoord(0, 1, math.max(0, 1 - height / 256), 1)
    c.glow:SetTexCoord(0, 1, 0, (height + (c.selected and 5 or 0)) / 128)
    c:Show(); return y + height + 4
end
function U.Render(self)
    if not self.model then return end
    self.rendering = true
    hidePool(self.cards); hidePool(self.bars); hidePool(self.stats); hidePool(self.headings)
    self.headingIndex, self.barIndex = 0, 0
    self:RenderCategories()
    self.notice:SetText(self.model.native.notice or "Native completion and Legacy rewards remain controlled by Forever.")
    show(self.searchHint, self.search == "")
    for _, tab in ipairs(self.tabs) do
        local selected = tab.view == self.tab
        for _, suffix in ipairs({ "Left", "Middle", "Right" }) do
            show(region(tab, suffix), not selected); show(region(tab, suffix .. "Disabled"), selected)
        end
    end
    local y, index = 4, 0
    if self.tab == "statistics" then
        y = self:Heading("Character Statistics", y)
        for i, stat in ipairs(ns.CustomAchievementAdapter.Statistics()) do
            local f = pool(self, "stats", i, "Button", self.contentChild, "FAWrathStatTemplate")
            f:SetSize(490, 24); f:SetPoint("TOPLEFT", 0, -y)
            show(f.headerLeft, stat.heading); show(f.headerRight, stat.heading); show(f.headerMiddle, stat.heading)
            show(f.title, stat.heading); show(f.text, not stat.heading)
            f.title:SetText(stat.heading and stat[1] or ""); f:SetText(stat.heading and "" or stat[1])
            f.value:SetText(stat[2]); f:Show(); y = y + 26
        end
    elseif self.focus then
        y = self:Heading("Linked Achievement", y)
        y = self:RenderCard(self.focus, 1, y)
    elseif self.category == "summary" and self.search == "" and self.filter == "All" then
        y = self:Heading("Recent Achievements", y)
        local recent = {}
        for _, row in ipairs(self.model.records) do if row.completed then recent[#recent + 1] = row end end
        table.sort(recent, function(a, b)
            -- Native API dates lack time-of-day; keep their date-based ordering.
            local function dateKey(r)
                if r.timestamp then return r.timestamp end
                local m, d, yr = (r.date or ""):match("(%d+)/(%d+)/(%d+)")
                if not m then return 0 end
                local value = ns.LegacyReadOnly.Call(time, { year = 2000 + tonumber(yr), month = tonumber(m), day = tonumber(d), hour = 0 })
                return value and ns.LegacyReadOnly.Number(value[1]) or 0
            end
            local ad, bd = dateKey(a), dateKey(b)
            return ad == bd and a.key < b.key or ad > bd
        end)
        for i = 1, math.min(#recent, 4) do y = self:RenderCard(recent[i], i, y) end
        if #recent == 0 then y = self:Heading("No recorded completions yet", y) end
        y = self:Heading("Progress Overview", y + 12)
        y = self:SummaryBar("summary", "Achievements Earned", y)
        for _, key in ipairs({ "legacy", "custom" }) do
            y = self:SummaryBar(key, self.model.byCategory[key].name, y)
            for i, cat in ipairs(self.model.byCategory[key].children) do
                self:SummaryBar(cat.key, cat.name, y, (i - 1) % 2)
                if i % 2 == 0 then y = y + 42 end
            end
            if #self.model.byCategory[key].children % 2 == 1 then y = y + 42 end
        end
    else
        local rows = P.Rows(self.model, self.category, self.search, self.filter)
        y = self:Heading(self.model.byCategory[self.category].name, y)
        -- A ScrollFrame supplies the viewport; pool only the visible cards.
        -- Keep Wrath's 84-pixel collapsed height without creating thousands of
        -- complete frame hierarchies in the aggregate Legacy category.
        local offset = self.contentScroll:GetVerticalScroll()
        local expandedHeight
        for _, row in ipairs(rows) do
            if row.key == self.selected then
                expandedHeight = self:RenderCard(row, 1, 0)
                self.cards[1]:Hide()
                break
            end
        end
        for _, row in ipairs(rows) do
            local height = row.key == self.selected and expandedHeight or 88
            if y + height >= offset - 88 and y <= offset + 490 then
                index = index + 1
                self:RenderCard(row, index, y)
            end
            y = y + height
        end
        if #rows == 0 then y = self:Heading("No matching achievements", y) end
    end
    self.contentChild:SetHeight(math.max(y + 12, 402))
    self.contentScroll:UpdateScrollChildRect()
    self.rendering = false
end
