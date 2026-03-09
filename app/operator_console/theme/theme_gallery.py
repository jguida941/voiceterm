"""Extended theme gallery: 88 additional theme seeds for the Operator Console.

Organized by visual family so users can browse by mood or aesthetic.
Each entry is (theme_id, display_name, base_bg, border, accent, accent_soft,
warning, danger, text, text_muted, text_dim).
"""

from __future__ import annotations

from .colors import ThemeSeed

# ── IDE / Editor Classics ──────────────────────────────────────────────

_IDE_SEEDS = (
    ("vscode_dark", "VS Code Dark", "#1e1e1e", "#3c3c3c", "#007acc", "#4ec9b0", "#cca700", "#f14c4c", "#d4d4d4", "#9d9d9d", "#6a6a6a"),
    ("monokai", "Monokai", "#272822", "#75715e", "#a6e22e", "#66d9ef", "#e6db74", "#f92672", "#f8f8f2", "#cfcfc2", "#75715e"),
    ("one_dark", "One Dark", "#282c34", "#5c6370", "#61afef", "#98c379", "#e5c07b", "#e06c75", "#abb2bf", "#828997", "#5c6370"),
    ("material_dark", "Material Dark", "#263238", "#546e7a", "#80cbc4", "#c3e88d", "#ffcb6b", "#f07178", "#eeffff", "#b2ccd6", "#546e7a"),
    ("solarized_dark", "Solarized Dark", "#002b36", "#586e75", "#268bd2", "#859900", "#b58900", "#dc322f", "#93a1a1", "#839496", "#586e75"),
    ("night_owl", "Night Owl", "#011627", "#5f7e97", "#82aaff", "#22da6e", "#ffcb8b", "#ef5350", "#d6deeb", "#7fdbca", "#5f7e97"),
    ("palenight", "Palenight", "#292d3e", "#676e95", "#82aaff", "#c3e88d", "#ffcb6b", "#f07178", "#a6accd", "#959dcb", "#676e95"),
    ("moonlight", "Moonlight", "#222436", "#636da6", "#82aaff", "#c3e88d", "#ffc777", "#ff757f", "#c8d3f5", "#a9b8e8", "#636da6"),
    ("andromeda", "Andromeda", "#23262e", "#6e7191", "#00e8c6", "#96e072", "#ffe66d", "#ee5d43", "#d5ced9", "#b0a8b8", "#6e7191"),
    ("synthwave", "Synthwave '84", "#262335", "#7b6995", "#ff7edb", "#72f1b8", "#fede5d", "#fe4450", "#f0e3ff", "#c0a8d8", "#7b6995"),
    ("shades_of_purple", "Shades of Purple", "#2d2b55", "#7c6f9f", "#fad000", "#a599e9", "#ff9d00", "#ec3a37", "#e3dfff", "#b0a6d4", "#7c6f9f"),
    ("horizon", "Horizon", "#1c1e26", "#6c6f93", "#e95678", "#25b0bc", "#fab795", "#e95678", "#d5d8da", "#9da5b4", "#6c6f93"),
    ("panda", "Panda Syntax", "#292a2b", "#757575", "#19f9d8", "#6fc1ff", "#ffb86c", "#ff75b5", "#e6e6e6", "#b0b0b0", "#757575"),
    ("cobalt2", "Cobalt 2", "#193549", "#4f6d7a", "#ffc600", "#0088ff", "#ffc600", "#ff628c", "#ffffff", "#b0c4d8", "#4f6d7a"),
    ("ayu_dark", "Ayu Dark", "#0a0e14", "#464b5d", "#e6b450", "#7fd962", "#e6b450", "#f07178", "#bfbdb6", "#8b8680", "#464b5d"),
)

# ── Nature / Organic ───────────────────────────────────────────────────

