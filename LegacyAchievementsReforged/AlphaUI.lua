-------------------------------------------------------------------------------
--  Alpha UI: the shared look of Piotr's addons (a copy kept in each addon,
--  so none depends on another). Exposed on the addon namespace as ns.Alpha.
--
--  Page widgets (SectionHeader, Toggle, Slider, Dropdown, DualRow,
--  WideDualButton), cards with gaps, square checkboxes, accent bars on the
--  headers, pill tabs and a colour palette the themes fill in. Text uses the
--  game's own font (whatever is in the Fonts folder).
-------------------------------------------------------------------------------

local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local FONT_BOLD = FONT

local C = {
    bg = { 0.047, 0.075, 0.106, 0.97 },
    card = { 0.078, 0.122, 0.168, 0.92 },
    cardHover = { 0.098, 0.150, 0.205, 0.95 },
    edge = { 1, 1, 1, 0.07 },
    accent = { 0.18, 0.77, 0.71 },
    text = { 0.93, 0.95, 0.97 },
    dim = { 0.62, 0.68, 0.74 },
}

local ROW_H, GAP, PAD = 44, 6, 20

local _, ns = ...
local Kit = { FONT = FONT, style = "alpha", COLORS = C }
ns.Alpha = Kit

function Kit.Accent() return C.accent[1], C.accent[2], C.accent[3] end

function Kit.MakeFont(parent, size, flags, r, g, b, a)
    local fs = parent:CreateFontString(nil, "OVERLAY")
    fs:SetFont((size and size >= 15) and FONT_BOLD or FONT, size or 13, flags or "")
    if r then fs:SetTextColor(r, g, b, a or 1) end
    return fs
end

-- One physical screen pixel in the frame's own units. A 1-unit line is 1.3 or
-- 1.4 pixels at most UI scales, so it rounds to 1 or 2 pixels depending on
-- where it lands; one real pixel is the same width everywhere.
function Kit.PixelSize(frame)
    local scale = frame:GetEffectiveScale()
    if not scale or scale <= 0 then return 1 end
    -- The client's own helper: the size, in this frame's units, of at least
    -- one whole screen pixel.
    if PixelUtil and PixelUtil.GetNearestPixelSize then
        return PixelUtil.GetNearestPixelSize(1, scale, 1)
    end
    local _, height = GetPhysicalScreenSize()
    if not height or height <= 0 then return 1 end
    return (768 / height) / scale
end

-- Thin lines must land on whole pixels: by default the client smooths a
-- texture that sits between two pixels, which shows as a line that is
-- thicker and fainter on some sides.
function Kit.Snap(tex)
    if tex.SetSnapToPixelGrid then tex:SetSnapToPixelGrid(true) end
    if tex.SetTexelSnappingBias then tex:SetTexelSnappingBias(0) end
    return tex
end

-- Bordered frames, so their edges can be put back on whole pixels after the
-- frame moves (scrolling, dragging). Hidden ones drop out and come back with
-- their OnShow.
local bordered = {}

