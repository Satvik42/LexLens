import { Button } from '../components/ui';

export default function NotFound() {
  return (
    <div className="page container page--narrow" style={{ textAlign: 'center' }}>
      <h1 className="page-title">Page not found</h1>
      <p className="page-subtitle" style={{ margin: '8px auto 20px' }}>
        That link does not match a LexLens screen.
      </p>
      <Button to="/">Back to home</Button>
    </div>
  );
}
