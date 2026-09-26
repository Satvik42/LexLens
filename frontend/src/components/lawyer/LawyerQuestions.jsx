import { useState } from 'react';
import { Button } from '../ui';
import EvidenceChip from '../evidence/EvidenceChip';

export default function LawyerQuestions({ documentId, questions, onQuestionsChange }) {
  const [draft, setDraft] = useState('');
  const [copied, setCopied] = useState(false);

  function addQuestion(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    onQuestionsChange([...questions, { id: `custom-${Date.now()}`, text, reason: 'Added by you', evidence: [] }]);
    setDraft('');
  }

  async function copyAll() {
    const body = questions.map((item, index) => `${String(index + 1).padStart(2, '0')}. ${item.text}`).join('\n');
    await navigator.clipboard.writeText(body);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function exportList() {
    const body = [
      'Questions to Clarify with a Legal Professional',
      '',
      ...questions.map((item, index) => `${String(index + 1).padStart(2, '0')}. ${item.text}`),
      '',
      'LexLens provides document-grounded information and assistance. It is not a substitute for professional legal advice.',
    ].join('\n');
    const blob = new Blob([body], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'lexlens-lawyer-questions.txt';
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="lawyer">
      <ol className="lawyer__list">
        {questions.map((item, index) => (
          <li key={item.id} className="lawyer__item">
            <span className="lawyer__num" aria-hidden="true">
              {String(index + 1).padStart(2, '0')}
            </span>
            <div>
              <p>{item.text}</p>
              {item.reason ? <p className="text-secondary text-sm">{item.reason}</p> : null}
              {item.evidence?.length ? (
                <div className="row row--wrap" style={{ marginTop: 8 }}>
                  {item.evidence.map((evidence) => (
                    <EvidenceChip key={`${item.id}-${evidence.page}-${evidence.section}`} documentId={documentId} evidence={evidence} />
                  ))}
                </div>
              ) : null}
            </div>
          </li>
        ))}
      </ol>

      <form className="lawyer__add" onSubmit={addQuestion}>
        <label className="field" style={{ flex: 1 }}>
          <span className="sr-only">Add your own question</span>
          <input className="input" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Add your own question" />
        </label>
        <Button type="submit" variant="secondary" icon="plus">
          Add your own question
        </Button>
      </form>

      <div className="row row--wrap lawyer__actions">
        <Button variant="secondary" icon="copy" onClick={copyAll}>
          {copied ? 'Copied' : 'Copy all questions'}
        </Button>
        <Button variant="secondary" icon="download" onClick={exportList}>
          Export
        </Button>
        <Button variant="ghost" icon="print" onClick={() => window.print()}>
          Print / save as PDF
        </Button>
      </div>
    </div>
  );
}
