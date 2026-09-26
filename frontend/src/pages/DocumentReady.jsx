import { Link, useParams } from 'react-router-dom';
import { Button, Icon } from '../components/ui';
import DocumentMeta from '../components/document/DocumentMeta';
import DocumentGate from '../components/document/DocumentGate';

export default function DocumentReady() {
  const { documentId } = useParams();
  return (
    <DocumentGate documentId={documentId}>
      {({ document }) => (
        <div className="page container ready-screen">
          <Link className="back-link" to="/upload">
            <Icon name="arrowLeft" size={16} />
            Back
          </Link>
          <div className="ready-heading">
            <span className="icon-box icon-box--success" aria-hidden="true">
              <Icon name="check" size={22} />
            </span>
            <h1 className="page-title">Your document is ready!</h1>
          </div>
          <div className="ready-grid">
            <article className="card ready-file">
              <DocumentMeta document={document} />
              <Button variant="ghost" size="sm" to="/upload">
                Replace file
              </Button>
            </article>
            <article className="card ready-prompt">
              <h2>What would you like to understand?</h2>
              <p className="text-secondary">Choose an option to get started.</p>
              <ul className="ready-hints">
                <li>Notice</li>
                <li>Pay</li>
                <li>Restrictions</li>
                <li>Concerns</li>
              </ul>
              <Button to={`/documents/${document.id}/intents`} iconRight="arrowRight">
                Choose an option
              </Button>
            </article>
          </div>
        </div>
      )}
    </DocumentGate>
  );
}
