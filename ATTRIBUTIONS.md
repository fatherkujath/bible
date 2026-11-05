# Attributions

Generated from `data-pipeline/sources.json` by `python -m sic_pipeline attributions`. Do not edit by hand.

Scripture in Context displays only content from the sources below or written by the user.
Each record in the reference database stores the source it came from.

## Open (public domain, CC0 or CC BY)

### Berean Standard Bible

- **License:** Public domain (dedicated by Berean Bible / Bible Hub, April 30, 2023) (full text: `licenses/BSB.txt`)
- **Credit:** The Holy Bible, Berean Standard Bible, BSB. Produced in cooperation with Bible Hub, Discovery Bible, OpenBible.info, and the Berean Bible Translation Committee. Dedicated to the public domain.
- **Source:** https://github.com/scrollmapper/bible_databases at commit `59b18c5af5845728c275d5b7178ad0d024172b1f`
- **Homepage:** https://berean.bible
- **Notes:** Fetched from the scrollmapper/bible_databases mirror (OSIS JSON with word-level Strong's alignment) because it can be pinned to a git commit. The official downloads at bereanbible.com are the upstream source; the mirror's README labels the text CC0.

### STEPBible Data (Tyndale House, Cambridge)

- **License:** CC BY 4.0 (full text: `licenses/STEPBible-CC-BY-4.0.txt`)
- **Credit:** Data created by www.STEPBible.org based on work at Tyndale House Cambridge (CC BY 4.0). Source: https://STEPBible.github.io/STEPBible-Data
- **Source:** https://github.com/STEPBible/STEPBible-Data at commit `5de0a47f35f0fc13dfe1430d104e5db8a4285f9c`
- **Homepage:** https://www.stepbible.org
- **Notes:** STEPBible asks users to note any changes they make to the data. Changes made by this pipeline are listed in data-pipeline/CHANGES-TO-SOURCE-DATA.md. TIPNR descriptions (@Briefest, @Brief, @Short, @Article and the #Summary field) are described in the STEPBible README as created by Claude 3 AI and are NOT imported (sourcing rule 1).

## Share-alike (CC BY-SA) — kept in separate sa_ tables

### Theographic Bible Metadata

- **License:** CC BY-SA 4.0 (full text: `licenses/Theographic-CC-BY-SA-4.0.txt`)
- **Credit:** Theographic Bible Metadata by Robert Rouse (viz.bible), licensed CC BY-SA 4.0. Includes Easton's Bible Dictionary (1897, public domain text).
- **Source:** https://github.com/robertrouse/theographic-bible-metadata at commit `3f461f2f3cf8939f2b79430ae238a36528024ed3`
- **Homepage:** https://theographic.netlify.app
- **Notes:** Event and verse dates follow one chronology (Ussher-style, e.g. creation at 4003 BC). The app must label them 'per Theographic' (sourcing rule 4). Theographic's own KJV verse text is not imported.
