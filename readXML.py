import sys
from xml.etree import ElementTree as ET


def main(*argv):
    doc = ET.parse("extracted_mxl/lg-12741397.xml")  # Saved (and corrected) the file from PasteBin
    root = doc.getroot()
    namespaces = {  # Manually extracted from the XML file, but there could be code written to automatically do that.
        "zs": "http://www.loc.gov/zing/srw/",
        "": "http://www.loc.gov/MARC21/slim",
    }

    datafield_nodes_path = "./zs:records/zs:record/zs:recordData/record/datafield"  # XPath
    datafield_attribute_filters = [
        {
            "tag": "100",
            "ind1": "1",
            "ind2": " ",
        },
        {
            "tag": "245",
            "ind1": "1",
            "ind2": "0",
        },
    ]
    #datafield_attribute_filters = []  # Decomment this line to clear filters (and process each datafield node)
    ret = []
    for datafield_node in root.iterfind(datafield_nodes_path, namespaces=namespaces):
        if datafield_attribute_filters:
            skip_node = True
            for attr_dict in datafield_attribute_filters:
                for k, v in attr_dict.items():
                    if datafield_node.get(k) != v:
                        break
                else:
                    skip_node = False
                    break
            if skip_node:
                continue
        for subfield_node in datafield_node.iterfind("./subfield[@code='a']", namespaces=namespaces):
            ret.append(subfield_node.text)
    print("Results:")
    for i, e in enumerate(ret, start=1):
        print("{:2d}: {:s}".format(i, e))


if __name__ == "__main__":
    print("Python {:s} {:03d}bit on {:s}\n".format(" ".join(elem.strip() for elem in sys.version.split("\n")),
                                                   64 if sys.maxsize > 0x100000000 else 32, sys.platform))
    rc = main(*sys.argv[1:])
    print("\nDone.")
    sys.exit(rc)
