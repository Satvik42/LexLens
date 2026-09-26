import { render, screen } from '@testing-library/react';
import NotDetermined from './NotDetermined';

test('renders the required not-determined sections without inventing an answer', () => {
  render(
    <NotDetermined
      explanation="I couldn't identify a clause that explains what happens to stock options after resignation."
      whatIFound="No relevant stock-option or equity clause was identified in this document."
      professionalQuestions={['What happens to vested options after resignation?', 'Is there a separate equity agreement?']}
    />,
  );
  expect(screen.getByText(/cannot be determined from this document/i)).toBeInTheDocument();
  expect(screen.getByText(/what i found/i)).toBeInTheDocument();
  expect(screen.getByText(/no relevant stock-option or equity clause/i)).toBeInTheDocument();
  expect(screen.getByText(/you may want to ask a legal professional/i)).toBeInTheDocument();
  expect(screen.getByText(/vested options/i)).toBeInTheDocument();
});
