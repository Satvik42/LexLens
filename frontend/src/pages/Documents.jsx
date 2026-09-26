import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCard, Button, Card } from '../components/ui';
import DocumentMeta from '../components/document/DocumentMeta';
import { deleteDocument, listDocuments } from '../services/documents';
import { useDocumentStore } from '../state/documentStore';
import { formatDate } from '../utils/formatting';

export default function Documents() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const setDocument = useDocumentStore((state) => state.setDocument);
  const removeDocument = useDocumentStore((state) => state.removeDocument);

  useEffect(() => {
    listDocuments()
      .then((result) => {
        setItems(result);
        result.forEach(setDocument);
      })
      .catch(setError);
  }, [setDocument]);

  async function onDelete(id) {
    await deleteDocument(id);
    removeDocument(id);
    setItems((current) => current.filter((item) => item.id !== id));
  }

  return (
    <div className="page container">
      <div className="row row--between row--wrap" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="page-title">My Documents</h1>
          <p className="page-subtitle">Documents on this account. Each analysis stays tied to the file it came from.</p>
        </div>
        <Button to="/upload" icon="upload">
          Analyze a Document
        </Button>
      </div>
      {error ? <AlertCard tone="danger">{error.message}</AlertCard> : null}
      {items && !items.length ? (
        <Card>
          <h2 className="section-title">No document selected</h2>
          <p className="text-secondary" style={{ margin: '8px 0 16px' }}>
            Upload a legal document to get started.
          </p>
          <Button to="/upload">Upload document</Button>
        </Card>
      ) : null}
      <div className="document-list">
        {items?.map((document) => (
          <article key={document.id} className="card card--padded document-list__item">
            <DocumentMeta document={document} compact />
            <p className="text-muted text-sm">Uploaded {formatDate(document.created_at)}</p>
            <div className="row row--wrap">
              <Link className="btn btn--primary btn--sm" to={`/documents/${document.id}`}>
                Open
              </Link>
              <Link className="btn btn--secondary btn--sm" to={`/documents/${document.id}/intents`}>
                Analyze
              </Link>
              <button type="button" className="btn btn--danger btn--sm" onClick={() => onDelete(document.id)}>
                Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
