// Render hidden/bidi/tag characters as visible ⟦U+XXXX⟧ markers. Mirrors bera.text.visible_escape.
// All text is rendered through React's escaping; this only makes invisible characters visible.

function isHidden(cp: number): boolean {
  return (
    cp === 0x061c ||
    cp === 0x200e ||
    cp === 0x200f ||
    (cp >= 0x202a && cp <= 0x202e) ||
    (cp >= 0x2066 && cp <= 0x2069) ||
    [0x200b, 0x200c, 0x200d, 0x2060, 0xfeff, 0x180e, 0x00ad].includes(cp) ||
    (cp >= 0xe0000 && cp <= 0xe007f) ||
    (cp < 0x20 && cp !== 0x09 && cp !== 0x0a && cp !== 0x0d) ||
    (cp >= 0x7f && cp <= 0x9f)
  );
}

export function visibleEscape(text: string | null | undefined): string {
  if (text == null) return "";
  let out = "";
  for (const ch of text) {
    const cp = ch.codePointAt(0) ?? 0;
    out += isHidden(cp) ? `⟦U+${cp.toString(16).toUpperCase().padStart(4, "0")}⟧` : ch;
  }
  return out;
}
