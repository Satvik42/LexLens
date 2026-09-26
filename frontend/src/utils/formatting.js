const DOCUMENT_TYPE_LABELS = {
  EMPLOYMENT: 'Employment Agreement',
  RENTAL: 'Rental Agreement',
  NDA: 'Non-Disclosure Agreement',
  FREELANCE: 'Freelance Contract',
  VENDOR: 'Vendor Agreement',
  INTERNSHIP: 'Internship Agreement',
  SAAS_TERMS: 'SaaS Terms',
  FOUNDER: 'Founder Agreement',
  PARTNERSHIP: 'Partnership Agreement',
  SERVICE: 'Service Agreement',
  POLICY: 'Policy',
  GENERAL: 'General Agreement',
};

export function documentTypeLabel(type) {
  return DOCUMENT_TYPE_LABELS[type] ?? 'Agreement';
}

export function formatFileSize(bytes) {
  if (!Number.isFinite(bytes)) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function pluralize(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export function fileTypeLabel(mimeType) {
  if (mimeType === 'application/pdf') return 'PDF';
  if (mimeType?.includes('wordprocessingml')) return 'DOCX';
  if (mimeType === 'text/plain') return 'TXT';
  return 'Document';
}

export function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}
