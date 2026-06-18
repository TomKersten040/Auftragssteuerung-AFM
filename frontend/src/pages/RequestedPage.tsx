import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { usePageData } from '../hooks/usePageData';
import MotorTable from '../components/MotorTable';

export default function RequestedPage() {
  const { data, loading, error, reload } = usePageData('requested');

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ m: 2 }}>Fehler beim Laden: {error}</Alert>;
  if (!data) return null;

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h1" sx={{ mb: 0.5 }}>Angeforderte Abholungen</Typography>
        <Typography variant="body1" color="text.secondary">
          Alle offenen Abholaufträge mit Zuweisung.
        </Typography>
      </Box>
      <Paper elevation={0} sx={{ p: 3, border: 1, borderColor: 'divider', borderRadius: 2 }}>
        <MotorTable
          entries={data.entries}
          persons={data.request_persons}
          groups={data.groups}
          motorTypes={data.motor_types}
          storageLocations={data.storage_locations}
          currentProfile={data.current_profile}
          view="requested"
          onReload={reload}
        />
      </Paper>
    </Box>
  );
}
