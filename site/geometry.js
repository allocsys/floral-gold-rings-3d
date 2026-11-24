// Tab definitions for the viewer (no geometry here: all models are Meshy GLBs, see index.html).
// Units are millimetres. Bands: only the ID / width / thickness sliders; solitaires: only the inner diameter.
export const DEFAULTS = {
  band1:      { ID: 19 },
  band2:      { ID: 17 },
  solitaire3: { ID: 17 },
  solitaire2: { ID: 17 },
  solitaire4: { ID: 17 },
  solitaire5: { ID: 17 },
};
export const LABELS = { band1: 'Wide band', band2: 'Band', solitaire3: 'Solitaire', solitaire2: 'Solitaire 2', solitaire4: 'Solitaire 3', solitaire5: 'Solitaire 4' };
export const CONTROLS = [
  ['ID', 'Inner diameter', 14, 24, 0.1],
  ['w', 'Width', 1.5, 8, 0.1, ['band1', 'band2']],
  ['t', 'Thickness', 0.8, 3, 0.05, ['band1', 'band2']],
];
