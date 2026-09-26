/** Semantic evidence states → user-facing wording, tone and icon. Meaning is always conveyed by text. */
export const STATUS_META = {
  EXPLICITLY_STATED: { label: 'Explicitly stated', tone: 'success', icon: 'check' },
  PARTIALLY_DETERMINED: { label: 'Partially determined', tone: 'info', icon: 'info' },
  NOT_FOUND: { label: 'Not found in this document', tone: 'neutral', icon: 'circleDashed' },
  POTENTIAL_INCONSISTENCY: { label: 'Potential inconsistency', tone: 'warning', icon: 'alert' },
};

export function statusMeta(status) {
  return STATUS_META[status] ?? { label: status ?? 'Unknown', tone: 'neutral', icon: 'info' };
}

export const CONCERN_META = {
  POTENTIAL_CONCERN: { label: 'Potential concern', tone: 'warning', icon: 'alert' },
  POTENTIAL_INCONSISTENCY: { label: 'Potential inconsistency', tone: 'warning', icon: 'alert' },
  IMPORTANT_CLAUSE: { label: 'Important clause', tone: 'info', icon: 'info' },
  AMBIGUOUS: { label: 'Ambiguous / needs clarification', tone: 'neutral', icon: 'circleDashed' },
};

export const CHANGE_META = {
  CHANGED: { label: 'Changed', tone: 'warning' },
  NEW: { label: 'New', tone: 'success' },
  REMOVED: { label: 'Removed', tone: 'danger' },
  UNCHANGED: { label: 'Unchanged', tone: 'neutral' },
};
