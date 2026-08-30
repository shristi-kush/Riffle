#!/usr/bin/env python
"""Generate the sample PDFs used by the evaluation harness.

These fictional GreenLeaf Energy documents give the evaluation set a stable,
self-contained ground truth. The original three product/company guides keep
the extractive smoke-set facts. Two extra SKU guides (SunMax 370, PowerCell 15)
are near-duplicate distractors so retrieval can actually fail.

Regenerate with:

    python scripts/make_sample_docs.py

Requires ``reportlab`` (dev-only; not needed at runtime since the generated
PDFs are committed under ``data/eval/docs/``).
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "eval" / "docs"

DOCS: dict[str, list[str]] = {
    "greenleaf_solar_panel.pdf": [
        "GreenLeaf SunMax 400 Solar Panel - Product Guide",
        "GreenLeaf Energy manufactures the SunMax 400, a residential solar "
        "panel built around monocrystalline silicon cells.",
        "The SunMax 400 has a rated power output of 400 watts and a module "
        "efficiency of 21.5 percent.",
        "Each panel weighs 21 kilograms and measures 1.7 meters by 1.0 meters.",
        "The SunMax 400 operates reliably across a temperature range of minus "
        "40 degrees Celsius to 85 degrees Celsius.",
        "GreenLeaf backs the SunMax 400 with a 25 year performance warranty.",
        "The panel is designed to pair directly with the GreenLeaf PowerCell "
        "10 home battery for whole-home backup.",
        "Mechanical mounting uses a standard 35 millimetre frame with four "
        "grounding points. The junction box is IP68 rated and the cable "
        "leads are 1.2 metres of 4 millimetre-squared PV wire with MC4 "
        "connectors. Bypass diodes protect the module under partial shade.",
        "Certified to IEC 61215 and IEC 61730. The nameplate lists a maximum "
        "system voltage of 1000 volts DC. Do not confuse this 400 watt module "
        "with the lower-output SunMax 370, which has a shorter warranty and "
        "a different cell architecture; the two SKUs are not interchangeable "
        "for array stringing without a redesign of the inverter setpoints.",
        "Recommended array tilt follows local latitude. Annual degradation is "
        "specified at 0.45 percent per year after the first year. Shipping "
        "pallets hold 30 modules. Installers must torque rail clamps to 16 "
        "newton-metres and observe the fire classification on the label.",
    ],
    "greenleaf_sunmax_370.pdf": [
        "GreenLeaf SunMax 370 Solar Panel - Product Guide",
        "The SunMax 370 is GreenLeaf's value residential module. It uses "
        "polycrystalline silicon cells rather than the monocrystalline cells "
        "in the SunMax 400.",
        "The SunMax 370 has a rated power output of 370 watts and a module "
        "efficiency of 19.8 percent.",
        "Each panel weighs 19.4 kilograms and measures 1.65 meters by 1.0 "
        "meters.",
        "GreenLeaf backs the SunMax 370 with a 20 year performance warranty, "
        "which is five years shorter than the SunMax 400 warranty.",
        "The SunMax 370 is designed to pair with the GreenLeaf PowerCell 15 "
        "home battery, not the PowerCell 10.",
        "Operating temperature is minus 35 degrees Celsius to 80 degrees "
        "Celsius. Frame colour is silver. Pallet quantity is 32 modules. "
        "IEC 61215 certification applies. Maximum system voltage is 1000 "
        "volts DC. Annual degradation is 0.55 percent per year.",
        "Installers sometimes mix 370 and 400 watt modules on one roof; "
        "GreenLeaf does not support mixed-SKU strings. The 370 uses a 30 "
        "millimetre frame, so it does not share rails with the SunMax 400.",
        "Replacement glass, junction-box lids, and MC4 pigtails are unique "
        "part numbers. Ordering the 400-watt spare kit for a 370 array will "
        "fail incoming inspection.",
    ],
    "greenleaf_battery.pdf": [
        "GreenLeaf PowerCell 10 Home Battery - Technical Specification",
        "The PowerCell 10 is a lithium iron phosphate (LiFePO4) home battery "
        "produced by GreenLeaf Energy.",
        "It has a nominal capacity of 10 kilowatt-hours and a usable capacity "
        "of 9.2 kilowatt-hours.",
        "The PowerCell 10 delivers a maximum continuous power of 5 kilowatts.",
        "Its round-trip efficiency is 94 percent.",
        "GreenLeaf provides a 10 year warranty on the PowerCell 10.",
        "The battery is compatible with the SunMax 400 solar panel and can be "
        "stacked in multiples for larger storage needs.",
        "Enclosure rating is IP55 for indoor or covered outdoor walls. "
        "Nominal voltage is 48 volts. The internal inverter is hybrid and "
        "supports a 200 amp pass-through. Operating temperature is 0 to 45 "
        "degrees Celsius while charging.",
        "Do not confuse the PowerCell 10 with the PowerCell 15. The 15 uses a "
        "different cell chemistry, a longer warranty, and is sized for the "
        "SunMax 370, not the SunMax 400. Firmware, floor stands, and backup "
        "interface kits are SKU-specific.",
        "Commissioning requires a licensed electrician. The battery ships at "
        "30 percent state of charge. Floor loading is 95 kilograms. Noise is "
        "under 35 dBA. A Wi-Fi and Ethernet gateway reports state of charge "
        "to the GreenLeaf app.",
    ],
    "greenleaf_powercell_15.pdf": [
        "GreenLeaf PowerCell 15 Home Battery - Technical Specification",
        "The PowerCell 15 is a nickel manganese cobalt (NMC) home battery "
        "produced by GreenLeaf Energy for larger homes.",
        "It has a nominal capacity of 15 kilowatt-hours and a usable capacity "
        "of 13.8 kilowatt-hours.",
        "The PowerCell 15 delivers a maximum continuous power of 7 kilowatts.",
        "Its round-trip efficiency is 92 percent, two points below the "
        "PowerCell 10.",
        "GreenLeaf provides a 12 year warranty on the PowerCell 15, which is "
        "longer than the PowerCell 10 warranty but applies only to this SKU.",
        "The PowerCell 15 is compatible with the SunMax 370 solar panel. It is "
        "not the recommended pairing for the SunMax 400.",
        "Nominal voltage is 48 volts. Floor loading is 118 kilograms. The "
        "unit is IP54. Charging is limited below 5 degrees Celsius. Stacking "
        "is limited to two cabinets on a single gateway.",
        "NMC cells require a tighter thermal envelope than LiFePO4. The "
        "manual forbids installing a PowerCell 15 on the same backup bus as a "
        "PowerCell 10. Spare parts, contactors, and BMS firmware differ.",
    ],
    "greenleaf_company.pdf": [
        "GreenLeaf Energy - Company Overview and Sustainability Report",
        "GreenLeaf Energy was founded in 2015 and is headquartered in Austin, "
        "Texas.",
        "As of 2024 the company employs 320 people and reported annual revenue "
        "of 85 million US dollars.",
        "GreenLeaf's mission is to make affordable clean energy accessible to "
        "every household.",
        "Since 2020 the company has reduced its manufacturing carbon footprint "
        "by 40 percent.",
        "GreenLeaf recycles 95 percent of its manufacturing waste.",
        "The company now sells its products in 12 countries across three "
        "continents.",
        "For comparison, 2023 figures were lower: GreenLeaf employed 280 "
        "people and reported 62 million US dollars of revenue. Do not cite "
        "2023 headcount or 2023 revenue when a question asks for the latest "
        "reported year.",
        "A European commercial office opened in Berlin in 2022. Berlin is a "
        "sales office only. Corporate headquarters remain in Austin, Texas. "
        "Manufacturing is in Monterrey, Mexico. None of those sites replace "
        "Austin as the headquarters city.",
        "The board meets quarterly in Austin. Investor relations publishes "
        "the 2024 headcount and revenue in this overview; press mentions of "
        "the Berlin office do not change the legal domicile.",
    ],
}


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    for filename, paragraphs in DOCS.items():
        path = OUT_DIR / filename
        doc = SimpleDocTemplate(str(path), pagesize=LETTER)
        story = []
        story.append(Paragraph(paragraphs[0], styles["Title"]))
        story.append(Spacer(1, 18))
        for para in paragraphs[1:]:
            story.append(Paragraph(para, styles["BodyText"]))
            story.append(Spacer(1, 10))
        doc.build(story)
        print(f"Wrote {path}")


if __name__ == "__main__":
    build()
