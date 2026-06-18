import { Chip } from '@mui/material';

type MotorStatus = 'iO' | 'niO' | 'wiO';
type PickupStatus = 'Offen' | 'Angefordert' | 'In Bearbeitung' | 'Abgeholt' | 'Nicht erforderlich';

export function MotorStatusChip({ status }: { status: MotorStatus }) {
  const config: Record<MotorStatus, { color: 'success' | 'error' | 'warning'; variant: 'filled' | 'outlined' }> = {
    iO: { color: 'success', variant: 'filled' },
    niO: { color: 'error', variant: 'filled' },
    wiO: { color: 'warning', variant: 'filled' },
  };
  const { color, variant } = config[status];
  return <Chip label={status} color={color} variant={variant} size="small" sx={{ fontWeight: 700, fontSize: '0.75rem' }} />;
}

export function PickupStatusChip({ status }: { status: PickupStatus }) {
  const config: Record<PickupStatus, { color: 'default' | 'primary' | 'warning' | 'success' | 'info'; variant: 'filled' | 'outlined' }> = {
    Offen: { color: 'default', variant: 'outlined' },
    Angefordert: { color: 'primary', variant: 'filled' },
    'In Bearbeitung': { color: 'warning', variant: 'filled' },
    Abgeholt: { color: 'success', variant: 'filled' },
    'Nicht erforderlich': { color: 'info', variant: 'outlined' },
  };
  const { color, variant } = config[status];
  return <Chip label={status} color={color} variant={variant} size="small" sx={{ fontWeight: 600, fontSize: '0.75rem' }} />;
}
