import xmlGenerate
import random
import numpy as np
import fluidsynth
import time

def find_steady_state(P):
    eigenvalues, eigenvectors = np.linalg.eig(P.T)
    steady_state_vector = None
    for i, eigenvalue in enumerate(eigenvalues):
        if np.isclose(eigenvalue, 1):
            steady_state_vector = eigenvectors[:, i].real
            break
    if steady_state_vector is not None:
        steady_state_vector /= steady_state_vector.sum()
        return steady_state_vector
    else:
        return None

matrix = xmlGenerate.getMatrix()
chord_list = xmlGenerate.getChordList()
chord_index = xmlGenerate.getChordIndex()

numpyMatrix = np.array(matrix)

steady_state = find_steady_state(numpyMatrix)

chordSteady = []

if steady_state is not None:
    for count, state in enumerate(steady_state):
        chordSteady.append([chord_list[count], state])
    sortedChordStead = sorted(chordSteady, key=lambda x: x[1], reverse=True)
    print(sortedChordStead)
else:
    print("No steady state found.")
