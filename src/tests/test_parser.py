from ast import parse
from src.parser import CfgParser
from collections import OrderedDict

cfg_one_header_one_attribute = [
  'WeaponData\n',
  '{\n',
  '\t"attribute"\t"value"\n',
  '}\n'
]

parsed_cfg_one_header_one_attribute = OrderedDict([
  ('WeaponData', OrderedDict([
    ('attribute', 'value')
  ]))
])



cfg_nested_headers_with_siblings = [
  '"OuterHeader"\n',
  '{\n',
  '\t// This is a comment\n',
  '\tInnerHeader1\n',
  '\t{\n',
  '\t\t"attribute1"\t"value1"\n',
  '\t\t"attribute2"\t"value2"\n',
  '\t}\n',
  '\tInnerHeader2\n',
  '\t{\n',
  '\t\t"attribute3"\t"value3"\n',
  '\t\t"attribute4"\t"value4"\n',
  '\t}\n',
  '}\n'
]

parsed_cfg_nested_headers_with_siblings = OrderedDict([
  ('"OuterHeader"', OrderedDict([
    ('#comment_0', 'This is a comment'),
    ('InnerHeader1', OrderedDict([
      ('attribute1', 'value1'),
      ('attribute2', 'value2')
    ])),
    ('InnerHeader2', OrderedDict([
      ('attribute3', 'value3'),
      ('attribute4', 'value4')
    ]))
  ]))
])



cfg_weird_formatting = [
  "OuterHeader\n",
  "\t\t\t\t\t\t\t\t\t{",
  "         //            \t  Comment",
  " \t     InnerHeader1      {\n",
  " \t\t \"attribute1    \t\"   \t\t \"  \tvalue1 \" \t\t\t\n",
  "      }\n",
  " \t\"InnerHeader2\"\n",
  " \t\t\t\t { \t\n",
  " \"attribute2\"     \"value2\"\n",
  "  }     \n",
  "}\n"
]

parsed_cfg_weird_formatting = OrderedDict([
  ('OuterHeader', OrderedDict([
    ('#comment_0', 'Comment'),
    ('InnerHeader1', OrderedDict([
      ('attribute1', 'value1'),
    ])),
    ('"InnerHeader2"', OrderedDict([
      ('attribute2', 'value2'),
    ]))
  ]))
])

cfg_weird_formatting_reconstructed = [
  'OuterHeader\n',
  '{\n',
  '\t// Comment\n',
  '\tInnerHeader1\n',
  '\t{\n',
  '\t\t"attribute1"\t"value1"\n',
  '\t}\n',
  '\t"InnerHeader2"\n',
  '\t{\n',
  '\t\t"attribute2"\t"value2"\n',
  '\t}\n',
  '}\n'
]

cfg_invalid_1 = ['', '\n']
cfg_invalid_2 = ['abc', 'def', 'ghi']
cfg_invalid_3 = [
  'Header {} {}{}{}}{',
  'Header {',
  '`attribute`: `value`',
  'data: {{',
  'data: [',
  '}}]'
]
cfg_invalid_4 = [
  'Header2: {',
  'Header3: {',
  'Header4: {',
  'Header5: {',
  'Header6: {',
  'Header7: {',
  'Header8: {',
  'invalid: attribute',
  '}',
  '}',
  '}',
  '}',
  '}',
  '}',
  '}'
]


cfg_full = '''WeaponData
    {
    // Attributes Base.
    "printname"	"#TF_Weapon_Bat"
    "BuiltRightHanded"	"0"
    "MeleeWeapon"	"1"
    "weight"	"1"
    "WeaponType"	"melee"
    "ITEM_FLAG_NOITEMPICKUP"	"1"
    "HasTeamSkins_Viewmodel"	"1"

    // Attributes TF.
    "Damage"	"35"
    "TimeFireDelay"	"0.5"
    "TimeIdle"	"5.0"

    // Ammo & Clip
    "primary_ammo"	"None"
    "secondary_ammo"	"None"

    // Buckets.
    "bucket"	"2"
    "bucket_position"	"0"

    // Model & Animation.
    "anim_prefix"	"bat"

    // Sounds for the weapon. There is a max of 16 sounds per category (i.e. max 16 "single_shot" sounds)
    SoundData
    {
      "melee_miss"	"Weapon_Bat.Miss"
      "melee_hit"	"Weapon_Bat.HitFlesh"
      "melee_hit_world"	"Weapon_Bat.HitWorld"
      "burst"	"Weapon_Bat.MissCrit"
    }

    // Weapon Sprite data is loaded by the Client DLL.
    TextureData
    {
      "weapon"
      {
        "file"	"sprites/bucket_bat_red"
        "x"	"0"
        "y"	"0"
        "width"	"200"
        "height"	"128"
      }
      "weapon_s"
      {
        "file"	"sprites/bucket_bat_blue"
        "x"	"0"
        "y"	"0"
        "width"	"200"
        "height"	"128"
      }
      "ammo"
      {
        "file"	"sprites/a_icons1"
        "x"	"55"
        "y"	"60"
        "width"	"73"
        "height"	"15"
      }
      "crosshair"
      {
        "file"	"vgui/replay/thumbnails/crosshair1OL"
        "x"	"0"
        "y"	"0"
        "width"	"64"
        "height"	"64"
      }
      "autoaim"
      {
        "file"	"sprites/crosshairs"
        "x"	"0"
        "y"	"48"
        "width"	"24"
        "height"	"24"
      }
    }
  }
'''.split('\n')
cfg_full = [line.strip() for line in cfg_full if line]

