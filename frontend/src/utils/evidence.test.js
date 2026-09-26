import { evidenceLabel, splitBlockForEvidence, viewerPath } from './evidence';

test('formats evidence labels as Page X · §Y', () => {
  expect(evidenceLabel({ page: 14, section: '8.2' })).toBe('Page 14 · §8.2');
});

test('builds a viewer path with evidence and page', () => {
  expect(viewerPath('doc-1', { id: 'ev', page: 8 })).toBe('/documents/doc-1/view?evidence=ev&page=8');
});

test('splits a block around verified offsets', () => {
  const block = { text: 'provide sixty (60) days written notice now', start: 10, end: 52 };
  const [before, match, after] = splitBlockForEvidence(block, { start_offset: 18, end_offset: 48 });
  expect(match).toBe('sixty (60) days written notice');
  expect(before).toBe('provide ');
  expect(after).toBe(' now');
});
