import { useState } from 'react';
import {
  Box, Typography, Paper, TextField, Button, IconButton, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, CircularProgress, Alert,
  FormControl, InputLabel, Select, MenuItem, Stack, Dialog, DialogTitle,
  DialogContent, DialogActions, Divider, Chip,
} from '@mui/material';
import { DeleteOutlined, AddOutlined, DownloadOutlined } from '@mui/icons-material';
import { usePageData } from '../hooks/usePageData';
import type { Person, Group } from '../types/api';

function PersonsSection({ persons, groups, onReload }: { persons: Person[]; groups: Group[]; onReload: () => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [groupId, setGroupId] = useState('');
  const [saving, setSaving] = useState(false);

  const addPerson = async () => {
    if (!name.trim()) return;
    setSaving(true);
    const body = new URLSearchParams({ person_name: name, person_email: email, group_id: groupId });
    await fetch('/api/settings/persons/add', { method: 'POST', body });
    setName(''); setEmail(''); setGroupId('');
    setSaving(false);
    onReload();
  };

  const deletePerson = async (id: number) => {
    await fetch(`/api/settings/persons/${id}/delete`, { method: 'POST', body: new URLSearchParams() });
    onReload();
  };

  const updateGroup = async (id: number, gid: string) => {
    await fetch(`/api/settings/persons/${id}/group`, {
      method: 'POST',
      body: new URLSearchParams({ group_id: gid }),
    });
    onReload();
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>Personen verwalten</Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3, alignItems: 'flex-end' }}>
        <TextField size="small" label="Name" value={name} onChange={(e) => setName(e.target.value)} sx={{ minWidth: 180 }} />
        <TextField size="small" label="E-Mail" value={email} onChange={(e) => setEmail(e.target.value)} sx={{ minWidth: 220 }} />
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Gruppe</InputLabel>
          <Select value={groupId} label="Gruppe" onChange={(e) => setGroupId(e.target.value)}>
            <MenuItem value=""><em>Keine Gruppe</em></MenuItem>
            {groups.map((g) => <MenuItem key={g.id} value={String(g.id)}>{g.name}</MenuItem>)}
          </Select>
        </FormControl>
        <Button variant="contained" startIcon={<AddOutlined />} onClick={addPerson} disabled={saving || !name.trim()}>
          Person hinzufügen
        </Button>
      </Box>

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>E-Mail</TableCell>
              <TableCell>Gruppe</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {persons.length === 0 && (
              <TableRow><TableCell colSpan={4}><Typography variant="body2" color="text.secondary">Keine Personen vorhanden.</Typography></TableCell></TableRow>
            )}
            {persons.map((person) => (
              <TableRow key={person.id} hover>
                <TableCell>{person.name}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">{person.email || '—'}</Typography>
                </TableCell>
                <TableCell>
                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <Select
                      value={person.group_id ? String(person.group_id) : ''}
                      onChange={(e) => updateGroup(person.id, e.target.value)}
                      displayEmpty
                    >
                      <MenuItem value=""><em>Keine Gruppe</em></MenuItem>
                      {groups.map((g) => <MenuItem key={g.id} value={String(g.id)}>{g.name}</MenuItem>)}
                    </Select>
                  </FormControl>
                </TableCell>
                <TableCell>
                  <IconButton size="small" color="error" onClick={() => deletePerson(person.id)}>
                    <DeleteOutlined fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}

function GroupsSection({ groups, persons, onReload }: { groups: Group[]; persons: Person[]; onReload: () => void }) {
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);

  const addGroup = async () => {
    if (!name.trim()) return;
    setSaving(true);
    await fetch('/api/settings/groups/add', { method: 'POST', body: new URLSearchParams({ group_name: name }) });
    setName('');
    setSaving(false);
    onReload();
  };

  const deleteGroup = async (id: number) => {
    await fetch(`/api/settings/groups/${id}/delete`, { method: 'POST', body: new URLSearchParams() });
    onReload();
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>Gruppen verwalten</Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'flex-end' }}>
        <TextField size="small" label="Gruppenname" value={name} onChange={(e) => setName(e.target.value)} />
        <Button variant="contained" startIcon={<AddOutlined />} onClick={addGroup} disabled={saving || !name.trim()}>
          Gruppe anlegen
        </Button>
      </Box>

      {groups.length === 0 ? (
        <Typography variant="body2" color="text.secondary">Keine Gruppen vorhanden.</Typography>
      ) : (
        <Stack spacing={1}>
          {groups.map((group) => {
            const members = persons.filter((p) => p.group_id === group.id);
            return (
              <Box key={group.id} sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1.5, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight={600} sx={{ minWidth: 120 }}>{group.name}</Typography>
                <Box sx={{ flex: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {members.length === 0
                    ? <Typography variant="caption" color="text.secondary">Keine Mitglieder</Typography>
                    : members.map((m) => <Chip key={m.id} label={m.name} size="small" />)
                  }
                </Box>
                <IconButton size="small" color="error" onClick={() => deleteGroup(group.id)}>
                  <DeleteOutlined fontSize="small" />
                </IconButton>
              </Box>
            );
          })}
        </Stack>
      )}
    </Paper>
  );
}

function DangerZone({ onReload }: { onReload: () => void }) {
  const [open, setOpen] = useState(false);
  const [resetting, setResetting] = useState(false);

  const reset = async () => {
    setResetting(true);
    await fetch('/api/settings/reset-db', {
      method: 'POST',
      body: new URLSearchParams({ confirm_reset: 'yes' }),
    });
    setResetting(false);
    setOpen(false);
    onReload();
  };

  return (
    <Paper sx={{ p: 3, border: 2, borderColor: 'error.light' }}>
      <Typography variant="h5" color="error" gutterBottom>Gefahrenzone</Typography>
      <Typography variant="body2" sx={{ mb: 2 }}>
        Alle Motor-Einträge und Abholdaten werden gelöscht. Personen und Gruppen bleiben erhalten.
      </Typography>
      <Button variant="outlined" color="error" onClick={() => setOpen(true)}>
        Datenbank zurücksetzen
      </Button>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Datenbank zurücksetzen?</DialogTitle>
        <DialogContent>
          <Typography>Alle Motor-Einträge und Abholdaten werden <strong>unwiderruflich gelöscht</strong>. Personen/Profile bleiben erhalten.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Abbrechen</Button>
          <Button color="error" variant="contained" onClick={reset} disabled={resetting}>
            {resetting ? 'Lösche...' : 'Ja, zurücksetzen'}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

export default function SettingsPage() {
  const { data, loading, error, reload } = usePageData('settings');

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Fehler beim Laden: {error}</Alert>;
  if (!data) return null;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h2">Einstellungen</Typography>
        <Button
          variant="outlined"
          startIcon={<DownloadOutlined />}
          component="a"
          href="/api/export"
        >
          CSV exportieren
        </Button>
      </Box>

      <PersonsSection persons={data.request_persons} groups={data.groups} onReload={reload} />
      <Divider />
      <GroupsSection groups={data.groups} persons={data.request_persons} onReload={reload} />
      <Divider />
      <DangerZone onReload={reload} />
    </Box>
  );
}
