import xmlGenerate
import random
import numpy as np
import fluidsynth
import time

matrix = xmlGenerate.getMatrix()
chord_list = xmlGenerate.getChordList()
chord_index = xmlGenerate.getChordIndex()

# MATRIX MANIPULATION
# Higher = more entropy, Lower = less changes
# Emphasizes/Minimizes the existing row probability vectors
def scale_temperature(matrix, temperature=1.0):
    assert temperature > 0, "Temperature must be positive"
    log_matrix = np.log(matrix + 1e-9)  # Avoid log(0)
    scaled = np.exp(log_matrix / temperature)
    scaled = np.maximum(scaled, 0)
    scaled /= scaled.sum(axis=1, keepdims=True)
    return scaled

def inject_noise(matrix, epsilon=0.01):
    noisy = matrix + epsilon * np.random.rand(*matrix.shape)
    noisy /= noisy.sum(axis=1, keepdims=True)  # Renormalize rows
    return noisy



matrix = scale_temperature(matrix, 0.5)
# matrix = inject_noise(matrix, 0.0001)


# --------------- TRAJECTORY THROUGH THE ROW STOCHASTIC MATRIX ----------
initial = random.choice(chord_list)
generated = [initial]

for _ in range(1000):
    i = chord_index[initial]
    probs = matrix[i]
    j = np.random.choice(len(chord_list), p=probs)
    next_chord = chord_list[j]
    generated.append(next_chord)
    initial = next_chord

note_sequences = list(generated)

# -------------------- MIDI PLAYBACK --------------------
def note_to_midi(note):
    if note in ["00", "0", "", None]:
        return None
    try:
        note = note.replace('*', '')  # Handle natural sign as a no-op

        # Expect format like "D4b" or "C4#"
        if len(note) < 2:
            return None

        pitch_letter = note[0]
        if note[2:] in ('#', 'b'):  # with accidental
            octave = int(note[1])
            accidental = note[2]
        else:
            octave = int(note[1])
            accidental = ''

        pitch = pitch_letter + accidental

        # Convert flats to equivalent sharps
        flat_to_sharp = {
            'Cb': 'B', 'Db': 'C#', 'Eb': 'D#', 'Fb': 'E',
            'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'
        }
        pitch = flat_to_sharp.get(pitch, pitch)

        note_map = ['C', 'C#', 'D', 'D#', 'E', 'F',
                    'F#', 'G', 'G#', 'A', 'A#', 'B']

        return note_map.index(pitch) + 12 * (octave + 1)
    except Exception as e:
        print(f"Error converting note '{note}': {e}")
        return None




SOUNDFONT_PATH = "../FluidR3_GM/FluidR3_GM.sf2"
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

try:
    play_chords(note_sequences, duration=0.2)
except KeyboardInterrupt:
    print("Playback interrupted by user (Ctrl+C).")
finally:
    fs.delete()
    print("Fluidsynth resources cleaned up.")
