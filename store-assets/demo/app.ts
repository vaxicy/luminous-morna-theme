/**
 * Luminous Morna Theme - syntax preview
 *
 * Light  canvas #FCFBED  ink #2D2C25  accent #1D7D75
 * Dark   canvas #2A2919  ink #F1F0E9  accent #25A096
 */

import { readFileSync } from "node:fs";

export type Level = "quiet" | "warm" | "radiant";

export interface Swatch {
  readonly name: string;
  readonly hex: string;
  readonly level: Level;
}

export const PALETTE: readonly Swatch[] = [
  { name: "canvas", hex: "#FCFBED", level: "quiet" },
  { name: "accent", hex: "#1D7D75", level: "radiant" },
  { name: "bloom", hex: "#BED8CB", level: "warm" },
  { name: "shadow", hex: "#2D2C25", level: "quiet" },
];

const CHANNEL = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i;

/** Relative luminance, so we can sort the palette by brightness. */
export function luminance(hex: string): number {
  const match = CHANNEL.exec(hex);
  if (!match) {
    throw new TypeError(`Not a hex colour: ${hex}`);
  }

  const [r, g, b] = match.slice(1).map((part) => parseInt(part, 16) / 255);
  const linear = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);

  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
}

export function sortByBrightness(swatches: readonly Swatch[] = PALETTE): Swatch[] {
  return [...swatches].sort((a, b) => luminance(b.hex) - luminance(a.hex));
}

export async function loadTheme(path: string): Promise<Record<string, string>> {
  const raw = readFileSync(path, "utf8");
  const { colors } = JSON.parse(raw) as { colors: Record<string, string> };

  for (const [key, value] of Object.entries(colors)) {
    if (key.startsWith("editor.")) {
      console.log(`  ${key.padEnd(34)} ${value}`);
    }
  }

  return colors;
}

if (process.argv[1] && process.argv[2] !== "--no-run") {
  await loadTheme(process.argv[1]);
  console.log(`\n${sortByBrightness().length} swatches ready.`);
}
