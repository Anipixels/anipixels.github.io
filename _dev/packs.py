"""Facts about the released Anipixels packs, used by build.py.

Every number, title and URL here was checked against a file on disk on 6 Oct 2026:
  - release/STORE_TEXT.md            (Crisp Cards, Crisp Cozy, Crisp Kit, Crisp Quest)
  - the sampler's own README.txt and LICENSE.txt inside *_Free_Sampler.zip (all eight)
  - the README.txt inside the full pack zip (category counts for UI, Puzzle, Jingles, Juice)
  - dist/manifest.json               (sound names, lengths, sprite-sheet cells)
  - C:\\Claude Code\\MONEY_HANDOFF.md  (itch prices, "checked 6 Oct 2026", and the bundle)
Crisp UI's old release/UPLOAD_GUIDE.txt describes the 102-sound v1.0 at $2.99 and was NOT used.
Category counts are asserted against the manifests / store text again by build.py.
"""

SITE = "https://anipixels.github.io/"
PRICE_DATE = "6 October 2026"
ITCH = "https://anipixels.itch.io/"

BUNDLE = dict(
    name="Crisp Everything Bundle",
    url="https://itch.io/s/203391/crisp-everything-bundle",
    price="14.99",
    singles="45.92",
)

GAMES = [
    ("Tune Trail", "tune-trail", "Marble music puzzle: place deflectors so the marble hits the chimes in melody order."),
    ("Chime Gems", "chime-gems", "Match-3 puzzle."),
    ("Chime Blocks", "chime-blocks", "Block puzzle on an 8 x 8 board."),
    ("Chime Sort", "chime-sort", "Ball sort puzzle."),
    ("Chime Tiles", "chime-tiles", "Triple tile-match puzzle."),
    ("Chime Drop", "chime-drop", "Drop and merge puzzle."),
    ("Chime Connect", "chime-connect", "Pair-link puzzle."),
]

SOUND_LICENCE = (
    "Use the sounds in any number of commercial or non-commercial projects (games, apps, websites, videos, streams, game jams). "
    "Edit, layer, pitch or otherwise modify them. Credit is appreciated but never required. "
    "You may not resell, redistribute or give away the sounds themselves, on their own or as part of another sound library or asset pack, "
    "modified or not, and you may not claim them as your own original work in a sound library."
)
VFX_LICENCE = (
    "Use the effects in any number of commercial or non-commercial projects (games, apps, websites, videos, streams, game jams). "
    "Edit, recolour, resize or otherwise modify them. Credit is appreciated but never required. "
    "You may not resell, redistribute or give away the effects themselves, on their own or as part of another asset pack, "
    "modified or not, and you may not claim them as your own original work in an asset pack."
)
UI_LICENCE = (
    "Use the graphics in any number of commercial or non-commercial projects (games, apps, websites, videos, streams, game jams). "
    "Edit, recolour, resize or otherwise modify them. Credit is appreciated but never required. "
    "You may not resell, redistribute or give away the graphics themselves, on their own or as part of another asset pack, UI kit or template, "
    "modified or not, and you may not claim them as your own original work in an asset pack."
)
SOUND_MADE = ("Every sound is synthesised from scratch by code that was written with Claude, an AI assistant. "
              "No recorded samples and no AI audio-generation models were used.")
VFX_MADE = ("Every frame is drawn by code that was written with the help of Claude, an AI assistant. "
            "No AI image generators, no traced or third-party art.")
UI_MADE = ("Every shape is drawn procedurally by code that was written with the help of Claude, an AI assistant. "
           "No AI image generators, no traced or third-party art, no font files.")
SOUND_FORMATS = [
    "WAV: 44.1 kHz, 16-bit, stereo (for editing and highest quality).",
    "OGG Vorbis: small files, ready for Godot, Unity, GameMaker and web.",
    "Every sound is loudness-matched, starts on its first sample (no dead air) and peaks at or below -1 dBFS.",
]


def sound_faq(name, n, sampler_n, noun="sounds", extra=()):
    return [
        ("Can I use %s in a commercial game?" % name,
         "Yes. The licence allows any number of commercial or non-commercial projects: games, apps, websites, videos, streams and game jams."),
        ("Do I have to give credit?", "No. Credit is appreciated but never required."),
        ("Which engines does it work with?",
         "Any engine or tool that plays WAV or OGG files. The pack's README names Godot, Unity, GameMaker and web."),
        ("Can I edit the %s?" % noun, "Yes. You may edit, layer, pitch or otherwise modify them."),
        ("Can I try it before buying?",
         "Yes. The free itch.io page has a playable browser demo and a free sampler with %d of the %d %s as WAV and OGG. "
         "The same %d sampler files can be played on this site's UI sound board." % (sampler_n, n, noun, sampler_n)),
    ] + list(extra) + [
        ("Was AI used to make it?",
         "Yes, for the code. " + SOUND_MADE),
    ]


