import { Icon, IconButton } from '../ui';

export default function ViewerToolbar({ filename, page, pageCount, zoom, search, onPage, onZoom, onSearch }) {
  return (
    <div className="viewer-toolbar">
      <p className="viewer-toolbar__name">{filename}</p>
      <div className="viewer-toolbar__controls">
        <IconButton icon="chevronLeft" label="Previous page" disabled={page <= 1} onClick={() => onPage(page - 1)} />
        <label className="viewer-page">
          <span className="sr-only">Current page</span>
          <input
            type="number"
            min={1}
            max={pageCount}
            value={page}
            onChange={(event) => onPage(Number(event.target.value) || 1)}
          />
          <span aria-hidden="true">/ {pageCount}</span>
        </label>
        <IconButton icon="chevronRight" label="Next page" disabled={page >= pageCount} onClick={() => onPage(page + 1)} />
        <IconButton icon="zoomOut" label="Zoom out" onClick={() => onZoom(Math.max(0.7, +(zoom - 0.1).toFixed(2)))} />
        <span className="viewer-zoom">{Math.round(zoom * 100)}%</span>
        <IconButton icon="zoomIn" label="Zoom in" onClick={() => onZoom(Math.min(1.6, +(zoom + 0.1).toFixed(2)))} />
        <label className="viewer-search">
          <Icon name="search" size={14} />
          <span className="sr-only">Search this document</span>
          <input type="search" placeholder="Search" value={search} onChange={(event) => onSearch(event.target.value)} />
        </label>
      </div>
    </div>
  );
}
