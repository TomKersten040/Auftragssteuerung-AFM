import { useState } from 'react';
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Checkbox, Button, Select, MenuItem, Collapse, IconButton,
  Typography, TextField, FormControl, InputLabel, Stack, Tooltip,
  Divider, alpha,
} from '@mui/material';
import {
  ExpandMoreOutlined, ExpandLessOutlined, EmailOutlined,
  CheckCircleOutlined, PlayArrowOutlined, RadioButtonUncheckedOutlined,
  EditOutlined, AssignmentTurnedInOutlined,
} from '@mui/icons-material';
import type { MotorEntry, Person, Group } from '../types/api';
import { MotorStatusChip, PickupStatusChip } from './StatusChip';

interface MotorTableProps {
  entries: MotorEntry[];
  persons: Person[];
  groups: Group[];
  motorTypes: string[];
  storageLocations: string[];
  currentProfile: string;
  view: string;
  onReload: () => void;
}

function AssignSelect({ persons, groups, value, onChange }: {
  persons: Person[];
  groups: Group[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <Select value={value} onChange={(e) => onChange(e.target.value)} size="small" displayEmpty sx={{ minWidth: 180 }}>
      <MenuItem value=""><em>Nicht zugewiesen</em></MenuItem>
      {groups.map((g) => (
        <MenuItem key={`__group__:${g.name}`} value={`__group__:${g.name}`}>
          Gruppe: {g.name}
        </MenuItem>
      ))}
      {groups.length > 0 && <Divider />}
      {persons.map((p) => (
        <MenuItem key={p.name} value={p.name}>{p.name}</MenuItem>
      ))}
    </Select>
  );
}

function EntryEditor({ entry, persons, groups, motorTypes, storageLocations, view, onReload, onClose }: {
  entry: MotorEntry;
  persons: Person[];
  groups: Group[];
  motorTypes: string[];
  storageLocations: string[];
  view: string;
  onReload: () => void;
  onClose: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    motor_type: entry.motor_type,
    stator_number: entry.stator_number,
    status: entry.status,
    entry_date: entry.entry_date,
    entry_time: entry.entry_time,
    storage_location: entry.storage_location,
    remarks: entry.remarks ?? '',
    pickup_assigned_to: entry.pickup_assigned_group
      ? `__group__:${entry.pickup_assigned_group}`
      : (entry.pickup_assigned_to ?? ''),
    pickup_request_comment: entry.pickup_request_comment ?? '',
    picked_up: entry.picked_up === 1,
    pickup_done_by: entry.pickup_done_by ?? '',
    pickup_done_date: entry.pickup_done_date ?? '',
    pickup_done_time: entry.pickup_done_time ?? '',
  });

  const set = (key: string, val: string | boolean) =>
    setForm((prev) => ({ ...prev, [key]: val }));

  const save = async () => {
    setSaving(true);
    const body = new URLSearchParams({ next: `/${view}` });
    Object.entries(form).forEach(([k, v]) => body.append(k, v === true ? '1' : v === false ? '0' : String(v)));
    await fetch(`/api/entry/${entry.id}/update`, { method: 'POST', body });
    setSaving(false);
    onReload();
    onClose();
  };

  return (
    <Box sx={{ p: 3, bgcolor: 'background.paper', borderTop: 1, borderColor: 'divider' }}>
      <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 2 }}>
        Eintrag bearbeiten
      </Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' }, gap: 2 }}>
        <FormControl size="small">
          <InputLabel>Motor</InputLabel>
          <Select value={form.motor_type} label="Motor" onChange={(e) => set('motor_type', e.target.value)}>
            {motorTypes.map((m) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
          </Select>
        </FormControl>
        <TextField size="small" label="Statornummer" value={form.stator_number} onChange={(e) => set('stator_number', e.target.value)} />
        <FormControl size="small">
          <InputLabel>Lagerort</InputLabel>
          <Select value={form.storage_location} label="Lagerort" onChange={(e) => set('storage_location', e.target.value)}>
            {storageLocations.map((l) => <MenuItem key={l} value={l}>{l}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl size="small">
          <InputLabel>Status</InputLabel>
          <Select value={form.status} label="Status" onChange={(e) => set('status', e.target.value)}>
            {['iO', 'niO', 'wiO'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
          </Select>
        </FormControl>
        <TextField size="small" label="Datum" type="date" value={form.entry_date} onChange={(e) => set('entry_date', e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" label="Uhrzeit" type="time" value={form.entry_time} onChange={(e) => set('entry_time', e.target.value)} InputLabelProps={{ shrink: true }} />
        <FormControl size="small">
          <InputLabel>Zuweisen an</InputLabel>
          <Select value={form.pickup_assigned_to} label="Zuweisen an" onChange={(e) => set('pickup_assigned_to', e.target.value)} displayEmpty>
            <MenuItem value="">Nicht zugewiesen</MenuItem>
            {groups.map((g) => (
              <MenuItem key={`__group__:${g.name}`} value={`__group__:${g.name}`}>Gruppe: {g.name}</MenuItem>
            ))}
            {groups.length > 0 && <Divider />}
            {persons.map((p) => (
              <MenuItem key={p.name} value={p.name}>{p.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <Box />
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mt: 2 }}>
        <TextField size="small" label="Anmerkungen" multiline rows={2} value={form.remarks} onChange={(e) => set('remarks', e.target.value)} />
        <TextField size="small" label="Kommentar zur Abholung" multiline rows={2} value={form.pickup_request_comment} onChange={(e) => set('pickup_request_comment', e.target.value)} />
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr 1fr 1fr' }, gap: 2, alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Checkbox checked={form.picked_up} onChange={(e) => set('picked_up', e.target.checked)} size="small" />
          <Typography variant="body2">Abgeholt</Typography>
        </Box>
        <TextField size="small" label="Abgeholt durch" value={form.pickup_done_by} onChange={(e) => set('pickup_done_by', e.target.value)} />
        <TextField size="small" label="Abhol-Datum" type="date" value={form.pickup_done_date} onChange={(e) => set('pickup_done_date', e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" label="Abhol-Uhrzeit" type="time" value={form.pickup_done_time} onChange={(e) => set('pickup_done_time', e.target.value)} InputLabelProps={{ shrink: true }} />
      </Box>

      <Stack direction="row" spacing={1.5} sx={{ mt: 3 }}>
        <Button variant="contained" onClick={save} disabled={saving} sx={{ px: 3 }}>
          {saving ? 'Speichern...' : 'Speichern'}
        </Button>
        <Button variant="outlined" onClick={onClose}>Abbrechen</Button>
      </Stack>
    </Box>
  );
}

export default function MotorTable({
  entries, persons, groups, motorTypes, storageLocations, currentProfile, view, onReload,
}: MotorTableProps) {
  const [selected, setSelected] = useState<number[]>([]);
  const [bulkAssign, setBulkAssign] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const toggleSelect = (id: number) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);

  const toggleAll = () =>
    setSelected(selected.length === entries.length ? [] : entries.map((e) => e.id));

  const bulkAction = async (action: 'picked_up' | 'assign') => {
    if (!selected.length) return;
    const body = new URLSearchParams({ action, next: `/${view}` });
    if (action === 'assign') {
      if (!bulkAssign) return;
      body.append('assign_to', bulkAssign);
    }
    selected.forEach((id) => body.append('entry_ids', String(id)));
    await fetch('/api/entries/bulk', { method: 'POST', body });
    setSelected([]);
    onReload();
  };

  const startPickup = async (id: number) => {
    await fetch(`/api/entry/${id}/start`, {
      method: 'POST',
      body: new URLSearchParams({ next: `/${view}` }),
    });
    onReload();
  };

  const togglePickedUp = async (id: number) => {
    await fetch(`/api/entry/${id}/toggle-picked-up`, {
      method: 'POST',
      body: new URLSearchParams({ next: `/${view}` }),
    });
    onReload();
  };

  if (entries.length === 0) {
    return (
      <Box sx={{ py: 8, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">Keine passenden Einträge vorhanden.</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {selected.length > 0 && (
        <Paper
          elevation={0}
          sx={(theme) => ({
            p: 2,
            mb: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            flexWrap: 'wrap',
            bgcolor: alpha(theme.palette.primary.main, 0.06),
            border: 1,
            borderColor: 'primary.main',
            borderRadius: 2,
          })}
        >
          <Typography variant="body2" color="primary.main" fontWeight={700}>
            {selected.length} ausgewählt
          </Typography>
          <Button
            variant="contained"
            size="small"
            color="success"
            startIcon={<AssignmentTurnedInOutlined />}
            onClick={() => bulkAction('picked_up')}
          >
            Als abgeholt markieren
          </Button>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <AssignSelect persons={persons} groups={groups} value={bulkAssign} onChange={setBulkAssign} />
            <Button variant="contained" size="small" onClick={() => bulkAction('assign')}>
              Zuweisen
            </Button>
          </Box>
        </Paper>
      )}

      <TableContainer>
        <Table size="small" sx={{ '& .MuiTableCell-root': { py: 1.25 } }}>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  size="small"
                  indeterminate={selected.length > 0 && selected.length < entries.length}
                  checked={selected.length === entries.length && entries.length > 0}
                  onChange={toggleAll}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Erfasst</TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Motor</TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Statornr.</TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Lagerort</TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Abholstatus</TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Info</TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', color: 'text.secondary' }}>Aktionen</TableCell>
              <TableCell sx={{ width: 40 }} />
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.map((entry) => {
              const isExpanded = expandedId === entry.id;
              const assignedTo = entry.pickup_assigned_group
                ? `Gruppe: ${entry.pickup_assigned_group}`
                : entry.pickup_assigned_to || '';

              return [
                <TableRow
                  key={entry.id}
                  hover
                  selected={selected.includes(entry.id)}
                  sx={{ '& > *': { borderBottom: isExpanded ? 0 : undefined } }}
                >
                  <TableCell padding="checkbox">
                    <Checkbox size="small" checked={selected.includes(entry.id)} onChange={() => toggleSelect(entry.id)} />
                  </TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>
                    <Typography variant="body2" fontWeight={500}>{entry.entry_date}</Typography>
                    <Typography variant="caption" color="text.secondary">{entry.entry_time}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{entry.motor_type}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight={700}>{entry.stator_number}</Typography>
                  </TableCell>
                  <TableCell><MotorStatusChip status={entry.status} /></TableCell>
                  <TableCell>
                    <Typography variant="body2">{entry.storage_location}</Typography>
                  </TableCell>
                  <TableCell><PickupStatusChip status={entry.pickup_status} /></TableCell>
                  <TableCell>
                    {assignedTo && <Typography variant="caption" color="text.secondary">{assignedTo}</Typography>}
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5}>
                      {!entry.picked_up && currentProfile && entry.pickup_assigned_to === currentProfile && !entry.pickup_started_by && (
                        <Tooltip title="Bearbeitung übernehmen">
                          <IconButton size="small" color="warning" onClick={() => startPickup(entry.id)} sx={{ border: 1, borderColor: 'divider' }}>
                            <PlayArrowOutlined fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {entry.pickup_assigned_email && (
                        <Tooltip title="E-Mail öffnen">
                          <IconButton size="small" component="a" href={entry.mailto_url} sx={{ border: 1, borderColor: 'divider' }}>
                            <EmailOutlined fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title={entry.picked_up ? 'Bereits abgeholt' : 'Als abgeholt markieren'}>
                        <IconButton
                          size="small"
                          color={entry.picked_up ? 'success' : 'default'}
                          onClick={() => !entry.picked_up && togglePickedUp(entry.id)}
                          sx={{ border: 1, borderColor: 'divider' }}
                        >
                          {entry.picked_up ? <CheckCircleOutlined fontSize="small" /> : <RadioButtonUncheckedOutlined fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                  <TableCell padding="checkbox">
                    <IconButton size="small" onClick={() => setExpandedId(isExpanded ? null : entry.id)}>
                      {isExpanded ? <ExpandLessOutlined /> : <EditOutlined fontSize="small" />}
                    </IconButton>
                  </TableCell>
                </TableRow>,
                <TableRow key={`${entry.id}-detail`}>
                  <TableCell colSpan={10} sx={{ p: 0, border: isExpanded ? undefined : 0 }}>
                    <Collapse in={isExpanded} unmountOnExit>
                      <EntryEditor
                        entry={entry}
                        persons={persons}
                        groups={groups}
                        motorTypes={motorTypes}
                        storageLocations={storageLocations}
                        view={view}
                        onReload={onReload}
                        onClose={() => setExpandedId(null)}
                      />
                    </Collapse>
                  </TableCell>
                </TableRow>,
              ];
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
