import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import IntentCard from './IntentCard';

const operation = {
  key: 'NOTICE_EXIT',
  label: 'Notice & Exit Terms',
  icon: 'exit',
  description: 'Understand notice periods, resignation, termination and exit conditions.',
};

function LocationProbe() {
  const location = useLocation();
  return <div>{location.pathname}</div>;
}

function renderCard() {
  return render(
    <MemoryRouter initialEntries={['/intents']}>
      <Routes>
        <Route
          path="/intents"
          element={<IntentCard operation={operation} documentId="doc-1" documentType="EMPLOYMENT" />}
        />
        <Route path="/documents/:id/analyze/:operation" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter>,
  );
}

test('is keyboard focusable and has an accessible name', () => {
  renderCard();
  const card = screen.getByRole('link', { name: /notice & exit terms/i });
  expect(card).toHaveAttribute('tabindex', '0');
  card.focus();
  expect(card).toHaveFocus();
});

test('activates with Enter and Space', async () => {
  const user = userEvent.setup();
  renderCard();
  const card = screen.getByRole('link', { name: /notice & exit terms/i });
  card.focus();
  await user.keyboard('{Enter}');
  expect(screen.getByText('/documents/doc-1/analyze/NOTICE_EXIT')).toBeInTheDocument();
});
