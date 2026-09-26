import { Link, useParams } from 'react-router-dom';
import { AlertCard, Button, Icon } from '../components/ui';
import DocumentGate from '../components/document/DocumentGate';
import AnalyzingState from '../components/results/AnalyzingState';
import SuggestedQuestions from '../components/results/SuggestedQuestions';
import NotDetermined from '../components/results/NotDetermined';
import KeyTermsResult from '../components/results/KeyTermsResult';
import CompensationResult from '../components/results/CompensationResult';
import NoticeExitResult from '../components/results/NoticeExitResult';
import RestrictionsResult from '../components/results/RestrictionsResult';
import ConcernsResult from '../components/results/ConcernsResult';
import ObligationsResult from '../components/results/ObligationsResult';
import { useAnalysis } from '../hooks/useAnalysis';
import { getOperation } from '../utils/operations';

const RENDERERS = {
  KEY_TERMS: KeyTermsResult,
  COMPENSATION: CompensationResult,
  NOTICE_EXIT: NoticeExitResult,
  RESTRICTIONS: RestrictionsResult,
  CONCERNS: ConcernsResult,
  OBLIGATIONS: ObligationsResult,
};

export default function Analysis() {
  const { documentId, operation } = useParams();
  const spec = getOperation(operation);
  const { result, status, error, run } = useAnalysis(documentId, operation, { enabled: Boolean(spec) });

  return (
    <DocumentGate documentId={documentId}>
      {({ document }) => (
        <div className="page container">
          <Link className="back-link" to={`/documents/${document.id}/intents`}>
            <Icon name="arrowLeft" size={16} />
            What do you want to know?
          </Link>
          <header style={{ margin: '20px 0 24px' }}>
            <p className="eyebrow">{document.filename}</p>
            <h1 className="page-title">{spec?.label || 'Analysis'}</h1>
            <p className="page-subtitle">{spec?.description}</p>
          </header>

          {!spec ? <AlertCard tone="danger">Unknown operation.</AlertCard> : null}
          {status === 'loading' ? <AnalyzingState title={`Analyzing ${spec?.label?.toLowerCase() || 'your document'}`} /> : null}
          {status === 'error' ? (
            <div className="stack">
              <AlertCard tone="danger" title="We couldn't analyze this document.">
                {error?.message || 'The document was uploaded successfully, but analysis did not finish.'}
              </AlertCard>
              <div className="row">
                <Button onClick={() => run({ force: true })}>Try again</Button>
                <Button variant="secondary" to="/upload">
                  Upload another document
                </Button>
              </div>
            </div>
          ) : null}

          {result ? <AnalysisBody documentId={document.id} operation={operation} result={result} /> : null}
        </div>
      )}
    </DocumentGate>
  );
}

function AnalysisBody({ documentId, operation, result }) {
  const Renderer = RENDERERS[operation];
  const empty = !result.findings?.length && !result.concerns?.length && !result.inconsistencies?.length;

  if (result.status === 'NOT_FOUND' && empty) {
    return (
      <>
        <NotDetermined
          title="Cannot be determined from this document"
          explanation={result.summary}
          whatIFound={result.summary}
          professionalQuestions={result.professional_questions}
        />
        <SuggestedQuestions documentId={documentId} questions={result.related_questions} />
      </>
    );
  }

  return (
    <div className="stack" style={{ gap: 28 }}>
      {result.summary ? <p className="text-secondary">{result.summary}</p> : null}
      {Renderer ? <Renderer documentId={documentId} result={result} /> : <p>{result.summary}</p>}
      <SuggestedQuestions documentId={documentId} questions={result.related_questions} />
      {result.professional_questions?.length ? (
        <SuggestedQuestions
          documentId={documentId}
          questions={result.professional_questions}
          heading="You may want to ask a legal professional"
        />
      ) : null}
    </div>
  );
}
