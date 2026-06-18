import { Box, Typography, Paper, CircularProgress, Alert, Divider } from '@mui/material';
import { Grid } from '@mui/material';
import {
  FactoryOutlined, CheckCircleOutlined, CancelOutlined, WarningAmberOutlined, PersonOutlined,
} from '@mui/icons-material';
import { usePageData } from '../hooks/usePageData';
import MotorTable from '../components/MotorTable';
import NewEntryForm from '../components/NewEntryForm';
import type { Stats, LocationStat } from '../types/api';

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      <Box
        sx={{
          bgcolor: color,
          borderRadius: 1.5,
          p: 1.25,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'common.white',
        }}
      >
        {icon}
      </Box>
      <Box>
        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
          {title}
        </Typography>
        <Typography variant="h3" sx={{ lineHeight: 1.2 }}>{value}</Typography>
      </Box>
    </Paper>
  );
}

function LocationChart({ data }: { data: LocationStat[] }) {
  const max = Math.max(...data.map((d) => d.total), 1);
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {data.map((loc) => (
        <Box key={loc.storage_location}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.75 }}>
            <Typography variant="body2" fontWeight={600}>{loc.storage_location}</Typography>
            <Typography variant="caption" color="text.secondary">{loc.total}</Typography>
          </Box>
          <Box sx={{ display: 'flex', height: 8, borderRadius: 4, overflow: 'hidden', bgcolor: 'action.hover' }}>
            {loc.io_count > 0 && (
              <Box sx={{ width: `${(loc.io_count / max) * 100}%`, bgcolor: 'success.main', transition: 'width 0.3s' }} />
            )}
            {loc.nio_count > 0 && (
              <Box sx={{ width: `${(loc.nio_count / max) * 100}%`, bgcolor: 'error.main', transition: 'width 0.3s' }} />
            )}
            {loc.wio_count > 0 && (
              <Box sx={{ width: `${(loc.wio_count / max) * 100}%`, bgcolor: 'warning.main', transition: 'width 0.3s' }} />
            )}
          </Box>
        </Box>
      ))}
      <Box sx={{ display: 'flex', gap: 2.5, mt: 0.5 }}>
        {[{ label: 'iO', color: 'success.main' }, { label: 'niO', color: 'error.main' }, { label: 'wiO', color: 'warning.main' }].map((l) => (
          <Box key={l.label} sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
            <Box sx={{ width: 10, height: 10, bgcolor: l.color, borderRadius: '50%' }} />
            <Typography variant="caption" color="text.secondary">{l.label}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

function StatsCards({ stats }: { stats: Stats }) {
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard title="Gesamt" value={stats.total} icon={<FactoryOutlined />} color="primary.main" />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard title="Status iO" value={stats.io} icon={<CheckCircleOutlined />} color="success.main" />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard title="Status niO" value={stats.open_nio} icon={<CancelOutlined />} color="error.main" />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard title="Meine offenen" value={stats.my_open} icon={<PersonOutlined />} color="secondary.main" />
      </Grid>
    </Grid>
  );
}

export default function DashboardPage() {
  const { data, loading, error, reload } = usePageData('dashboard');

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ m: 2 }}>Fehler beim Laden: {error}</Alert>;
  if (!data) return null;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box>
        <Typography variant="h1" sx={{ mb: 0.5 }}>Motor Auftragssteuerung</Typography>
        <Typography variant="body1" color="text.secondary">
          Überblick über alle erfassten Motoren und Abholaufträge
        </Typography>
      </Box>

      <StatsCards stats={data.stats} />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <NewEntryForm
            motorTypes={data.motor_types}
            storageLocations={data.storage_locations}
            persons={data.request_persons}
            groups={data.groups}
            defaultDate={new Date().toISOString().slice(0, 10)}
            defaultTime={new Date().toTimeString().slice(0, 5)}
            onSaved={reload}
          />
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper elevation={0} sx={{ p: 3, height: '100%', border: 1, borderColor: 'divider', borderRadius: 2 }}>
            <Typography variant="h5" gutterBottom>Status nach Lagerort</Typography>
            <Divider sx={{ mb: 2 }} />
            <LocationChart data={data.status_by_location} />
          </Paper>
        </Grid>
      </Grid>

      <Paper elevation={0} sx={{ p: 3, border: 1, borderColor: 'divider', borderRadius: 2 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Letzte Einträge</Typography>
        <Divider sx={{ mb: 2 }} />
        <MotorTable
          entries={data.entries}
          persons={data.request_persons}
          groups={data.groups}
          motorTypes={data.motor_types}
          storageLocations={data.storage_locations}
          currentProfile={data.current_profile}
          view="dashboard"
          onReload={reload}
        />
      </Paper>
    </Box>
  );
}