-- 1 px edges in a colour. Each edge is placed on the first whole screen pixel
-- inside the frame's side: a frame side that falls between two pixels would
-- otherwise give a blurred or a missing line.
function Kit.MakeBorder(frame, r, g, b, a)
    local edges = {}
    local function edge()
        local t = frame:CreateTexture(nil, "BORDER")
        t:SetColorTexture(r or 1, g or 1, b or 1, a or 1)
        Kit.Snap(t)
        edges[#edges + 1] = t
        return t
    end
    local top, bottom, left, right = edge(), edge(), edge(), edge()

    function edges:Align()
        local px = Kit.PixelSize(frame)
        local L, R, T, B = frame:GetLeft(), frame:GetRight(), frame:GetTop(), frame:GetBottom()
        local oL, oR, oT, oB = 0, 0, 0, 0
        if L and R and T and B then
            -- Distance from each side to the nearest whole pixel inside it,
            -- never negative: a line a hair outside the frame could round to
            -- the pixel beyond it and look cut off.
            oL = math.max(0, math.ceil(L / px - 0.01) * px - L)
            oR = math.max(0, R - math.floor(R / px + 0.01) * px)
            oT = math.max(0, T - math.floor(T / px + 0.01) * px)
            oB = math.max(0, math.ceil(B / px - 0.01) * px - B)
        end
        top:ClearAllPoints()
        top:SetPoint("TOPLEFT", oL, -oT)
        top:SetPoint("TOPRIGHT", -oR, -oT)
        top:SetHeight(px)
        bottom:ClearAllPoints()
        bottom:SetPoint("BOTTOMLEFT", oL, oB)
        bottom:SetPoint("BOTTOMRIGHT", -oR, oB)
        bottom:SetHeight(px)
        left:ClearAllPoints()
        left:SetPoint("TOPLEFT", oL, -oT)
        left:SetPoint("BOTTOMLEFT", oL, oB)
        left:SetWidth(px)
        right:ClearAllPoints()
        right:SetPoint("TOPRIGHT", -oR, -oT)
        right:SetPoint("BOTTOMRIGHT", -oR, oB)
        right:SetWidth(px)
    end
    function edges:SetColor(r2, g2, b2, a2)
        for _, t in ipairs(self) do t:SetColorTexture(r2, g2, b2, a2) end
    end

    edges:Align()
    bordered[edges] = frame
    frame:HookScript("OnShow", function()
        bordered[edges] = frame
        edges:Align()
    end)
    frame:HookScript("OnSizeChanged", function() edges:Align() end)
    -- Positions settle on the next frame after creation.
    C_Timer.After(0, function() edges:Align() end)
    return edges
end

-- Puts every visible border back on whole pixels (after a scroll or a drag).
function Kit.RealignBorders()
    for edges, frame in pairs(bordered) do
        if frame:IsVisible() then edges:Align() else bordered[edges] = nil end
    end
end

-- A texture a whole number of screen pixels inside the frame's pixel-aligned
-- edges (the same edges MakeBorder uses), so the gap is even on every side.
-- units: the inset wanted, in the frame's own units; rounded to pixels.
function Kit.PixelInset(frame, tex, units)
    local inset = {}
    function inset:Align()
        local px = Kit.PixelSize(frame)
        local L, R, T, B = frame:GetLeft(), frame:GetRight(), frame:GetTop(), frame:GetBottom()
        local oL, oR, oT, oB = 0, 0, 0, 0
        if L and R and T and B then
            oL = math.ceil(L / px - 0.01) * px - L
            oR = R - math.floor(R / px + 0.01) * px
            oT = T - math.floor(T / px + 0.01) * px
            oB = math.ceil(B / px - 0.01) * px - B
        end
        local k = math.max(2, math.floor(units / px + 0.5)) * px
        tex:ClearAllPoints()
        tex:SetPoint("TOPLEFT", oL + k, -(oT + k))
        tex:SetPoint("BOTTOMRIGHT", -(oR + k), oB + k)
    end
    inset:Align()
    bordered[inset] = frame
    frame:HookScript("OnShow", function()
        bordered[inset] = frame
        inset:Align()
    end)
    frame:HookScript("OnSizeChanged", function() inset:Align() end)
    C_Timer.After(0, function() inset:Align() end)
    return inset
end

-------------------------------------------------------------------------------
--  Tweens: one shared OnUpdate eases every running animation and hides
--  itself when none is left. A tween with the same key replaces the last
--  one. With animations off (Kit.animate false) each jumps to its end.
-------------------------------------------------------------------------------
Kit.animate = true
local tweens = {}
local tweenDriver = CreateFrame("Frame")
tweenDriver:Hide()
local running = {}
tweenDriver:SetScript("OnUpdate", function(_, elapsed)
    -- Walk a snapshot: step()/done() may start new tweens (toastIn's done starts
    -- toastShine), and adding keys to a table during pairs() breaks next().
    local n = 0
    for key in pairs(tweens) do n = n + 1; running[n] = key end
    for i = 1, n do
        local key = running[i]
        running[i] = nil
        local tw = tweens[key]
        if tw then
            tw.t = tw.t + elapsed
            local f = math.min(1, tw.t / tw.duration)
            local e = 1 - (1 - f) ^ 3 -- ease-out cubic
            tw.step(e)
            -- step() may have replaced this tween under the same key; leave the new one.
            if f >= 1 and tweens[key] == tw then
                tweens[key] = nil
                if tw.done then tw.done() end
            end
        end
    end
    if not next(tweens) then tweenDriver:Hide() end
end)

-- step(e) gets 0..1 (eased); done() runs once at the end.
function Kit.Tween(key, duration, step, done)
    if not Kit.animate or duration <= 0 then
        step(1)
        if done then done() end
        return
    end
    tweens[key] = { t = 0, duration = duration, step = step, done = done }
    step(0)
    tweenDriver:Show()
end

function Kit.Lerp(a, b, e) return a + (b - a) * e end

-------------------------------------------------------------------------------
--  Growing bars: a fill texture eases from zero to its width. Each bar keeps
--  its own start time, so bars made while others still grow do not jump.
-------------------------------------------------------------------------------
local growing = {}
local growDriver = CreateFrame("Frame")
growDriver:Hide()
growDriver:SetScript("OnUpdate", function()
    local now = GetTime()
    for tex, g in pairs(growing) do
        local f = math.min(1, (now - g.t0) / g.dur)
        local e = 1 - (1 - f) ^ 3
        tex:SetWidth(math.max(1, g.width * e))
        if f >= 1 then growing[tex] = nil end
    end
    if not next(growing) then growDriver:Hide() end
end)

-- delay: seconds before it starts, to stagger a list of bars.
function Kit.GrowBar(tex, width, delay, duration)
    width = math.max(1, width)
    if not Kit.animate then
        growing[tex] = nil
        tex:SetWidth(width)
        return
    end
    tex:SetWidth(1)
    growing[tex] = { width = width, t0 = GetTime() + (delay or 0), dur = duration or 0.6 }
    growDriver:Show()
end

local function Fill(tex, c) tex:SetColorTexture(c[1], c[2], c[3], c[4] or 1) end

local function TitleCase(s)
    if s:upper() ~= s then return s end
    return (s:lower():gsub("(%a)([%w']*)", function(a, b) return a:upper() .. b end))
end

local function Tooltip(frame, title, text)
    if not text then return end
    frame:HookScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:AddLine(title, 1, 1, 1)
        GameTooltip:AddLine(text, nil, nil, nil, true)
        GameTooltip:Show()
    end)
    frame:HookScript("OnLeave", function() GameTooltip:Hide() end)
