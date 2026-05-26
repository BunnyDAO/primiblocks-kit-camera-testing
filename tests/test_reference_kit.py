"""Smoke test for the camera-testing kit's display_calibration template.

Renders the template against kit/vars.example.json and asserts:

  - the rendered artifact parses as valid XML
  - the root element is <Sequence> with the expected direct children
  - the <Items> element contains exactly 20 <SequenceItem>s in the same
    order, xsi:type, UserName, and PatternSetupName as the reference file
    A264_B_v0.37_260318.seqxc that this kit was bootstrapped from
  - `primiblocks lint --kit-dir kit` exits 0

These tests run on every PR via the inherited cross-OS CI matrix.
"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from primiblocks.render import render


REPO_ROOT = Path(__file__).parent.parent
KIT_DIR = REPO_ROOT / "kit"
XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


# Expected ordering matches the reference A264_B_v0.37_260318.seqxc.
# Each tuple: (analysis xsi:type, UserName, PatternSetupName)
EXPECTED_ITEMS = [
    ("DemuraSdcN.RegisterPixelsSdcN", "Register Pixels G",     "G255"),
    ("DemuraSdcN.RegisterPixelsSdcN", "Register Pixels R",     "R255"),
    ("DemuraSdcN.RegisterPixelsSdcN", "Register Pixels B",     "B255"),
    ("RegisterPixels.RegisterPixels", "Light Source",          "w1"),
    ("RegisterPixels.RegisterPixels", "Synthetic G",           "W373_DBV650"),
    ("RegisterPixels.RegisterPixels", "Synthetic R",           "W373_DBV650"),
    ("RegisterPixels.RegisterPixels", "Synthetic B",           "W373_DBV650"),
    ("RegisterPixels.RegisterPixels", "Synthetic G",           "W17_DBV100(W16)"),
    ("RegisterPixels.RegisterPixels", "Synthetic R",           "W17_DBV100(W16)"),
    ("RegisterPixels.RegisterPixels", "Synthetic B",           "W17_DBV100(W16)"),
    ("RegisterPixels.RegisterPixels", "Synthetic G",           "W44_DBV10"),
    ("RegisterPixels.RegisterPixels", "Synthetic R",           "W44_DBV10"),
    ("RegisterPixels.RegisterPixels", "Synthetic B",           "W44_DBV10"),
    ("RegisterPixels.RegisterPixels", "Synthetic G",           "W34_DBV10"),
    ("RegisterPixels.RegisterPixels", "Synthetic R",           "W34_DBV10"),
    ("RegisterPixels.RegisterPixels", "Synthetic B",           "W34_DBV10"),
    ("RegisterPixels.RegisterPixels", "Synthetic G",           "W18_DBV10(W16)"),
    ("RegisterPixels.RegisterPixels", "Synthetic R",           "W18_DBV10(W16)"),
    ("RegisterPixels.RegisterPixels", "Synthetic B",           "W18_DBV10(W16)"),
    ("DemuraSdcN.DemuraTifSdcMobile_Async", "Demura Tif SDC Async", "W373_DBV650"),
]


@pytest.fixture(scope="module")
def rendered_xml() -> str:
    vars_all = json.loads((KIT_DIR / "vars.example.json").read_text(encoding="utf-8"))
    return render("display_calibration", vars_all["display_calibration"], kit_dir=KIT_DIR)


@pytest.fixture(scope="module")
def rendered_root(rendered_xml) -> ET.Element:
    return ET.fromstring(rendered_xml)


def test_rendered_output_is_nonempty(rendered_xml):
    assert len(rendered_xml) > 100_000, (
        f"expected >100KB of rendered XML; got {len(rendered_xml)}"
    )


def test_rendered_output_parses_as_xml(rendered_root):
    assert rendered_root.tag == "Sequence", (
        f"unexpected root tag: {rendered_root.tag!r}"
    )


def test_rendered_root_has_expected_direct_children(rendered_root):
    expected = {
        "XmlVersion", "ChannelIndex", "ChannelActive", "Items",
        "PatternSetupList", "FOImanager", "ModelName",
        "NumUnitsTested", "NumUnitsFailed", "CameraDistanceM",
    }
    actual = {child.tag.split("}")[-1] for child in rendered_root}
    assert expected.issubset(actual), f"missing root children: {expected - actual}"


def test_items_count_matches_reference(rendered_root):
    items = list(rendered_root.find("Items"))
    assert len(items) == 20, f"expected 20 SequenceItems; got {len(items)}"


@pytest.mark.parametrize("index", range(20))
def test_each_item_matches_reference_structure(rendered_root, index):
    """Every rendered SequenceItem must match the reference file's xsi:type,
    UserName, and PatternSetupName at the same index."""
    items = list(rendered_root.find("Items"))
    item = items[index]
    analysis = item.find("Analysis")
    actual_type = analysis.get(XSI_TYPE, "")
    actual_user_name = analysis.findtext("UserName", "")
    actual_pattern_setup = item.findtext("PatternSetupName", "")
    expected_type, expected_user_name, expected_pattern_setup = EXPECTED_ITEMS[index]
    assert actual_type == expected_type, (
        f"item [{index}] xsi:type: expected {expected_type!r}, got {actual_type!r}"
    )
    assert actual_user_name == expected_user_name, (
        f"item [{index}] UserName: expected {expected_user_name!r}, "
        f"got {actual_user_name!r}"
    )
    assert actual_pattern_setup == expected_pattern_setup, (
        f"item [{index}] PatternSetupName: expected {expected_pattern_setup!r}, "
        f"got {actual_pattern_setup!r}"
    )


def test_kit_lints_clean():
    """`primiblocks lint` exits 0 against the live kit/."""
    r = subprocess.run(
        [sys.executable, "-m", "primiblocks", "lint", "--kit-dir", str(KIT_DIR)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (
        f"primiblocks lint failed:\nstdout={r.stdout}\nstderr={r.stderr}"
    )
