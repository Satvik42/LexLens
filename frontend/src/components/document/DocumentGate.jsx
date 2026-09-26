import { Link } from 'react-router-dom';
import { AlertCard, Button } from '../ui';
import { useDocument } from '../../hooks/useDocument';
import { reprocessDocument } from '../../services/documents';

export default function DocumentGate({ documentId, children }) {
  const { document, loading, error, reload } = useDocument(documentId);

  if (loading) {
    return (
      <div className="page-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        Loading your document…
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="page container page--narrow">
        <AlertCard tone="danger" title="We couldn't open this document">
          {error?.message || 'The document was not found, or you do not have access to it.'}
        </AlertCard>
        <div style={{ marginTop: 16 }}>
          <Button to="/documents">My Documents</Button>
        </div>
      </div>
    );
  }

  if (document.processing_status === 'FAILED') {
    return (
      <div className="page container page--narrow">
        <AlertCard tone="danger" title="We couldn't process this document">
          {document.processing_error || 'Try uploading a clearer copy, or a text-based PDF.'}
        </AlertCard>
        <div className="row" style={{ marginTop: 16 }}>
          <Button
            onClick={async () => {
              await reprocessDocument(document.id);
              reload();
            }}
          >
            Try again
          </Button>
          <Button variant="secondary" to="/upload">
            Upload another document
          </Button>
        </div>
      </div>
    );
  }

  if (document.processing_status !== 'READY') {
    return (
      <div className="page container page--narrow">
        <div className="card card--padded analyzing" role="status" aria-live="polite">
          <div className="row">
            <span className="spinner" aria-hidden="true" />
            <div>
              <h1 className="section-title">Processing your document…</h1>
              <p className="text-secondary">This may take a moment. Your document is being processed securely.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return children({ document, reload });
}

export function EmptyDocument() {
  return (
    <div className="page container page--narrow">
      <div className="card card--padded" style={{ textAlign: 'center' }}>
        <h1 className="page-title">No document selected</h1>
        <p className="page-subtitle" style={{ margin: '8px auto 20px' }}>
          Upload a legal document to get started.
        </p>
        <Link className="btn btn--primary" to="/upload">
          Upload document
        </Link>
      </div>
    </div>
  );
}