end

-- A card row: background, border, hover, label on the left.
local function Card(parent, y, text, tooltip, width, x)
    local row = CreateFrame("Frame", nil, parent)
    row:SetSize(width or (parent:GetWidth() - PAD * 2), ROW_H)
    row:SetPoint("TOPLEFT", parent, "TOPLEFT", x or PAD, y)
    row:EnableMouse(true)
    local bg = row:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    Fill(bg, C.card)
    Kit.MakeBorder(row, unpack(C.edge))
    row:SetScript("OnEnter", function() Fill(bg, C.cardHover) end)
    row:SetScript("OnLeave", function() Fill(bg, C.card) end)
    if text then
        local label = Kit.MakeFont(row, 13, nil, unpack(C.text))
        label:SetPoint("LEFT", 14, 0)
        label:SetText(text)
        row.label = label
    end
    Tooltip(row, text, tooltip)
    return row
end

-------------------------------------------------------------------------------
--  Controls (placed inside a card or a half of one)
-------------------------------------------------------------------------------
local function Checkbox(host, get, set)
    local box = CreateFrame("Button", nil, host)
    box:SetSize(18, 18)
    -- A dark well with a 1 px ring (pixel-aligned like every border) and a
    -- filled square when on.
    local well = box:CreateTexture(nil, "BACKGROUND")
    well:SetAllPoints()
    local ring = Kit.MakeBorder(box, 1, 1, 1, 0.35)
    local tick = Kit.Snap(box:CreateTexture(nil, "OVERLAY"))
    Kit.PixelInset(box, tick, 4)
    local state = Kit.MakeFont(host, 12, nil, unpack(C.dim))
    state:SetPoint("RIGHT", box, "LEFT", -8, 0)
    local function paint()
        local on = get() and true or false
        well:SetColorTexture(C.bg[1], C.bg[2], C.bg[3], 1)
        tick:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 1)
        if on then
            ring:SetColor(C.accent[1], C.accent[2], C.accent[3], 1)
        else
            ring:SetColor(1, 1, 1, 0.35)
        end
        tick:SetShown(on)
        state:SetText(on and "On" or "Off")
        state:SetTextColor(on and C.accent[1] or C.dim[1], on and C.accent[2] or C.dim[2], on and C.accent[3] or C.dim[3])
    end
    box:SetScript("OnClick", function() set(not get()); paint() end)
    paint()
    return box
