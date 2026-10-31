# python show/build.py <id> lines  ->  quiz/vo/show-<id>/<i>.txt + .speed   (then: sh voice/voice.sh show-<id>)
# python show/build.py <id>        ->  show/<id>.timing.js (timeline for show3d.html) + show/<id>.raw.wav
# "Show it" reels (dark, one live number on top): the first frame is an action already happening, every step is drawn
# as it happens, and a counter moves while you watch. Captions run word by word from Whisper word timings of the voice.
import json, os, subprocess, sys, wave, pathlib
import numpy as np

HERE = pathlib.Path(__file__).parent
VO = HERE.parent / 'quiz' / 'vo'
SR, FPS = 48000, 30
FF = os.environ.get('FFMPEG', 'ffmpeg')
WPY = os.environ.get('WHISPER_PY', 'python')                 # a Python with faster-whisper installed
START, TAIL = .1, 1.4

# Facts for 'enter' (first visit to a site over HTTPS): DNS resolves the name to an IP, TCP opens with SYN / SYN-ACK / ACK,
# TLS agrees on session keys (key exchange) so the traffic is encrypted, then HTTP GET -> 200 OK, then the browser fetches the
# page's other files and renders. Timings depend on distance and caching, so the counter is labelled illustrative.
# line = (caption text, what the voice says, scene, robot pose, counter value in ms when the line ends)
# Every reel ends like the best explainers: one 'twist' line that flips the hook, then 'cta' = "send this to someone who..."
# (sends are what reach new people) with the share sheet and @mish.builds on screen. No recap list: it makes people swipe.
REELS = {
    'enter': {
        'kicker': 'WHAT HAPPENS WHEN YOU PRESS ENTER',
        'lines': [
            ('You press Enter. Less than half a second later, the page is on your screen.',
             'You press Enter. Less than half a second later, the page is on your screen.', 'key', 'wow', 0, ['Enter.', 'half']),
            ('In between, your request travels to a server and back.',
             'In between, your request travels to a server and back.', 'route', 'point-up-right', 6, ['server']),
            ('Step one: directions. DNS turns google.com into an address.',
             'Step one: directions. D N S turns google dot com into an address.', 'dns', 'explain', 42, ['DNS', 'address.']),
            ('Then a handshake. Three quick messages, so both sides know the line works.',
             'Then a handshake. Three quick messages, so both sides know the line works.', 'tcp', 'count', 118, ['handshake.', 'Three']),
            ('Then they agree on a secret key, so nobody in between can read a thing.',
             'Then they agree on a secret key, so nobody in between can read a thing.', 'tls', 'crossed', 196, ['secret', 'key,']),
            ('Only now does it ask for the page. The server answers: OK.',
             'Only now does it ask for the page. The server answers: okay.', 'http', 'present', 262, ['page.', 'OK.']),
            ('Your browser builds it, piece by piece.',
             'Your browser builds it, piece by piece.', 'render', 'thumbs-up', 300, ['builds']),
            ('All of that, in about three hundred milliseconds.',
             'All of that, in about three hundred milliseconds.', 'outro', 'shocked', 300, ['three', 'hundred', 'milliseconds.']),
            ('So the page never just loaded. It was mailed to you in pieces, in a third of a second.',
             'So the page never just loaded. It was mailed to you in pieces, in a third of a second.', 'twist', 'present', 300, ['mailed', 'pieces,']),
            ('Send this to the friend who says the internet is slow.',
             'Send this to the friend who says the internet is slow.', 'cta', 'wave', 300, ['Send', 'slow.']),
        ],
    },
    # Facts for 'tap' (contactless card payment, authorization only): the card's chip makes a one-time cryptogram for this
    # transaction (EMV), the terminal sends the authorization request to the shop's payment processor (acquirer side), the card
    # network routes it to the issuing bank, which checks the cryptogram, the funds/limit and fraud rules, and the approve/decline
    # answer goes back the same way. Usually a second or two; the counter is labelled illustrative.
    'tap': {
        'kicker': 'WHAT HAPPENS WHEN YOU TAP YOUR CARD',
        'lines': [
            ('You tap your card. A second or two later, the screen says approved.',
             'You tap your card. A second or two later, the screen says approved.', 'tap', 'wow', 0, ['tap', 'approved.']),
            ('In that instant, the chip signs this one payment with a code that only works once.',
             'In that instant, the chip signs this one payment, with a code that only works once.', 'chip', 'point-up-right', 80, ['chip', 'once.']),
            ('The terminal sends it to the shop\'s payment processor.',
             'The terminal sends it to the shop\'s payment processor.', 'shop', 'explain', 350, ['processor.']),
            ('The card network finds your bank, wherever it is.',
             'The card network finds your bank, wherever it is.', 'network', 'present', 700, ['network', 'bank,']),
            ('Your bank checks three things. Is it really your card? Is there money? Does it look like fraud?',
             'Your bank checks three things. Is it really your card? Is there money? Does it look like fraud?', 'bank', 'count', 1400, ['three', 'card?', 'money?', 'fraud?']),
            ('Then the answer flies all the way back.',
             'Then the answer flies all the way back.', 'back', 'point-up-left', 1750, ['back.']),
            ('Approved. All of that in under two seconds.',
             'Approved. All of that in under two seconds.', 'approved', 'shocked', 1800, ['Approved.', 'two', 'seconds.']),
            ('So your card never paid anything. It asked your bank, and your bank said yes.',
             'So your card never paid anything. It asked your bank, and your bank said yes.', 'twist', 'present', 1800, ['never', 'paid', 'yes.']),
            ('Send this to someone who still pays cash.',
             'Send this to someone who still pays cash.', 'cta', 'wave', 1800, ['Send', 'cash.']),
        ],
    },
    # Facts for 'cloud' (cloud gaming, generic, no service named): the game runs on a server with a GPU in a data center; your
    # controller input is sent over the network; the server renders the frame, a hardware encoder compresses it as video
    # (H.264/HEVC/AV1) and streams it back; your device decodes and shows it, typically at 60 frames a second or more.
    # Button-to-screen latency on a good connection is tens of milliseconds; the counter is labelled illustrative.
    'cloud': {
        'kicker': 'WHAT HAPPENS IN CLOUD GAMING',
        'lines': [
            ('You press jump. The game isn\'t even running on your device.',
             'You press jump. The game isn\'t even running on your device.', 'press', 'wow', 0, ['jump.', "isn't"]),
            ('Your button press flies to a data center as a tiny packet.',
             'Your button press flies to a data center, as a tiny packet.', 'input', 'point-up-right', 15, ['data', 'center']),
            ('There, a graphics card runs the game and draws the next frame.',
             'There, a graphics card runs the game, and draws the next frame.', 'gpu', 'explain', 28, ['graphics', 'card', 'frame.']),
            ('Then that frame gets squeezed into video in a few milliseconds.',
             'Then that frame gets squeezed into video, in a few milliseconds.', 'encode', 'count', 34, ['squeezed', 'video']),
            ('It streams back to you, and your device unpacks it onto the screen.',
             'It streams back to you, and your device unpacks it onto the screen.', 'stream', 'present', 55, ['streams', 'back']),
            ('Sixty times a second. About fifty milliseconds from button to screen.',
             'Sixty times a second. About fifty milliseconds, from button to screen.', 'repeat', 'shocked', 55, ['Sixty', 'fifty', 'milliseconds']),
            ("So you're not playing the game. You're watching a live video of it that listens to your thumbs.",
             "So you're not playing the game. You're watching a live video of it, that listens to your thumbs.", 'twist', 'present', 55, ['watching', 'video', 'thumbs.']),
            ('Send this to the friend who blames lag for every loss.',
             'Send this to the friend who blames lag for every loss.', 'cta', 'wave', 55, ['Send', 'lag']),
        ],
    },
    # Facts for 'faceid' (generic "face unlock" as on recent phones with a depth camera): an infrared flood illuminator lights
    # the face (works in the dark), a dot projector casts more than 30,000 invisible infrared dots, an infrared camera reads them
    # into a depth map, a secure chip on the phone compares it with the stored template (the data stays on the device). The
    # published false-match odds for a random person are less than 1 in 1,000,000. A flat photo has no depth, so it fails.
    # Rendered in Blender (cgi/faceid.py); the counter here counts dots, not milliseconds.
    'faceid': {
        'kicker': 'WHEN YOUR PHONE SEES YOU',
        'unit': 'dots',
        'badges': {'unlock': ['1 in 1,000,000', 'less']},     # scene: [text shown in the counter, from this word on]
        'lines': [
            ('Your phone just shot invisible dots at your face. Guess how many.',     # answered by 'dots' (30,000)
             'Your phone just shot invisible dots at your face. Guess how many.', 'glance', 'wow', 0, ['invisible', 'Guess']),
            ('First, invisible infrared light washes over your face. That\'s why it works in the dark.',
             'First, invisible infrared light washes over your face. That\'s why it works in the dark.', 'flood', 'point-up-right', 0, ['infrared', 'dark.']),
            ('Then a tiny projector fires more than thirty thousand dots onto it.',
             'Then a tiny projector fires more than thirty thousand dots onto it.', 'dots', 'shocked', 30000, ['thirty', 'thousand', 'dots']),
            ('A camera reads where every dot lands, and builds a depth map of your face.',
             'A camera reads where every dot lands, and builds a depth map of your face.', 'depth', 'explain', 30000, ['depth', 'map']),
            ('A chip inside compares it with the map it saved. Your face never leaves the phone.',
             'A chip inside compares it with the map it saved. Your face never leaves the phone.', 'compare', 'skeptical', 30000, ['compares', 'never']),
            ('That\'s why a photo of you can\'t fool it. A photo is flat.',
             'That\'s why a photo of you can\'t fool it. A photo is flat.', 'photo', 'crossed', 30000, ['photo', 'flat.']),
            ('Match. Unlocked. The odds a stranger gets in: less than one in a million.',
             'Match. Unlocked. The odds a stranger gets in: less than one in a million.', 'unlock', 'thumbs-up', 30000, ['Unlocked.', 'million.']),
            ('So your phone never looked at you. It touched your face with thirty thousand points of light.',
             'So your phone never looked at you. It touched your face, with thirty thousand points of light.', 'twist', 'present', 30000, ['touched', 'light.']),
            ('Send this to the friend who still types a passcode.',
             'Send this to the friend who still types a passcode.', 'cta', 'wave', 30000, ['Send', 'passcode.']),
        ],
    },
    # Facts for 'ask' (a chat AI answering, generic, no product named): text is split into tokens, each token becomes a vector
    # of numbers (embedding); inference runs on GPUs in a data center; the model's parameters (billions of learned numbers) are
    # multiplied with those vectors; self-attention lets every token weigh every other token; the output is a probability for
    # each possible next token, one is picked, appended, and the model runs again (autoregressive) - which is why answers
    # stream word by word. Counter = tokens written: the answer 'The capital of France is Paris.' is about 7 tokens; values illustrative. Rendered in Blender (cgi/ask.py).
    'ask': {
        'kicker': 'WHEN YOU ASK AN AI',
        'unit': 'tokens',
        'lines': [
            ('Guess how many times an AI runs, just to write one sentence.',        # answered by the twist (7)
             'Guess how many times an AI runs, just to write one sentence.', 'send', 'wow', 0, ['Guess', 'one']),
            ('Your words get chopped into tokens, and each one becomes a long list of numbers.',
             'Your words get chopped into tokens, and each one becomes a long list of numbers.', 'tokens', 'count', 0, ['tokens,', 'numbers.']),
            ('Those numbers fly to a data center, into racks of graphics chips.',
             'Those numbers fly to a data center, into racks of graphics chips.', 'datacenter', 'point-up-right', 0, ['data', 'center,', 'chips.']),
            ('There, billions of numbers the model learned in training get multiplied with yours.',
             'There, billions of numbers the model learned in training get multiplied with yours.', 'weights', 'explain', 0, ['billions', 'learned']),
            ('Every word checks every other word, to work out what you actually mean.',
             'Every word checks every other word, to work out what you actually mean.', 'attention', 'skeptical', 0, ['every', 'other', 'mean.']),
            ('Out comes one thing: the most likely next piece of the answer.',
             'Out comes one thing: the most likely next piece of the answer.', 'predict', 'shocked', 1, ['one', 'next']),
            ('That piece goes back in, and the whole thing runs again. For every single token.',
             'That piece goes back in, and the whole thing runs again. For every single token.', 'loop', 'present', 7, ['again.', 'every']),
            ('That\'s why the answer appears word by word. It\'s being written while you watch.',
             'That\'s why the answer appears word by word. It\'s being written while you watch.', 'why', 'thumbs-up', 7, ['word', 'by', 'written']),
            ('Seven runs, for one sentence. The answer didn\'t exist until you asked.',
             'Seven runs, for one sentence. The answer didn\'t exist until you asked.', 'twist', 'present', 7, ['Seven', "didn't", 'exist']),
            ('Send this to the friend who thinks AI just googles stuff.',
             'Send this to the friend who thinks AI just googles stuff.', 'cta', 'wave', 7, ['Send', 'googles']),
        ],
    },
    # Facts for 'ocean' (all sourced): over 99% of international data rides submarine cables (ITU); deep-sea
    # cable about as wide as a garden hose, armoured and buried near shore (TeleGeography); inside: glass fibres, copper power
    # layer, steel wires, polyethylene; fibres hair-thin, data as light; boosters every few dozen km; NY-London round trip ~60 ms;
    # fish bites caused zero faults 2007-2014 (ICPC/TeleGeography), most faults are fishing gear and anchors; repair ships grapnel
    # the cable up and splice it on deck. Rendered in Blender (cgi/ocean.py). Counter = round-trip milliseconds.
    'ocean': {
        'kicker': 'WHEN YOUR MESSAGE CROSSES AN OCEAN',
        'unit': 'ms',
        'badges': {'share': ['99%+', 'Over']},
        'lead': 3,                                            # lines with the short gap after them: the cold open plus the hook
        'lines': [
            ('Why didn\'t this break the internet?',          # cold open: the shark bite (frames reused from the 'shark' scene)
             'Why didn\'t this break the internet?', 'cold', 'shocked', 0, ['break', 'internet?']),
            ('"The cloud" isn\'t in the sky. It\'s at the bottom of the ocean.',
             'The cloud isn\'t in the sky. It\'s at the bottom of the ocean.', 'hook', 'wow', 0, ['cloud"', 'bottom', 'ocean.']),
            ('Hit send, and your message races to the coast.',
             'Hit send, and your message races to the coast.', 'coast', 'point-up-right', 0, ['send,', 'coast.']),
            ('There, it plunges into a cable on the sea floor.',
             'There, it plunges into a cable on the sea floor.', 'dive', 'shocked', 0, ['plunges', 'floor.']),
            ('Over 99% of data between continents travels this way.',
             'Over ninety-nine percent of data between continents travels this way.', 'share', 'explain', 0, ['99%', 'continents']),
            ('Out in the deep, it\'s about as wide as a garden hose.',
             'Out in the deep, it\'s about as wide as a garden hose.', 'hose', 'skeptical', 0, ['garden', 'hose.']),
            ('Near shore, it\'s wrapped in steel armour and buried in the sand.',
             'Near shore, it\'s wrapped in steel armour and buried in the sand.', 'armour', 'crossed', 0, ['armour', 'buried']),
            ('Cut it open: steel wires, copper, plastic, and glass at the very centre.',
             'Cut it open: steel wires, copper, plastic, and glass at the very centre.', 'cut', 'explain', 0, ['open:', 'glass']),
            ('Those glass fibres are as thin as a human hair.',
             'Those glass fibres are as thin as a human hair.', 'fibre', 'wow', 0, ['thin', 'hair.']),
            ('Your message becomes flashes of light, racing through the glass.',
             'Your message becomes flashes of light, racing through the glass.', 'light', 'point-up-right', 0, ['flashes', 'light,']),
            ('Every few dozen kilometres, a booster makes the fading light strong again.',
             'Every few dozen kilometres, a booster makes the fading light strong again.', 'booster', 'explain', 0, ['booster', 'strong']),
            ('It crosses the ocean and back in about sixty milliseconds.',
             'It crosses the ocean and back in about sixty milliseconds.', 'latency', 'shocked', 60, ['sixty', 'milliseconds.']),
            ('Sharks have bitten cables. But from 2007 to 2014, fish caused zero faults.',
             'Sharks have bitten cables. But from two thousand seven to twenty fourteen, fish caused zero faults.', 'shark', 'skeptical', 60, ['Sharks', 'zero']),
            ('The real danger? Fishing gear and ship anchors.',
             'The real danger? Fishing gear, and ship anchors.', 'anchor', 'crossed', 60, ['danger?', 'anchors.']),
            ('When one breaks, a ship hooks it off the sea floor and fixes it on deck.',
             'When one breaks, a ship hooks it off the sea floor, and fixes it on deck.', 'repair', 'present', 60, ['hooks', 'deck.']),
            ('So "the cloud" is a hair-thin thread of glass, lying in the dark.',
             'So the cloud is a hair-thin thread of glass, lying in the dark.', 'twist', 'present', 60, ['thread', 'glass,']),
            ('Send this to the friend who thinks the internet comes from satellites.',
             'Send this to the friend who thinks the internet comes from satellites.', 'cta', 'wave', 60, ['Send', 'satellites.']),
        ],
    },
    # Facts for 'call' (group video call, generic): the camera captures ~30 frames a second; video codecs send mostly what
    # changed since the previous frame; acoustic echo cancellation removes the far-end audio your mic picks up from your
    # speakers; in group calls a server (SFU) forwards each person's stream to everyone else; the receiver decodes and plays
    # audio and video in sync. Conversation feels natural under roughly 150 ms one way (ITU-T G.114); counter is illustrative.
    'call': {
        'kicker': 'WHAT HAPPENS IN A VIDEO CALL',
        'lines': [
            ('You say hi on a video call. A split second later, your friends hear it.',
             'You say hi on a video call. A split second later, your friends hear it.', 'hi', 'wave', 0, ['hi', 'split']),
            ('First, your camera takes about thirty pictures every second.',
             'First, your camera takes about thirty pictures every second.', 'camera', 'point-up-right', 33, ['thirty', 'pictures']),
            ('Each picture is squeezed down to only what changed since the last one.',
             'Each picture is squeezed down, to only what changed since the last one.', 'squeeze', 'explain', 55, ['squeezed', 'changed']),
            ('Your mic gets cleaned too, so your friends never hear their own echo.',
             'Your mic gets cleaned too, so your friends never hear their own echo.', 'echo', 'skeptical', 75, ['cleaned', 'echo.']),
            ('A server in the middle copies your stream to everyone in the call.',
             'A server in the middle copies your stream, to everyone in the call.', 'server', 'present', 125, ['server', 'everyone']),
            ('Their app unpacks it and plays your face and voice in sync.',
             'Their app unpacks it, and plays your face and voice in sync.', 'arrive', 'thumbs-up', 150, ['face', 'voice', 'sync.']),
            ('Under about 150 milliseconds, so it feels like talking face to face.',
             'Under about a hundred and fifty milliseconds, so it feels like talking face to face.', 'outro', 'shocked', 150, ['150', 'milliseconds,']),
            ('So you never saw your friends. You saw thirty fresh pictures a second, rebuilt from what changed.',
             'So you never saw your friends. You saw thirty fresh pictures a second, rebuilt from what changed.', 'twist', 'present', 150, ['never', 'saw', 'rebuilt']),
            ("Send this to the friend who always says you're frozen.",
             "Send this to the friend who always says you're frozen.", 'cta', 'wave', 150, ['Send', 'frozen.']),
        ],
    },
}

