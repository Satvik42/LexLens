import { useEffect, useRef, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { AlertCard, Button, Icon } from '../components/ui';
import DocumentGate from '../components/document/DocumentGate';
import NotDetermined from '../components/results/NotDetermined';
import SuggestedQuestions from '../components/results/SuggestedQuestions';
import EvidenceCard from '../components/evidence/EvidenceCard';
import StatusBadge from '../components/evidence/StatusBadge';
import { askQuestion } from '../services/analysis';
import { useDocumentStore } from '../state/documentStore';

export default function AskDocument() {
  const { documentId } = useParams();
  const [params] = useSearchParams();
  const preset = params.get('q') || '';
  const cached = useDocumentStore((state) => state.conversations[documentId]);
  const setConversation = useDocumentStore((state) => state.setConversation);
  const [question, setQuestion] = useState(preset);
  const [conversationId, setConversationId] = useState(cached?.id ?? null);
  const [messages, setMessages] = useState(cached?.messages ?? []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const asked = useRef(new Set());

  useEffect(() => {
    if (preset) setQuestion(preset);
    if (preset && !asked.current.has(preset)) {
      asked.current.add(preset);
      submit(preset);
    }
    // one-shot when arriving with ?q=
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preset]);

  async function submit(text) {
    const value = (text ?? question).trim();
    if (value.length < 3 || busy) return;
    setBusy(true);
    setError(null);
    setQuestion('');
    try {
      const answer = await askQuestion(documentId, value, conversationId);
      const next = { id: answer.conversation_id, messages: [...messages, { question: value, answer }] };
      setConversationId(answer.conversation_id);
      setMessages(next.messages);
      setConversation(documentId, next);
    } catch (err) {
      setError(err.message);
      setQuestion(value);
    } finally {
      setBusy(false);
    }
  }

  return (
    <DocumentGate documentId={documentId}>
      {({ document }) => (
        <div className="page container page--narrow">
          <Link className="back-link" to={`/documents/${document.id}/intents`}>
            <Icon name="arrowLeft" size={16} />
            Back
          </Link>
          <header style={{ margin: '20px 0 24px' }}>
            <h1 className="page-title">Ask about the document</h1>
            <p className="page-subtitle">Every answer is grounded in {document.filename}. If the document does not say, we will say so.</p>
          </header>

          <div className="ask-thread">
            {messages.map((item) => (
              <QaTurn key={item.answer.id} documentId={document.id} item={item} />
            ))}
            {busy ? (
              <div className="card card--padded" role="status">
                <span className="spinner" aria-hidden="true" /> Looking in the document…
              </div>
            ) : null}
            {error ? <AlertCard tone="danger">{error}</AlertCard> : null}
          </div>

          <form
            className="ask-box"
            onSubmit={(event) => {
              event.preventDefault();
              submit();
            }}
          >
            <label className="field" style={{ flex: 1 }}>
              <span className="sr-only">Ask about this document</span>
              <input
                className="input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about this document…"
              />
            </label>
            <Button type="submit" icon="send" disabled={busy || question.trim().length < 3}>
              Ask
            </Button>
          </form>
        </div>
      )}
    </DocumentGate>
  );
}

function QaTurn({ documentId, item }) {
  const { question, answer } = item;
  const missing = answer.status === 'NOT_FOUND';
  return (
    <section className="ask-turn">
      <p className="ask-user">{question}</p>
      <div className="card card--padded">
        {missing ? (
          <NotDetermined
            title={answer.title || 'Cannot be determined from this document'}
            explanation={answer.explanation}
            whatIFound={answer.what_i_found}
            professionalQuestions={answer.professional_questions}
          />
        ) : (
          <>
            <StatusBadge status={answer.status} />
            <h2 className="section-title" style={{ marginTop: 12 }}>
              {answer.title || 'Answer'}
            </h2>
            <p style={{ marginTop: 8 }}>{answer.answer || answer.explanation}</p>
            {answer.evidence?.length ? (
              <div className="stack" style={{ marginTop: 16, gap: 12 }}>
                <p className="eyebrow">Evidence</p>
                {answer.evidence.map((evidence) => (
                  <EvidenceCard
                    key={`${evidence.id || evidence.page}-${evidence.text}`}
                    documentId={documentId}
                    evidence={evidence}
                    relatedQuestions={answer.related_questions}
                  />
                ))}
              </div>
            ) : null}
          </>
        )}
        <SuggestedQuestions documentId={documentId} questions={answer.related_questions} />
      </div>
    </section>
  );
}