_NATURE_SEEDS = (
    ("everforest", "Everforest", "#2d353b", "#859289", "#a7c080", "#83c092", "#dbbc7f", "#e67e80", "#d3c6aa", "#9da9a0", "#859289"),
    ("forest", "Deep Forest", "#1a2820", "#4a6050", "#69db7c", "#38d9a9", "#ffd43b", "#ff6b6b", "#e0f0e0", "#a0c8a0", "#5a7860"),
    ("sage", "Sage", "#1e2722", "#5a6e5c", "#87c08a", "#69b4c9", "#d4b06a", "#c96060", "#dce8dc", "#a0b8a0", "#5a6e5c"),
    ("moss", "Moss", "#1c2420", "#4e5e4c", "#7eb87e", "#5ab8a8", "#d4a84a", "#d06060", "#d0e0d0", "#90b090", "#506850"),
    ("desert", "Desert Sand", "#2a2118", "#7a6848", "#d4a053", "#8ab070", "#d4a053", "#c85a4a", "#ede0d0", "#b8a088", "#7a6848"),
    ("autumn_harvest", "Autumn Harvest", "#241c1a", "#6e4e3e", "#e07840", "#d4a030", "#e0a030", "#c84030", "#f0e0d0", "#b89880", "#7a5e4a"),
    ("aurora", "Aurora Borealis", "#0f1926", "#3a5070", "#7edba0", "#b48edd", "#f0c060", "#e06070", "#d8e8f0", "#90a8c0", "#4a6880"),
    ("golden_dawn", "Golden Dawn", "#2a2520", "#6a5840", "#d4a860", "#c07090", "#d4a860", "#c05050", "#f0e8e0", "#b0a090", "#6a5840"),
    ("deep_ocean", "Deep Ocean", "#0a1628", "#3a5878", "#4ab8e8", "#40d8b0", "#f0c060", "#e06060", "#d0e8f8", "#80a8c8", "#3a5878"),
    ("earth_tone", "Earth Tone", "#221e1a", "#5e5040", "#b08858", "#80a868", "#c8a040", "#b85040", "#e8e0d0", "#a89880", "#685840"),
)

# ── Warm ───────────────────────────────────────────────────────────────

_WARM_SEEDS = (
    ("ember", "Ember", "#1e1412", "#6a3830", "#e85030", "#f0a040", "#f0a040", "#e04030", "#f8e8e0", "#c09080", "#7a4838"),
    ("campfire", "Campfire", "#201814", "#6a4830", "#e88840", "#f0c060", "#f0c060", "#d05040", "#f0e8e0", "#b89878", "#705838"),
    ("sunset_blvd", "Sunset Boulevard", "#1e1618", "#6a3850", "#e06888", "#f0a060", "#f0b050", "#d04050", "#f8e8f0", "#c08898", "#6a4858"),
    ("copper", "Copper", "#1c1614", "#6a4830", "#c87848", "#90b870", "#d8a840", "#c84838", "#f0e0d0", "#b09078", "#6a5038"),
    ("espresso", "Espresso", "#1a1614", "#5a4838", "#b89870", "#80a890", "#d0a040", "#c05040", "#e8e0d8", "#a89880", "#685848"),
    ("cinnamon", "Cinnamon", "#1e1816", "#684838", "#d07040", "#90a870", "#d0a040", "#c84838", "#f0e0d0", "#a89078", "#685040"),
    ("terracotta", "Terracotta", "#201816", "#7a5840", "#c07050", "#80b0a0", "#d8a040", "#b84838", "#f0e0d0", "#b09880", "#6a5040"),
    ("amber_term", "Amber Terminal", "#1a1608", "#4a4020", "#ffb000", "#d09000", "#ffb000", "#e05030", "#ffe0a0", "#c8a060", "#6a5830"),
)

# ── Cool / Ice ─────────────────────────────────────────────────────────

