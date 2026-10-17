# Reverses the "fic-poison" script by TricksOfLoki
# Removes junk text injected to disrupt AI training scrapers
# Handles both "tame" mode (junk <p> blocks) and "default" mode (junk <span> insertions)
# By reverse-engineering: https://github.com/TricksOfLoki/fic-poison

import re
from io import open
from sys import argv
from os.path import exists, isfile
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser(
        description="Remove poison text injected by fic-poison (TricksOfLoki)"
    )
    parser.add_argument(
        "filename", type=str, help="Poisoned HTML file to clean"
    )
    parser.add_argument(
        "-c", "--classname", default="poison", type=str,
        help="CSS class used for poison elements (default: poison)"
    )
    return parser.parse_args()


def remove_poison(content: str, poison_class: str) -> str:
    """
    Strips all poison injections from the HTML content.

    The original add_poison.py works in two modes, but both leave
    distinctive fingerprints we can target:

    TAME MODE — injects entire <p class="CLASS">...junk...</p> blocks
    between existing paragraphs. The junk is 10–100 random words from
    a word list, space-separated, inside a <p> with the poison class.
    There's also a newline before each poison <p> in the output.

    DEFAULT MODE — injects <span class="CLASS">word</span> elements
    at random intervals (every 5–50 visible characters) throughout
    the text. CRITICALLY, the original script uses a zero-width space
    (U+200B) between '<' and 'span' / '/span', making them:
        <\u200bspan class="CLASS">word<\u200b/span>
    These are NOT valid HTML tags — they render as literal text in
    browsers but would pollute any naive text extraction pipeline.

    This function handles both modes simultaneously, plus edge cases
    like single-quoted class attributes or extra whitespace.
    """

    cleaned = content

    # ──────────────────────────────────────────────────────────
    # 1. TAME MODE: Remove <p class="poison">...</p> blocks
    # ──────────────────────────────────────────────────────────
    # The injected paragraphs look like:
    #   \n<p class="poison">word1 word2 word3 ... </p>
    # We match the optional leading newline too, since the original
    # script adds '\n' before each poison paragraph.
    tame_pattern = re.compile(
        r'\n?<p\s+class=["\']' + re.escape(poison_class) + r'["\']>'
        r'[^<]*'       # junk words (no nested HTML inside these)
        r'</p>',
        re.IGNORECASE
    )
    cleaned = tame_pattern.sub('', cleaned)

    # ──────────────────────────────────────────────────────────
    # 2. DEFAULT MODE: Remove <(ZWSP)span class="poison">...<(ZWSP)/span>
    # ──────────────────────────────────────────────────────────
    # The original script puts a zero-width space (U+200B) between
    # '<' and 'span' / '/span'. We match with or without it, in case
    # someone ran a modified version without the ZWSP.
    #
    # The junk content is always a single word (one entry from the
    # word list), but we match any non-'<' content to be safe.
    zwsp = '\u200b'  # zero-width space
    default_pattern = re.compile(
        r'<' + zwsp + r'?span\s+class=["\']' + re.escape(poison_class) + r'["\']>'
        r'[^<]*'       # the junk word
        r'<' + zwsp + r'?/span>',
        re.IGNORECASE
    )
    cleaned = default_pattern.sub('', cleaned)

    # ──────────────────────────────────────────────────────────
    # 3. STRAY ZWSP CLEANUP
    # ──────────────────────────────────────────────────────────
    # The ZWSP chars only exist because of the poison script — the
    # original fic wouldn't have had them. Remove any orphaned ones
    # that might remain after stripping the spans.
    # (Be conservative: only strip ZWSPs that are adjacent to '<' or
    # '>' since those are the ones the script planted.)
    cleaned = cleaned.replace('<' + zwsp, '<')
    cleaned = cleaned.replace(zwsp + '>', '>')

    return cleaned


def report_diff(original: str, cleaned: str):
    """Show stats on what was removed."""
    orig_len = len(original)
    clean_len = len(cleaned)
    removed = orig_len - clean_len
    if removed > 0:
        pct = (removed / orig_len) * 100
        print(f"  Removed {removed:,} characters ({pct:.1f}% of file)")
    else:
        print("  No poison found — file unchanged.")
        print("  (Check that the class name matches what was used to poison it)")


if __name__ == "__main__":
    try:
        if len(argv) > 1:
            args = parse_args()
            filename = args.filename
            poison_class = args.classname
        else:
            print("=== fic-poison remover ===\n")
            filename = input("Poisoned file path (e.g. fic_poisoned.txt):\n> ").strip()
            poison_class = input(
                "Poison class name (press Enter for 'poison'):\n> "
            ).strip() or "poison"

        # Validate input
        if not filename:
            raise Exception("No filename provided.")
        if not exists(filename) or not isfile(filename):
            raise Exception(
                f"File not found: {filename}\n"
                "Make sure the path is correct (use full path if needed)."
            )

        # Read the poisoned file
        with open(filename, mode="r", encoding="utf-8") as f:
            content = f.read()

        print(f"\nProcessing: {filename}")
        print(f"Poison class: '{poison_class}'")

        # Remove the poison
        cleaned = remove_poison(content, poison_class)
        report_diff(content, cleaned)

        # Save cleaned file
        if filename.endswith("_poisoned.txt"):
            # Reverse the naming convention from add_poison.py
            new_filename = filename.replace("_poisoned.txt", "_cleaned.txt")
        else:
            dot = filename.rfind(".")
            if dot != -1:
                new_filename = filename[:dot] + "_cleaned" + filename[dot:]
            else:
                new_filename = filename + "_cleaned"

        with open(new_filename, mode="w", encoding="utf-8") as f:
            f.write(cleaned)

        print(f"\nSaved cleaned file to: {new_filename}")

    except Exception as e:
        print(f"\nError: {e}")

    input("\nPress Enter to close window")
