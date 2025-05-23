import xml.etree.ElementTree as ET

def parse_musicxml_all_note_info(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Get namespace if present
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'

    notes_data = []

    for part in root.findall(f"{ns}part"):
        part_id = part.attrib.get('id')
        for measure in part.findall(f"{ns}measure"):
            measure_number = measure.attrib.get('number')
            current_time = 0
            divisions = 1
            attributes = measure.find(f"{ns}attributes")
            if attributes is not None:
                divisions_tag = attributes.find(f"{ns}divisions")
                if divisions_tag is not None:
                    divisions = int(divisions_tag.text)

            for elem in measure.findall(f"{ns}note"):
                print(f"Processing note: {elem.attrib}")  # Debugging: Show note attributes

                # Initialize the note info dictionary
                note_info = {
                    'measure': measure_number,
                    'part_id': part_id,
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
                    'start_time': current_time,
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
                if duration is not None:
                    note_info['duration'] = int(duration.text)
                else:
                    print(f"Warning: Missing duration for note in measure {measure_number}")  # Debugging: Duration check

                # Type (eighth, quarter, etc.)
                typ = elem.find(f"{ns}type")
                if typ is not None:
                    note_info['type'] = typ.text
                else:
                    print(f"Warning: Missing type for note in measure {measure_number}")  # Debugging: Type check

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

                # Chord
                if elem.find(f"{ns}chord") is not None:
                    note_info['chord'] = True
                    note_info['start_time'] = current_time

                # Append the note to the data
                notes_data.append(note_info)

                # Only advance time if not a chord note
                if elem.find(f"{ns}chord") is None and duration is not None:
                    current_time += int(duration.text)
                elif duration is None:
                    print(f"Warning: Missing duration for chord note in measure {measure_number}")  # Debugging: Missing duration for chord

            # After processing the notes in the measure, print the current time
            print(f"End of measure {measure_number}, current_time: {current_time}")  # Debugging: Check time progress

    return notes_data

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python parse_musicxml_all_note_info.py <musicxml_file>")
        sys.exit(1)
    xml_path = sys.argv[1]
    notes = parse_musicxml_all_note_info(xml_path)

    # Debugging: Check the first few notes
    print("First few notes:")
    print(notes[:5])

    measureData = []
    data = ["measure 1"]
    measureCounter = 1
    for note in notes:
        if int(note['measure']) == measureCounter:
            data.append(note)
        else:
            measureData.append(data)
            measureCounter += 1
            data = [f"measure {measureCounter}"]

    # Handle the last measure if needed
    if data:
        measureData.append(data)

    # Debugging: Print the measure data
    print("Measure Data:")
    for measure in measureData:
        print("------------------------")
        for note in measure:
            print(note)
            print()


    for note in notes:
        print(note)
        print()