end

local function SliderControl(host, width, minVal, maxVal, step, get, set)
    local holder = CreateFrame("Frame", nil, host)
    holder:SetSize(width, 20)
    local value = Kit.MakeFont(holder, 12, nil, C.accent[1], C.accent[2], C.accent[3], 1)
    value:SetPoint("RIGHT", 0, 0)
    value:SetWidth(44)
    value:SetJustifyH("RIGHT")
    local track = CreateFrame("Frame", nil, holder)
    track:SetPoint("LEFT", 0, 0)
    track:SetPoint("RIGHT", value, "LEFT", -12, 0)
    track:SetHeight(16)
    track:EnableMouse(true)
    local line = track:CreateTexture(nil, "BACKGROUND")
    line:SetHeight(2)
    line:SetPoint("LEFT")
    line:SetPoint("RIGHT")
    line:SetColorTexture(1, 1, 1, 0.15)
    local fill = track:CreateTexture(nil, "ARTWORK")
    fill:SetHeight(2)
    fill:SetPoint("LEFT")
    fill:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 1)
    local knob = track:CreateTexture(nil, "OVERLAY")
    knob:SetSize(8, 8)
    knob:SetColorTexture(1, 1, 1, 1)
    local function paint()
        local v = get()
        local f = (v - minVal) / math.max(1e-9, maxVal - minVal)
        local w = math.max(1, (track:GetWidth() or 100) * f)
        fill:SetWidth(w)
        knob:ClearAllPoints()
        knob:SetPoint("CENTER", track, "LEFT", w, 0)
        value:SetText(tostring(math.floor(v + 0.5)))
    end
    local function setFromCursor()
        local x = GetCursorPosition() / track:GetEffectiveScale()
        local left, w = track:GetLeft(), track:GetWidth()
        if not left or w <= 0 then return end
        local f = math.min(1, math.max(0, (x - left) / w))
        local v = minVal + f * (maxVal - minVal)
        v = math.floor(v / step + 0.5) * step
        set(v)
        paint()
    end
    track:SetScript("OnMouseDown", function(self)
        setFromCursor()
        self:SetScript("OnUpdate", function()
            if IsMouseButtonDown("LeftButton") then setFromCursor() else track:SetScript("OnUpdate", nil) end
        end)
    end)
    track:SetScript("OnSizeChanged", paint)
    C_Timer.After(0, paint)
    return holder
end

