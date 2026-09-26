import { useEffect, useState } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
import { AlertCard } from '../components/ui';
import DocumentGate from '../components/document/DocumentGate';
import DocumentViewer from '../components/viewer/DocumentViewer';
import { useDocumentPages } from '../hooks/useDocument';
import { getEvidence } from '../services/documents';
import { normalizeEvidence } from '../utils/evidence';

export default function Viewer() {
  const { documentId } = useParams();
  const location = useLocation();
  const [params] = useSearchParams();
  const { pages, loading, error } = useDocumentPages(documentId);
  const [evidence, setEvidence] = useState(() => normalizeEvidence(location.state?.evidence));
  const relatedQuestions = location.state?.relatedQuestions ?? [];

  useEffect(() => {
    const fromState = normalizeEvidence(location.state?.evidence);
    if (fromState) {
      setEvidence(fromState);
      return;
    }
    const id = params.get('evidence');
    if (!id) return;
    getEvidence(documentId, id)
      .then((row) =>
        setEvidence(
          normalizeEvidence({
            id: row.id,
            page: row.page_number,
            section: row.section,
            text: row.text,
            start_offset: row.start_offset,
            end_offset: row.end_offset,
            heading: row.location_data?.heading,
            verified: row.verified,
          }),
        ),
      )
      .catch(() => {});
  }, [documentId, location.state, params]);

  return (
    <DocumentGate documentId={documentId}>
      {({ document }) => {
        if (loading) {
          return (
            <div className="page-state" role="status">
              <span className="spinner" aria-hidden="true" />
              Opening the document…
            </div>
          );
        }
        if (error || !pages) {
          return (
            <div className="page container">
              <AlertCard tone="danger">We couldn&apos;t load the document pages.</AlertCard>
            </div>
          );
        }
        return (
          <DocumentViewer document={document} pages={pages} evidence={evidence} relatedQuestions={relatedQuestions} />
        );
      }}
    </DocumentGate>
  );
}
