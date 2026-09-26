import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import PageView from './PageView';
import ViewerToolbar from './ViewerToolbar';
import EvidenceCard from '../evidence/EvidenceCard';
import SuggestedQuestions from '../results/SuggestedQuestions';
import { evidenceLabel, normalizeEvidence } from '../../utils/evidence';

export default function DocumentViewer({ document, pages, evidence, relatedQuestions = [] }) {
  const item = normalizeEvidence(evidence);
  const [page, setPage] = useState(item?.page || 1);
  const [zoom, setZoom] = useState(1);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (item?.page) setPage(item.page);
  }, [item?.page, item?.id]);

  const current = useMemo(() => pages.find((entry) => entry.page_number === page) ?? pages[0], [pages, page]);

  useEffect(() => {
    const mark = window.document.querySelector('.evidence-highlight');
    if (mark) mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [page, item?.id, item?.text]);

  useEffect(() => {
    function onKey(event) {
      if (event.target.matches('input, textarea')) return;
      if (event.key === 'ArrowLeft') setPage((currentPage) => Math.max(1, currentPage - 1));
      if (event.key === 'ArrowRight') setPage((currentPage) => Math.min(pages.length, currentPage + 1));
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [pages.length]);

  return (
    <div className="viewer">
      <aside className="viewer__panel">
        <Link className="back-link" to={`/documents/${document.id}/intents`}>
          Back to analysis
        </Link>
        {item ? (
          <>
            <p className="eyebrow" style={{ marginTop: 16 }}>
              Selected evidence
            </p>
            <h2 className="section-title" style={{ margin: '8px 0 12px' }}>
              {evidenceLabel(item)}
            </h2>
            <EvidenceCard documentId={document.id} evidence={item} relatedQuestions={relatedQuestions} />
          </>
        ) : (
          <p className="text-secondary" style={{ marginTop: 16 }}>
            Open a source chip from an analysis to highlight the supporting text.
          </p>
        )}
        <SuggestedQuestions documentId={document.id} questions={relatedQuestions} heading="Related questions" />
      </aside>
      <section className="viewer__stage">
        <ViewerToolbar
          filename={document.filename}
          page={page}
          pageCount={pages.length}
          zoom={zoom}
          search={search}
          onPage={(next) => setPage(Math.min(pages.length, Math.max(1, next)))}
          onZoom={setZoom}
          onSearch={setSearch}
        />
        <div className="viewer__page-wrap">
          {current ? <PageView page={current} evidence={item?.page === current.page_number ? item : null} searchTerm={search} zoom={zoom} /> : null}
        </div>
      </section>
    </div>
  );
}