def readwav(p):
    with wave.open(str(p)) as w: return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768

SFX = HERE.parent / 'sfx' / 'cc0'
_cache = {}
def load(name):
    if name not in _cache:
        raw = subprocess.run([FF, '-v', 'error', '-i', str(SFX / f'{name}.mp3'), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
        _cache[name] = np.frombuffer(raw, dtype='<i2').astype(float) / 32768
    return _cache[name]

def put(buf, name, t, gain):
    x = load(name) * gain; i = max(0, int(t * SR)); j = min(len(buf), i + len(x)); buf[i:j] += x[:j - i]

# visual events inside each scene (seconds after the line starts), the same numbers show3d.html animates with
EVENTS = {'key': [('pop', .0, .35)], 'route': [('whoosh', .3, .25)], 'dns': [('pop', .5, .3), ('tick', 1.6, .3), ('pop', 2.4, .35)],
          'tcp': [('blip', .9, .25), ('blip', 1.7, .25), ('blip', 2.5, .25)], 'tls': [('pop', 1.4, .35)],
          'http': [('whoosh', .3, .2), ('pop', 2.2, .35)], 'render': [('tick', .3, .25), ('tick', .7, .25), ('tick', 1.1, .25)],
          'outro': [('pop', .2, .4)], 'cta': [],
          'tap': [('pop', .0, .35)], 'chip': [('blip', .6, .3)], 'shop': [('whoosh', .3, .25)], 'network': [('whoosh', .4, .25)],
          'bank': [('tick', 1.6, .35), ('tick', 2.8, .35), ('tick', 4.0, .35)], 'back': [('whoosh', .2, .25)], 'approved': [('pop', .05, .45)],
          'press': [('pop', .0, .35)], 'input': [('whoosh', .3, .25)], 'gpu': [('blip', .8, .3)], 'encode': [('tick', .6, .3), ('tick', 1.0, .3)],
          'stream': [('whoosh', .2, .25)], 'repeat': [('pop', .1, .35)],
          'hi': [('pop', .0, .3)], 'camera': [('tick', .5, .25), ('tick', .9, .25), ('tick', 1.3, .25)], 'squeeze': [('blip', .9, .3)],
          'echo': [('pop', 1.6, .3)], 'server': [('whoosh', .3, .25)], 'arrive': [('pop', .4, .35)]}

def sfx(lines, n):
    b = np.zeros(n)
    for k, L in enumerate(lines):
        if k: put(b, 'whoosh', L['t0'] - .12, .2)
        for name, dt, g in EVENTS.get(L['scene'], []): put(b, name, L['t0'] + dt, g)
    return b

def music(rms, n, name='music2'):
    m = load(name); m = np.tile(m, n // len(m) + 1)[:n]; m = m / (np.abs(m).max() + 1e-9)
    talk = np.repeat(np.convolve((rms > .08).astype(float), np.ones(9) / 9, 'same'), SR // FPS)
    talk = np.pad(talk, (0, max(0, n - len(talk))))[:n]
    g = (.13 - .06 * talk) * np.clip(np.arange(n) / (.6 * SR), 0, 1) * np.clip((n - np.arange(n)) / (1.4 * SR), 0, 1)
    return m * g

WORDS = r'''
import sys, json
from faster_whisper import WhisperModel
m = WhisperModel('small.en', device='cpu', compute_type='int8'); out = []
for f in sys.argv[1:]:
    segs, _ = m.transcribe(f, language='en', beam_size=5, word_timestamps=True)
    out.append([[w.start, w.end] for s in segs for w in s.words])
print(json.dumps(out))
'''

def build(rid):
    R = REELS[rid]; d = VO / f'show-{rid}'; n = len(R['lines'])
    V = [readwav(d / f'{i}.wav') for i in range(n)]
    W = json.loads(subprocess.run([WPY, '-I', '-c', WORDS] + [str(d / f'{i}.wav') for i in range(n)], capture_output=True, text=True, check=True).stdout)
    t, lines = START, []
    for i, (line, v, ww) in enumerate(zip(R['lines'], V, W)):
        cap, _, scene, pose, ms, hot = line
        dur = len(v) / SR; words = cap.split()
        if len(ww) == len(words): st = [a for a, _ in ww]
        else:                                                           # count differs (DNS, google.com): spread by length
            c = np.cumsum([0] + [len(x) + 2 for x in words[:-1]]); st = list(c / (c[-1] + len(words[-1]) + 2) * (ww[-1][1] if ww else dur))   # spoken part only, not trailing silence
        lines.append({'t0': round(t, 3), 't1': round(t + dur, 3), 'scene': scene, 'ms': ms,
                      'words': [{'w': w, 't': round(t + s, 3), 'hot': w in hot} for w, s in zip(words, st)]})
        t += dur + (.14 if i < R.get('lead', 2) or i >= n - 2 else .3)
    end = t + TAIL
    for i, L in enumerate(lines): L['end'] = lines[i + 1]['t0'] if i + 1 < n else round(end, 3)
    out = np.zeros(int(end * SR) + 1)
    for L, v in zip(lines, V): i = int(L['t0'] * SR); out[i:i + len(v)] += v
    out = out / (np.abs(out).max() + 1e-9) * .9
    hop = SR // FPS
    rms = np.array([np.sqrt((out[i:i + hop] ** 2).mean()) for i in range(0, len(out) - hop, hop)])
    mix = out + sfx(lines, len(out)) + music(rms, len(out))
    mix = mix / (np.abs(mix).max() + 1e-9) * .9
    with wave.open(str(HERE / f'{rid}.raw.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
    rms = np.convolve(rms, [.25, .5, .25], 'same'); rms = np.clip(rms / (np.percentile(rms[rms > 1e-3], 95) + 1e-9), 0, 1)
    poses = [{'t': 0 if i == 0 else round(L['t0'] - .05, 3), 'pose': R['lines'][i][3]} for i, L in enumerate(lines)]
    (HERE / f'{rid}.timing.js').write_text('window.SHOW = ' + json.dumps({'end': round(end, 3), 'kicker': R['kicker'], 'unit': R.get('unit', 'ms'), 'badges': R.get('badges', {}), 'lines': lines,
        'poses': poses, 'mouth': [round(float(x), 3) for x in rms]}) + '\n', encoding='utf-8')
    print(f'{rid}: {end:.1f}s, {n} lines')

if len(sys.argv) > 2 and sys.argv[2] == 'lines':
    d = VO / f'show-{sys.argv[1]}'; d.mkdir(parents=True, exist_ok=True)
    L = REELS[sys.argv[1]]['lines']; n = len(L)
    for i, line in enumerate(L):
        (d / f'{i}.txt').write_text(line[1], encoding='utf-8')
        (d / f'{i}.speed').write_text('1.15,1.08' if i == 0 else '1.15' if i < 2 or i >= n - 2 else '1.0', encoding='utf-8')
    print(n, 'lines')
else:
    build(sys.argv[1])
