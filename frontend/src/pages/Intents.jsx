import { Link, useParams } from "react-router-dom";
import { Icon } from "../components/ui";
import IntentGrid from "../components/intent/IntentGrid";
import DocumentGate from "../components/document/DocumentGate";
import DocumentMeta from "../components/document/DocumentMeta";

export default function Intents() {
  const { documentId } = useParams();
  return (
    <DocumentGate documentId={documentId}>
      {({ document }) => (
        <div className="page container">
          <Link className="back-link" to={`/documents/${document.id}`}>
            <Icon name="arrowLeft" size={16} />
            Back
          </Link>
          <header className="intent-header">
            <div>
              <h1 className="page-title">What do you want to know?</h1>
              <p className="page-subtitle">Choose an option to get a focused analysis of this document.</p>
            </div>
            <DocumentMeta document={document} compact />
          </header>
          <IntentGrid
            documentId={document.id}
            documentType={document.document_type}
          />
        </div>
      )}
    </DocumentGate>
  );
}
