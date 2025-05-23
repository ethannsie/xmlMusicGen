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
data = jeffHEATON.jeffCode(songName, fileType)

# -------------------- STORE DATA IN DB --------------------
for frame_index, bar_data in enumerate(data):
    notes = [bar_data[i][1] if i < len(bar_data) else "N/A" for i in range(8)]
    influences = [bar_data[i][2] if i < len(bar_data) else 0.0 for i in range(8)]

    db.addSongEntry(
        songName,
        frame_index,
        *notes,
        *influences
    )
