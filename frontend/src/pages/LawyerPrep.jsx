import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertCard, Icon } from '../components/ui';
import DocumentGate from '../components/document/DocumentGate';
import AnalyzingState from '../components/results/AnalyzingState';
import LawyerQuestions from '../components/lawyer/LawyerQuestions';
import { getLawyerQuestions } from '../services/analysis';
import { useDocumentStore } from '../state/documentStore';

export default function LawyerPrep() {
  const { documentId } = useParams();
  const cached = useDocumentStore((state) => state.lawyerQuestions[documentId]);
  const setLawyerQuestions = useDocumentStore((state) => state.setLawyerQuestions);
  const [questions, setQuestions] = useState(cached?.questions ?? []);
  const [status, setStatus] = useState(cached ? 'ready' : 'loading');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (cached) return;
    getLawyerQuestions(documentId)
      .then((result) => {
        setLawyerQuestions(documentId, result);
        setQuestions(result.questions);
        setStatus('ready');
      })
      .catch((err) => {
        setError(err.message);
        setStatus('error');
      });
  }, [cached, documentId, setLawyerQuestions]);

  return (
    <DocumentGate documentId={documentId}>
      {({ document }) => (
        <div className="page container page--narrow">
          <Link className="back-link" to={`/documents/${document.id}/intents`}>
            <Icon name="arrowLeft" size={16} />
            Back
          </Link>
          <header style={{ margin: '20px 0 24px' }}>
            <h1 className="page-title">Questions to Clarify with a Legal Professional</h1>
            <p className="page-subtitle">
              Based on your document, here are some important questions you may want to discuss.
            </p>
          </header>
          {status === 'loading' ? <AnalyzingState title="Preparing questions from your document" /> : null}
          {status === 'error' ? <AlertCard tone="danger">{error}</AlertCard> : null}
          {status === 'ready' ? (
            <LawyerQuestions documentId={document.id} questions={questions} onQuestionsChange={setQuestions} />
          ) : null}
        </div>
      )}
    </DocumentGate>
  );
}
