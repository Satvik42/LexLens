import { useId, useRef, useState } from 'react';
import { Icon } from '../ui';

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
};

const ACCEPT = Object.keys(ACCEPTED).concat(Object.values(ACCEPTED).flat()).join(',');
const MAX_BYTES = 20 * 1024 * 1024;

function extensionOf(name) {
  const index = name.lastIndexOf('.');
  return index >= 0 ? name.slice(index).toLowerCase() : '';
}

export function validateFile(file) {
  if (!file) return 'Choose a PDF, DOCX or TXT file.';
  const ext = extensionOf(file.name);
  const allowedExt = ['.pdf', '.docx', '.txt'];
  if (!allowedExt.includes(ext) && !ACCEPTED[file.type]) {
    return 'This file type is not supported. Upload a PDF, DOCX or TXT file.';
  }
  if (file.size > MAX_BYTES) {
    return 'This file is larger than 20 MB. Try a smaller copy.';
  }
  return null;
}

/**
 * Accessible drag-and-drop upload. The hidden file input is labelled by the visible heading.
 */
export default function UploadZone({ onFile, disabled = false, error, compact = false }) {
  const inputId = useId();
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState(null);
  const message = error ?? localError;

  function handleFiles(files) {
    const file = files?.[0];
    const problem = validateFile(file);
    setLocalError(problem);
    if (!problem) onFile(file);
  }

  return (
    <div
      className={`upload-zone ${dragging ? 'upload-zone--dragging' : ''} ${disabled ? 'upload-zone--disabled' : ''}`}
      onDragEnter={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => {
        if (event.currentTarget.contains(event.relatedTarget)) return;
        setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        if (!disabled) handleFiles(event.dataTransfer.files);
      }}
    >
      <div className="icon-box icon-box--lg" aria-hidden="true">
        <Icon name="upload" size={28} />
      </div>
      <h1 className="upload-zone__title" id={`${inputId}-label`}>
        {compact ? 'Upload a second document' : 'Upload your legal document'}
      </h1>
      <p className="text-secondary">Drop your file here, or click to browse.</p>
      {compact ? null : <p className="upload-zone__formats">PDF, DOCX, TXT · up to 20 MB</p>}
      <input
        ref={inputRef}
        id={inputId}
        className="sr-only"
        type="file"
        accept={ACCEPT}
        disabled={disabled}
        aria-labelledby={`${inputId}-label`}
        onChange={(event) => handleFiles(event.target.files)}
      />
      <button
        type="button"
        className="btn btn--primary"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
      >
        <Icon name="upload" size={16} />
        Choose File
      </button>
      {message ? (
        <p className="field__error" role="alert">
          {message}
        </p>
      ) : null}
    </div>
  );
}
