#!/usr/bin/env python3
"""Generate addon-owned presentation templates from the supplied Wrath XML.

No community implementation is used. Run from any directory; output is committed
and needs no Python at runtime. Reference files are never written by this tool.
"""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
URI = 'http://www.blizzard.com/wow/ui/'
ET.register_namespace('', URI)
def tag(name): return '{' + URI + '}' + name
source = ET.parse(ROOT / 'References/WrathAchievementUI/Blizzard_AchievementUI.xml').getroot()
out = ET.Element(tag('Ui'))
mapping = {
    'AchievementFrameSummaryCategoryTemplate': 'FAWrathSummaryBarTemplate',
    'AchievementCheckButtonTemplate': 'FAWrathTrackTemplate',
    'AchievementFrameTabButtonTemplate': 'FAWrathTabTemplate',
    'MetaCriteriaTemplate': 'FAWrathMetaTemplate',
    'AchievementProgressBarTemplate': 'FAWrathProgressTemplate',
    'AchievementCategoryTemplate': 'FAWrathCategoryTemplate',
    'AchievementIconFrameTemplate': 'FAWrathIconTemplate',
    'AchievementCriteriaTemplate': 'FAWrathCriterionTemplate',
    'AchievementTemplate': 'FAWrathCardTemplate',
    'StatTemplate': 'FAWrathStatTemplate',
}
loads = {
    'FAWrathSummaryBarTemplate': 'SummaryBarOnLoad',
    'FAWrathTabTemplate': 'TabOnLoad',
    'FAWrathMetaTemplate': 'MetaOnLoad',
    'FAWrathProgressTemplate': 'ProgressOnLoad',
    'FAWrathCategoryTemplate': 'CategoryOnLoad',
    'FAWrathIconTemplate': 'IconOnLoad',
    'FAWrathCriterionTemplate': 'CriterionOnLoad',
    'FAWrathCardTemplate': 'CardOnLoad',
    'FAWrathStatTemplate': 'StatOnLoad',
}
def scripts(e, handlers):
    s = ET.SubElement(e, tag('Scripts'))
    for event, handler in handlers.items():
        ET.SubElement(s, tag(event)).text = 'ForeverAchievementsWrathUI.' + handler + '(self);'
def adapt(e):
    for node in e.iter():
        for key, value in list(node.attrib.items()):
            if key in ('name', 'inherits', 'relativeTo'):
                node.set(key, mapping.get(value, value))
        if node.get('inherits') == 'TooltipBorderBackdropTemplate': node.set('inherits', 'BackdropTemplate')
        # These fonts belong to the original load-on-demand UI. Define our own
        # equivalents so loading its globals/backend is unnecessary.
        if node.get('inherits', '').startswith('Achievement'):
            node.set('inherits', 'FAWrath' + node.get('inherits'))
        if node.get('inherits') in ('GameFontNormalLeftBottom', 'GameFontHighlightLeft', 'GameFontHighlightRight'):
            style = node.get('inherits')
            node.set('inherits', 'GameFontNormal' if 'Normal' in style else 'GameFontHighlight')
            node.set('justifyH', 'RIGHT' if 'Right' in style else 'LEFT')
            if 'Bottom' in style: node.set('justifyV', 'BOTTOM')
        if node.get('style') == 'GameFontHighlightLeft':
            node.set('style', 'GameFontHighlight')
        for child in list(node):
            if child.tag == tag('Scripts'): node.remove(child)
    return e
for original, renamed in mapping.items():
    e = adapt(deepcopy(next(n for n in source if n.get('name') == original)))
    handlers = {'OnLoad': loads[renamed]} if renamed in loads else {}
    if renamed == 'FAWrathCardTemplate':
        handlers.update(OnClick='CardClick', OnEnter='CardEnter', OnLeave='CardLeave')
        shield = e.find("./" + tag('Frames') + '/' + tag('Frame') + "[@name='$parentShield']")
        scripts(shield, {'OnLoad': 'ShieldOnLoad'})
    elif renamed == 'FAWrathCategoryTemplate': handlers['OnClick'] = 'CategoryClick'
    elif renamed == 'FAWrathTrackTemplate': handlers['OnClick'] = 'TrackClick'
    elif renamed == 'FAWrathMetaTemplate': handlers['OnClick'] = 'MetaClick'
    elif renamed == 'FAWrathTabTemplate': handlers['OnClick'] = 'TabClick'
    if handlers: scripts(e, handlers)
    if renamed == 'FAWrathSummaryBarTemplate':
        button = e.find('./' + tag('Frames') + '/' + tag('Button'))
        scripts(button, {'OnClick': 'SummaryClick'})
    out.append(e)

# Port the actual original metal/wood/parchment body and roof. Backend-specific
# scroll frames, comparison panel, global dropdown and close button are omitted.
original = next(n for n in source if n.get('name') == 'AchievementFrame')
window = ET.SubElement(out, tag('Frame'), {'name': 'FAWrathWindowTemplate', 'virtual': 'true', 'enableMouse': 'true'})
window.append(deepcopy(original.find(tag('Size'))))
window.append(deepcopy(original.find(tag('Layers'))))
frames = ET.SubElement(window, tag('Frames'))
header = deepcopy(original.find('./' + tag('Frames') + '/' + tag('Frame') + "[@name='$parentHeader']"))
for node in header.iter():
    if 'relativeTo' in node.attrib:
        node.set('relativeTo', node.get('relativeTo').replace('AchievementFrame', 'FAWrathAchievementFrame'))
frames.append(header)

# Namespaced fonts use standard game font objects, and original Wrath heights.
for name, height in [('AchievementCriteriaFont', 12), ('AchievementDateFont', 12),
                     ('AchievementDescriptionFont', 12), ('AchievementPointsFont', 20)]:
    font = ET.Element(tag('Font'), {'name': 'FAWrath' + name, 'inherits': 'GameFontHighlight', 'virtual': 'true'})
    ET.SubElement(font, tag('FontHeight')).append(ET.Element(tag('AbsValue'), {'val': str(height)}))
    if name == 'AchievementDateFont':
        ET.SubElement(font, tag('Color'), {'r': '1', 'g': '.82', 'b': '0'})
    out.insert(0, font)

ET.indent(out, space='  ')
dest = ROOT / 'ForeverAchievements/UI/WrathAchievementUI.xml'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text('<!-- Adapted from the unmodified files in References/WrathAchievementUI.\n'
                '     Generated by tools/adapt_wrath_templates.py; native backend scripts excluded. -->\n'
                + ET.tostring(out, encoding='unicode') + '\n')
print('Generated', dest.relative_to(ROOT))
