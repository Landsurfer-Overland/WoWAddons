"""Renamed runtime, package layout, and non-destructive saved-data migration."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from lupa.lua51 import LuaRuntime
from test_progression_addendum import CoreHarness
from tools import migrate_saved_variables as migration
from tools import package_release as release

ROOT = Path(__file__).resolve().parents[1]
ADDON = "LegacyAchievementsReforged"


class SaveMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wtf = self.root / "WTF"
        self.wtf.mkdir()

    def source(self, where, table="PriorAddonDB", data=None):
        path = self.wtf / "Account" / "Account One" / where / "SavedVariables" / "PriorAddon.lua"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data or (table + ' = {done={lvl10=1730000000},money=38,history={"retain"}}\r\n').encode())
        return path

    def test_account_and_multiple_character_tables_are_copied_with_identical_data(self):
        paths = [self.source("", data=b'PriorAddonDB = {settings={legacyUI=true,size="Compact"},chars={Alt={done={lvl10=1730000000}}},moneyConfig={thresholds={gold5000=750000}}}\r\n'),
                 self.source("Realm One/First", "PriorAddonCharDB"),
                 self.source("Realm Two/Second", "PriorAddonCharDB")]
        original = {p: p.read_bytes() for p in paths}
        plan = migration.migration_plan(self.wtf, "PriorAddon")
        self.assertEqual(len(plan), 3)
        self.assertTrue(all(not item.target.exists() for item in plan))
        migration.apply_plan(plan)
        for item in plan:
            self.assertEqual(item.source.read_bytes(), original[item.source])
            expected = original[item.source].replace(b"PriorAddonDB =", b"LegacyAchievementsReforgedDB =").replace(b"PriorAddonCharDB =", b"LegacyAchievementsReforgedCharDB =")
            self.assertEqual(item.target.read_bytes(), expected)
        lua = LuaRuntime()
        for item in plan:
            lua.execute(item.target.read_bytes().decode())
        lua.execute('''
            assert(LegacyAchievementsReforgedDB.settings.legacyUI and LegacyAchievementsReforgedDB.settings.size=='Compact')
            assert(LegacyAchievementsReforgedDB.moneyConfig.thresholds.gold5000==750000)
            assert(LegacyAchievementsReforgedDB.chars.Alt.done.lvl10==1730000000)
            assert(LegacyAchievementsReforgedCharDB.done.lvl10==1730000000)
            assert(LegacyAchievementsReforgedCharDB.money==38 and LegacyAchievementsReforgedCharDB.history[1]=='retain')
        ''')

    def test_strings_comments_backup_and_non_save_files_are_not_changed(self):
        data = b'\xef\xbb\xbfPriorAddonDB = {note="PriorAddonDB = keep",nested={PriorAddonCharDB="keep"}}\r\n-- PriorAddonDB = comment\r\n'
        source = self.source("", data=data)
        backup = source.with_suffix(".lua.bak")
        backup.write_bytes(b"backup")
        unrelated = self.wtf / "PriorAddon.lua"
        unrelated.write_bytes(b"unrelated")
        plan = migration.migration_plan(self.wtf, "PriorAddon")
        self.assertEqual(len(plan), 1)
        migration.apply_plan(plan)
        self.assertEqual(plan[0].target.read_bytes(), data.replace(b'\xef\xbb\xbfPriorAddonDB =', b'\xef\xbb\xbfLegacyAchievementsReforgedDB =', 1))
        self.assertEqual(source.read_bytes(), data)
        self.assertEqual(backup.read_bytes(), b"backup")
        self.assertEqual(unrelated.read_bytes(), b"unrelated")

    def test_conflict_on_later_character_aborts_before_any_target_is_written(self):
        first = self.source("Realm/First", "PriorAddonCharDB")
        second = self.source("Realm/Second", "PriorAddonCharDB")
        target = second.with_name(ADDON + ".lua")
        target.write_bytes(b"newer save")
        with self.assertRaisesRegex(ValueError, "Existing target save differs"):
            migration.migration_plan(self.wtf, "PriorAddon")
        self.assertFalse(first.with_name(ADDON + ".lua").exists())
        self.assertEqual(target.read_bytes(), b"newer save")

    def test_successful_migration_can_be_repeated_without_changes(self):
        self.source("")
        migration.apply_plan(migration.migration_plan(self.wtf, "PriorAddon"))
        self.assertEqual(migration.migration_plan(self.wtf, "PriorAddon"), [])

    def test_save_created_after_preview_is_not_overwritten(self):
        self.source("")
        plan = migration.migration_plan(self.wtf, "PriorAddon")
        plan[0].target.write_bytes(b"newer save")
        with self.assertRaises(FileExistsError):
            migration.apply_plan(plan)
        self.assertEqual(plan[0].target.read_bytes(), b"newer save")

    def test_write_failure_rolls_back_new_copies_and_keeps_sources(self):
        sources = [self.source(""), self.source("Realm/Alt", "PriorAddonCharDB")]
        original = {p: p.read_bytes() for p in sources}
        plan = migration.migration_plan(self.wtf, "PriorAddon")
        real_open = Path.open

        def fail_second(path, *args, **kwargs):
            if path == plan[1].target:
                raise OSError("Simulated write failure")
            return real_open(path, *args, **kwargs)

        with patch.object(Path, "open", fail_second):
            with self.assertRaises(OSError):
                migration.apply_plan(plan)
        self.assertTrue(all(not item.target.exists() for item in plan))
        self.assertTrue(all(p.read_bytes() == original[p] for p in sources))

    def test_invalid_identifier_missing_saves_and_unsupported_data_stop_safely(self):
        for identifier in ("../Other", ADDON, ""):
            with self.assertRaises(ValueError):
                migration.migration_plan(self.wtf, identifier)
        with self.assertRaisesRegex(ValueError, "No source saves"):
            migration.migration_plan(self.wtf, "PriorAddon")
        self.source("", data=b'print("never executed")\n')
        with self.assertRaisesRegex(ValueError, "No supported saved table"):
            migration.migration_plan(self.wtf, "PriorAddon")


class ReforgedPackageTests(unittest.TestCase):
    def test_package_has_one_installable_root_all_dependencies_and_no_dev_files(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = release.package(folder)
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                self.assertTrue(all(n.startswith(ADDON + "/") for n in names))
                self.assertIn(ADDON + "/" + ADDON + ".toc", names)
                self.assertIn(ADDON + "/CREDITS.md", names)
                self.assertIn(ADDON + "/Media/ReforgedChime.wav", names)
                self.assertIn(ADDON + "/Media/AchievementEarned.ogg", names)
                self.assertFalse(any("/tests/" in n or "/References/" in n or "/tools/" in n for n in names))
                self.assertEqual(z.testzip(), None)
                for name in names:
                    self.assertEqual(z.read(name), (ROOT / name).read_bytes())
            self.assertTrue(archive.with_suffix(".zip.sha256").is_file())

    def test_release_is_reproducible_and_existing_artifact_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            first = release.package(Path(folder) / "first")
            second = release.package(Path(folder) / "second")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with self.assertRaises(FileExistsError):
                release.package(Path(folder) / "first")

    def test_missing_runtime_dependency_fails_before_creating_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            addon = root / ADDON
            addon.mkdir()
            (addon / (ADDON + ".toc")).write_text('## Version: 0.5.0-alpha\nMissing.lua\n')
            output = root / "release"
            with self.assertRaisesRegex(ValueError, "Missing TOC file"):
                release.package(output, root)
            self.assertFalse(output.exists())


class ReforgedRuntimeIdentityTests(unittest.TestCase):
    def test_commands_and_binding_headers_use_new_identity(self):
        h = CoreHarness()
        h.load("Themes.lua")
        h.execute('''
            assert(SLASH_LEGACYACHIEVEMENTSREFORGED1=='/lar')
            assert(SLASH_LEGACYACHIEVEMENTSREFORGED2=='/reforged')
            assert(SLASH_LEGACYACHIEVEMENTSREFORGED3=='/legacyachievements')
            assert(type(SlashCmdList.LEGACYACHIEVEMENTSREFORGED)=='function')
            assert(BINDING_HEADER_LEGACYACHIEVEMENTSREFORGED=='Legacy Achievements Reforged')
            assert(ns.LAR.TAG:find('Legacy Achievements Reforged',1,true))
            SlashCmdList.LEGACYACHIEVEMENTSREFORGED('help')
        ''')

    def test_new_account_and_character_save_names_are_declared_by_toc(self):
        toc = (ROOT / ADDON / (ADDON + ".toc")).read_text()
        self.assertIn('## Title: Legacy Achievements Reforged\n', toc)
        self.assertIn('## SavedVariables: LegacyAchievementsReforgedDB\n', toc)
        self.assertIn('## SavedVariablesPerCharacter: LegacyAchievementsReforgedCharDB\n', toc)
        self.assertIn('## IconTexture: Interface\\AddOns\\LegacyAchievementsReforged\\Media\\icon\n', toc)


if __name__ == '__main__':
    unittest.main()
