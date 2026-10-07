"""Executable composition vocabulary shared by planning and native rendering.

These descriptions deliberately describe available geometry, not an open canvas.
Every composition keeps the accepted section text, bindings and source footer.
"""

COMPOSITION_CATALOG = {
    "poster": {
        "description": "An asymmetric typographic poster: a strong title rail and offset content blocks.",
        "constraints": "1–4 sections. Title occupies an ink panel, accepted content stays in native text to its right. Existing charts and processes keep their data and use an offset text rail instead.",
        "focal_section_id": "Unused; exact accepted section order is retained.",
    },
    "balanced": {
        "description": "Equal visual importance: independent columns or editorial rows.",
        "constraints": "1–4 sections. Columns suit short parallel points; rows suit longer text. Charts reserve the right half; processes reserve a top strip.",
        "focal_section_id": "Unused; sections have equal hierarchy.",
    },
    "feature": {
        "description": "One large lead section with a quieter supporting sidebar.",
        "constraints": "1–4 sections. Use for a clear main takeaway. With a chart, the focal section leads the left stack. All sections retain their exact content.",
        "focal_section_id": "ID of the accepted section to emphasize; defaults to the first section.",
    },
    "bands": {
        "description": "Wide horizontal editorial bands, each with its own heading and text.",
        "constraints": "1–4 sections. Useful for ordered implications or dense parallel explanations. Band height follows content length; no merged sections.",
        "focal_section_id": "Unused; section order determines band order.",
    },
}