_COOL_SEEDS = (
    ("arctic", "Arctic", "#0c1420", "#4a6878", "#88d0f0", "#60c8b0", "#f0c060", "#e06060", "#e0f0f8", "#90b8d0", "#4a6878"),
    ("frost", "Frost", "#101822", "#4a6070", "#80c8e0", "#60b8a0", "#e0b860", "#d86060", "#e0e8f0", "#88a8c0", "#4a6070"),
    ("glacier", "Glacier", "#0e1620", "#406070", "#70c0e0", "#50c8a8", "#e0b060", "#d85858", "#d8e8f0", "#80a0b8", "#406070"),
    ("midnight_blue", "Midnight", "#0a0e18", "#303858", "#6888d0", "#50a080", "#d0a050", "#d06060", "#d0d8e8", "#8090b0", "#404868"),
    ("sapphire", "Sapphire", "#0c1224", "#304870", "#5090e0", "#40c890", "#e0b050", "#d85858", "#d0e0f0", "#7898c0", "#385070"),
    ("twilight_shade", "Twilight", "#14121e", "#504870", "#a080d0", "#60b8a0", "#d8b060", "#d06070", "#d8d0e8", "#9088b0", "#504870"),
    ("deep_sea", "Deep Sea", "#081418", "#305050", "#40b8b8", "#50c878", "#d0a860", "#d06060", "#d0e8e8", "#7898a0", "#385058"),
    ("ice", "Ice", "#101820", "#506878", "#a0d8f0", "#80c8b0", "#e0c060", "#d86868", "#e8f0f8", "#98b8d0", "#506878"),
)

# ── Neon / Cyberpunk ───────────────────────────────────────────────────

_NEON_SEEDS = (
    ("cyberpunk", "Cyberpunk", "#0c0a1a", "#4a2870", "#ff2a6d", "#00f0ff", "#ffd000", "#ff2a6d", "#f0e0ff", "#b088d0", "#5a3880"),
    ("neon_nights", "Neon Nights", "#0a0a14", "#303050", "#39ff14", "#ff6ec7", "#ffff00", "#ff073a", "#e0ffe0", "#90d080", "#405040"),
    ("laserwave", "Laserwave", "#1e1430", "#584878", "#eb64b9", "#40b4c4", "#ffe261", "#ff5370", "#e0d0f0", "#b090c8", "#584878"),
    ("retrowave", "Retrowave", "#16082a", "#4a2870", "#ff00aa", "#00ccff", "#ffd700", "#ff3366", "#e8d0f8", "#a078c8", "#4a2870"),
    ("electric", "Electric", "#0a0e1e", "#2a3858", "#00b4ff", "#00ff88", "#ffcc00", "#ff3344", "#d0e8ff", "#80a0d0", "#304060"),
    ("plasma", "Plasma", "#120a1e", "#482870", "#b040ff", "#00e8d0", "#ffb800", "#ff3860", "#e0d0ff", "#a080c8", "#483070"),
    ("vaporwave", "Vaporwave", "#1a1028", "#504068", "#ff71ce", "#01cdfe", "#fede5d", "#ff5555", "#f0e0ff", "#b098c8", "#504068"),
    ("outrun", "Outrun", "#10061e", "#402060", "#ff6600", "#c040ff", "#ffcc00", "#ff2244", "#f0d0ff", "#a068c0", "#402060"),
)

# ── Pastel / Soft ──────────────────────────────────────────────────────

_PASTEL_SEEDS = (
    ("pastel_dream", "Pastel Dream", "#1e1c24", "#585468", "#dda0dd", "#98d8c8", "#f0d890", "#e88888", "#e8e0f0", "#b0a8c0", "#685e78"),
    ("cotton_candy", "Cotton Candy", "#1c1a22", "#584e68", "#ffb3d9", "#b3e0ff", "#ffe0a0", "#ff8888", "#f0e8f8", "#b8a8c8", "#604e70"),
    ("lavender_mist", "Lavender Mist", "#1a1a24", "#504870", "#b8a0e0", "#90c8b8", "#e0c888", "#d88888", "#e0d8f0", "#a098c0", "#504870"),
    ("soft_mint", "Soft Mint", "#1a2220", "#4a6058", "#88d8b8", "#a0c0e0", "#e0c888", "#d88888", "#e0f0e8", "#98b8a8", "#4a6058"),
    ("peach_blossom", "Peach Blossom", "#221c1c", "#685050", "#f0a888", "#c8a0d0", "#e0c080", "#d88080", "#f0e8e8", "#b8a0a0", "#685858"),
    ("baby_blue", "Baby Blue", "#161c24", "#485870", "#88b8e0", "#98d0b8", "#e0c080", "#d88888", "#e0e8f0", "#98a8c0", "#485870"),
    ("mauve", "Mauve", "#1e1a20", "#584858", "#c090b0", "#90b8c8", "#d8b878", "#d08080", "#e8e0e8", "#a898a8", "#585058"),
    ("lilac", "Lilac", "#1c1a24", "#504868", "#b898d8", "#88c0b0", "#d8c088", "#d08888", "#e8e0f0", "#a098b8", "#504868"),
)

