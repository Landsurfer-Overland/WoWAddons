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
        # Forever uses the current character/guild two-row shield sheet. The
        # supplied Wrath XML predates the guild row; sampling the entire height
        # stacks both shields. Keep the original single region and player row.
        shield.find('.//' + tag('TexCoords')).set('bottom', '.5')
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
# scroll frames, comparison panel and global dropdown are omitted. The original
# close button is rebound to the reversible controller below.
original = next(n for n in source if n.get('name') == 'AchievementFrame')
window = ET.SubElement(out, tag('Frame'), {'name': 'FAWrathWindowTemplate', 'virtual': 'true',
                                        'enableMouse': 'true', 'inherits': 'BackdropTemplate'})
window.append(deepcopy(original.find(tag('Size'))))
window.append(deepcopy(original.find(tag('Layers'))))
# The original achievement frame uses a 64px tiled wooden backdrop in addition
# to its corner ornaments. Its Lua-owned equivalent restores those missing
# connecting edges. A matching full-page parchment removes the baked dark/light
# split between navigation and content without stretching the ornate roof.
body_layers = window.find(tag('Layers'))
body_background = next(layer for layer in body_layers if layer.get('level') == 'BACKGROUND')
page = ET.SubElement(body_background, tag('Texture'), {
    'name': '$parentPageParchment', 'file': 'Interface\\AchievementFrame\\UI-Achievement-AchievementBackground'})
anchors = ET.SubElement(page, tag('Anchors'))
for point, x, y in [('TOPLEFT', '25', '-23'), ('BOTTOMRIGHT', '-25', '23')]:
    ET.SubElement(ET.SubElement(anchors, tag('Anchor'), {'point': point}), tag('Offset'), {'x': x, 'y': y})
ET.SubElement(page, tag('TexCoords'), {'left': '0', 'right': '1', 'top': '0', 'bottom': '.5'})
category_bg = window.find('.//' + tag('Texture') + "[@name='$parentCategoriesBG']")
category_bg.set('file', 'Interface\\AchievementFrame\\UI-Achievement-AchievementBackground')
ET.SubElement(category_bg, tag('TexCoords'), {'left': '0', 'right': '1', 'top': '0', 'bottom': '.5'})
footer = ET.SubElement(body_background, tag('Texture'), {
    'name': '$parentFooterBacking', 'file': 'Interface\\TutorialFrame\\TutorialFrameBackground'})
anchors = ET.SubElement(footer, tag('Anchors'))
ET.SubElement(ET.SubElement(anchors, tag('Anchor'), {'point': 'TOPLEFT', 'relativePoint': 'BOTTOMLEFT'}),
              tag('Offset'), {'x': '13', 'y': '8'})
ET.SubElement(ET.SubElement(anchors, tag('Anchor'), {'point': 'BOTTOMRIGHT', 'relativePoint': 'BOTTOMRIGHT'}),
              tag('Offset'), {'x': '-13', 'y': '-57'})
frames = ET.SubElement(window, tag('Frames'))
header = deepcopy(original.find('./' + tag('Frames') + '/' + tag('Frame') + "[@name='$parentHeader']"))
for node in header.iter():
    if 'relativeTo' in node.attrib:
        node.set('relativeTo', node.get('relativeTo').replace('AchievementFrame', 'FAWrathAchievementFrame'))
frames.append(header)
header.find(tag('Size') + '/' + tag('AbsDimension')).set('y', '118')

# Two matching Wrath point counters fit within the existing roof. They use the
# original point-border and tiny-shield artwork, not another outer frame.
border = header.find('.//' + tag('Texture') + "[@name='$parentPointBorder']")
border.find(tag('Size') + '/' + tag('AbsDimension')).set('x', '170')
border.find('.//' + tag('Offset')).set('x', '-174')
border.find('.//' + tag('Offset')).set('y', '19')
title = header.find('.//' + tag('FontString') + "[@name='$parentTitle']")
title.find(tag('Size')).set('x', '188')
title.find(tag('Size')).set('y', '18')
title.find('.//' + tag('Offset')).set('y', '11')
title.set('text', 'Achievement Points')
title.set('inherits', 'GameFontNormalLarge')
points = header.find('.//' + tag('FontString') + "[@name='$parentPoints']")
points.set('inherits', 'GameFontHighlightLarge')
points.find(tag('Size')).set('y', '20')
points.find('.//' + tag('Offset')).set('x', '-10')
points.find('.//' + tag('Offset')).set('y', '-10')
for name, replacement in [('PointBorder', 'LegacyPointBorder'), ('Title', 'LegacyTitle'),
                          ('Points', 'LegacyPoints'), ('Shield', 'LegacyShield')]:
    item = deepcopy(header.find('.//*[@name="$parent' + name + '"]'))
    item.set('name', '$parent' + replacement)
    for node in item.iter():
        if 'relativeTo' in node.attrib:
            value = node.get('relativeTo')
            value = value.replace('HeaderPointBorder', 'HeaderLegacyPointBorder')
            if value == '$parentPoints': value = '$parentLegacyPoints'
            node.set('relativeTo', value)
    if name == 'PointBorder': item.find('.//' + tag('Offset')).set('x', '174')
    if name == 'Title':
        item.set('text', 'Legacy Points')
    layer = next(layer for layer in header.find(tag('Layers')) if header.find('.//*[@name="$parent' + name + '"]') in list(layer))
    layer.append(item)

# A neutral, native-size achievement seal anchors the two independent totals.
# The client has separate character/guild rows; use the same player-row crop as
# the achievement cards and avoid enlarging the lower-resolution tiny shield.
artwork = next(layer for layer in header.find(tag('Layers')) if layer.get('level') == 'ARTWORK')
crest = ET.SubElement(artwork, tag('Texture'), {
    'name': '$parentCrest', 'file': 'Interface\\AchievementFrame\\UI-Achievement-Shields-NoPoints'})
ET.SubElement(crest, tag('Size'), {'x': '66', 'y': '64'})
ET.SubElement(ET.SubElement(ET.SubElement(crest, tag('Anchors')), tag('Anchor'), {'point': 'BOTTOM'}),
              tag('Offset'), {'x': '0', 'y': '9'})
ET.SubElement(crest, tag('TexCoords'), {'left': '0', 'right': '.5', 'top': '0', 'bottom': '.5'})

close = deepcopy(original.find('./' + tag('Frames') + '/' + tag('Button') + "[@name='$parentCloseButton']"))
adapt(close)
for node in close.iter():
    if node.get('relativeTo') == 'AchievementFrame': node.set('relativeTo', 'FAWrathAchievementFrame')
scripts(close, {'OnClick': 'CloseClick'})
frames.append(close)

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
