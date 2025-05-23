import jeffHEATON
import numpy as np
import random
import time
import fluidsynth
import db
import os

# -------------------- SETUP --------------------
songName = "fein"
fileType = "wav"
if not os.path.isfile("musicTest.db"):
    db.setup()

# -------------------- LOAD DATA --------------------
# data = jeffHEATON.jeffCode(songName, fileType)

# -------------------- STORE DATA IN DB --------------------
# for frame_index, bar_data in enumerate(data):
#     notes = [bar_data[i][1] if i < len(bar_data) else "N/A" for i in range(8)]
#     influences = [bar_data[i][2] if i < len(bar_data) else 0.0 for i in range(8)]
#
#     db.addSongEntry(
#         songName,
#         frame_index,
#         *notes,
#         *influences
#     )

data = db.getAllTableData("songs", "songName", songName)

# -------------------- PREPROCESS --------------------
note_data = []
influence_data = []

for line in data:
    notes = list(line[3:11])
    influences = list(line[11:])

    while len(notes) < 8:
        notes.append("N/A")
    while len(influences) < 8:
        influences.append(0)

    note_data.append(notes)
    influence_data.append(influences)

# more preprocess

note_data = np.array(note_data, dtype=object)
influence_data = np.array(influence_data, dtype=float)

# -------------------- STANDARDIZE INFLUENCE --------------------

means = np.mean(influence_data, axis=1)
stds = np.std(influence_data, axis=1)

for count, line in enumerate(influence_data):
    for counter, item in enumerate(line):
        if item < means[count] - 1*stds[count]:
            note_data[count][counter] = "N/A"
            influence_data[count][counter] = "00"

stds[stds == 0] = 1e-8

# normalized = (influence_data - means[:, None]) / stds[:, None]
# influence_data[normalized < -1] = 0

na_mask = (note_data == "N/A")
note_data[na_mask] = "00"
influence_data[na_mask] = 0

# -------------------- DEDUPLICATE --------------------
deduped_notes = [note_data[0].tolist()]
deduped_influences = [influence_data[0].tolist()]
counter = 0

for i in range(1, len(note_data)):
    if counter > 4:
        deduped_notes.append(note_data[i - 1].tolist())
        deduped_influences.append(influence_data[i - 1].tolist())
        counter = 0
    elif not np.array_equal(note_data[i], note_data[i - 1]):
        deduped_notes.append(note_data[i].tolist())
        deduped_influences.append(influence_data[i].tolist())
    else:
        counter += 1

# -------------------- BUILD CHORD STRINGS --------------------
import re

def split_chord_string(chord_string):
    # Handle the special case for "00"
    tokens = []
    i = 0
    while i < len(chord_string):
        if chord_string[i:i+2] == "00":
            tokens.append("00")
            i += 2
        elif chord_string[i+1] == '#':
            tokens.append(chord_string[i:i+3])  # e.g., C#4
            i += 3
        else:
            tokens.append(chord_string[i:i+2])  # e.g., C4
            i += 2
    return tokens

chords = []
for notes, influences in zip(deduped_notes, deduped_influences):
    sorted_notes = [note for note, _ in sorted(zip(notes, influences), reverse=True)]
    # chord = split_chord_string(sorted_notes)
    # print(sorted_notes)
    chords.append(sorted_notes)
# print(chords)

# -------------------- TRANSITION MATRIX --------------------
single_counts = {}
pair_counts = {}

for i, chord in enumerate(chords):
    chord_tuple = tuple(chord)
    single_counts[chord_tuple] = single_counts.get(chord_tuple, 0) + 1
    if i < len(chords) - 1:
        next_chord_tuple = tuple(chords[i + 1])
        pair = (chord_tuple, next_chord_tuple)
        pair_counts[pair] = pair_counts.get(pair, 0) + 1


chord_list = list(single_counts)
chord_index = {chord: i for i, chord in enumerate(chord_list)}

matrix = np.zeros((len(chord_list), len(chord_list)))

for from_chord in chord_list:
    i = chord_index[from_chord]
    row_sum = 0
    for to_chord in chord_list:
        j = chord_index[to_chord]
        count = pair_counts.get((from_chord, to_chord), 0)
        matrix[i, j] = count
        row_sum += count
    if row_sum == 0:
        matrix[i] = 1 / len(chord_list)
    else:
        matrix[i] /= row_sum

# -------------------- MARKOV CHAIN GENERATION --------------------
initial = random.choice(chord_list)
generated = [initial]

for _ in range(1000):
    i = chord_index[initial]
    probs = matrix[i]
    j = np.random.choice(len(chord_list), p=probs)
    next_chord = chord_list[j]

    generated.append(next_chord)
    initial = next_chord

# -------------------- CHORD PARSING --------------------
def parse_chord(chord_str):
    notes = []
    buf = ""
    for char in chord_str:
        buf += char
        if len(buf) == 2 or (len(buf) == 3 and buf[1] in "#b"):
            notes.append(buf)
            buf = ""
    return notes

note_sequences = [parse_chord(chord) for chord in generated]

# -------------------- MIDI PLAYBACK --------------------
def note_to_midi(note):
    if note in ["00", "0", "", None]:
        return None
    try:
        note_map = ['C', 'C#', 'D', 'D#', 'E', 'F',
                    'F#', 'G', 'G#', 'A', 'A#', 'B']
        if len(note) == 2:
            key, octave = note[0], int(note[1])
        elif len(note) == 3:
            key, octave = note[:2], int(note[2])
        else:
            return None
        return note_map.index(key) + 12 * (octave + 1)
    except:
        return None

SOUNDFONT_PATH = "FluidR3_GM/FluidR3_GM.sf2"
fs = fluidsynth.Synth()
fs.start()
sfid = fs.sfload(SOUNDFONT_PATH)
fs.program_select(0, sfid, 0, 0)

def play_chords(chords, duration=0.1, velocity=100):
    current = set()
    for chord in chords:
        print("Now playing:", chord)
        next_notes = set(filter(None, (note_to_midi(n) for n in chord)))
        for note in current - next_notes:
            fs.noteoff(0, note)
        for note in next_notes - current:
            fs.noteon(0, note, velocity)
        time.sleep(duration)
        current = next_notes
    for note in current:
        fs.noteoff(0, note)

play_chords(note_sequences, duration=0.1)
fs.delete()
