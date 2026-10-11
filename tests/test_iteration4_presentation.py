"""Iteration 4 direct category lists and independently proven zone cards."""
import unittest

from test_legacy_wrath_ui import Harness
from test_iteration3_categories import FIXTURES


ZONE_FIXTURES = r'''
function ZonePair(id, label, key)
    key = key or "explore"..id
    local custom=CustomRow(key,"exploration","EASTERN KINGDOMS",nil)
    custom.id=id; custom.name="Explore "..label
    custom.description="Explore "..label..", revealing the covered areas of the world map."
    custom.customGeography="Eastern Kingdoms"
    custom.exploration={kind="zone",zoneID=id,zoneName=label,mapID=id+1000,areas={{"A",1,1}}}
    custom.completedByOtherCharacter=true; custom.completionDetail="Completed by Aldrin"
    local native=NativeRow(id,custom.name,1)
    native.description=custom.description; native.completed=true; native.scopeType="account"
    native.completionScope="native_account"; native.pointValue=1; native.points=1
    native.date="10/10/26"; native.dateSort=20261010
    return custom,native
end
relationReads=0
function GetAchievementNumCriteria(id) relationReads=relationReads+1; return 1 end
function GetAchievementCriteriaInfo(id,index)
    relationReads=relationReads+1
    return "A",43,true,1,1,nil,0,id,"1 / 1",id+100000,true
end
function ZoneCatalog(rows)
    return NativeCatalog({NativeCategory(1,"Eastern Kingdoms",2),NativeCategory(2,"Exploration")},rows)
end
'''


