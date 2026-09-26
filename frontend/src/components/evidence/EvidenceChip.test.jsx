import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import EvidenceChip from './EvidenceChip';

const evidence = { id: 'ev-1', page: 8, section: '8.2', text: 'sixty (60) days written notice' };

test('renders a source chip that links to the document viewer', () => {
  render(
    <MemoryRouter>
      <EvidenceChip documentId="doc-1" evidence={evidence} />
    </MemoryRouter>,
  );
  const chip = screen.getByRole('link', { name: /page 8 · §8\.2/i });
  expect(chip).toHaveAttribute('href', '/documents/doc-1/view?evidence=ev-1&page=8');
});
