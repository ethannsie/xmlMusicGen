import jeffHEATON
import numpy as np
import random
import time
import fluidsynth
import db
import os

# -------------------- SETUP --------------------
songName = "blue"
fileType = "wav"
if not os.path.isfile("musicTest.db"):
    db.setup()

# -------------------- LOAD DATA --------------------
data = db.getAllTableData("songs", "songName", songName)

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

note_data = np.array(note_data, dtype=object)
influence_data = np.array(influence_data, dtype=float)

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

generated = note_data
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

play_chords(note_sequences, duration=0.3)
fs.delete()
