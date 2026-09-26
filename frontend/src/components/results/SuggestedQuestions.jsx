import { useNavigate } from 'react-router-dom';

export default function SuggestedQuestions({ documentId, questions, heading = 'You might also want to know' }) {
  const navigate = useNavigate();
  if (!questions?.length) return null;

  return (
    <section className="suggested" aria-label={heading}>
      <h2 className="suggested__heading">{heading}</h2>
      <ul className="suggested__list">
        {questions.map((question) => (
          <li key={question}>
            <button
              type="button"
              className="chip chip--question"
              onClick={() => navigate(`/documents/${documentId}/ask?q=${encodeURIComponent(question)}`)}
            >
              {question}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