local openMenu
local function DropdownControl(host, width, values, order, get, set)
    local btn = CreateFrame("Button", nil, host)
    btn:SetSize(width, 26)
    local bg = btn:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0, 0, 0, 0.35)
    local border = Kit.MakeBorder(btn, 1, 1, 1, 0.2)
    local text = Kit.MakeFont(btn, 12, nil, unpack(C.text))
    text:SetPoint("LEFT", 10, 0)
    text:SetPoint("RIGHT", -24, 0)
    text:SetJustifyH("LEFT")
    text:SetWordWrap(false)
    -- Chevron drawn from two thin rotated bars, so it matches the flat look.
    local chevron = CreateFrame("Frame", nil, btn)
    chevron:SetSize(12, 8)
    chevron:SetPoint("RIGHT", -10, 0)
    local bars = {}
    for _, side in ipairs({ -1, 1 }) do
        local bar = chevron:CreateTexture(nil, "OVERLAY")
        bar:SetSize(7, 1.5)
        bar:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 1)
        bar:SetPoint("CENTER", chevron, "CENTER", side * 2.4, 0)
        bar:SetRotation(side * math.pi / 4)
        bars[side] = bar
    end
    -- open 0 = pointing down, 1 = pointing up; eased between the two.
    local function Chevron(open)
        for side, bar in pairs(bars) do bar:SetRotation(side * math.pi / 4 * (1 - 2 * open)) end
    end
    local function TurnChevron(toOpen)
        local from = toOpen and 0 or 1
        Kit.Tween(btn, 0.16, function(e) Chevron(Kit.Lerp(from, 1 - from, e)) end)
    end
    local function paint() text:SetText(values[get()] or tostring(get())) end
    btn:SetScript("OnEnter", function() border:SetColor(C.accent[1], C.accent[2], C.accent[3], 0.8) end)
    btn:SetScript("OnLeave", function() border:SetColor(1, 1, 1, 0.2) end)
    btn:SetScript("OnClick", function(self)
        -- A second click on the same dropdown closes its list.
        if openMenu then
            local mine = openMenu.owner == self
            openMenu:Hide()
            if mine then return end
        end
        local menu = CreateFrame("Frame", nil, UIParent)
        menu.owner = self
        menu:SetFrameStrata("FULLSCREEN_DIALOG")
        menu:SetWidth(width)
        menu:SetPoint("TOPLEFT", self, "BOTTOMLEFT", 0, -2)
        local mbg = menu:CreateTexture(nil, "BACKGROUND")
        mbg:SetAllPoints()
        Fill(mbg, { C.bg[1], C.bg[2], C.bg[3], 0.99 })
        Kit.MakeBorder(menu, C.accent[1], C.accent[2], C.accent[3], 0.6)
        local keys = order or {}
        if not order then for k in pairs(values) do keys[#keys + 1] = k end end
        menu:SetClampedToScreen(true)
        local y = -4
        local items, widest = {}, 0
        for _, k in ipairs(keys) do
            local item = CreateFrame("Button", nil, menu)
            items[#items + 1] = item
            item:SetSize(width - 8, 22)
            item:SetPoint("TOPLEFT", 4, y)
            local hl = item:CreateTexture(nil, "BACKGROUND")
            hl:SetAllPoints()
            hl:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], k == get() and 0.22 or 0)
            local it = Kit.MakeFont(item, 12, nil, unpack(C.text))
            it:SetPoint("LEFT", 8, 0)
            it:SetText(values[k] or k)
            widest = math.max(widest, it:GetStringWidth() or 0)
            item:SetScript("OnEnter", function() if k ~= get() then hl:SetColorTexture(1, 1, 1, 0.06) end end)
            item:SetScript("OnLeave", function() if k ~= get() then hl:SetColorTexture(0, 0, 0, 0) end end)
            item:SetScript("OnClick", function() set(k); paint(); menu:Hide() end)
            y = y - 22
        end
        menu:SetHeight(-y + 4)
        -- As wide as the longest entry (8 px text inset each side), never
        -- narrower than the button: long names stayed outside the frame.
        local menuW = math.max(width, math.ceil(widest) + 8 + 16 + 8)
        menu:SetWidth(menuW)
        for _, item in ipairs(items) do item:SetWidth(menuW - 8) end
        menu:EnableMouse(true)
        menu:SetScript("OnHide", function()
            if openMenu == menu then openMenu = nil end
            TurnChevron(false)
        end)
        -- Fades in while sliding down a few pixels from the button.
        menu:SetAlpha(0)
        Kit.Tween(menu, 0.14, function(e)
            menu:SetAlpha(e)
            menu:SetPoint("TOPLEFT", self, "BOTTOMLEFT", 0, Kit.Lerp(6, -2, e))
        end)
        TurnChevron(true)
        -- Close on a click anywhere else.
        menu:SetScript("OnUpdate", function()
            if IsMouseButtonDown("LeftButton") and not menu:IsMouseOver() and not self:IsMouseOver() then menu:Hide() end
        end)
        openMenu = menu
    end)
    paint()
    return btn
end

Kit.Dropdown = DropdownControl

-------------------------------------------------------------------------------
--  Page widgets: each takes the parent and a y offset, returns the row and its height
-------------------------------------------------------------------------------
local W = {}
Kit.W = W

