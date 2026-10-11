-- Development quarantine for the original alpha presentation. Keep its source
-- and shared features for later integration, without exposing its old window.
-- To research the original UI, change this single flag to true and /reload.
-- This deliberately does not write SavedVariables or expose a player toggle.
local _, ns = ...
local policy = { enabled = false }
ns.OriginalUI = policy
function policy.IsEnabled() return policy.enabled == true end
