# primiblocks-kit-camera-testing

> **A [PrimiBlocks](https://github.com/BunnyDAO/PrimiBlocks) kit for generating display-calibration `.seqxc` sequence files from typed, contract-validated inputs.** A vision engineer answers 6 questions in Claude Code; the kit emits an ~882KB `.seqxc` ready for the sequencer.

Built on PrimiBlocks v0.2.0+.

---

## What this kit does

Replaces hand-authored display-calibration `.seqxc` files with a **typed template** + **conversation-driven fill-in** via the bundled `/primi-fill` skill. The template reproduces the same 20-item structure used in production calibration runs (`A264_B_v0.37_260318.seqxc` and similar):

- 3× SDC-N register-pixel items (G / R / B color channels)
- 1× Light Source measurement
- N × 3 synthetic G/R/B measurements (one set per measurement point you supply)
- 1× Demura TIF SDC Async computation

The 12 primitive-internal vars (user_name, pattern_setup_name, tristimulus, etc.) are marked `hidden: true` so the fill-skill walks the user through only the 6 conceptually meaningful inputs.

## Quickstart

```bash
git clone https://github.com/BunnyDAO/primiblocks-kit-camera-testing.git
cd primiblocks-kit-camera-testing
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
primiblocks doctor
```

Then either drive it conversationally:

```
# In Claude Code:
/primi-fill
# → pick `display_calibration`, answer 6 questions, preview, write
```

Or render directly from a vars file:

```bash
primiblocks render display_calibration --vars kit/vars.example.json --out my-calibration.seqxc
```

## The 6 user-facing inputs

When you run `/primi-fill display_calibration`, you're walked through:

| Var                         | Type   | Purpose                                                                                  |
|-----------------------------|--------|------------------------------------------------------------------------------------------|
| `measurement_points`        | list   | List of `{pattern_setup, notes_prefix, ...}` dicts — one per measurement point          |
| `final_demura_pattern_setup`| string | PatternSetupName for the trailing Demura TIF Async step                                  |
| `xml_version`               | string | XmlVersion declared at the sequence root (default "1.8")                                 |
| `channel_index`             | int    | ChannelIndex (default 0)                                                                 |
| `g_max_dut_keystone`        | float  | Max DUT keystone for the G channel (default 0.04)                                        |
| `rb_max_dut_keystone`       | float  | Max DUT keystone for the R and B channels (default 1.0)                                  |

Everything else (per-color tristimulus selection, per-item notes, internal pattern wiring, the 502KB `<PatternSetupList>`, the `<FOImanager>` config) is locked into the primitives + template body — invisible to the fill-skill walkthrough.

## Verification

The reference `vars.example.json` reproduces the same 20-item structure as `A264_B_v0.37_260318.seqxc`. Rendered output:

- Parses as valid XML (UTF-8, with the `xsd`/`xsi` namespaces preserved)
- 20 `<SequenceItem>` elements in the same order as the original
- Each item matches the original on `xsi:type`, `UserName`, `PatternSetupName`

To re-verify after edits: `primiblocks lint` and `primiblocks render display_calibration --vars kit/vars.example.json --out /tmp/check.seqxc && xmllint --noout /tmp/check.seqxc`.

## Customizing this kit

This is a **forkable** repo. To adapt to a different display-calibration shape (e.g., add a `gamma_check` step, change measurement defaults, support a different tristimulus convention):

1. Open the relevant primitive (`kit/primitives/*.j2`) and edit its body + contract
2. Or add a new primitive via `primiblocks new primitive my_new_step`
3. Compose into the template with `primitives: [..., my_new_step]` in the template frontmatter and `{% include "primitives/my_new_step.j2" %}` in the body
4. `primiblocks lint` to catch any drift

The framework code (`primiblocks/`) is inherited from PrimiBlocks and should not be touched — submit upstream PRs if the renderer needs a feature.

## Limitations

- **No XSD validation against the camera software's schema.** The kit emits structurally valid XML matching the reference file's shape, but doesn't verify against an XSD. To add: drop a post-render check into your workflow (or wait for PrimiBlocks post-render hooks, planned for v0.3.0).
- **List-item shape isn't deeply validated.** `measurement_points` is `type: list, min: 1` but each item's dict shape (`pattern_setup`, `notes_prefix`, ...) isn't type-checked. A bad entry surfaces as a Jinja error at render. Workaround: copy the structure from `vars.example.json`.
- **Inherited PrimiBlocks scaffolding is verbose.** The repo contains the full PrimiBlocks renderer + tests + the original LLM-prompt SOP/docs. You can delete `docs/prd/`, `docs/adr/`, `issues/`, and `docs/diagrams/` if you want a cleaner repo — they're PrimiBlocks's own history, not yours. (Or leave them as reference.)

## Provenance

Bootstrapped from [PrimiBlocks](https://github.com/BunnyDAO/PrimiBlocks) v0.2.0 by extracting the structure of the `A264_B_v0.37_260318.seqxc` reference file. Primitives were generated programmatically from that file with Jinja2 placeholders for the 8–10 fields per analysis type that vary between instances (out of 306–326 simple fields each).

## License

MIT.
