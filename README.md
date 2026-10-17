# reverse-fic-poison

Antidote for [TricksOfLoki/fic-poison](https://github.com/TricksOfLoki/fic-poison) — removes the junk text that script injects into AO3 fanfiction HTML files.

If you've downloaded a fic that's been poisoned (garbled random words woven into the text), or you're an author who wants to undo the poisoning on your own work, this script strips it clean.

## What does fic-poison do?

The original `add_poison.py` injects garbage text into HTML-formatted fanfiction to sabotage AI training scrapers. It hides the junk from human readers using AO3's [workskin](https://archiveofourown.org/skins) CSS system, but any scraper doing raw text extraction picks up the noise.

It operates in two modes:

### Tame mode

The blunt approach. Splits the HTML on `</p>` tags and inserts a whole new paragraph of junk between every real paragraph:

```html
<p>She walked to the door.</p>
<p class="poison">banana helicopter tuesday mortgage quantum fishstick...</p>
<p>The hallway was dark.</p>
```

Each junk paragraph contains 10–100 random words from a bundled word list, wrapped in a `<p>` tag with the poison CSS class.

### Default mode

The sneaky approach. Reads the file character by character, skips over HTML tags and entities, and every 5–50 *visible characters* injects a single random word inside a `<span>`:

```html
She wal<​span class="poison">helicopter</​span>ked to the door.
```

**The twist:** the original script inserts a [zero-width space](https://en.wikipedia.org/wiki/Zero-width_space) (U+200B) between `<` and `span`, making `<​span>` — which is *not* a valid HTML tag. Browsers won't parse it as an element. The junk is hidden purely by the CSS workskin, and any text extractor that doesn't understand CSS gets word salad.

## How does the removal work?

Two targeted regex passes that catch both modes simultaneously:

1. **Tame cleanup** — matches `<p class="poison">...anything...</p>` (including the newline the original script prepends) and deletes the entire block
2. **Default cleanup** — matches `<span class="poison">...word...</span>` with or without the zero-width space between `<` and `span`/`/span`
3. **Stray ZWSP sweep** — removes any leftover zero-width space characters adjacent to `<` or `>`, since those only exist because of the poisoning

The script auto-detects which mode was used — you don't need to know or specify it.

## Usage

### Requirements

Python 3.6+ (no external dependencies — just `re`, `argparse`, and stdlib)

### Command line

```bash
# Basic usage (assumes poison class is "poison")
python remove_poison.py my_fic_poisoned.txt

# Custom class name (if the author used something other than "poison")
python remove_poison.py my_fic_poisoned.txt -c hidden
```

### Interactive mode

Just run it with no arguments and it'll prompt you:

```bash
python remove_poison.py
```

```
=== fic-poison remover ===

Poisoned file path (e.g. fic_poisoned.txt):
> my_fic_poisoned.txt
Poison class name (press Enter for 'poison'):
>
```

### Output

The cleaned file is saved alongside the original:

- `my_fic_poisoned.txt` → `my_fic_cleaned.txt`
- `chapter1.html` → `chapter1_cleaned.html`

The original file is never modified.

## How do I know if a fic is poisoned?

If you're seeing random words scattered throughout the text of a downloaded fic, it's likely been poisoned with default mode. If there are entire paragraphs of nonsense between the real paragraphs, that's tame mode.

You can also check the HTML source for elements with a `class` attribute — common class names are `poison`, `hidden`, or custom names the author chose. The default in `fic-poison` is `poison`.

## Web tool

Don't want to run Python? Use the **[online fic cleaner](https://claude.ai/artifact/7oRb3dYGqqkB1uW2AhmWSR)** — paste your HTML, get clean text back. Everything runs in your browser; your fic never leaves your device.

## Related

- [TricksOfLoki/fic-poison](https://github.com/TricksOfLoki/fic-poison) — the original poisoning script this is an antidote for

## Limitations

- Only handles files poisoned by [TricksOfLoki/fic-poison](https://github.com/TricksOfLoki/fic-poison) specifically. Other poisoning methods would need different removal logic.
- If the author used a custom class name and you don't know what it is, you'll need to inspect the HTML source to find it. Look for `<p class="something">` or `<span class="something">` tags containing random words.
- The script operates on local HTML files. It does not interact with AO3 directly.

## License

[MIT](LICENSE)
