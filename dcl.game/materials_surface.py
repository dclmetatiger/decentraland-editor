# Materials with these keywords get different PBR values on build
# this affects only Metallic and Roughness
# the first array value is the Metallic value, second the Roughness
# for all other Materials, the default settings are used (not shiny)

default_metallic  = 0.0
default_roughness = 1.0

surfacekeywords = {
    
    # Starducks
    "mapobjects/starducks/floaties/donut":                   (0.2, 0.8),        # not so shiny
    "mapobjects/starducks/floaties/donut_chocolate":         (0.2, 0.8),        # not so shiny
    "mapobjects/starducks/floaties/donut_sugar":             (0.2, 0.8),        # not so shiny
    "mapobjects/starducks/floaties/rubberduck":              (0.2, 0.8),        # not so shiny
    "mapobjects/starducks/floaties/rubikcube":               (0.0, 0.5),        # medium
    "mapobjects/starducks/floaties/flamingo":                (0.9, 0.6),        # more shiny
    "mapobjects/starducks/floaties/unicorn":                 (0.9, 0.6),        # more shiny
    "mapobjects/starducks/inflatable/inflatable_chair":      (0.5, 0.5),        # more shiny
    
    # Halloween
    "mapobjects/halloween/frankendonut":                     (0.2, 0.8),        # not so shiny
    "mapobjects/halloween/ghostdonut":                       (0.2, 0.8),        # not so shiny
    "mapobjects/halloween/frankenduck":                      (0.2, 0.8),        # not so shiny
    "mapobjects/halloween/rubikcube":                        (0.0, 0.5),        # medium
    "mapobjects/halloween/flamingo_halloween":               (0.9, 0.6),        # more shiny
    "mapobjects/halloween/unicorn_halloween":                (0.9, 0.6),        # more shiny
    "mapobjects/halloween/gravestone":                       (0.0, 1.0),        # not so shiny
    "mapobjects/halloween/grave10":                          (0.0, 1.0)         # not so shiny
}