class Iteration4PresentationTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute(FIXTURES + ZONE_FIXTURES)

    def check(self, code):
        self.h.execute(code)

    def test_relationship_sort_excludes_unrelated_rows_but_retains_catalog_and_priority(self):
        self.check('''
            local w,wn=ZonePair(802,'Westfall'); local e,en=ZonePair(776,'Elwynn Forest')
            local moon,mn=ZonePair(855,'Moonglade'); local absent=ZonePair(760,'Alterac Mountains')
            local rows={moon,absent,e,w}
            for i=1,300 do rows[#rows+1]=CustomRow('unrelated'..i,'general','GENERAL',nil) end
            SetCustomRows(rows)
            local sort=table.sort; local candidateSorts=0
            table.sort=function(list,compare)
                if list[1] and list[1].exploration then
                    candidateSorts=candidateSorts+1
                    assert(#list==3)
                    for _,row in ipairs(list) do assert(row.exploration.kind=='zone' and row.exploration.zoneID~=760) end
                end
                return sort(list,compare)
            end
            local model=ns.LegacyPresentation.Build(nil,ZoneCatalog({wn,en,mn}))
            assert(candidateSorts==1 and relationReads==6 and #model.relationships==3)
            assert(model.relationships[1].nativeID==802 and model.relationships[2].nativeID==776 and model.relationships[3].nativeID==855)
            assert(model.byKey[absent.key].source=='custom' and #model.records==304)
            for i=1,300 do assert(model.byKey['custom:unrelated'..i]) end
            assert(#calls==0)
        ''')

    def test_parent_lists_direct_assignments_but_counts_include_descendants(self):
        self.check('''
            local general=CustomRow("prof75","professions","PROFESSIONS","prof")
            local fish=CustomRow("fish75","professions","FISHING","fishing")
            fish.completed=true
            SetCustomRows({general,fish})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            local P=ns.LegacyPresentation
            assert(#P.Rows(m,"professions")==1 and P.Rows(m,"professions")[1].key==general.key)
            assert(#P.Rows(m,"professions:fishing")==1)
            local done,total=P.Count(m,"professions"); assert(done==1 and total==2)
            P.Invalidate(m)
            assert(#P.Rows(m,"professions")==1)
            done,total=P.Count(m,"professions"); assert(done==1 and total==2)
            assert(not m.byCategory["professions:primary"])
        ''')

    def test_broad_reputation_stays_parent_and_faction_rows_remain_children(self):
        self.check('''
            local broad=CustomRow("ex5","reputation","EXALTED","exalted")
            local neutral=CustomRow("repPowderfuse","reputation","FOREVER FACTIONS",nil)
            local alliance=CustomRow("ambAlliance","reputation","HOME CITIES",nil); alliance.faction="Alliance"
            SetCustomRows({broad,neutral,alliance})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(#ns.LegacyPresentation.Rows(m,"reputation")==1)
            assert(m.byKey[broad.key].category=="reputation")
            assert(m.byKey[neutral.key].category=="reputation:other-factions")
            assert(m.byKey[alliance.key].category=="reputation:alliance")
            local _,total=ns.LegacyPresentation.Count(m,"reputation"); assert(total==3)
        ''')

    def test_dungeons_pvp_and_fallback_keep_specific_assignment(self):
        self.check('''
            SetCustomRows({CustomRow("spelunker","dungeons","DUNGEONS",nil),CustomRow("hkill100","pvp","HONORABLE KILLS",nil)})
            local n=NativeRow(77777,"Unmapped",3); n.achievementType="standard"
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(3,"Unknown")},{n}))
            assert(#ns.LegacyPresentation.Rows(m,"dungeons")==0)
            assert(#ns.LegacyPresentation.Rows(m,"dungeons:dungeons")==1)
            assert(#ns.LegacyPresentation.Rows(m,"pvp")==0)
            assert(#ns.LegacyPresentation.Rows(m,"pvp:honorable-kills")==1)
            assert(#ns.LegacyPresentation.Rows(m,"feats")==0)
            assert(m.byKey[n.key].achievementType=="standard" and m.unmappedIDs[1]==77777)
        ''')

    def test_extra_supported_profession_uses_actual_native_subject(self):
        self.check('''
            SetCustomRows({})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(1,"Jewelcrafting",2),NativeCategory(2,"Tradeskills")},{NativeRow(990,"Gem Cutter",1)}))
            assert(m.byKey['legacy:990'].category=='professions:skill-jewelcrafting')
            assert(#ns.LegacyPresentation.Rows(m,'professions')==0)
        ''')

    def test_playable_class_api_allows_extra_class_and_rejects_metadata_only_class(self):
        self.check('''
            GetNumClasses=function() return 3 end
            GetClassInfo=function(id)
                if id==1 then return 'Warrior','WARRIOR',1 elseif id==2 then return 'Traveler','TRAVELER',14 end
                return 'Evoker','EVOKER',13
            end
            C_GameRules={IsClassAllowedForGameMode=function(id) return id~=13 end}
            local a=CustomRow('traveler60','classes','CLASSES',nil); a.classToken='TRAVELER'
            SetCustomRows({a})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(m.byCategory['classes:warrior'] and m.byCategory['classes:traveler'])
            assert(not m.byCategory['classes:evoker'])
            assert(m.byKey[a.key].category=='classes:traveler')
            assert(#ns.LegacyPresentation.Rows(m,'classes')==0)
        ''')

    def test_class_metadata_without_game_mode_proof_needs_reference_or_actual_class(self):
        self.check('''
            GetNumClasses=function() return 2 end
            GetClassInfo=function(id) return id==1 and 'Warrior' or 'Evoker',id==1 and 'WARRIOR' or 'EVOKER',id==1 and 1 or 13 end
            ns.FOREVER_ACH={{title='CLASSES',list={{ids={61499},group='Warrior',name='Novice Warrior'}}}}
            SetCustomRows({})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(m.byCategory['classes:warrior'] and not m.byCategory['classes:evoker'])
        ''')

    def test_exact_native_class_definition_is_mapped_out_of_mixed_category(self):
        self.check('''
            ns.FOREVER_ACH={{title='CLASSES',list={{ids={61499},group='Warrior',name='Novice Warrior'}}}}
            SetCustomRows({})
            local n=NativeRow(61499,'Novice Warrior',1)
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(1,'Adventure')},{n}))
            assert(m.byKey[n.key].category=='classes:warrior' and #m.unmappedIDs==0)
            n.name='Different reused ID'
            m=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(1,'Adventure')},{n}))
            assert(m.byKey[n.key].category=='feats:other-legacy')
        ''')

    def test_equivalent_zone_uses_one_card_and_keeps_both_original_keys(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n}))
            local card=m.byKey[c.key]
            assert(#m.records==1 and #ns.LegacyPresentation.Rows(m,'exploration:eastern-kingdoms')==1)
            assert(card==m.byKey[n.key] and card.source=='combined')
            assert(card.completed==false and card.pointValue==10 and card.pointType=='character')
            assert(card.character.completed==false and card.native.completed==true and card.native.pointValue==1)
            assert(card.completedByOtherCharacter and card.completionDetail=='Completed by Aldrin')
            assert(ns.LegacyPresentation.SourceRecord(m,n.key)==card.native and card.native.id==802)
            assert(n.source=='legacy' and n.category=='legacy-category:1' and c.source=='custom')
            assert(saved.done.first==1730000000 and saved.history[1]=='keep')
        ''')

    def test_combined_source_counts_points_and_recents_are_independent(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n}))
            local P=ns.LegacyPresentation
            local done,total=P.Count(m,'custom'); assert(done==0 and total==1)
            done,total=P.Count(m,'legacy'); assert(done==1 and total==1)
            done,total=P.Count(m,'exploration'); assert(done==0 and total==1)
            local s=P.Summary(m)
            assert(s.custom.points==0 and s.custom.completed==0 and s.native.points==16 and s.native.completed==1)
            assert(#s.native.recent==1 and s.native.recent[1].source=='legacy' and #s.custom.recent==0)
        ''')

    def test_combined_filter_selection_uses_independent_source_and_state(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n})); local P=ns.LegacyPresentation
            assert(#P.Rows(m,'exploration:eastern-kingdoms','','Character Achievements')==1)
            assert(#P.Rows(m,'exploration:eastern-kingdoms','','Legacy Challenges')==1)
            assert(#P.Rows(m,'exploration:eastern-kingdoms','','Completed')==0)
            assert(#P.Rows(m,'exploration:eastern-kingdoms','','Incomplete')==1)
            assert(#P.Rows(m,'legacy','','Completed')==1 and #P.Rows(m,'custom','','Completed')==0)
            assert(#P.Rows(m,'legacy')==1 and #P.Rows(m,'custom')==1)
            assert(#P.Rows(m,'legacy-category:1')==1)
        ''')

    def test_combined_criteria_are_lazy_independent_sections_and_searchable(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            ns.CustomAchievementAdapter.Criteria=function() return {items={{name='Custom objective',completed=false}},available=true,complete=true,count=1} end
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n})); local card=m.byKey[c.key]
            local reads=relationReads
            assert(not card.criteriaCache and not card.native.criteriaCache)
            assert(#ns.LegacyPresentation.Rows(m,'exploration:eastern-kingdoms','custom objective')==0)
            local data=ns.LegacyPresentation.Criteria(card)
            assert(#data.sections==2 and data.sections[1].record.completed==false and data.sections[2].record.completed==true)
            assert(data.items[1].name=='Custom objective' and data.nativeCriteria.items[1].completed==true)
            assert(#ns.LegacyPresentation.Rows(m,'exploration:eastern-kingdoms','custom objective')==1)
            local after=relationReads
            ns.LegacyPresentation.Criteria(card)
            for i=1,20 do ns.LegacyPresentation.Rows(m,'exploration:eastern-kingdoms','custom objective') end
            assert(relationReads==after and after>reads)
        ''')

    def test_same_title_or_same_id_with_different_requirements_does_not_merge(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            GetAchievementCriteriaInfo=function() return 'Different area',43,false,0,1 end
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n}))
            assert(#m.records==2 and m.byKey[c.key]~=m.byKey[n.key])
            assert(#m.relationshipAudit==1 and m.relationshipAudit[1].reason:find('requirements differ',1,true))
            n.id=998; n.key='legacy:998'
            m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n}))
            assert(#m.records==2 and #m.relationships==0)
        ''')

    def test_wrong_criterion_kind_or_threshold_stays_separate(self):
        self.check('''
            local c,n=ZonePair(855,'Moonglade'); SetCustomRows({c})
            GetAchievementCriteriaInfo=function() return 'A',27,true,1,1 end
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n}))
            assert(#m.records==2)
            GetAchievementCriteriaInfo=function() return 'A',43,true,2,2 end
            m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n}))
            assert(#m.records==2)
        ''')

    def test_requirement_cache_never_copies_current_completion_points_or_native_progress(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            local P=ns.LegacyPresentation
            local first=P.Build(nil,ZoneCatalog({n})); local reads=relationReads
            c.completed=true; c.timestamp=123456; n.completed=false; n.pointValue=7; n.points=7
            local next=P.Build(nil,ZoneCatalog({n})); local card=next.byKey[c.key]
            assert(relationReads==reads and card.completed==true and card.native.completed==false and card.native.pointValue==7)
            assert(first.byKey[c.key].completed==false and first.byKey[c.key].native.completed==true)
        ''')

    def test_positive_proof_cache_includes_build_and_full_authored_requirement_set(self):
        self.check('''
            local build='70338'; GetBuildInfo=function() return '1.60.1',build,'Oct 9 2026',16001 end
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            local P=ns.LegacyPresentation
            assert(#P.Build(nil,ZoneCatalog({n})).relationships==1); local reads=relationReads
            build='70339'
            P.Build(nil,ZoneCatalog({n})); assert(relationReads>reads); reads=relationReads
            c.exploration.areas={{'B',1,1}}
            assert(#P.Build(nil,ZoneCatalog({n})).relationships==0 and relationReads>reads)
        ''')

    def test_global_attempt_budget_prioritizes_reported_zones_and_never_schedules_more_builds(self):
        self.check('''
            local a,an=ZonePair(760,'Alterac Mountains')
            local w,wn=ZonePair(802,'Westfall'); local e,en=ZonePair(776,'Elwynn Forest'); local moon,mn=ZonePair(855,'Moonglade')
            SetCustomRows({a,moon,e,w}); ns.LegacyPresentation.MAX_RELATION_READS=4
            local native=ZoneCatalog({an,wn,en,mn}); local P=ns.LegacyPresentation
            local m=P.Build(nil,native)
            assert(relationReads==4 and #m.relationships==2 and #m.relationshipAudit==2)
            assert(m.byKey[w.key].source=='combined' and m.byKey[e.key].source=='combined')
            assert(m.byKey[moon.key].source=='custom')
            P.Build(nil,native); assert(relationReads==4)
            m=P.Build(nil,ZoneCatalog({an,wn,en,mn}))
            assert(relationReads==8 and #m.relationships==4)
            assert(#calls==0)
        ''')

    def test_failed_requirement_reads_retry_only_on_a_new_native_snapshot(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            GetAchievementNumCriteria=function() relationReads=relationReads+1; return nil end
            local native=ZoneCatalog({n}); local P=ns.LegacyPresentation
            assert(#P.Build(nil,native).relationships==0)
            P.Build(nil,native); assert(relationReads==1)
            GetAchievementNumCriteria=function() relationReads=relationReads+1; return 1 end
            assert(#P.Build(nil,ZoneCatalog({n})).relationships==1 and relationReads==3)
        ''')

    def test_loaded_native_criteria_can_prove_identity_without_extra_api_reads(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            n.criteriaCache={available=true,complete=true,count=1,items={{name='A',type=43,required=1,completed=true}}}
            GetAchievementNumCriteria=function() error('Must reuse loaded definition') end
            GetAchievementCriteriaInfo=GetAchievementNumCriteria
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n}))
            assert(#m.relationships==1 and relationReads==0 and m.byKey[c.key].character.completed==false)
        ''')

    def test_duplicate_catalog_keys_do_not_repeat_combined_cards_or_count_components_twice(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c,c})
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n,n}))
            assert(#m.records==1 and #m.duplicateKeys==2 and #m.relationships==1)
            local _,ct=ns.LegacyPresentation.Count(m,'custom'); local _,nt=ns.LegacyPresentation.Count(m,'legacy')
            assert(ct==1 and nt==1)
        ''')

    def test_unindexed_combined_model_preserves_source_counts_and_native_recents(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            local P=ns.LegacyPresentation; local m=P.Build(nil,ZoneCatalog({n}))
            P.Invalidate(m)
            local done,total=P.Count(m,'custom'); assert(done==0 and total==1)
            done,total=P.Count(m,'legacy'); assert(done==1 and total==1)
            assert(#P.Rows(m,'custom')==1 and #P.Rows(m,'legacy')==1)
            assert(#P.Recent(m,'legacy')==1 and P.Recent(m,'legacy')[1].key==n.key)
            assert(#P.Recent(m,'custom')==0)
        ''')

    def test_current_extra_playable_class_is_supported_without_class_enumeration(self):
        self.check('''
            UnitClass=function() return 'Traveler','TRAVELER',14 end
            GetNumClasses=nil; SetCustomRows({})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(m.byCategory['classes:traveler'])
        ''')

    def test_authoritative_class_denial_is_not_overwritten_by_old_references(self):
        self.check('''
            ns.FOREVER_ACH={{title='CLASSES',list={{ids={61499},group='Warrior',name='Novice Warrior'}}}}
            GetNumClasses=function() return 1 end
            GetClassInfo=function() return 'Warrior','WARRIOR',1 end
            C_GameRules={IsClassAllowedForGameMode=function() return false end}
            SetCustomRows({})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(not m.byCategory['classes:warrior'])
        ''')

    def test_fully_verified_continents_and_world_unify_with_independent_states(self):
        self.check('''
            local e,en=ZonePair(776,'Elwynn Forest'); local k,kn=ZonePair(855,'Moonglade'); k.customGeography='Kalimdor'
            local ek=CustomRow('exploreEK','exploration','AZEROTH',nil); ek.name='Explore Eastern Kingdoms'
            ek.exploration={kind='continent',children={e.key}}; ek.customGeography='Eastern Kingdoms'
            local kal=CustomRow('exploreKal','exploration','AZEROTH',nil); kal.name='Explore Kalimdor'
            kal.exploration={kind='continent',children={k.key}}; kal.customGeography='Kalimdor'
            local world=CustomRow('worldexplorer','exploration','AZEROTH',nil); world.name='World Explorer'
            world.exploration={kind='world',children={ek.key,kal.key}}
            local ne=NativeRow(62353,'Explore Eastern Kingdoms',1); local nk=NativeRow(62355,'Explore Kalimdor',1)
            local nw=NativeRow(62053,'Explore Azeroth',1); nw.completed=true; nw.scopeType='account'
            SetCustomRows({e,k,ek,kal,world})
            local zoneGetter=GetAchievementCriteriaInfo
            GetAchievementNumCriteria=function(id) relationReads=relationReads+1; return id==62053 and 2 or 1 end
            GetAchievementCriteriaInfo=function(id,index)
                local asset=({[62353]=776,[62355]=855})[id]
                if id==62053 then asset=index==1 and 62353 or 62355 end
                if asset then relationReads=relationReads+1; return 'Child',8,true,1,1,nil,0,asset end
                return zoneGetter(id,index)
            end
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({en,kn,ne,nk,nw}))
            assert(#m.relationships==5 and #m.records==5)
            assert(m.byKey[ek.key].source=='combined' and m.byKey[kal.key].source=='combined')
            assert(m.byKey[world.key]==m.byKey[nw.key] and m.byKey[world.key].completed==false and m.byKey[world.key].native.completed==true)
            assert(#ns.LegacyPresentation.Rows(m,'exploration:world')==1)
            local _,ct=ns.LegacyPresentation.Count(m,'custom'); local _,nt=ns.LegacyPresentation.Count(m,'legacy')
            assert(ct==5 and nt==5)
        ''')

    def test_meta_with_different_native_child_set_stays_separate_and_audited(self):
        self.check('''
            local c,n=ZonePair(776,'Elwynn Forest')
            local meta=CustomRow('exploreEK','exploration','AZEROTH',nil); meta.name='Explore Eastern Kingdoms'
            meta.exploration={kind='continent',children={c.key}}
            local nativeMeta=NativeRow(62353,'Explore Eastern Kingdoms',1)
            SetCustomRows({c,meta}); local getter=GetAchievementCriteriaInfo
            GetAchievementCriteriaInfo=function(id,index)
                if id==62353 then return 'Wrong zone',8,true,1,1,nil,0,802 end
                return getter(id,index)
            end
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n,nativeMeta}))
            assert(#m.relationships==1 and m.byKey[meta.key]~=m.byKey[nativeMeta.key])
            assert(#m.relationshipAudit==1 and m.relationshipAudit[1].reason=='Native meta child requirements differ')
        ''')

    def test_meta_does_not_unify_while_any_zone_requirements_are_unverified(self):
        self.check('''
            local c,n=ZonePair(776,'Elwynn Forest')
            local meta=CustomRow('exploreEK','exploration','AZEROTH',nil)
            meta.exploration={kind='continent',children={c.key}}
            local nativeMeta=NativeRow(62353,'Explore Eastern Kingdoms',1)
            SetCustomRows({c,meta}); GetAchievementCriteriaInfo=function() return 'Wrong area',43,true,1,1 end
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({n,nativeMeta}))
            assert(#m.relationships==0 and #m.relationshipAudit==2)
            assert(m.relationshipAudit[2].reason=='All underlying zone requirements are not yet verified')
        ''')

    def test_world_meta_is_not_merged_from_two_continent_titles_alone(self):
        self.check('''
            local c=CustomRow('worldexplorer','exploration','AZEROTH',nil); c.name='World Explorer'
            c.exploration={kind='world',children={'custom:exploreEK','custom:exploreKal'}}
            SetCustomRows({c})
            local n=NativeRow(62053,'Explore Azeroth',1)
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(1,'Explorer')},{n}))
            assert(#ns.LegacyPresentation.Rows(m,'exploration:world')==2)
            assert(#ns.LegacyPresentation.Rows(m,'exploration')==0 and #m.relationships==0)
        ''')


if __name__ == '__main__':
    unittest.main()
