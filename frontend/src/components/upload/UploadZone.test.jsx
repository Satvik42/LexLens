import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadZone, { validateFile } from './UploadZone';

test('labels the file input and shows the upload prompt', () => {
  render(<UploadZone onFile={() => {}} />);
  expect(screen.getByRole('heading', { name: /upload your legal document/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/upload your legal document/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
});

test('rejects unsupported file types before upload', () => {
  const file = new File(['nope'], 'photo.png', { type: 'image/png' });
  expect(validateFile(file)).toMatch(/not supported/i);
});

test('rejects files larger than 20 MB', () => {
  const file = new File(['x'], 'huge.pdf', { type: 'application/pdf' });
  Object.defineProperty(file, 'size', { value: 21 * 1024 * 1024 });
  expect(validateFile(file)).toMatch(/20 MB/i);
});

test('calls onFile for a valid PDF', async () => {
  const user = userEvent.setup();
  const onFile = vi.fn();
  render(<UploadZone onFile={onFile} />);
  const input = screen.getByLabelText(/upload your legal document/i);
  const file = new File(['%PDF-1.4'], 'agreement.pdf', { type: 'application/pdf' });
  await user.upload(input, file);
  expect(onFile).toHaveBeenCalledWith(file);
});
