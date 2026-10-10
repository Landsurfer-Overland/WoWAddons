-------------------------------------------------------------------------------
--  Themes: eight colour sets for the window, toast and tracker, plus the
--  window opacity and the key binding.
-------------------------------------------------------------------------------
local _, ns = ...
local FA = ns.FA
local C = FA.Kit.COLORS

local THEMES = {
    { key = "teal", label = "Sea Teal",
      bg = { 0.047, 0.075, 0.106 }, card = { 0.078, 0.122, 0.168 }, hover = { 0.098, 0.150, 0.205 },
      accent = { 0.18, 0.77, 0.71 }, text = { 0.93, 0.95, 0.97 }, dim = { 0.62, 0.68, 0.74 } },
    { key = "midnight", label = "Midnight",
      bg = { 0.020, 0.025, 0.035 }, card = { 0.045, 0.055, 0.070 }, hover = { 0.065, 0.080, 0.100 },
      accent = { 0.36, 0.60, 1.00 }, text = { 0.92, 0.94, 0.97 }, dim = { 0.56, 0.61, 0.68 } },
    { key = "gold", label = "Obsidian Gold",
      bg = { 0.030, 0.030, 0.030 }, card = { 0.068, 0.066, 0.062 }, hover = { 0.098, 0.094, 0.086 },
      accent = { 1.00, 0.78, 0.22 }, text = { 0.96, 0.94, 0.90 }, dim = { 0.66, 0.63, 0.57 } },
    { key = "ember", label = "Ember",
      bg = { 0.060, 0.034, 0.028 }, card = { 0.100, 0.060, 0.048 }, hover = { 0.138, 0.084, 0.066 },
      accent = { 1.00, 0.47, 0.20 }, text = { 0.97, 0.93, 0.90 }, dim = { 0.70, 0.62, 0.57 } },
    { key = "fel", label = "Fel",
      bg = { 0.028, 0.048, 0.030 }, card = { 0.052, 0.082, 0.054 }, hover = { 0.072, 0.112, 0.074 },
      accent = { 0.48, 0.92, 0.26 }, text = { 0.92, 0.96, 0.92 }, dim = { 0.60, 0.69, 0.60 } },
    { key = "arcane", label = "Arcane",
      bg = { 0.050, 0.034, 0.080 }, card = { 0.084, 0.060, 0.124 }, hover = { 0.114, 0.082, 0.164 },
      accent = { 0.74, 0.47, 1.00 }, text = { 0.95, 0.93, 0.98 }, dim = { 0.67, 0.62, 0.74 } },
    { key = "crimson", label = "Crimson",
      bg = { 0.054, 0.024, 0.030 }, card = { 0.094, 0.044, 0.052 }, hover = { 0.130, 0.060, 0.072 },
      accent = { 0.92, 0.22, 0.28 }, text = { 0.97, 0.92, 0.93 }, dim = { 0.70, 0.60, 0.62 } },
    { key = "frost", label = "Frost",
      bg = { 0.090, 0.112, 0.140 }, card = { 0.130, 0.160, 0.200 }, hover = { 0.160, 0.198, 0.248 },
      accent = { 0.56, 0.86, 1.00 }, text = { 0.95, 0.97, 1.00 }, dim = { 0.66, 0.74, 0.82 } },
}
local BY_KEY = {}
for _, t in ipairs(THEMES) do BY_KEY[t.key] = t end
FA.THEMES = THEMES

local function Copy(dst, src, alpha)
    dst[1], dst[2], dst[3] = src[1], src[2], src[3]
    if alpha then dst[4] = alpha end
end

-- Puts a theme's colours in the shared palette; every frame built after
-- this uses them, and the open ones are rebuilt.
function FA.ApplyTheme(key, quiet)
    local t = BY_KEY[key or ""] or THEMES[1]
    local S = FA.Settings()
    Copy(C.bg, t.bg, S.opacity or 0.97)
    Copy(C.card, t.card, 0.92)
    Copy(C.cardHover, t.hover, 0.95)
    Copy(C.accent, t.accent)
    Copy(C.text, t.text)
    Copy(C.dim, t.dim)
    if quiet then return end
    FA.ResetToast()
    if FA.StyleTracker then FA.StyleTracker() end
    FA.RebuildWindow()
end

-- Window background opacity, changed live.
function FA.SetOpacity(v)
    FA.Settings().opacity = v
    C.bg[4] = v
    local win = _G.ForeverAchievementsWindow
    if win and win.chromeBg then win.chromeBg:SetColorTexture(C.bg[1], C.bg[2], C.bg[3], v) end
end

local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
    FA.ApplyTheme(FA.Settings().theme, true)
    FA.Kit.animate = FA.Settings().animations ~= false
    if FA.StyleTracker then FA.StyleTracker() end
end)

-- Key binding (Key Bindings > AddOns > Forever Achievements).
BINDING_HEADER_FOREVERACHIEVEMENTS = "Forever Achievements"
BINDING_NAME_FOREVERACHIEVEMENTS_TOGGLE = "Open or close the window"
function ForeverAchievements_Toggle()
    if FA.IsShown() then FA.Hide() else FA.Open() end
end