# ── Corporate / Professional ───────────────────────────────────────────

_CORPORATE_SEEDS = (
    ("slate", "Slate", "#1a1c20", "#505860", "#6890b0", "#68a888", "#d0a860", "#c06060", "#d8e0e8", "#8898a8", "#505860"),
    ("graphite", "Graphite", "#1c1c1e", "#505054", "#8888a0", "#78a888", "#c8a060", "#b86060", "#d8d8e0", "#888890", "#505058"),
    ("charcoal", "Charcoal", "#1a1a1c", "#484848", "#7888a0", "#70a080", "#c0a060", "#b05858", "#d0d0d8", "#808088", "#484850"),
    ("steel", "Steel", "#181c20", "#4a5868", "#7098c0", "#60a888", "#c8a860", "#b86060", "#d0d8e8", "#8090a8", "#4a5868"),
    ("titanium", "Titanium", "#1e2024", "#505868", "#8898b0", "#78b890", "#d0b060", "#c06060", "#d8e0e8", "#8890a0", "#505868"),
    ("executive", "Executive", "#141218", "#3a3048", "#c8a870", "#70a8c0", "#d0a860", "#c06060", "#e0d8e8", "#9088a0", "#4a4058"),
    ("boardroom", "Boardroom", "#16141a", "#403848", "#a090b0", "#80a890", "#c8a060", "#b86060", "#d8d0e0", "#8880a0", "#403848"),
    ("mercury", "Mercury", "#1c1e22", "#585c64", "#a0a8b8", "#88b8a0", "#d0b060", "#c06868", "#e0e4e8", "#9098a0", "#585c64"),
)

# ── Retro / Terminal ───────────────────────────────────────────────────

_RETRO_SEEDS = (
    ("matrix", "Matrix", "#0a0f0a", "#204020", "#00ff41", "#00b828", "#c8d020", "#d03030", "#00ff41", "#00c030", "#207020"),
    ("retro_green", "Retro Green", "#0c1208", "#2a4020", "#33ff33", "#20c830", "#d0d020", "#d04040", "#40ff40", "#28c828", "#186818"),
    ("fallout", "Fallout Pip-Boy", "#1a1c0c", "#3a4020", "#18d818", "#a8c020", "#c8c020", "#c04040", "#20e020", "#18b018", "#2a5020"),
    ("commodore", "Commodore 64", "#1a1a40", "#4040a0", "#8888ff", "#88d860", "#d8c858", "#d85858", "#c0c0ff", "#8888c8", "#4848a0"),
    ("tango", "Tango", "#1e2024", "#555753", "#729fcf", "#8ae234", "#fce94f", "#ef2929", "#d3d7cf", "#babdb6", "#555753"),
    ("seti", "Seti", "#151718", "#3b4048", "#55b5db", "#9fca56", "#e6cd69", "#cd3f45", "#d4d7d6", "#a0a4a8", "#4b5058"),
    ("flatland", "Flatland", "#1d1f21", "#505050", "#82b1ff", "#b6d877", "#f8bc45", "#f3716b", "#f0f0f0", "#b8b8b8", "#686868"),
    ("wombat", "Wombat", "#242424", "#514d4a", "#8ac6f2", "#95e454", "#cae682", "#e5786d", "#f6f3e8", "#c3c0b8", "#656055"),
)

# ── Rose Pine Family ──────────────────────────────────────────────────

_ROSE_PINE_SEEDS = (
    ("rose_pine", "Rose Pine", "#191724", "#6e6a86", "#ebbcba", "#31748f", "#f6c177", "#eb6f92", "#e0def4", "#908caa", "#6e6a86"),
    ("rose_pine_moon", "Rose Pine Moon", "#232136", "#6e6a86", "#ea9a97", "#3e8fb0", "#f6c177", "#eb6f92", "#e0def4", "#908caa", "#6e6a86"),
)

