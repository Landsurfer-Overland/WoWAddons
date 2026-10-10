"""Bounded presentation/native work; execution doubles are not client timing."""
import unittest

from test_legacy_wrath_ui import Harness


class PresentationPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute('''
            measured = {}
            ns.LegacyPerf = {
                Begin = function(name) return name end,
                Finish = function(token) end,
                Count = function(name, amount) measured[name] = (measured[name] or 0) + amount end,
            }
        ''')

    def test_repeated_counts_and_summary_do_not_rescan_all_records(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local m = P.Build()
            local originalRows = P.Rows
            local queries = 0
            P.Rows = function(...) queries = queries + 1; return originalRows(...) end
            local first = P.Summary(m)
            local afterInitial = queries
            for i = 1, 50 do
                for _, category in ipairs(m.roots) do P.Count(m, category.key) end
                local nextSummary = P.Summary(m)
                assert(nextSummary.custom.completed == first.custom.completed)
                assert(nextSummary.native.total == first.native.total)
            end
            assert(queries == afterInitial, 'Counts/summary must use snapshot aggregates')
            assert(measured['summary.cache_hits'] == 50)
        ''')

    def test_cached_queries_return_independent_arrays_and_scan_only_selected_membership(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local m = P.Build()
            measured = {}
            local first = P.Rows(m, 'custom', 'custom', 'All')
            assert(#first == 2 and measured['search.rows'] == 2)
            first[1], first[2] = nil, nil
            local second = P.Rows(m, 'custom', 'custom', 'All')
            assert(#second == 2 and measured['search.rows'] == 2)
            table.sort(second, function(a,b) return a.key > b.key end)
            local third = P.Rows(m, 'custom', 'custom', 'All')
            assert(third[1].key == 'custom:first' and third[2].key == 'custom:second')
            local raw = P.Rows(m, 'custom')
            raw[1] = nil
            assert(#P.Rows(m, 'custom') == 2)
        ''')

    def test_large_catalog_counts_and_source_queries_use_precomputed_membership(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local native = {available=true,partial=false,points=0,
                categories={{key='legacy-category:1',id=1,name='General',parent='legacy'}},records={}}
            for i = 1, 2500 do
                native.records[i] = {key='legacy:'..(100000+i),id=100000+i,source='legacy',
                    category='legacy-category:1',name='Native '..i,description='Description',completed=false,
                    pointValue=0,pointType='none',achievementType='standard',scopeType='character'}
            end
            local model = P.Build(nil, native)
            assert(#model.records == 2502 and P.Count(model, 'general') == 1)
            measured = {}
            for i = 1, 50 do
                P.Count(model, 'summary'); P.Count(model, 'general'); P.Count(model, 'custom')
                assert(#P.Rows(model, 'custom', 'custom') == 2)
            end
            assert(measured['search.rows'] == 2,
                'A source query/sidebar refresh must not rescan 2500 unrelated native records')
            assert(measured['search.cache_hits'] == 49)
        ''')

    def test_query_cache_is_bounded_during_long_typing_sessions(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local m = P.Build()
            measured = {}
            P.Rows(m, 'custom', 'initial query')
            for i = 1, 80 do P.Rows(m, 'custom', 'typed query '..i) end
            local scans = measured['search.rows']
            P.Rows(m, 'custom', 'typed query 80')
            assert(measured['search.rows'] == scans)
            P.Rows(m, 'custom', 'initial query')
            assert(measured['search.rows'] == scans + 2, 'Old queries must be evicted')
        ''')

    def test_loaded_criteria_invalidate_search_without_changing_completion_counts(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local m = P.Build()
            local done,total,unknown = P.Count(m, 'custom')
            assert(#P.Rows(m, 'custom', 'saved criterion') == 0)
            local row = m.byKey['custom:first']
            local version = m.criteriaVersion
            P.Criteria(row)
            assert(m.criteriaVersion == version + 1)
            assert(#P.Rows(m, 'custom', 'saved criterion') == 1)
            P.Criteria(row)
            assert(m.criteriaVersion == version + 1)
            local nextDone,nextTotal,nextUnknown = P.Count(m, 'custom')
            assert(done == nextDone and total == nextTotal and unknown == nextUnknown)
        ''')

    def test_recent_and_summary_results_cannot_mutate_cached_aggregates(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local m = P.Build()
            local first = P.Summary(m)
            first.custom.completed = 999
            first.custom.recent[1] = nil
            first.categories[1].name = 'changed by caller'
            first.categories[1].completed = 999
            local nextSummary = P.Summary(m)
            assert(nextSummary.custom.completed == 1 and #nextSummary.custom.recent == 1)
            assert(nextSummary.categories[1].name ~= 'changed by caller')
            assert(nextSummary.categories[1].completed ~= 999)
            local limited = P.Recent(m, 'custom', 0)
            assert(#limited == 0 and #P.Recent(m, 'custom') == 1)
            local recent = P.Recent(m, 'custom')
            recent[1] = nil
            assert(#P.Recent(m, 'custom') == 1)
        ''')

    def test_data_rebuild_preserves_live_completion_and_loaded_search_stays_snapshot_local(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local original = P.Build()
            P.Criteria(original.byKey['custom:first'])
            saved.done.second = 1740000000
            local refreshed = P.Build(nil, original.native)
            assert(P.Count(original, 'custom') == 1)
            assert(P.Count(refreshed, 'custom') == 2)
            assert(#P.Rows(original, 'custom', 'saved criterion') == 1)
            assert(#P.Rows(refreshed, 'custom', 'saved criterion') == 0)
        ''')

    def test_handmade_models_and_explicit_invalidation_remain_mutable(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local m = P.Build()
            m.records = { {key='custom:manual',source='custom',category='general',completed=nil,name='Manual'} }
            local done,total,unknown = P.Count(m, 'summary')
            assert(done == 0 and total == 1 and unknown == 1)
            m.records[1].completed = true
            assert(P.Count(m, 'summary') == 1)
            local original = P.Build()
            original.byKey['custom:second'].completed = true
            P.Invalidate(original)
            assert(P.Count(original, 'custom') == 2)
        ''')

    def test_native_overlapping_categories_share_one_attempt_budget(self):
        self.h.execute('''
            local A = ns.LegacyAdapter
            A.MAX_CATEGORIES, A.MAX_RECORDS = 8, 40
            GetCategoryList = function() return {1,2,3,4,5,6,7,8} end
            GetCategoryInfo = function() return 'General', -1 end
            GetCategoryNumAchievements = function() return 40,0,40 end
            local attempts = 0
            GetAchievementInfo = function()
                attempts = attempts + 1
                return 999, 'Duplicated native', 0, false, nil,nil,nil,'Actual description',0,237387,''
            end
            local catalog = A.Catalog()
            assert(attempts == A.MAX_RECORDS and catalog.attemptedRecords == attempts)
            assert(#catalog.records == 1 and #catalog.duplicates == 39 and catalog.partial)
            local row = catalog.records[1]
            assert(row.source == 'legacy' and row.scopeType == 'character' and row.completed == false)
            assert(row.pointValue == 0 and row.pointType == 'none' and row.achievementType == 'standard')
            assert(measured['native.info_attempts'] == attempts and #calls == 0)
        ''')

    def test_native_classification_reads_shared_missing_ancestry_once_per_snapshot(self):
        self.h.execute('''
            local A = ns.LegacyAdapter
            GetCategoryList = function() return {1} end
            local metadataReads = 0
            GetCategoryInfo = function(id)
                metadataReads = metadataReads + 1
                return 'General', id + 1
            end
            GetCategoryNumAchievements = function() return A.MAX_RECORDS,0,A.MAX_RECORDS end
            GetAchievementInfo = function(category,index)
                return 1000+index, 'Native '..index, 0, false, nil,nil,nil,'Description',0,237387,''
            end
            local catalog = A.Catalog()
            assert(#catalog.records == 2500 and catalog.attemptedRecords == 2500)
            assert(metadataReads == A.MAX_CATEGORY_DEPTH,
                'Shared incomplete ancestry must not repeat its bounded walk per record')
            for _, row in ipairs(catalog.records) do
                assert(row.achievementType == 'unknown' and row.pointType == 'none')
                assert(row.pointValue == 0 and row.scopeType == 'character' and row.completed == false)
            end
            metadataReads = 0
            GetCategoryInfo = function(id)
                metadataReads = metadataReads + 1
                return 'General', id == 1 and 2 or -1
            end
            local refreshed = A.Catalog()
            assert(refreshed.records[1].achievementType == 'standard' and metadataReads == 2,
                'Unknown evidence must not persist into a later native snapshot')
        ''')

    def test_native_provider_missing_category_metadata_is_snapshot_cached(self):
        self.h.execute('''
            local A = ns.LegacyAdapter
            GetCategoryList = nil
            local metadataReads, categoryReads = 0, 0
            GetCategoryInfo = function() metadataReads = metadataReads + 1; return nil end
            GetAchievementCategory = function() categoryReads = categoryReads + 1; return 7 end
            GetAchievementInfo = function(id)
                return id, 'Native '..id, 0, false, nil,nil,nil,'Description',0,237387,''
            end
            local page = {DetailPane={ScrollBox={GetDataProvider=function()
                return {GetCollection=function() return {{id=888},{id=889},{id=890},{id=891}} end}
            end}}}
            local catalog = A.Catalog(page)
            assert(#catalog.records == 4 and catalog.partial and categoryReads == 4)
            assert(metadataReads == 1, 'Mapping and classification share unavailable metadata')
            assert(catalog.records[1].achievementType == 'unknown')
            GetCategoryInfo = function() return 'General', -1 end
            local refreshed = A.Catalog(page)
            assert(refreshed.records[1].achievementType == 'standard')
            assert(refreshed.records[1].category == 'legacy-category:7')
        ''')

    def test_distinct_provider_categories_share_one_metadata_attempt_budget(self):
        self.h.execute('''
            local A = ns.LegacyAdapter
            GetCategoryList = nil
            local metadataReads = 0
            GetCategoryInfo = function(id)
                metadataReads = metadataReads + 1
                -- Every lookup supplies another ancestor, including unique
                -- provider categories encountered after the shared API cap.
                return 'General', id + 1
            end
            GetAchievementCategory = function(id) return id * 100 end
            GetAchievementInfo = function(id)
                return id, 'Native '..id, 0, false, nil,nil,nil,'Description',0,237387,''
            end
            local collection = {}
            for i = 1, A.MAX_RECORDS do collection[i] = {id=100000+i} end
            local page = {DetailPane={ScrollBox={GetDataProvider=function()
                return {GetCollection=function() return collection end}
            end}}}
            local catalog = A.Catalog(page)
            assert(#catalog.records == 2500 and catalog.attemptedRecords == 2500)
            assert(metadataReads == A.MAX_CATEGORIES and catalog.attemptedCategories == metadataReads)
            assert(catalog.partial and catalog.records[2500].achievementType == 'unknown')
            assert(catalog.records[2500].scopeType == 'character' and catalog.records[2500].pointValue == 0)
            assert(measured['native.category_attempts'] == metadataReads and #calls == 0)
        ''')

    def test_off_catalog_resolve_caches_success_and_unavailable_until_data_refresh(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local model = P.Build()
            local reads = 0
            ns.LegacyAdapter.Resolve = function(id)
                reads = reads + 1
                if id == 888 then return {key='legacy:888',id=id,completed=false,pointValue=0} end
            end
            local resolved = P.Resolve(model, 'legacy:888')
            for i = 1, 50 do
                assert(P.Resolve(model, 'legacy:888') == resolved)
                assert(P.Resolve(model, 'legacy:889') == nil)
            end
            assert(reads == 2 and resolved.completed == false and resolved.pointValue == 0)
            assert(P.Resolve(model, 'custom:missing') == nil and reads == 2)
            local refreshed = P.Build(nil, model.native)
            P.Resolve(refreshed, 'legacy:889')
            assert(reads == 3)
            P.Invalidate(model)
            P.Resolve(model, 'legacy:889')
            assert(reads == 4)
        ''')

    def test_off_catalog_resolution_cache_is_bounded(self):
        self.h.execute('''
            local P = ns.LegacyPresentation
            local model = P.Build()
            local reads = 0
            ns.LegacyAdapter.Resolve = function() reads = reads + 1; return nil end
            for i = 1, 300 do P.Resolve(model, 'legacy:'..(100000+i)) end
            assert(#model._resolvedOrder == 256)
            P.Resolve(model, 'legacy:100300')
            assert(reads == 300)
            P.Resolve(model, 'legacy:100001')
            assert(reads == 301 and #model._resolvedOrder == 256)
        ''')

    def test_unavailable_reads_and_provider_fallback_cannot_exceed_global_attempt_budget(self):
        self.h.execute('''
            local A = ns.LegacyAdapter
            A.MAX_RECORDS = 25
            GetCategoryList = function() return {1,2,3} end
            GetCategoryInfo = function() return 'General', -1 end
            GetCategoryNumAchievements = function() return 20,0,20 end
            local attempts = 0
            GetAchievementInfo = function() attempts = attempts + 1; return nil end
            local page = {DetailPane={ScrollBox={GetDataProvider=function()
                return {GetCollection=function() return {{id=888},{id=889}} end}
            end}}}
            local catalog = A.Catalog(page)
            assert(attempts == 25 and catalog.attemptedRecords == 25)
            assert(#catalog.records == 0 and catalog.partial and #calls == 0)
        ''')


if __name__ == '__main__':
    unittest.main()
