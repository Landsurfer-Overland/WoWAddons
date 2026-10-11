"""Header totals from the production character proof/catalog/model pipeline.

An unknown progress quantity is distinct from an unverified saved completion.
The UI must retain that distinction instead of fabricating a definitive total.
These fixtures do not identify a particular live player's unavailable record.
"""
import unittest

from test_progression_addendum import CoreHarness


SETUP = r'''
SelectAchievements("explore855", "explore802", "exploreEK", "exploreKal", "worldexplorer")
testZone="Elwynn Forest"; testSubzone="Goldshire"
C_Map.GetBestMapForUnit=function() return testZone=="Moonglade" and 1450 or 1429 end
C_Map.GetMapInfo=function(id)
    if id==1450 then return {mapID=id,name="Moonglade"} end
    if id==1429 then return {mapID=id,name="Elwynn Forest"} end
end
C_MapExplorationInfo={GetExploredMapTextures=function(id)
    assert(id==1450)
    return {{offsetX=244,offsetY=89,textureWidth=512,textureHeight=512,isShownByMouseOver=false}}
end}
local records={}
for _,key in ipairs({"explore855", "explore802", "exploreEK", "exploreKal", "worldexplorer"}) do
    records[#records+1]=ns.FA.BY_KEY[key]
end
ns.FA.CATEGORIES={{key="exploration",label="Exploration"}}
ns.FA.CATEGORY_ORDER={"exploration"}
ns.FA.CATEGORY_SECTIONS={exploration={{title="KALIMDOR",list=records}}}
-- Make the client date formatter expose the actual timestamp it receives.
function date(format,timestamp) assert(format=="%m/%d/%y"); return "date:"..timestamp end
nativeCatalog={categories={},records={},byKey={},available=true,partial=false,points=16}
GameFontNormal={name="normal"}; GameFontNormalSmall={name="small"}
GameFontHighlight={name="highlight"}
host=CreateFrame("Frame","Iteration6HeaderBindingHost"); host:SetSize(960,760)
function headerGuard(fn) fn() end
view=ns.WrathAchievementUI.Create(host,headerGuard,function() error("Unexpected data refresh") end,{})
function BindHeader()
    local model=ns.LegacyPresentation.Build(nil,nativeCatalog)
    view:SetModel(model)
    return model,model.custom.byKey["custom:explore855"]
end
'''


class Iteration6HeaderBindingTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute(SETUP)
        # Reload the adapter after the production core replaces the fixture FA.
        self.h.load("Integrations/CustomAdapter.lua")

    def test_unknown_live_progress_without_saved_completion_keeps_known_zero(self):
        self.h.execute(r'''
            local model,row=BindHeader()
            assert(row.current==nil and row.completed==false and row.timestamp==nil)
            assert(model.custom.points==0 and model.custom.pointsAvailable==true)
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=="0")
            assert(FAWrathAchievementFrameHeaderLegacyPoints:GetText()=="16")
            local lowerBound,_,_,_,known=ns.FA.TotalPoints()
            assert(lowerBound==0 and known==true)
            assert(saved.done.explore855==nil and saved.done.first==1730000000)
            assert(saved.history[1]=="keep" and #calls==0)
        ''')

    def test_retained_unverified_moonglade_history_makes_definitive_total_unavailable(self):
        self.h.execute(r'''
            saved.done.explore855=123456
            local originalDone,originalHistory=saved.done,saved.history
            local model,row=BindHeader()
            assert(row.completed==nil and row.timestamp==nil and row.historicalTimestamp==123456)
            assert(row.completionVerificationReason=="Historical exploration completion retained; character discovery is unverified")
            assert(model.custom.points==nil and model.custom.pointsAvailable==false)
            assert(model.custom.confirmedPoints==0 and model.custom.unverifiedPointRecords==1)
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=="0+")
            assert(FAWrathAchievementFrameHeaderLegacyPoints:GetText()=="16")
            local lowerBound,_,_,_,known=ns.FA.TotalPoints()
            assert(lowerBound==0 and known==false)
            view:Render(); view:SetModel(model)
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=="0+")
            assert(saved.done==originalDone and saved.history==originalHistory)
            assert(saved.done.explore855==123456 and saved.done.first==1730000000)
            assert(saved.history[1]=="keep" and #calls==0)
        ''')

    def test_positive_character_evidence_recovers_actual_points_and_original_date(self):
        self.h.execute(r'''
            saved.done.explore855=1730000321
            local originalDone=saved.done
            local unavailable=BindHeader()
            assert(unavailable.custom.points==nil)
            testZone="Moonglade"; testSubzone="Nighthaven"
            local model,row=BindHeader()
            assert(row.completed==true and row.timestamp==1730000321)
            assert(row.date=="date:1730000321" and row.pointValue==ns.FA.BY_KEY.explore855.pts)
            assert(model.custom.points==10 and model.custom.pointsAvailable==true)
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=="10")
            assert(FAWrathAchievementFrameHeaderLegacyPoints:GetText()=="16")
            local lowerBound,_,_,_,known=ns.FA.TotalPoints()
            assert(lowerBound==10 and known==true)
            testZone="Elwynn Forest"; testSubzone="Goldshire"
            C_Map=nil; C_MapExplorationInfo=nil
            model,row=BindHeader()
            assert(row.completed==true and row.date=="date:1730000321" and model.custom.points==10)
            assert(saved.done==originalDone and saved.done.explore855==1730000321)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


if __name__ == "__main__":
    unittest.main()
