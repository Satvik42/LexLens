import { Badge } from '../ui';
import { statusMeta } from '../../utils/status';

export default function StatusBadge({ status }) {
  const meta = statusMeta(status);
  return (
    <Badge tone={meta.tone} icon={meta.icon}>
      {meta.label}
    </Badge>
  );
}
