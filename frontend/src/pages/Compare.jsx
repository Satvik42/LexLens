import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertCard, Button, Icon } from '../components/ui';
import DocumentGate from '../components/document/DocumentGate';
import DocumentMeta from '../components/document/DocumentMeta';
import ComparisonTable from '../components/compare/ComparisonTable';
import AnalyzingState from '../components/results/AnalyzingState';
import UploadZone from '../components/upload/UploadZone';
import { listDocuments, uploadDocument, getDocumentStatus } from '../services/documents';
import { createComparison } from '../services/analysis';

export default function Compare() {
  const { documentId } = useParams();
  const [library, setLibrary] = useState([]);
  const [otherId, setOtherId] = useState('');
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);

  useEffect(() => {
    listDocuments().then(setLibrary).catch(() => {});
  }, []);

  async function run(updatedId) {
    setStatus('loading');
    setError(null);
    try {
      const comparison = await createComparison(documentId, updatedId);
      setResult(comparison);
      setStatus('ready');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  async function onUpload(file) {
    setStatus('uploading');
    try {
      const uploaded = await uploadDocument(file);
      let current = uploaded;
      while (current.processing_status !== 'READY' && current.processing_status !== 'FAILED') {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        current = { ...current, ...(await getDocumentStatus(current.id)) };
      }
      if (current.processing_status !== 'READY') {
        setStatus('error');
        setError(current.processing_error || 'The second document could not be processed.');
        return;
      }
      setOtherId(current.id);
      await run(current.id);
    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
  }

  return (
    <DocumentGate documentId={documentId}>
      {({ document }) => (
        <div className="page container">
          <Link className="back-link" to={`/documents/${document.id}/intents`}>
            <Icon name="arrowLeft" size={16} />
            Back
          </Link>
          <header style={{ margin: '20px 0 24px' }}>
            <h1 className="page-title">Compare Documents</h1>
            <p className="page-subtitle">
              Compare another version. Each changed row links to evidence in both documents.
            </p>
          </header>

          <div className="ready-grid" style={{ marginBottom: 24 }}>
            <article className="card card--padded">
              <p className="eyebrow">Original</p>
              <DocumentMeta document={document} compact />
            </article>
            <article className="card card--padded">
              <p className="eyebrow">Updated</p>
              <label className="field">
                <span className="field__label">Choose a document you already uploaded</span>
                <select className="input" value={otherId} onChange={(event) => setOtherId(event.target.value)}>
                  <option value="">Select…</option>
                  {library
                    .filter((item) => item.id !== document.id && item.processing_status === 'READY')
                    .map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.filename}
                      </option>
                    ))}
                </select>
              </label>
              <div style={{ marginTop: 12 }}>
                <Button disabled={!otherId} onClick={() => run(otherId)}>
                  Compare
                </Button>
              </div>
              <p className="text-muted text-sm" style={{ margin: '16px 0 8px' }}>
                Or upload a second file
              </p>
              {status === 'uploading' ? (
                <p role="status">Processing the second document…</p>
              ) : (
                <UploadZone onFile={onUpload} compact />
              )}
            </article>
          </div>

          {status === 'loading' ? <AnalyzingState title="Comparing the two documents" /> : null}
          {status === 'error' ? <AlertCard tone="danger">{error}</AlertCard> : null}
          {result ? (
            <div className="stack" style={{ gap: 16 }}>
              <p className="text-secondary">{result.summary}</p>
              <ComparisonTable result={result} />
            </div>
          ) : null}
        </div>
      )}
    </DocumentGate>
  );
}
