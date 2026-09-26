import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Icon } from '../components/ui';
import UploadZone from '../components/upload/UploadZone';
import { getDocument, getDocumentStatus, uploadDocument } from '../services/documents';
import { useDocumentStore } from '../state/documentStore';
import { ApiError } from '../services/api';

export default function Upload() {
  const navigate = useNavigate();
  const setDocument = useDocumentStore((state) => state.setDocument);
  const [phase, setPhase] = useState('idle');
  const [error, setError] = useState(null);

  async function onFile(file) {
    setError(null);
    setPhase('uploading');
    try {
      const uploaded = await uploadDocument(file);
      if (uploaded.processing_status === 'READY') {
        setDocument(uploaded);
        navigate(`/documents/${uploaded.id}`);
        return;
      }
      setDocument(uploaded);
      setPhase('processing');
      await waitUntilReady(uploaded.id, setDocument, navigate, setPhase, setError);
    } catch (err) {
      setPhase('error');
      setError(err instanceof ApiError ? err.message : "We couldn't upload this document. Check the file type and size and try again.");
    }
  }

  return (
    <div className="page container upload-page">
      <Link className="back-link" to="/">
        <Icon name="arrowLeft" size={16} />
        Back
      </Link>
      <div className="upload-card">
        {phase === 'uploading' || phase === 'processing' ? (
          <div className="upload-progress" role="status" aria-live="polite">
            <span className="icon-box icon-box--lg" aria-hidden="true">
              <span className="spinner" />
            </span>
            <h1 className="upload-zone__title">{phase === 'uploading' ? 'Uploading…' : 'Processing your document…'}</h1>
            <p className="text-secondary">This may take a moment. Your document is being processed securely.</p>
          </div>
        ) : (
          <UploadZone onFile={onFile} error={error} />
        )}
      </div>
      <ul className="upload-footnotes">
        <li>
          <span className="icon-box" aria-hidden="true">
            <Icon name="shield" size={16} />
          </span>
          Your files are secure
        </li>
        <li>
          <span className="icon-box" aria-hidden="true">
            <Icon name="calendar" size={16} />
          </span>
          Processed privately
        </li>
        <li>
          <span className="icon-box" aria-hidden="true">
            <Icon name="file" size={16} />
          </span>
          PDF, DOCX, TXT
        </li>
      </ul>
    </div>
  );
}

async function waitUntilReady(id, setDocument, navigate, setPhase, setError) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    const status = await getDocumentStatus(id);
    if (status.processing_status === 'READY') {
      setDocument(await getDocument(id));
      navigate(`/documents/${id}`);
      return;
    }
    if (status.processing_status === 'FAILED') {
      setPhase('error');
      setError(status.processing_error || "We couldn't process this document. Try uploading a clearer copy.");
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  setPhase('error');
  setError('Processing is taking longer than expected. Open My Documents and try again.');
}