function W:SectionHeader(parent, text, y)
    local frame = CreateFrame("Frame", nil, parent)
    frame:SetSize(parent:GetWidth() - PAD * 2, 34)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", PAD, y)
    local bar = frame:CreateTexture(nil, "ARTWORK")
    bar:SetSize(3, 16)
    bar:SetPoint("BOTTOMLEFT", 0, 6)
    bar:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 1)
    local label = Kit.MakeFont(frame, 15, nil, unpack(C.text))
    label:SetPoint("LEFT", bar, "RIGHT", 8, 0)
    label:SetText(TitleCase(text))
    return frame, 34
end

function W:Toggle(parent, text, y, getValue, setValue, tooltip)
    local row = Card(parent, y, text, tooltip)
    local box = Checkbox(row, getValue, setValue)
    box:SetPoint("RIGHT", -14, 0)
    return row, ROW_H + GAP
end

function W:Slider(parent, text, y, minVal, maxVal, step, getValue, setValue, tooltip)
    local row = Card(parent, y, text, tooltip)
    local s = SliderControl(row, 300, minVal, maxVal, step, getValue, setValue)
    s:SetPoint("RIGHT", -14, 0)
    return row, ROW_H + GAP
end

function W:Dropdown(parent, text, y, values, getValue, setValue, order, tooltip)
    local row = Card(parent, y, text, tooltip)
    local dd = DropdownControl(row, 220, values, order, getValue, setValue)
    dd:SetPoint("RIGHT", -14, 0)
    return row, ROW_H + GAP
end

function W:DualRow(parent, y, leftCfg, rightCfg)
    local total = parent:GetWidth() - PAD * 2
    local half = math.floor((total - GAP) / 2)
    local function build(cfg, x)
        if not cfg then return end
        local card = Card(parent, y, cfg.text, cfg.tooltip, half, x)
        if cfg.type == "dropdown" then
            DropdownControl(card, 150, cfg.values, cfg.order, cfg.getValue, cfg.setValue):SetPoint("RIGHT", -12, 0)
        elseif cfg.type == "slider" then
            SliderControl(card, 150, cfg.min, cfg.max, cfg.step or 1, cfg.getValue, cfg.setValue):SetPoint("RIGHT", -12, 0)
        elseif cfg.type == "toggle" then
            Checkbox(card, cfg.getValue, cfg.setValue):SetPoint("RIGHT", -12, 0)
        end
    end
    build(leftCfg, PAD)
    build(rightCfg, PAD + half + GAP)
    return nil, ROW_H + GAP
end

local function Button(parent, text, width, onClick)
    local b = CreateFrame("Button", nil, parent)
    b:SetSize(width, 34)
    local bg = b:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 0.12)
    local border = Kit.MakeBorder(b, C.accent[1], C.accent[2], C.accent[3], 0.7)
    local label = Kit.MakeFont(b, 13, nil, unpack(C.text))
    label:SetPoint("CENTER")
    label:SetText(text)
    b:SetScript("OnEnter", function() bg:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 0.3) end)
    b:SetScript("OnLeave", function() bg:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 0.12) end)
    b:SetScript("OnClick", onClick)
    return b
end
Kit.Button = Button

function W:WideDualButton(parent, text1, text2, y, onClick1, onClick2, width)
    local total = parent:GetWidth() - PAD * 2
    width = math.min(width or 260, math.floor((total - GAP) / 2))
    local frame = CreateFrame("Frame", nil, parent)
    frame:SetSize(total, 44)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", PAD, y)
    Button(frame, text1, width, onClick1):SetPoint("LEFT", 0, 0)
    Button(frame, text2, width, onClick2):SetPoint("LEFT", width + GAP, 0)
    return frame, 44 + GAP
end

