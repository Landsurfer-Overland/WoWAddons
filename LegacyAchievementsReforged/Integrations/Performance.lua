-- Optional session-only aggregates. No per-call history, SavedVariables or
-- native progression changes; the disabled path does not read either clock.
local _, ns = ...
local LAR, R = ns.LAR, ns.LegacyReadOnly
local P = { MAX_NAMES = 64, MAX_TOKENS = 128, MAX_NAME_LENGTH = 64, MAX_VALUE = 1e15 }
ns.LegacyPerf = P

local enabled, epoch = false, 0
local metrics, nameCount, tokens, ring, cursor = {}, 0, {}, {}, 0
local dropped, droppedNames, droppedTokens, clockUnavailable = 0, 0, 0, 0

local function add(a, b)
    return math.min(P.MAX_VALUE, a + math.min(P.MAX_VALUE, b))
end
local function name(value)
    value = R.Text(value)
    if not value or #value == 0 or #value > P.MAX_NAME_LENGTH or value:find("%c") then return nil end
    return value
end
local function metric(value)
    value = name(value)
    if not value then dropped = add(dropped, 1); return nil end
    local row = metrics[value]
    if not row then
        if nameCount >= P.MAX_NAMES then
            dropped, droppedNames = add(dropped, 1), add(droppedNames, 1)
            return nil
        end
        row, nameCount = { name = value }, nameCount + 1
        metrics[value] = row
    end
    return row
end
local function readClock(source)
    local fn
    if source == "profile" then fn = debugprofilestop else fn = GetTime end
    local result = R.Call(fn)
    local value = result and R.Number(result[1])
    if not value or value < 0 then return nil end
    if source == "game" then value = R.Number(value * 1000) end
    return value
end
local function startClock()
    local value = readClock("profile")
    if value then return value, "profile" end
    value = readClock("game")
    if value then return value, "game" end
end
local function clearTokens()
    epoch, tokens, ring, cursor = epoch + 1, {}, {}, 0
end

function P.IsEnabled() return enabled end
function P.Reset()
    metrics, nameCount = {}, 0
    dropped, droppedNames, droppedTokens, clockUnavailable = 0, 0, 0, 0
    clearTokens()
end
function P.Enable(value)
    if R.Bool(value) == nil then return enabled end
    enabled = value
    if enabled then P.Reset() else clearTokens() end
    return enabled
end
function P.Begin(value)
    if not enabled then return nil end
    local row = metric(value)
    if not row then return nil end
    local generation = epoch
    local started, source = startClock()
    if not enabled or epoch ~= generation then return nil end
    if not started then clockUnavailable = add(clockUnavailable, 1) end
    cursor = cursor % P.MAX_TOKENS + 1
    local previous = ring[cursor]
    if previous and tokens[previous] then
        tokens[previous] = nil
        dropped, droppedTokens = add(dropped, 1), add(droppedTokens, 1)
    end
    local token = {}
    tokens[token] = { metric = row, started = started, source = source, epoch = epoch, slot = cursor }
    ring[cursor] = token
    return token
end
function P.Finish(token)
    if not enabled then return false end
    if not R.Safe(token) or type(token) ~= "table" then return false end
    local operation = tokens[token]
    if not operation or operation.epoch ~= epoch then return false end
    tokens[token] = nil
    if ring[operation.slot] == token then ring[operation.slot] = nil end
    local duration
    if operation.started then
        local finished = readClock(operation.source)
        if finished then duration = R.Number(finished - operation.started) end
        if duration and duration < 0 then duration = nil end
    end
    if not enabled or operation.epoch ~= epoch then return false end
    local row = operation.metric
    local timing = row.timing or { calls = 0, measured = 0, total = 0, max = 0 }
    row.timing = timing
    timing.calls = add(timing.calls, 1)
    timing.last = nil
    if duration then
        duration = math.min(P.MAX_VALUE, duration)
        timing.measured, timing.total = add(timing.measured, 1), add(timing.total, duration)
        timing.max, timing.last = math.max(timing.max, duration), duration
    elseif operation.started then clockUnavailable = add(clockUnavailable, 1) end
    return true
end
function P.Count(value, amount)
    if not enabled then return false end
    if amount == nil then amount = 1 end
    amount = R.Number(amount)
    if not amount or amount < 0 then return false end
    local row = metric(value)
    if not row then return false end
    row.counter = add(row.counter or 0, amount)
    return true
end

function P.Snapshot()
    local out = { enabled = enabled, timings = {}, counters = {}, names = nameCount,
        dropped = dropped, droppedNames = droppedNames, droppedTokens = droppedTokens, clockUnavailable = clockUnavailable,
        limits = { names = P.MAX_NAMES, tokens = P.MAX_TOKENS, nameLength = P.MAX_NAME_LENGTH, value = P.MAX_VALUE } }
    for key, row in pairs(metrics) do
        if row.timing then
            local timing = row.timing
            out.timings[key] = { calls = timing.calls, measured = timing.measured,
                total = timing.total, max = timing.max, last = timing.last }
        end
        if row.counter ~= nil then out.counters[key] = row.counter end
    end
    return out
end
local function message(text)
    if type(print) == "function" then pcall(print, (LAR.TAG or "Legacy Achievements Reforged") .. " Performance: " .. text) end
end
function P.Report()
    local snapshot = P.Snapshot()
    message((snapshot.enabled and "on" or "off") .. "; " .. snapshot.names .. " metric names, " .. snapshot.dropped
        .. " dropped, " .. snapshot.clockUnavailable .. " clock samples unavailable.")
    local names = {}
    for key in pairs(metrics) do names[#names + 1] = key end
    table.sort(names)
    for _, key in ipairs(names) do
        local timing, counter = snapshot.timings[key], snapshot.counters[key]
        local details = {}
        if timing then
            details[#details + 1] = ("calls=%g, measured=%g"):format(timing.calls, timing.measured)
            if timing.measured > 0 then
                details[#details + 1] = ("total=%.3f ms, avg=%.3f ms, max=%.3f ms, last=%s"):format(
                    timing.total, timing.total / timing.measured, timing.max,
                    timing.last and ("%.3f ms"):format(timing.last) or "unavailable")
            else details[#details + 1] = "timing unavailable" end
        end
        if counter ~= nil then details[#details + 1] = ("count=%g"):format(counter) end
        if #details > 0 then message(key .. ": " .. table.concat(details, "; ")) end
    end
    return snapshot
end

LAR.SLASH.perf = function(input)
    local command = R.Text(input)
    command = command and command:lower():match("^%s*(.-)%s*$") or ""
    if command == "on" then P.Enable(true); message("on; session metrics reset.")
    elseif command == "off" then P.Enable(false); message("off; retained metrics available with /lar perf report.")
    elseif command == "report" or command == "" then P.Report()
    elseif command == "reset" then P.Reset(); message("session metrics reset.")
    else message("Use /lar perf on|off|report|reset.") end
end
