import os
import sys

if __name__ == "__main__":
    print("Name the New Directory...", file=sys.stderr)
    output: str = input()

    with open(os.path.join(os.path.dirname(__file__), "newdir_dialog_output.txt"), "w") as ndo:
        ndo.write(output)
        ndo.close()