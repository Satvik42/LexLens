/**
 * Evidence helpers shared by chips, cards and the document viewer.
 */

export function evidenceLabel(evidence) {
  if (!evidence) return '';
  const page = evidence.page ?? evidence.page_number;
  const section = evidence.section ? ` · §${evidence.section}` : '';
  return `Page ${page}${section}`;
}

export function viewerPath(documentId, evidence) {
  const params = new URLSearchParams();
  const page = evidence?.page ?? evidence?.page_number;
  if (evidence?.id) params.set('evidence', evidence.id);
  if (page) params.set('page', String(page));
  const query = params.toString();
  return `/documents/${documentId}/view${query ? `?${query}` : ''}`;
}

/** Normalize an API evidence object (analysis shape or /evidence endpoint shape) to one structure. */
export function normalizeEvidence(raw) {
  if (!raw) return null;
  return {
    id: raw.id ?? null,
    page: raw.page ?? raw.page_number,
    section: raw.section ?? null,
    heading: raw.heading ?? raw.location_data?.heading ?? null,
    text: raw.text,
    start_offset: raw.start_offset ?? null,
    end_offset: raw.end_offset ?? null,
    block_id: raw.block_id ?? raw.location_data?.block_id ?? null,
    verified: raw.verified ?? false,
  };
}

/**
 * Split a block's text into [before, match, after] for the given evidence, or null if the evidence is not in it.
 * Prefers verified offsets; falls back to a case-insensitive text search.
 */
export function splitBlockForEvidence(block, evidence) {
  if (!block || !evidence) return null;
  const { start_offset: start, end_offset: end } = evidence;
  if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
    const overlapStart = Math.max(start, block.start);
    const overlapEnd = Math.min(end, block.end);
    if (overlapEnd <= overlapStart) return null;
    const localStart = overlapStart - block.start;
    const localEnd = overlapEnd - block.start;
    return [block.text.slice(0, localStart), block.text.slice(localStart, localEnd), block.text.slice(localEnd)];
  }
  if (!evidence.text) return null;
  const index = block.text.toLowerCase().indexOf(evidence.text.toLowerCase());
  if (index < 0) return null;
  return [block.text.slice(0, index), block.text.slice(index, index + evidence.text.length), block.text.slice(index + evidence.text.length)];
}

/** Split text around every case-insensitive occurrence of `term`: returns alternating [plain, match, plain, ...]. */
export function splitByTerm(text, term) {
  if (!term) return [text];
  const lower = text.toLowerCase();
  const needle = term.toLowerCase();
  const parts = [];
  let cursor = 0;
  let index = lower.indexOf(needle);
  while (index >= 0) {
    parts.push(text.slice(cursor, index), text.slice(index, index + needle.length));
    cursor = index + needle.length;
    index = lower.indexOf(needle, cursor);
  }
  parts.push(text.slice(cursor));
  return parts;
}
