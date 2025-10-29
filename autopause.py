
import re
import sys
import tempfile
import os
import time

from pathlib import Path

def parse_swap_instructions(lines):
    """Extract layer heights from the swap instruction block."""
    swaps = []
    in_block = False
    for line in lines:
        if "; Swap Instructions:" in line:
            in_block = True
            continue
        if in_block:
            if not line.startswith(";"):
                break  # end of block
            match = re.search(r"At layer #\d+ \(([\d.]+)mm\)", line)
            if match:
                height = float(match.group(1))
                swaps.append(height)
    return swaps


def insert_pauses(lines, swap_heights, command):
    """Insert M600 after matching Z-heights."""
    new_lines = []
    pauses = 0
    heights = []
    for line in lines:
        new_lines.append(line)
        match = re.match(r"^G1\s+Z([\d.]+)", line.strip())
        if match:
            z = float(match.group(1))
            heights.append(z)
            for h in swap_heights:
                # Compare with small tolerance (float rounding)
                if abs(z - h) < 0.001:
                    print(f"z {z} {command}")
                    new_lines.append(command)
                    new_lines.append("\n")
                    pauses = pauses + 1
                    break
    
    if (pauses != len(swap_heights)):
        print(heights)
        print("vs")
        print(swap_heights)

        raise Exception("heights don't match")

    return new_lines


def process_gcode(file_path, command):
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    swap_heights = parse_swap_instructions(lines)
    if not swap_heights:
        raise Exception("No swap instructions found - error displayed for 60sec ...")

    new_lines = insert_pauses(lines, swap_heights, command)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_pauses.py <file.gcode>")
    else:       
        gcodeFile = sys.argv[-1]  # last argument
        command = sys.argv[1] if len(sys.argv) > 2 else "M600"

        print(f"input file: {gcodeFile}")
        print(f"insert command at layer change: {command}")

        time.sleep(1)

        # Read g-code into memory
        with open(gcodeFile, "r") as f:
            inputLines = f.readlines()
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, "orig.gcode")

        with open(file_path, "w") as f:
            f.writelines(inputLines)

        print(gcodeFile + ".orig")

        try:
            process_gcode(gcodeFile, command)
        
            print("ok")
            time.sleep(1)  # wartet 2 Sekunden

        except Exception as e:
            print(e)
            time.sleep(60)
