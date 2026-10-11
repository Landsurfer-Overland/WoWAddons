# Saved progress migration

The addon folder and save names are now `LegacyAchievementsReforged`,
`LegacyAchievementsReforgedDB` (account) and `LegacyAchievementsReforgedCharDB`
(character). WoW loads saves according to the addon folder/TOC name, so the new
identity cannot automatically read files belonging to a disabled prior addon.
There are no hidden old-name aliases or encoded identifiers in the new runtime.

Use the one-time Python 3 tool **before logging in with the renamed addon**:

1. Exit WoW completely and back up your client's **WTF** folder.
2. Find the previous addon folder's basename in `Interface/AddOns`, or the
   basename of its `.lua` file under `WTF/Account/.../SavedVariables`.
   Use that basename, without `.lua`, as `SOURCE_ADDON` below.
3. From the repository root, preview all account and character copies:

   ```powershell
   py tools/migrate_saved_variables.py --wtf-root "C:\PATH\TO\CLIENT\WTF" --source-addon SOURCE_ADDON
   ```

4. Confirm the listed client/account/character paths, then repeat with `--apply`:

   ```powershell
   py tools/migrate_saved_variables.py --wtf-root "C:\PATH\TO\CLIENT\WTF" --source-addon SOURCE_ADDON --apply
   ```

5. Install `LegacyAchievementsReforged` in `Interface/AddOns` and disable the
   prior addon. Log in on each character and confirm saved achievements,
   historical timestamps, tracking, configured thresholds, window settings and
   cross-character records remain. Commands now begin with `/lar`.

The tool copies every matching account/character `.lua` file below the supplied
WTF folder, changing only the two top-level saved-table identifiers. It never
executes Lua or edits achievement keys, counters, identities, dates, table
contents, source files or `.bak` files. Earlier source saves serve as rollback
copies. Identical target copies are safe to rerun. Any differing target aborts
the entire preflight: **do not delete a newer save to make migration proceed**;
restore/merge from your backup deliberately instead. This tool does not merge
two histories or guess which contains newer progress.

If you already logged in with the renamed addon, its new save may exist; close
WoW and back up both identities before resolving a conflict. Never run migration
while the game is writing saves. To roll back the addon, disable the new folder
and re-enable the previous one; its original saves remain unchanged.

Saved keybindings and earlier chat hyperlinks use a different identity and do
not become aliases. Rebind an addon-specific key if one was configured; generate
new achievement links with this build. All peers must use the renamed addon to
exchange its `LAR` addon-message protocol.
