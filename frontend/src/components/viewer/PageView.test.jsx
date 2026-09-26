import { render, screen } from '@testing-library/react';
import PageView from './PageView';

const page = {
  page_number: 8,
  text: 'Either party may terminate this Agreement by providing sixty (60) days written notice to the other party.',
  blocks: [
    {
      block_id: 'b1',
      text: '8.2 Termination',
      start: 0,
      end: 15,
      is_heading: true,
    },
    {
      block_id: 'b2',
      text: 'Either party may terminate this Agreement by providing sixty (60) days written notice to the other party.',
      start: 16,
      end: 122,
    },
  ],
};

const evidence = {
  id: 'ev-1',
  page: 8,
  section: '8.2',
  text: 'sixty (60) days written notice',
};

test('highlights supporting text in yellow and shows a textual source', () => {
  render(<PageView page={page} evidence={evidence} />);
  const mark = screen.getByText('sixty (60) days written notice');
  expect(mark.tagName).toBe('MARK');
  expect(mark).toHaveClass('evidence-highlight');
  expect(screen.getByText('Source: Page 8 · §8.2')).toBeInTheDocument();
});
