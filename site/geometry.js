// Tab definitions for the viewer (no geometry here: all four models are Meshy GLBs, see index.html).
// Units are millimetres. Bands: only the ID / width / thickness sliders; solitaires: only the inner diameter.
export const DEFAULTS = {
  band1:      { ID: 19 },
  band2:      { ID: 17 },
  solitaire:  { ID: 17 }, // site/solitaire_meshy2.glb
  solitaire2: { ID: 17 }, // site/solitaire_6.glb
  solitaire3: { ID: 17 }, // site/nodiamond1.glb (= reference/meshy/NoDiamond1.glb rotated: ring axis y -> z, head z -> +y; no stone)
};
export const LABELS = { band1: 'Wide band', band2: 'Band', solitaire: 'Solitaire', solitaire2: 'Solitaire 2', solitaire3: 'Solitaire 3' };
export const CONTROLS = [
  ['ID', 'Inner diameter', 14, 24, 0.1],
  ['w', 'Width', 1.5, 8, 0.1, ['band1', 'band2']],
  ['t', 'Thickness', 0.8, 3, 0.05, ['band1', 'band2']],
];