-------------------------------------------------------------------------------
--  Window chrome and pill tabs
-------------------------------------------------------------------------------
function Kit.Chrome(win, title, subtitle, onClose)
    local bg = win:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    Fill(bg, C.bg)
    win.chromeBg = bg -- kept so the opacity can change live
    Kit.MakeBorder(win, 1, 1, 1, 0.08)
    local strip = win:CreateTexture(nil, "ARTWORK")
    strip:SetHeight(3)
    strip:SetPoint("TOPLEFT")
    strip:SetPoint("TOPRIGHT")
    strip:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 1)

    local t = Kit.MakeFont(win, 20, nil, unpack(C.text))
    t:SetPoint("TOPLEFT", 30, -20)
    t:SetText(title)
    local badge = CreateFrame("Frame", nil, win)
    badge:SetSize(48, 18)
    badge:SetPoint("LEFT", t, "RIGHT", 10, 0)
    local bbg = badge:CreateTexture(nil, "BACKGROUND")
    bbg:SetAllPoints()
    bbg:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 0.2)
    local bt = Kit.MakeFont(badge, 11, nil, C.accent[1], C.accent[2], C.accent[3], 1)
    bt:SetPoint("CENTER")
    bt:SetText("ALPHA")
    local sub = Kit.MakeFont(win, 12, nil, unpack(C.dim))
    sub:SetPoint("LEFT", badge, "RIGHT", 10, 0)
    sub:SetText(subtitle)

    local close = CreateFrame("Button", nil, win)
    close:SetSize(28, 28)
    close:SetPoint("TOPRIGHT", -12, -12)
    -- Round hover glow (a colour fill under a circular mask).
    local glow = close:CreateTexture(nil, "BACKGROUND")
    glow:SetAllPoints()
    glow:SetColorTexture(1, 1, 1, 1)
    glow:SetVertexColor(C.accent[1], C.accent[2], C.accent[3], 0)
    if glow.AddMaskTexture then
        local mask = close:CreateMaskTexture()
        mask:SetAllPoints(glow)
        mask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
        glow:AddMaskTexture(mask)
    end
    -- The cross: two thin bars, like the dropdown chevron.
    local bars = {}
    for _, angle in ipairs({ math.pi / 4, -math.pi / 4 }) do
        local bar = close:CreateTexture(nil, "OVERLAY")
        bar:SetSize(12, 1.5)
        bar:SetPoint("CENTER")
        bar:SetColorTexture(1, 1, 1, 1)
        bar:SetVertexColor(C.dim[1], C.dim[2], C.dim[3], 1)
        bar:SetRotation(angle)
        bars[#bars + 1] = bar
    end
    close:SetScript("OnEnter", function()
        glow:SetVertexColor(C.accent[1], C.accent[2], C.accent[3], 0.18)
        for _, bar in ipairs(bars) do bar:SetVertexColor(C.accent[1], C.accent[2], C.accent[3], 1); bar:SetSize(13, 2) end
    end)
    close:SetScript("OnLeave", function()
        glow:SetVertexColor(C.accent[1], C.accent[2], C.accent[3], 0)
        for _, bar in ipairs(bars) do bar:SetVertexColor(C.dim[1], C.dim[2], C.dim[3], 1); bar:SetSize(12, 1.5) end
    end)
    close:SetScript("OnClick", onClose)
end

function Kit.MakeTab(win, text)
    local tab = CreateFrame("Button", nil, win)
    tab:SetHeight(24)
    local bg = tab:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    local label = Kit.MakeFont(tab, 13, nil, unpack(C.dim))
    label:SetPoint("CENTER")
    label:SetText(text)
    -- Width from the text, measured again once the font is ready.
    local function fit() tab:SetWidth(math.max(40, label:GetStringWidth() + 22)) end
    fit()
    C_Timer.After(0, fit)
    local active = false
    function tab:SetActive(on)
        active = on
        if on then
            bg:SetColorTexture(C.accent[1], C.accent[2], C.accent[3], 0.85)
            label:SetTextColor(0.03, 0.07, 0.09)
        else
            bg:SetColorTexture(1, 1, 1, 0.04)
            label:SetTextColor(unpack(C.dim))
        end
    end
    tab:SetScript("OnEnter", function() if not active then bg:SetColorTexture(1, 1, 1, 0.1) end end)
    tab:SetScript("OnLeave", function() if not active then bg:SetColorTexture(1, 1, 1, 0.04) end end)
    tab:SetActive(false)
    return tab
end

Kit.TAB_X = 30       -- tab row starts in line with the cards
Kit.TAB_Y = -56      -- tab row
Kit.CONTENT_Y = -92  -- content top
Kit.SEP = false      -- no rule under the tabs
