import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ComparisonTable from './ComparisonTable';

const result = {
  original_document_id: 'a',
  updated_document_id: 'b',
  original_filename: 'original.pdf',
  updated_filename: 'updated.pdf',
  rows: [
    {
      id: 'r1',
      term: 'Notice Period',
      original_value: '30 days',
      updated_value: '60 days',
      change: 'CHANGED',
      note: null,
      original_evidence: [{ id: 'e1', page: 4, section: '4.1', text: 'thirty (30) days' }],
      updated_evidence: [{ id: 'e2', page: 8, section: '8.2', text: 'sixty (60) days' }],
    },
  ],
};

test('renders an evidence-backed comparison table', () => {
  render(
    <MemoryRouter>
      <ComparisonTable result={result} />
    </MemoryRouter>,
  );
  expect(screen.getByRole('rowheader', { name: 'Notice Period' })).toBeInTheDocument();
  expect(screen.getByText('30 days')).toBeInTheDocument();
  expect(screen.getByText('60 days')).toBeInTheDocument();
  expect(screen.getByText('Changed')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /page 4 · §4\.1/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /page 8 · §8\.2/i })).toBeInTheDocument();
});
