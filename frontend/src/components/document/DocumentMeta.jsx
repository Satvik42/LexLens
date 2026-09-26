import { Icon } from '../ui';
import { documentTypeLabel, fileTypeLabel, formatFileSize, pluralize } from '../../utils/formatting';

export default function DocumentMeta({ document, compact = false }) {
  if (!document) return null;
  const pages = document.page_count != null ? pluralize(document.page_count, 'page') : null;
  const size = formatFileSize(document.size_bytes);
  const meta = [pages, size].filter(Boolean).join(' · ');

  return (
    <div className={`document-meta ${compact ? 'document-meta--compact' : ''}`}>
      <span className="icon-box icon-box--danger" aria-hidden="true">
        <Icon name="file" size={compact ? 18 : 22} />
      </span>
      <div>
        <p className="document-meta__name">{document.filename}</p>
        <p className="text-secondary text-sm">
          {fileTypeLabel(document.mime_type)}
          {meta ? ` · ${meta}` : ''}
        </p>
        {!compact ? (
          <p className="text-sm" style={{ marginTop: 6 }}>
            Detected as: <strong>{document.document_title || documentTypeLabel(document.document_type)}</strong>
          </p>
        ) : null}
      </div>
    </div>
  );
}