parsed_cfg_full = OrderedDict([
  ("WeaponData", OrderedDict([
    ("#comment_0", "Attributes Base."),

    ("printname", "#TF_Weapon_Bat"),
    ("BuiltRightHanded", "0"),
    ("MeleeWeapon", "1"),
    ("weight", "1"),
    ("WeaponType", "melee"),
    ("ITEM_FLAG_NOITEMPICKUP", "1"),
    ("HasTeamSkins_Viewmodel", "1"),

    ("#comment_1", "Attributes TF."),

    ("Damage", "35"),
    ("TimeFireDelay", "0.5"),
    ("TimeIdle", "5.0"),

    ("#comment_2", "Ammo & Clip"),

    ("primary_ammo", "None"),
    ("secondary_ammo", "None"),

    ("#comment_3", "Buckets."),

    ("bucket", "2"),
    ("bucket_position", "0"),

    ("#comment_4", "Model & Animation."),

    ("anim_prefix", "bat"),

    ("#comment_5", "Sounds for the weapon. There is a max of 16 sounds per category (i.e. max 16 \"single_shot\" sounds)"),

    ("SoundData", OrderedDict([
      ("melee_miss", "Weapon_Bat.Miss"),
      ("melee_hit", "Weapon_Bat.HitFlesh"),
      ("melee_hit_world", "Weapon_Bat.HitWorld"),
      ("burst", "Weapon_Bat.MissCrit")
    ])),

    ("#comment_6", "Weapon Sprite data is loaded by the Client DLL."),

    ("TextureData", OrderedDict([
      ("\"weapon\"", OrderedDict([
        ("file", "sprites/bucket_bat_red"),
        ("x", "0"),
        ("y", "0"),
        ("width", "200"),
        ("height", "128")
      ])),

      ("\"weapon_s\"", OrderedDict([
        ("file", "sprites/bucket_bat_blue"),
        ("x", "0"),
        ("y", "0"),
        ("width", "200"),
        ("height", "128")
      ])),

      ("\"ammo\"", OrderedDict([
        ("file", "sprites/a_icons1"),
        ("x", "55"),
        ("y", "60"),
        ("width", "73"),
        ("height", "15")
      ])),

      ("\"crosshair\"", OrderedDict([
        ("file", "vgui/replay/thumbnails/crosshair1OL"),
        ("x", "0"),
        ("y", "0"),
        ("width", "64"),
        ("height", "64")
      ])),

      ("\"autoaim\"", OrderedDict([
        ("file", "sprites/crosshairs"),
        ("x", "0"),
        ("y", "48"),
        ("width", "24"),
        ("height", "24")
      ]))
    ]))
  ]))
])


parser = CfgParser()

class TestParseCfg:
  def test_parse_one_header_one_attribute(self):
    output = parser.parse_cfg(cfg_one_header_one_attribute)
    assert output == parsed_cfg_one_header_one_attribute

  def test_parse_nested_headers_with_siblings(self):
    output = parser.parse_cfg(cfg_nested_headers_with_siblings)
    assert output == parsed_cfg_nested_headers_with_siblings

  def test_parse_weird_formatting(self):
    output = parser.parse_cfg(cfg_weird_formatting)
    assert output == parsed_cfg_weird_formatting

  def test_parse_invalid_cfgs(self):
    '''Make sure that parsing invalid configs does not throw an error'''
    parser.parse_cfg(cfg_invalid_1)
    parser.parse_cfg(cfg_invalid_2)
    parser.parse_cfg(cfg_invalid_3)
    parser.parse_cfg(cfg_invalid_4)

  def test_parse_full_cfg(self):
    output = parser.parse_cfg(cfg_full)
    assert output == parsed_cfg_full


class TestReconstructCfg:
  def test_reconstruct_one_header_one_attribute(self):
    output = parser.reconstruct_cfg(parsed_cfg_one_header_one_attribute)
    assert output == cfg_one_header_one_attribute

  def test_reconstruct_nested_headers_with_siblings(self):
    output = parser.reconstruct_cfg(parsed_cfg_nested_headers_with_siblings)
    assert output == cfg_nested_headers_with_siblings

  def test_reconstruct_weird_formatting(self):
    output = parser.reconstruct_cfg(parsed_cfg_weird_formatting)
    assert output == cfg_weird_formatting_reconstructed

  def test_reconstruct_full_cfg(self):
    output = parser.reconstruct_cfg(parsed_cfg_full)

    assert [x.strip() for x in output] == cfg_full
