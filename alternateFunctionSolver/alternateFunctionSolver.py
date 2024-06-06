#!/usr/bin/env python3

import sys
import setproctitle
import getopt
import xml.etree.ElementTree as ET
import json
from typing import List
import re
from pysat.formula import CNF
from pysat.solvers import Solver


def printError(
        *args,
        **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def printUsage():
    print("")
    print("available and optional parameter of this tool:")
    print("    --help                           prints out this help")
    print("    --input                          path to the input json file")


def parsePin(name: str, signals: List[str]):
    matches = re.findall("^P([A-Z])([0-9]*)$", name)

    if len(matches) == 0:
        return None

    return Pin(
        name=name,
        signals=signals,
        port=matches[0][0],
        number=int(matches[0][1]))

class Pin(object):
    def __init__(
            self,
            name: str,
            signals: List[str],
            port: str,
            number: int):
        self._name = name
        self._signals = signals        
        self._port = port
        self._number = number

    def __str__(self):
        return f"port {self._port}, pin {self._number} ({', '.join(self._signals)})"

    @property
    def name(self):
        return self._name

    @property
    def signals(self):
        return self._signals


def processInput(inputFileNameAndPath: str):
    with open(inputFileNameAndPath, "r") as inputFileHandle:
        inputFileContent = json.loads(inputFileHandle.read())

        if "MCU" not in inputFileContent:
            printError("MCU selection is missing in input file")
            return False

        selectedMCU = inputFileContent["MCU"]
        mcuFile = f"mcu/{selectedMCU}.xml"

        print(f"selected MCU: {selectedMCU}")
        xmlTree = ET.parse(mcuFile)
        root = xmlTree.getroot()
        #print([elem.tag for elem in root.iter()])
        namespaces = {"dummy": "http://dummy.com"}
        pins = []

        for pin in root.findall("dummy:Pin", namespaces):
            name = pin.attrib["Name"]
            signals = [signal.attrib["Name"] for signal in pin.findall("dummy:Signal", namespaces)]
            parsedPin = parsePin(name=name, signals=signals)

            if not parsedPin is None:
                pins.append(parsedPin)

        requiredSignals = inputFileContent["signals"]
        requiredInputs = int(inputFileContent["inputs"])

        print(f"{len(requiredSignals)} signals and {requiredInputs} inputs are required")

        conjunctiveNormalForm = [
            # A
            [1, -3, -5], [-1, 3, -5], [-1, -3, 5],
            # B
            [2, -4, -6], [-2, 4, -6], [-2, -4, 6],
            # PA0
            [1, -2], [-1, 2], [-1, -2],
            # PA1
            [3, -4], [-3, 4], [-3, -4],
            # PA2
            [5, -6], [-5, 6], [-5, -6]
        ]

        with Solver(bootstrap_with=conjunctiveNormalForm) as solver:
            print('formula is', f'{"s" if solver.solve() else "uns"}atisfiable')
            print('and the model is:', solver.get_model())


        return True


if __name__ == "__main__":
    setproctitle.setproctitle("alternateFunctionSolver")

    try:
        options, arguments = getopt.getopt(sys.argv[1:], "",
        [
            "help",
            "input=",
        ])
    except getopt.GetoptError:
        printError("invalid arguments")
        printUsage()
        sys.exit(1)

    for option, argument in options:
        if option == "--help":
            printUsage()
            sys.exit(0)
        elif option == "--input":
            success = processInput(inputFileNameAndPath=argument)

            if success:
                sys.exit(0)
            else:
                printError(f"processing of input file {argument} failed")
                sys.exit(1)
        else:
            printError("invalid option " + option)
            printUsage()
            sys.exit(1)

    printError("no input file selected")
    sys.exit(1)