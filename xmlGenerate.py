import readXML
import numpy as np
import random

# -------------------- LOAD DATA --------------------
score = readXML.grabData()

# -------------------- FLATTEN SCORE TO TIME FRAMES --------------------
# Takes the data from the XML and creates sequences of notes at each time step
note_frames = []
for measure in score:
    for slot in measure:
        if not slot:
            note_frames.append(["00"])
        else:
            note_frames.append(slot)

# -------------------- DEDUPLICATE FRAMES --------------------
# Helps to remove doubled frames (reduces the probability of staying on the same sequence)
deduped_frames = []
counter = 0
for i in range(len(note_frames)):
    if i == 0:
        deduped_frames.append(note_frames[0])
    elif counter > 6:
        deduped_frames.append(note_frames[i])
        counter = 0
    elif note_frames[i] != note_frames[i-1]:
        deduped_frames.append(note_frames[i])
        counter = 0
    else:
        counter += 1

# -------------------- BUILD CHORD TUPLES --------------------
# Turns the chords into tuples for manipulation
def notes_to_chord_tuple(notes):
    res = []
    for n in notes:
        n = n.replace(" ", "") if n else "00"
        if n in ["00", "0", "", None]:
            res.append("00")
        else:
            res.append(n)
    return tuple(sorted(res))

chord_tuples = [notes_to_chord_tuple(frame) for frame in deduped_frames]

# -------------------- TRANSITION MATRIX --------------------
single_counts = {}
pair_counts = {}
triple_counts = {}
quadruple_counts = {}

# Counts all of the unique chords and chord pairs and keeps count in the dicts
for i, chord in enumerate(chord_tuples):
    single_counts[chord] = single_counts.get(chord, 0) + 1
    if i < len(chord_tuples) - 1:
        pair = (chord, chord_tuples[i + 1])
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
    if i < len(chord_tuples) - 2:
        triple = (chord, chord_tuples[i+1], chord_tuples[i+2])
        triple_counts[triple] = triple_counts.get(triple,0) + 1
    if i < len(chord_tuples) - 3:
        quad = (chord, chord_tuples[i+1], chord_tuples[i+2], chord_tuples[i+3])
        quadruple_counts[quad] = quadruple_counts.get(quad,0) + 1

chord_list = list(single_counts)
chord_index = {chord: i for i, chord in enumerate(chord_list)}

# -------------------- MARKOV CHAIN GENERATION --------------------
matrix = np.zeros((len(chord_list), len(chord_list)))

# creates a row stochastic matrix that iterates through every single possible pairing
# It's possible that there is a sink, but it's not that probable....
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

def getMatrix():
    return matrix

def getChordList():
    return chord_list

def getChordIndex():
    return chord_index
