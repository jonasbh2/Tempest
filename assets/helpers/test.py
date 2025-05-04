#!/usr/bin/env python3
import tokenize

def strip_and_clean(input_path: str, output_path: str) -> None:
    # 1) Tokenize & strip comments
    pieces = []
    prev_end = (1, 0)
    with open(input_path, 'r', encoding='utf-8') as src:
        for tok_type, tok_text, (srow, scol), (erow, ecol), _ in \
                tokenize.generate_tokens(src.readline):

            prow, pcol = prev_end
            # preserve newlines
            if srow > prow:
                pieces.append('\n' * (srow - prow))
                pcol = 0
            # preserve spaces
            if scol > pcol:
                pieces.append(' ' * (scol - pcol))

            # skip comments
            if tok_type != tokenize.COMMENT:
                pieces.append(tok_text)

            prev_end = (erow, ecol)

    stripped = "".join(pieces)

    # 2) Collapse blank lines with special class‑rule
    out_lines = []
    blank_count = 0

    lines = stripped.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        is_blank = (line.strip() == "")
        is_class = line.lstrip().startswith("class ")

        if is_class:
            # ensure exactly two blanks before this class
            # drop any previous blank entries in out_lines tail:
            while out_lines and out_lines[-1].strip() == "":
                out_lines.pop()
            out_lines.extend(["\n", "\n"])
            blank_count = 0
            out_lines.append(line)
        elif is_blank:
            blank_count += 1
            # elsewhere allow only one blank
            if blank_count == 1:
                out_lines.append(line)
        else:
            blank_count = 0
            out_lines.append(line)

    # 3) Write result
    with open(output_path, 'w', encoding='utf-8') as dst:
        dst.write("".join(out_lines))

def main():
    infile  = "Tempest.py"
    outfile = "Tempest.cleaned.py"
    strip_and_clean(infile, outfile)
    print(f"✔ Cleaned file written to: {outfile}")

if __name__ == "__main__":
    main()
