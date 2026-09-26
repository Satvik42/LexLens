import { evidenceLabel, splitBlockForEvidence, splitByTerm } from '../../utils/evidence';

/**
 * Renders one normalized page. Evidence is highlighted in yellow via <mark>.
 * A textual source line is always shown so the highlight is not colour-only.
 */
export default function PageView({ page, evidence, searchTerm, zoom = 1 }) {
  const source = evidence ? `Source: ${evidenceLabel(evidence)}` : null;

  return (
    <article
      className="page-view"
      data-page={page.page_number}
      style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
      aria-label={`Page ${page.page_number}`}
    >
      <header className="page-view__header">
        <span>Page {page.page_number}</span>
        {source ? <span className="page-view__source">{source}</span> : null}
      </header>
      <div className="page-view__body">
        {(page.blocks?.length ? page.blocks : [{ block_id: 'full', text: page.text, start: 0, end: page.text.length }]).map((block) => (
          <Block key={block.block_id} block={block} evidence={evidence} searchTerm={searchTerm} />
        ))}
      </div>
    </article>
  );
}

function Block({ block, evidence, searchTerm }) {
  const Tag = block.is_heading ? 'h3' : 'p';
  const split = evidence ? splitBlockForEvidence(block, evidence) : null;

  if (split) {
    return (
      <Tag className={block.is_heading ? 'page-view__heading' : 'page-view__p'}>
        {renderWithSearch(split[0], searchTerm)}
        <mark className="evidence-highlight" id={`evidence-${evidence.id || evidence.page}`}>
          {split[1]}
        </mark>
        {renderWithSearch(split[2], searchTerm)}
      </Tag>
    );
  }

  return <Tag className={block.is_heading ? 'page-view__heading' : 'page-view__p'}>{renderWithSearch(block.text, searchTerm)}</Tag>;
}

function renderWithSearch(text, term) {
  if (!text) return null;
  if (!term) return text;
  const parts = splitByTerm(text, term);
  return parts.map((part, index) =>
    index % 2 === 1 ? (
      <mark key={`${part}-${index}`} className="search-highlight">
        {part}
      </mark>
    ) : (
      <span key={`${part}-${index}`}>{part}</span>
    ),
  );
}
