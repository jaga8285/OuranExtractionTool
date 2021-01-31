# OuranExtractionTool
A tool for extracting and patching bin files.
## Extraction
Place the script in a folder with the bin files. Run the script and enter "e" for extracting from a single file or "ea for extracting from all bin files in the folder. Extraction means the generation of .json files corresponding to the bin files. These json files contain all pointer information and pointer contents:
### Example of a pointer 
```json
{
    "Type": "Dialog",
    "Size": 30,
    "Offset": 80,
    "Text Position": 108648,
    "Pointer Position": 16114,
    "Original Text": "プロローグをスキップしますか？",
    "New Text": ""
}
```
* **"Type"**: What is assumed to be the content of this pointer. Can be Dialog, Choice, Chapter Name, or Speaker. If the type is a number, it means we don't know what it does, so you probably shouldn't touch it
* **"Original Text"**: What the pointer originally pointed to. This is the original japanese text in the game
* **"New Text"**: Fill in these field. Write the translation within the quotes. 

**NOTE**: If the original text contains blank spaces, copy them to the new text - they may not be blank spaces and contain some sort of important info - and add the new text after that. 
Example: `            "Original Text": "　　　　　　この私立桜蘭学院は",
`

You may **only** alter the "New Text" field for each pointer.

## Patching
After all the json alteration have been made, run the script again and enter "ia" to patch all the bin files, or "i" to patch a single bin file.


## Special thanks
JJJewel for compiling their findings about the pointers in this [link](https://sites.google.com/site/otomegameguide/hacking-info/ouran-ds)

azerty1 for providing base tool for this.

