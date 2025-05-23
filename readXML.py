import xml.etree.ElementTree as ET

def parse_musicxml_all_note_info(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'

    notes_data = []

    for part in root.findall(f"{ns}part"):
        part_id = part.attrib.get('id')
        for measure in part.findall(f"{ns}measure"):
            measure_number = measure.attrib.get('number')
            current_time = 0
            last_nonchord_time = 0
            divisions = 1
            attributes = measure.find(f"{ns}attributes")
            if attributes is not None:
                divisions_tag = attributes.find(f"{ns}divisions")
                if divisions_tag is not None:
                    divisions = int(divisions_tag.text)

            for elem in measure.findall(f"{ns}note"):
                is_chord = elem.find(f"{ns}chord") is not None
                note_start_time = last_nonchord_time if is_chord else current_time

                note_info = {
                    'measure': measure_number,
                    'part_id': part_id,
                    'staff': None,
                    'voice': None,
                    'is_rest': False,
                    'pitch': None,
                    'octave': None,
                    'alter': None,
                    'duration': None,
                    'type': None,
                    'dot': False,
                    'tie': [],
                    'notations': [],
                    'accidental': None,
                    'chord': is_chord,
                    'start_time': note_start_time,
                }

                # Voice
                voice = elem.find(f"{ns}voice")
                if voice is not None:
                    note_info['voice'] = int(voice.text)
                # Staff
                staff = elem.find(f"{ns}staff")
                if staff is not None:
                    note_info['staff'] = int(staff.text)
                # Rest or Pitch
                if elem.find(f"{ns}rest") is not None:
                    note_info['is_rest'] = True
                else:
                    pitch = elem.find(f"{ns}pitch")
                    if pitch is not None:
                        step = pitch.find(f"{ns}step")
                        octave = pitch.find(f"{ns}octave")
                        alter = pitch.find(f"{ns}alter")
                        note_info['pitch'] = step.text if step is not None else None
                        note_info['octave'] = int(octave.text) if octave is not None else None
                        note_info['alter'] = int(alter.text) if alter is not None else None
                # Duration
                duration = elem.find(f"{ns}duration")
                note_info['duration'] = int(duration.text) if duration is not None else None
                # Type (eighth, quarter, etc.)
                typ = elem.find(f"{ns}type")
                note_info['type'] = typ.text if typ is not None else None
                # Dotted note
                dot = elem.find(f"{ns}dot")
                note_info['dot'] = dot is not None
                # Tie
                for tie in elem.findall(f"{ns}tie"):
                    if 'type' in tie.attrib:
                        note_info['tie'].append(tie.attrib['type'])
                # Notations (slurs, ties, articulations, etc.)
                notations = elem.find(f"{ns}notations")
                if notations is not None:
                    for n in notations:
                        if n.tag.endswith('tied') and 'type' in n.attrib:
                            note_info['notations'].append({'tied': n.attrib['type']})
                        elif n.tag.endswith('slur') and 'type' in n.attrib:
                            note_info['notations'].append({'slur': n.attrib['type']})
                        elif n.tag.endswith('articulations'):
                            for art in n:
                                note_info['notations'].append(art.tag.split('}')[-1])
                        elif n.tag.endswith('dynamics'):
                            for dyn in n:
                                note_info['notations'].append(dyn.tag.split('}')[-1])
                # Accidental
                accidental = elem.find(f"{ns}accidental")
                if accidental is not None:
                    note_info['accidental'] = accidental.text

                notes_data.append(note_info)

                # Only advance current_time if not a chord note
                if not is_chord and duration is not None:
                    current_time += int(duration.text)
                    last_nonchord_time = note_info['start_time']

    # Group notes by measure
    measureData = []
    data = []
    last_measure = None
    for note in notes_data:
        measure = int(note['measure'])
        if last_measure is None or measure != last_measure:
            if data:
                measureData.append(data)
            data = [f"measure {measure}"]
            last_measure = measure
        data.append(note)
    if data:
        measureData.append(data)

    return measureData

def notes_to_uniform_grid(measureData):
    notesOnMeasures = []
    for measureCount, measure in enumerate(measureData):
        notesOnMeasures.append([[] for _ in range(64)])
        staff1MaxTime = 0
        staff2MinTime = None
        staff1MinTime = None
        staff2MaxTime = 0

        # Find min/max for each staff
        for note in measure[1:]:
            if note['staff'] == 1:
                if staff1MinTime is None:
                    staff1MinTime = note['start_time']
                else:
                    staff1MinTime = min(staff1MinTime, note['start_time'])
                staff1MaxTime = max(staff1MaxTime, note['start_time'] + (note['duration'] if note['duration'] else 0))
            if note['staff'] == 2:
                if staff2MinTime is None:
                    staff2MinTime = note['start_time']
                else:
                    staff2MinTime = min(staff2MinTime, note['start_time'])
                staff2MaxTime = max(staff2MaxTime, note['start_time'] + (note['duration'] if note['duration'] else 0))

        if staff2MinTime is None:
            staff2MinTime = 0
        if staff1MinTime is None:
            staff1MinTime = 0

        staff2Range = staff2MaxTime - staff2MinTime if staff2MaxTime > staff2MinTime else 1
        staff1Range = staff1MaxTime - staff1MinTime if staff1MaxTime > staff1MinTime else 1

        for note in measure[1:]:
            if not note['is_rest']:
                startTime = int(note['start_time'])
                duration = int(note['duration']) if note['duration'] else 0
                note_str = str(note['pitch']) + str(note['octave']) if note['pitch'] and note['octave'] is not None else ""
                if note.get('accidental') == "flat":
                    note_str += "b"
                elif note.get('accidental') == "sharp":
                    note_str += "#"
                elif note.get('accidental') == "natural":
                    note_str += "*"

                if note['staff'] == 1:
                    grid_start = int(round((startTime - staff1MinTime) * 64 / staff1Range)) if staff1Range else 0
                    grid_duration = int(round(duration * 64 / staff1Range)) if staff1Range else 1
                elif note['staff'] == 2:
                    grid_start = int(round((startTime - staff2MinTime) * 64 / staff2Range)) if staff2Range else 0
                    grid_duration = int(round(duration * 64 / staff2Range)) if staff2Range else 1
                else:
                    grid_start = 0
                    grid_duration = 0
                if grid_duration < 1:
                    grid_duration = 1

                for i in range(grid_duration):
                    idx = grid_start + i
                    if 0 <= idx < 64:
                        notesOnMeasures[measureCount][idx].append(note_str)
    return notesOnMeasures

def grabData():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_musicxml_uniform_grid.py <musicxml_file>")
        sys.exit(1)
    xml_path = sys.argv[1]
    measureData = parse_musicxml_all_note_info(xml_path)
    notesOnMeasures = notes_to_uniform_grid(measureData)

    # Print example output for first measure
    print("First measure, grid of notes:")
    return notesOnMeasures