COZY_VS_UI = ("How is Crisp Cozy different from Crisp UI?",
              "Crisp UI is clean and neutral: clicks, glass, bright chimes. Crisp Cozy is warm and rounded: wood, kalimba, bubbles, paper, "
              "and it adds a Cozy Actions folder. No sound appears in both packs. Measured across both packs, the average spectral centre of "
              "Crisp Cozy is about 860 Hz against 1910 Hz for Crisp UI, and its sounds fade in more gently (median attack 10 ms against 2 ms). "
              "The folder names match, so you can swap one pack for the other or mix them.")

PACKS = [
    dict(
        slug="crisp-ui", folder="CrispUI", zip="CrispUI_Free_Sampler.zip", name="Crisp UI",
        kind="Sound effects pack", accent="#6ee7b7", price="4.99", total=242, sampler_n=20, unit="sounds",
        manifest=True, licence="sound",
        h1="Crisp UI: 242 UI sound effects for games",
        title="Crisp UI - 242 UI Sound Effects for Games (WAV + OGG) | Anipixels",
        meta="Crisp UI is a pack of 242 interface and reward sound effects for game menus, HUDs and pickups. WAV + OGG, royalty-free, $4.99. Free 20-sound sampler.",
        card="242 sound effects for game menus, HUDs, rewards and pickups. WAV + OGG.",
        lead="Crisp UI is a pack of 242 sound effects for game menus, HUDs, rewards and pickups: clicks, hovers, toggles, confirm and error "
             "feedback, notifications, menu transitions, reward jingles, coins and text blips. Every sound comes as WAV and OGG.",
        cats=[("Buttons", 56), ("Toggles", 28), ("Feedback", 33), ("Notifications", 24), ("Menus", 20), ("Rewards", 22),
              ("Pickups", 25), ("Shop", 10), ("Text", 24)],
        specs=[
            "242 sounds in 9 folders.",
            "Sounds whose names end in _01, _02, _03 are variations: pick one at random so repeated clicks and pickups do not sound robotic.",
            "hover_*, scroll_tick, knob_turn and loading_tick are mixed quiet on purpose, because they play constantly.",
            "star_01 to star_03, combo_up_01 to combo_up_04 and countdown_3, _2, _1, countdown_go are tuned to climb in order.",
            "Pairs are tuned to match: toggle_on/off, checkbox_on/off, menu_open/close, popup_open/close, panel_slide_in/out, "
            "drawer_open/close, zoom_in/out, undo/redo, cart_add/remove, equip/unequip.",
        ],
        sampler="The free sampler has 20 of the 242 sounds as WAV and OGG: 5 button sounds, 2 toggles, 3 feedback sounds, 1 notification, "
                "2 menu sounds, 2 rewards, 2 pickups, 1 shop sound and 2 text sounds.",
        faq=lambda: sound_faq("Crisp UI", 242, 20, extra=[COZY_VS_UI]),
        shots=[("screenshot_demo.png", "The Crisp UI playable web demo: a mock game menu where every control plays a sound from the pack"),
               ("screenshot_contents.png", "Contents sheet listing the sounds in Crisp UI by folder")],
    ),
    dict(
        slug="crisp-puzzle", folder="CrispPuzzle", zip="CrispPuzzle_Free_Sampler.zip", name="Crisp Puzzle",
        kind="Sound effects pack", accent="#f9a8d4", price="5.99", total=100, sampler_n=20, unit="sounds",
        manifest=True, licence="sound",
        h1="Crisp Puzzle: 100 match-3 and puzzle game sound effects",
        title="Crisp Puzzle - 100 Match-3 & Puzzle Game Sound Effects | Anipixels",
        meta="Crisp Puzzle is a pack of 100 sound effects for match-3, falling-block, push-block and casual puzzle games, with tuned combo ladders. WAV + OGG, $5.99.",
        card="100 sound effects for match-3, falling-block, push-block and casual puzzle games. WAV + OGG.",
        lead="Crisp Puzzle is a pack of 100 sound effects for match-3, falling-block, push-block and casual puzzle games: swaps, matches, "
             "tile landings, line blasts, bombs, line clears and two 12-step combo ladders tuned to C major pentatonic.",
        cats=[("Tiles", 14), ("Matches", 7), ("Combo Ladders", 24), ("Specials", 10), ("Board", 11), ("Falling Blocks", 13),
              ("Push & Break", 12), ("Map & Jingles", 9)],
        specs=[
            "100 sounds in 8 folders.",
            "combo_bell_01 to 12 and combo_pluck_01 to 12 are tuned ladders (C major pentatonic): play the next one for each chained match and a cascade turns into a little melody.",
            "Sounds ending in _01, _02, _03 are variations: pick one at random each time.",
            "tile_land is short on purpose, so you can fire one per column when gems fall.",
            "score_tick is quiet on purpose, so you can repeat it while the score counts up.",
        ],
        sampler="The free sampler has 20 of the 100 sounds as WAV and OGG: 4 tile sounds, 2 matches, the first 5 steps of the bell combo ladder, "
                "2 specials, 4 board sounds, 2 falling-block sounds and the level-complete jingle.",
        faq=lambda: sound_faq("Crisp Puzzle", 100, 20),
        shots=[("screenshot_demo.png", "The Crisp Puzzle playable web demo"),
               ("screenshot_contents.png", "Contents sheet listing the sounds in Crisp Puzzle by folder")],
    ),
    dict(
        slug="crisp-jingles", folder="CrispJingles", zip="CrispJingles_Free_Sampler.zip", name="Crisp Jingles",
        kind="Music jingles pack", accent="#fbbf24", price="5.99", total=45, sampler_n=9, unit="jingles",
        manifest=True, licence="sound",
        h1="Crisp Jingles: 45 short music stingers for games",
        title="Crisp Jingles - 45 Game Music Jingles & Stingers in 3 Styles | Anipixels",
        meta="Crisp Jingles is a pack of 45 short musical stingers for games: 15 moments, each in chiptune, cozy and synth-pop styles. WAV + OGG, $5.99. 9 free.",
        card="45 short music stingers: 15 game moments, each in chiptune, cozy and synth-pop styles. WAV + OGG.",
        lead="Crisp Jingles is a pack of 45 short musical stingers for games: 15 moments such as level complete, game over and item get, "
             "each written once and produced in three styles (chiptune, cozy and synth-pop) with the same melody.",
        cats=[("Chiptune", 15), ("Cozy", 15), ("Synth Pop", 15)],
        specs=[
            "45 jingles in 3 folders: 15 moments x 3 styles.",
            "Each jingle exists in all three styles with the same melody: pick the style that fits your game, or mix them (for example chiptune in levels, cozy in menus).",
            "Every file ends in its own natural reverb tail, so jingles never cut off abruptly.",
            "Jingles are mixed a little louder than typical sound effects, so duck your music under them.",
        ],
        sampler="The free sampler has 9 of the 45 jingles as WAV and OGG: level complete, game over and item get, each in all three styles.",
        faq=lambda: sound_faq("Crisp Jingles", 45, 9, noun="jingles"),
        shots=[("screenshot_demo.png", "The Crisp Jingles web demo, where each jingle can be played in the browser"),
               ("screenshot_contents.png", "Contents sheet listing the 15 jingles and three styles in Crisp Jingles")],
    ),
    dict(
        slug="crisp-cards", folder="CrispCards", zip="CrispCards_Free_Sampler.zip", name="Crisp Cards",
        kind="Sound effects pack", accent="#f2c94c", price="4.99", total=105, sampler_n=20, unit="sounds",
        manifest=True, licence="sound",
        h1="Crisp Cards: 105 card game, deckbuilder and casino sound effects",
        title="Crisp Cards - 105 Card Game, Deckbuilder & Casino Sound Effects | Anipixels",
        meta="Crisp Cards is a pack of 105 sound effects for card games, deckbuilders and casino tables: flips, deals, shuffles, hits, chips, dice. WAV + OGG, $4.99.",
        card="105 sound effects for card games, deckbuilders and casino tables. WAV + OGG.",
        lead="Crisp Cards is a pack of 105 sound effects for card games, deckbuilders and casino tables: flips, deals, shuffles, hits, "
             "blocks, chips, dice, roulette and the menu sounds in between.",
        cats=[("Cards", 21, "flip, deal, slide, draw, place/play, pick up, hover lift, discard"),
              ("Deck", 7, "riffle shuffle (with bridge and squaring), overhand shuffle, fan out, empty deck thud"),
              ("Card Magic", 6, "burn/destroy crackle, upgrade shimmer, enchant, rare reveal, legendary reveal"),
              ("Combat", 15, "light and heavy hits, critical hit, block gain, block hit, shield break, enemy intent, enemy death"),
              ("Status", 11, "heal, buff, debuff, poison tick, energy gain, out of energy"),
              ("Turns & Stingers", 4, "turn start, turn end, victory fanfare, defeat"),
              ("Chips", 9, "single chip clack, stack, pile push, bet placed"),
              ("Dice & Coins", 9, "dice shake, dice roll, dice land, coin flip, coin land/spin-out"),
              ("Roulette & Wins", 7, "roulette spin with ball drop, wheel ticks, jackpot, small win, lose"),
              ("UI", 16, "buttons, hovers, confirm, cancel, not enough energy, reward appear/choose, gold gain, shop buy, map select")],
        specs=[
            "105 sounds in 10 folders.",
            "Variations (_01, _02, _03) for the sounds you hear constantly (flips, deals, draws, hits, chips, dice), so a dealt hand does not sound robotic.",
            "card_hover and ui_hover are quiet on purpose, because they fire constantly.",
            "shuffle_riffle ends with the deck being squared on the table; shuffle_overhand is the quicker one.",
            "turn_start, turn_end, victory, defeat, jackpot and lose are tuned stingers (C major / C minor), in key with each other.",
        ],
        sampler="The free sampler has 20 of the 105 sounds as WAV and OGG: card flip, deal, draw, place, hover, riffle shuffle, card burn, "
                "rare reveal, light hit, block, heal, energy gain, turn start, victory, chip clack, chip stack, dice roll, roulette spin, jackpot and confirm.",
        faq=lambda: sound_faq("Crisp Cards", 105, 20),
        shots=[("screenshot_demo.png", "The Crisp Cards playable web demo: a small deckbuilder duel where every card and hit plays a sound from the pack"),
               ("screenshot_contents.png", "Contents sheet listing the sounds in Crisp Cards by folder")],
    ),
    dict(
        slug="crisp-cozy", folder="CrispCozy", zip="CrispCozy_Free_Sampler.zip", name="Crisp Cozy",
        kind="Sound effects pack", accent="#fdba8c", price="4.99", total=261, sampler_n=20, unit="sounds",
        manifest=True, licence="sound",
        h1="Crisp Cozy: 261 cozy UI sound effects",
        title="Crisp Cozy - 261 Cozy UI Sound Effects (Soft, Cute, Wooden, Bubble) | Anipixels",
        meta="Crisp Cozy is a pack of 261 soft, cute UI sound effects for cozy games: wood taps, kalimba, bubbles, paper. WAV + OGG, royalty-free, $4.99. 20 free.",
        card="261 soft, cute UI sounds for cozy games: wood taps, kalimba, bubbles, paper. WAV + OGG.",
        lead="Crisp Cozy is a pack of 261 soft, cute user-interface sound effects for cozy games: farming and life sims, cat cafes, "
             "visual novels, casual puzzle and idle games. Every sound comes as WAV and OGG, is loudness-matched and is royalty-free for commercial use.",
        cats=[("Buttons", 44, "soft wooden taps and knocks, wooden-button clicks, felt and plush taps, bubble and cork pops, warm boops, kalimba plucks, quiet hovers, press / release, select, back"),
              ("Toggles", 24, "toggle, wooden switch and checkbox pairs, dropdown open / close, tab switches, a five-step slider ladder, scroll and knob ticks, stepper up / down"),
              ("Feedback", 29, "confirm, cancel, gentle errors (no buzzers), warning, denied, locked, save, undo / redo, delete, send / receive, loading tick and done"),
              ("Notifications", 21, "soft bell, kalimba and music-box notifications, message in / out, reminder, mail arriving, clock tick / tock, timer end, countdown 3-2-1-go, new day, a friend at the door"),
              ("Menus", 18, "menu, popup, panel, drawer, bag and book open / close pairs, paper page turns, soft cloth swishes"),
              ("Rewards", 23, "level up, achievement, stars 1-2-3 that climb in tune, quest complete, daily reward, wooden chest, unlock, XP ticks, a five-step combo ladder, rank up, streak, badge stamp, friendship up, collection complete, success and a kind 'aww' fail"),
              ("Pickups", 27, "coins and coin pours, gems, hearts, items, item drops, fruit, seeds, fish, shells, flowers, key, star"),
              ("Shop", 12, "purchase with a shop bell, small purchase, not enough coins, sell, equip / unequip, upgrade, basket add / remove, gift wrap, shop door bell, coin count"),
              ("Text", 25, "'animal talk' dialogue syllables in low, mid, high and squeak voices, soft wooden typewriter keys, space / return / backspace, dialogue advance and end"),
              ("Cozy Actions", 38, "plant seed, water plant, harvest pop, dig, cat purr and happy trill, bird chirps, cooking stir, light sizzle and 'dinner's ready' bell, crafting done, sleep, door chimes, door open / close, footsteps on wood and grass, floating bubbles, fishing cast and bite")],
        specs=[
            "261 sounds in 10 folders (142 named sounds; 181 of the files belong to numbered sets, which are variations or tuned steps).",
            "2.7 minutes of audio in total; 179 of the 261 sounds are 0.6 s or shorter, and the longest jingle is 2.4 s.",
            "Download size: 23 MB (one zip with both formats; 29 MB of WAV and 2.5 MB of OGG unzipped).",
            "Tuned to C major pentatonic, so sounds layered together stay in tune.",
            "Anything heard often has 2 to 5 variations; hovers and ticks are mixed quiet.",
            "Error sounds are low marimba steps and soft pats, not buzzers.",
            "Same folder names, loudness and key as Crisp UI, so the two packs can be mixed.",
        ],
        engines="Godot, Unity, Unreal, GameMaker, Construct, RPG Maker, Ren'Py, Phaser and other web frameworks: anything that plays WAV or OGG.",
        sampler="The free sampler has 20 of the 261 sounds as WAV and OGG: 5 button sounds, 2 toggles, 3 feedback sounds, 1 notification, "
                "3 menu sounds, 1 reward, 2 pickups, 1 'animal talk' syllable and 2 cozy actions (plant seed, water plant).",
        faq=lambda: [
            ("Can I use this in a commercial game?", "Yes. One purchase covers unlimited commercial and non-commercial projects."),
            ("Do I have to credit you?", "No. A credit to Anipixels is welcome but not required."),
            ("Which engines does it work with?",
             "Any engine or tool that plays WAV or OGG files: Godot, Unity, Unreal, GameMaker, Construct, RPG Maker, Ren'Py, Phaser and other web frameworks."),
            COZY_VS_UI,
            ("Was AI used?",
             "Yes, for the code. Every sound is synthesised from scratch by code that was written with Claude (an AI assistant). "
             "No recorded samples and no AI audio-generation models were used."),
            ("Can I try before buying?",
             "Yes. The web demo on the free itch.io page plays all 261 sounds in your browser, and the free sampler has 20 of them to download. "
             "The 20 sampler sounds can also be played on this site's UI sound board."),
        ],
        shots=[("screenshot_demo.png", "The Crisp Cozy web demo, which plays every sound in the browser"),
               ("screenshot_contents.png", "Contents sheet listing the sounds in Crisp Cozy by folder")],
    ),
    dict(
        slug="crisp-juice", folder="CrispVFX", zip="CrispJuice_Free_Sampler.zip", name="Crisp Juice",
        kind="VFX sprite sheets", accent="#7dd3fc", price="4.99", total=68, sampler_n=8, unit="effects",
        manifest=True, licence="vfx",
        h1="Crisp Juice: 68 VFX sprite sheets for casual and puzzle games",
        title="Crisp Juice - 68 VFX Sprite Sheets for Casual & Puzzle Games | Anipixels",
        meta="Crisp Juice is a pack of 68 sprite-sheet effects for casual and puzzle games: gem bursts, match pops, coins, stars, confetti, fireworks. PNG + Godot 4, $4.99.",
        card="68 sprite-sheet effects for casual and puzzle games: gem bursts, coins, stars, confetti. PNG + Godot 4 scenes.",
        lead="Crisp Juice is a pack of 68 sprite-sheet effects for casual and puzzle games: gem bursts, match pops, line blasts, coins, stars, "
             "confetti, fireworks, impacts, magic and highlight loops. The sheets are transparent PNGs with a sheets.json of frame data, "
             "plus a Godot 4 project with a ready-made scene for each effect.",
        cats=[("Gems", 30), ("Rewards", 10), ("Celebration", 7), ("Impacts", 8), ("Magic", 6), ("Highlights", 7)],
        specs=[
            "68 sprite sheets in 6 folders. Frames run left to right, top to bottom, and every cell is square.",
            "Cell sizes: 192 px (55 sheets), 256 px (11 sheets) and 128 px (2 sheets). 12 to 48 frames per effect, drawn for 30 frames per second.",
            "Transparent PNG with straight (non-premultiplied) alpha.",
            "12 sheets are flagged as loops in sheets.json and repeat seamlessly (the ten named _loop plus coin_spin_gold and coin_spin_silver); everything else plays once.",
            "17 sheets (glows, sparkles, lightning, fireworks) are marked \"additive\": true in sheets.json: they look best with additive blending on dark backgrounds and also work with normal blending.",
            "confetti_fall_loop tiles vertically, line_blast_h tiles horizontally and line_blast_v vertically, so they can be repeated to cover any width or height.",
            "sheets.json lists frame count, cell size, columns, rows, fps and loop flag for every sheet.",
        ],
        engines="Godot 4 (4.3 or newer): copy the addon folder into your project and drag an effect scene into your level; each scene is one Sprite2D "
                "that plays when it appears and removes itself when it finishes. Unity, GameMaker, Construct, Phaser and others: import a sheet and slice it as a grid "
                "using the cell size from sheets.json (Unity: Sprite Mode Multiple, Slice, Grid By Cell Size; GameMaker: Import Strip Image; "
                "Phaser: load.spritesheet with frameWidth and frameHeight), then play the frames at 30 fps.",
        sampler="The free sampler has 8 of the 68 effects, with sheets.json and the Godot 4 project: gem_burst_blue, match_pop_pink, star_burst_gold, "
                "coin_burst_gold, confetti_burst_01, ring_shockwave_white, tap_ripple and sparkle_twinkle_white_loop.",
        faq=lambda: [
            ("Can I use Crisp Juice in a commercial game?",
             "Yes. The licence allows any number of commercial or non-commercial projects: games, apps, websites, videos, streams and game jams."),
            ("Do I have to give credit?", "No. Credit is appreciated but never required."),
            ("Which engines does it work with?",
             "Any engine that can slice a PNG sprite sheet into a grid. The pack includes a Godot 4 project (4.3 or newer) with a scene per effect; "
             "the README gives the slicing steps for Unity, GameMaker and Phaser."),
            ("What frame rate are the effects made for?", "30 frames per second. sheets.json gives the frame count, cell size, columns and rows for every sheet."),
            ("Can I recolour or resize the effects?", "Yes. You may edit, recolour, resize or otherwise modify them."),
            ("Can I try it before buying?",
             "Yes. The free itch.io page has a playable browser demo and a free sampler with 8 of the 68 effects. "
             "The same 8 sampler sheets can be played on this site's VFX sprite sheet player."),
            ("Was AI used to make it?", "Yes, for the code. " + VFX_MADE),
        ],
        shots=[("screenshot_demo.png", "The Crisp Juice playable web demo"),
               ("screenshot_contents.png", "Contents sheet showing the effects in Crisp Juice by folder")],
    ),
    dict(
        slug="crisp-kit", folder="CrispKit", zip="CrispKit_Free_Sampler.zip", name="Crisp Kit",
        kind="Game UI kit", accent="#6ee7b7", price="6.99", total=1255, sampler_n=57, unit="pieces",
        manifest=False, licence="ui",
        h1="Crisp Kit: casual game UI kit with 8 themes, icons and Godot 4 themes",
        title="Crisp Kit - Casual Game UI Kit (Buttons, Panels, Icons, Godot 4 Theme) | Anipixels",
        meta="Crisp Kit is a flat, rounded UI kit for casual and mobile-style games: 100 pieces x 8 colour themes, 127 icons, 93 input prompts. PNG + SVG, 9-slice, $6.99.",
        card="100 UI pieces x 8 themes, 127 icons, 93 input prompts. PNG + SVG, 9-slice, Godot 4 themes.",
        lead="Crisp Kit is a flat, rounded UI kit for casual and mobile-style games: 100 pieces in each of 8 colour themes, 127 icons and "
             "93 keyboard, mouse and gamepad prompts. Everything comes as PNG (1x and 2x) and SVG with 9-slice borders listed, plus ready-made Godot 4 themes.",
        included_html=[
            "<strong>800 themed pieces</strong>: 100 per theme in 8 themes (mint, sky, gold, coral, violet, pink, slate, light), with the same file names in every theme so you can swap a whole look.",
            "Per theme: buttons (33), panels (9), bubbles (4), bars (5), sliders (5), toggles (12), tabs (4), inputs (3), badges (7), level select (4), misc (14).",
            "Buttons in 7 shapes (large, medium, small, pill, square, round, flat outline) with normal, hover, pressed and disabled states, plus close and plus buttons.",
            "Panels, window and modal frames, cards, 9-slice frames, tabs, text inputs, tooltip and speech bubbles, ribbons, badges, a resource pill, progress bars and fills (plain, striped, thin), slider track / fill / knob, check boxes, radio buttons, toggles, level-select tiles (unlocked, pressed, current, locked), list rows, slots, scroll bars, page dots.",
            "<strong>127 icons</strong> in white and dark: settings, home, play, pause, restart, sound, music, shop, cart, coin, gem, heart, star, trophy, lock, key, gift, chest, clock, shield, sword, map, user, friends, chat, mail, bell, leaderboard, calendar and many more.",
            "<strong>93 input prompts</strong> in a light and a dark style: 50 keyboard keys (A-Z, 0-9, arrows, Space, Enter, Shift, Ctrl, Alt, Esc, Tab, Backspace), 7 mouse glyphs and 36 generic gamepad glyphs (A/B/X/Y, plain face buttons, d-pad, LB/RB/LT/RT, sticks, Start/Select). No console logos.",
            "<strong>15 colour pieces</strong> that fit any theme: stars (full, half, empty, two sizes), coin, gem, heart, energy, crown, trophy, gift, key, alert badge.",
            "<strong>Godot 4 project</strong>: one Theme resource per colour theme (1x and 2x versions) that styles Button, CheckBox, CheckButton, ProgressBar, HSlider, LineEdit, TabContainer, panels, tooltips and more, with type variations for every extra shape, and a demo scene (main menu, shop, level select, widgets, settings popup, theme picker).",
        ],
        specs=[
            "3765 image files: 1255 images, each as PNG 1x, PNG 2x and SVG. That is 335 different designs (100 themed + 15 colour + 127 icons + 93 prompts); the themes, the two icon colours and the two prompt styles multiply them.",
            "65 of the 100 themed pieces are 9-slice / 3-slice. Borders are in sheets.json and in UNITY.txt.",
            "Icons are 32 px (1x) and 64 px (2x). Transparent PNG, straight alpha.",
            "palette.json lists the hex colours of every theme.",
            "No font is bundled. The demo and screenshots use the system font; any rounded bold font fits (Baloo 2, Fredoka and Nunito are free).",
            "Download size: CrispKit_Full.zip is 8.95 MB.",
        ],
        engines="Any engine that loads PNG or SVG. Godot 4 (4.3 or newer, tested in 4.7) gets ready-made themes. Unity, GameMaker, Construct, Phaser and others use the "
                "PNGs with their nine-slice feature and the border values from sheets.json. Unity: sprites only, no prefabs; UNITY.txt gives the border values to type into the Sprite Editor.",
        sampler="The free sampler has 57 pieces as PNG (1x and 2x) and SVG, with a sheets.json of sizes and 9-slice borders: 26 pieces from the mint theme, "
                "3 colour pieces (star full, star empty, coin), 20 white icons and 8 input prompts.",
        faq=lambda: [
            ("Which engines does it work with?",
             "Any engine that loads PNG or SVG. Godot 4 gets ready-made themes; Unity, GameMaker, Construct, Phaser and others use the PNGs with their nine-slice feature and the border values from sheets.json."),
            ("Can I recolour it?", "Yes. Edit the SVGs, tint the PNGs, or start from the light theme, which is neutral."),
            ("Can I mix themes?", "Yes. Every theme has the same pieces at the same sizes, so a coral close button drops into a mint window."),
            ("Is there a free version?", "Yes: Crisp Kit Free has 57 pieces to test in your project. The same 57 pieces can be previewed on this site's UI kit preview."),
            ("Do the sounds in the demo come with it?", "No, the click sounds in the web demo are previews from Crisp UI, a separate sound pack."),
            ("Can I use it in a commercial game, and do I have to give credit?",
             "It is royalty-free for commercial and non-commercial projects and no attribution is needed. You may not resell or redistribute the assets themselves, modified or not."),
            ("Was AI used to make it?", "Yes, for the code. " + UI_MADE),
        ],
        shots=[("screenshot_demo.png", "The Crisp Kit web demo, built from the real PNGs"),
               ("screenshot_screens.png", "Mock game screens built with Crisp Kit"),
               ("screenshot_themes.png", "The 8 colour themes of Crisp Kit"),
               ("screenshot_contents.png", "Contents sheet of the Crisp Kit themed pieces"),
               ("screenshot_icons.png", "The icons included in Crisp Kit")],
    ),
    dict(
        slug="crisp-quest", folder="CrispQuest", zip="CrispQuest_Free_Sampler.zip", name="Crisp Quest",
        kind="Fantasy RPG UI kit", accent="#f3c969", price="6.99", total=1141, sampler_n=52, unit="pieces",
        manifest=False, licence="ui",
        h1="Crisp Quest: fantasy RPG UI kit with 6 themes and 184 icons",
        title="Crisp Quest - Fantasy RPG UI Kit (Buttons, Panels, Inventory, Icons) | Anipixels",
        meta="Crisp Quest is a fantasy RPG UI kit: 135 pieces x 6 material themes, 184 icons. PNG 1x + 2x and SVG, 9-slice borders, Godot 4 themes. $6.99. Free sampler.",
        card="135 RPG UI pieces x 6 fantasy themes, 184 icons. PNG + SVG, 9-slice, Godot 4 themes.",
        lead="Crisp Quest is a fantasy RPG UI kit: 135 pieces in each of 6 material themes (Carved Wood, Parchment &amp; Ink, Stone &amp; Iron, "
             "Royal Gold, Elven Silver, Arcane), 147 fantasy icons in white and dark and 37 colour icons. Everything comes as PNG (1x and 2x) "
             "and SVG with 9-slice borders listed, plus ready-made Godot 4 themes.",
        included_html=[
            "<strong>810 themed pieces</strong>: 135 per theme in 6 themes, with the same file names and sizes in every theme so you can swap a whole look.",
            "The themes are different drawings, not recolours: each has its own corner shape and corner ornaments (brass brackets on carved wood, ink flourishes on parchment, riveted iron on stone, rubies on a gold frame, silver leaves, glowing arcane diamonds).",
            "Per theme: buttons (33), panels (8), dialogue (5), inventory (18), hotbar (9), bars (13), quest (5), tabs (4), toggles (7), sliders (5), scrollbar (3), inputs (6), banners (4), dividers (3), hud (11), texture (1).",
            "<strong>Buttons</strong> in large, medium, small and square sizes plus a secondary style and a round button, each with normal, hover, pressed and disabled states; close, arrow, plus and minus buttons.",
            "<strong>Panels and windows</strong>: panel, inset panel, ornate panel, window with a title bar, title plate, two hollow frames, tooltip.",
            "<strong>Dialogue</strong>: dialogue box, name plate, continue arrow, choice rows (normal and selected).",
            "<strong>Inventory</strong>: 48 px slots: empty, hover, selected, locked, five rarity borders (common, uncommon, rare, epic, legendary), eight equipment slots with ghost icons (head, chest, hands, feet, weapon, off-hand, ring, amulet) and a stack-count badge.",
            "<strong>Hotbar and skills</strong>: hotbar slot (normal and active), tray, round skill slot and ring, three cooldown overlays, hotkey cap.",
            "<strong>Bars and orbs</strong>: bar frame, ornate bar frame, thin bar, fills for health, mana, stamina and experience; orb frame, back, gloss and health / mana fills.",
            "<strong>Also</strong>: quest tracker rows and header, tabs, check box, radio, switch, slider, scroll bar, text input, dropdown, ribbons, hanging banner, heraldic shield, dividers, round and square minimap frames, three portrait frames, currency plate, level badge, toast, notification dot, list rows and a seamless background tile.",
            "<strong>147 fantasy icons</strong> in white and dark: weapons (16), armour (11), consumables (14), loot (14), tools (12), magic (10), status (17), map (18), classes (8), interface (27).",
            "<strong>37 colour icons</strong> where colour matters: potions, gems, coins, rarity marks, elements and a few more.",
            "<strong>Godot 4 project</strong>: one Theme resource per theme (1x and 2x versions) that styles Button, CheckBox, CheckButton, ProgressBar, HSlider, LineEdit, OptionButton, TabContainer, panels, tooltips and more, with type variations for the extra shapes (slots, rarity borders, window, dialogue box, hotbar...), and a demo scene.",
        ],
        specs=[
            "3423 image files: 1141 images, each as PNG 1x, PNG 2x and SVG. That is 319 different designs (135 themed + 184 icons); the 6 themes and the two icon colours multiply them.",
            "81 of the 135 themed pieces are 9-slice / 3-slice. Borders are in sheets.json and in UNITY.txt. Ornaments sit inside the borders, so the middles stretch cleanly.",
            "Slots are 48 px and icons 32 px at 1x (96 px and 64 px at 2x). Transparent PNG, straight alpha.",
            "palette.json lists the hex colours of every theme, the rarity colours and the bar colours.",
            "No font is bundled and no piece has lettering baked in. The demo and screenshots use the system serif; any bold serif fits (Cinzel, Alegreya and EB Garamond are free).",
            "Download size: CrispQuest_Full.zip is 11.21 MB.",
        ],
        engines="Any engine that loads PNG or SVG. Godot 4 (4.3 or newer; themes and demo scene load-tested headless in 4.7) gets ready-made themes. Unity, GameMaker, Construct, "
                "Phaser and others use the PNGs with their nine-slice feature and the border values from sheets.json. Unity: sprites only, no prefabs and no pre-set borders; "
                "UNITY.txt gives the border values to type into the Sprite Editor.",
        sampler="The free sampler has 52 pieces as PNG (1x and 2x) and SVG, with a sheets.json of sizes and 9-slice borders: 34 pieces from the Carved Wood theme, "
                "15 white icons and 3 colour icons.",
        faq=lambda: [
            ("Which engines does it work with?",
             "Any engine that loads PNG or SVG. Godot 4 gets ready-made themes; Unity, GameMaker, Construct, Phaser and others use the PNGs with their nine-slice feature and the border values from sheets.json."),
            ("Is it pixel art?", "No. It is smooth vector-style art, sharp at 1x and 2x; the SVGs scale to any size."),
            ("Can I mix themes?", "Yes. Every theme has the same pieces at the same sizes, so a gold close button drops into a stone window."),
            ("Can I recolour it?", "Yes. Edit the SVGs or tint the PNGs; palette.json has every colour used."),
            ("Are item illustrations included?", "The icons are flat symbol-style icons (white, dark and 37 in colour), not painted item art."),
            ("Is there a free version?", "Yes: Crisp Quest Free has 52 pieces to test in your project. The same 52 pieces can be previewed on this site's UI kit preview."),
            ("Can I use it in a commercial game, and do I have to give credit?",
             "It is royalty-free for commercial and non-commercial projects and no attribution is needed. You may not resell or redistribute the assets themselves, modified or not."),
            ("Was AI used to make it?", "Yes, for the code. " + UI_MADE),
        ],
        shots=[("screenshot_rpg.png", "A mock RPG screen built with Crisp Quest: inventory, character sheet, dialogue box, hotbar and quest tracker"),
               ("screenshot_themes.png", "The 6 material themes of Crisp Quest"),
               ("screenshot_inventory.png", "Inventory, equipment slots and hotbar in each of the six Crisp Quest themes"),
               ("screenshot_icons.png", "The fantasy icons included in Crisp Quest"),
               ("screenshot_contents.png", "Contents sheet of the Crisp Quest themed pieces"),
               ("screenshot_widgets.png", "Crisp Quest widgets (buttons, bars, sliders and inputs) shown in several themes")],
    ),
]

# Sanity: the single prices must add up to the bundle's "regular" price.
assert "%.2f" % sum(float(p["price"]) for p in PACKS) == BUNDLE["singles"], sum(float(p["price"]) for p in PACKS)