# ── Specialty / Modern ─────────────────────────────────────────────────

_SPECIALTY_SEEDS = (
    ("kanagawa", "Kanagawa", "#1f1f28", "#54546d", "#7e9cd8", "#98bb6c", "#e6c384", "#c34043", "#dcd7ba", "#a6a69c", "#727169"),
    ("flexoki_dark", "Flexoki Dark", "#100f0f", "#575653", "#d0a215", "#879a39", "#da702c", "#d14d41", "#cecdc3", "#878580", "#575653"),
    ("vesper", "Vesper", "#101010", "#505050", "#ff8800", "#a0c880", "#ffcc00", "#ff4040", "#d8d8d0", "#a0a098", "#606060"),
    ("vitesse_dark", "Vitesse Dark", "#121212", "#404040", "#4fc1ff", "#80c470", "#dbc074", "#c85042", "#dbd7ca", "#a0a094", "#555555"),
    ("zenburn", "Zenburn", "#3f3f3f", "#6f6f6f", "#8cd0d3", "#7f9f7f", "#dfaf8f", "#cc9393", "#dcdccc", "#b0b0a0", "#7f7f70"),
    ("base16_dark", "Base16 Dark", "#181818", "#585858", "#7cafc2", "#a1b56c", "#f7ca88", "#ab4642", "#d8d8d8", "#b8b8b8", "#585858"),
    ("mellow", "Mellow", "#161617", "#41424a", "#6cb6ff", "#6bc46d", "#c69026", "#f47067", "#c9d1d9", "#8b949e", "#484f58"),
    ("monochrome", "Monochrome", "#0e0e0e", "#444444", "#d0d0d0", "#a0a0a0", "#c8c8a0", "#c0a0a0", "#e8e8e8", "#a0a0a0", "#505050"),
    ("high_contrast", "High Contrast", "#000000", "#6fc3df", "#ffd700", "#00ff00", "#ffa500", "#ff0000", "#ffffff", "#d0d0d0", "#808080"),
    ("oxide", "Oxide", "#1a1210", "#5a3828", "#d07040", "#90a870", "#d0a040", "#c04030", "#e8d8c8", "#a88868", "#5a4030"),
    ("verdigris", "Verdigris", "#0e1a18", "#3a5850", "#50c0a0", "#70a8d0", "#d0b060", "#c86060", "#d0e8e0", "#80a898", "#3a5850"),
    ("github_dark", "GitHub Dark", "#0d1117", "#30363d", "#58a6ff", "#3fb950", "#d29922", "#f85149", "#c9d1d9", "#8b949e", "#484f58"),
    ("aura_dark", "Aura Dark", "#15141b", "#4d4d56", "#a277ff", "#61ffca", "#ffca85", "#ff6767", "#edecee", "#a5a2a8", "#4d4d56"),
)


def _expand(raw: tuple[tuple[str, ...], ...]) -> tuple[ThemeSeed, ...]:
    """Expand compact tuples into ThemeSeed instances."""
    return tuple(
        ThemeSeed(
            theme_id=row[0],
            display_name=row[1],
            base_bg=row[2],
            border=row[3],
            accent=row[4],
            accent_soft=row[5],
            warning=row[6],
            danger=row[7],
            text=row[8],
            text_muted=row[9],
            text_dim=row[10],
        )
        for row in raw
    )


GALLERY_SEEDS: tuple[ThemeSeed, ...] = (
    *_expand(_IDE_SEEDS),
    *_expand(_NATURE_SEEDS),
    *_expand(_WARM_SEEDS),
    *_expand(_COOL_SEEDS),
    *_expand(_NEON_SEEDS),
    *_expand(_PASTEL_SEEDS),
    *_expand(_CORPORATE_SEEDS),
    *_expand(_RETRO_SEEDS),
    *_expand(_ROSE_PINE_SEEDS),
    *_expand(_SPECIALTY_SEEDS),
)
