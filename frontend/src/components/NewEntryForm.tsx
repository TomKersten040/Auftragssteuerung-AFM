import { useState } from 'react';
import {
  Box, Button, TextField, FormControl, InputLabel, Select, MenuItem,
  Paper, Typography, IconButton, Stack, Divider,
} from '@mui/material';
import { AddOutlined, DeleteOutlined } from '@mui/icons-material';
import type { Person, Group } from '../types/api';

interface MotorRow {
  motor_type: string;
  stator_number: string;
  status: string;
}

interface Props {
  motorTypes: string[];
  storageLocations: string[];
  persons: Person[];
  groups: Group[];
  defaultDate: string;
  defaultTime: string;
  onSaved: () => void;
}

export default function NewEntryForm({ motorTypes, storageLocations, persons, groups, defaultDate, defaultTime, onSaved }: Props) {
  const [saving, setSaving] = useState(false);
  const [entryDate, setEntryDate] = useState(defaultDate);
  const [entryTime, setEntryTime] = useState(defaultTime);
  const [storageLocation, setStorageLocation] = useState(storageLocations[0] ?? '');
  const [remarks, setRemarks] = useState('');
  const [pickupComment, setPickupComment] = useState('');
  const [pickupAssigned, setPickupAssigned] = useState('');
  const [motors, setMotors] = useState<MotorRow[]>([
    { motor_type: motorTypes[0] ?? '', stator_number: '', status: 'iO' },
  ]);

  const addMotor = () =>
    setMotors((prev) => [...prev, { motor_type: motorTypes[0] ?? '', stator_number: '', status: 'iO' }]);

  const removeMotor = (i: number) =>
    setMotors((prev) => prev.filter((_, idx) => idx !== i));

  const updateMotor = (i: number, key: keyof MotorRow, val: string) =>
    setMotors((prev) => prev.map((m, idx) => idx === i ? { ...m, [key]: val } : m));

  const save = async () => {
    setSaving(true);
    const body = new URLSearchParams({
      entry_date: entryDate,
      entry_time: entryTime,
      storage_location: storageLocation,
      remarks,
      pickup_request_comment: pickupComment,
      pickup_assigned_to: pickupAssigned,
    });
    motors.forEach((m) => {
      body.append('motor_type', m.motor_type);
      body.append('stator_number', m.stator_number);
      body.append('status', m.status);
    });
    await fetch('/api/save', { method: 'POST', body });
    setSaving(false);
    setMotors([{ motor_type: motorTypes[0] ?? '', stator_number: '', status: 'iO' }]);
    setRemarks('');
    setPickupComment('');
    setPickupAssigned('');
    onSaved();
  };

  return (
    <Paper elevation={0} sx={{ p: 3, border: 1, borderColor: 'divider', borderRadius: 2 }}>
      <Typography variant="h5" gutterBottom>Neuen Motor erfassen</Typography>
      <Divider sx={{ mb: 2.5 }} />

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, gap: 2, mb: 3 }}>
        <TextField
          size="small" label="Datum" type="date" value={entryDate}
          onChange={(e) => setEntryDate(e.target.value)} InputLabelProps={{ shrink: true }}
        />
        <TextField
          size="small" label="Uhrzeit" type="time" value={entryTime}
          onChange={(e) => setEntryTime(e.target.value)} InputLabelProps={{ shrink: true }}
        />
        <FormControl size="small">
          <InputLabel>Lagerort</InputLabel>
          <Select value={storageLocation} label="Lagerort" onChange={(e) => setStorageLocation(e.target.value)}>
            {storageLocations.map((l) => <MenuItem key={l} value={l}>{l}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl size="small">
          <InputLabel>Zuweisen an</InputLabel>
          <Select value={pickupAssigned} label="Zuweisen an" onChange={(e) => setPickupAssigned(e.target.value)} displayEmpty>
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
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mb: 3 }}>
        <TextField size="small" label="Anmerkungen" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
        <TextField size="small" label="Kommentar zur Abholung" value={pickupComment} onChange={(e) => setPickupComment(e.target.value)} />
      </Box>

      <Divider sx={{ mb: 2 }} />
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.75rem' }}>
        Motoren
      </Typography>

      <Stack spacing={1.5}>
        {motors.map((motor, i) => (
          <Box
            key={i}
            sx={{
              display: 'flex',
              gap: 1.5,
              alignItems: 'center',
              flexWrap: 'wrap',
              p: 1.5,
              bgcolor: 'action.hover',
              borderRadius: 1.5,
            }}
          >
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Motor</InputLabel>
              <Select value={motor.motor_type} label="Motor" onChange={(e) => updateMotor(i, 'motor_type', e.target.value)}>
                {motorTypes.map((m) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
              </Select>
            </FormControl>
            <TextField
              size="small" label="Statornummer" value={motor.stator_number} sx={{ flex: 1, minWidth: 140 }}
              onChange={(e) => updateMotor(i, 'stator_number', e.target.value)}
            />
            <FormControl size="small" sx={{ minWidth: 90 }}>
              <InputLabel>Status</InputLabel>
              <Select value={motor.status} label="Status" onChange={(e) => updateMotor(i, 'status', e.target.value)}>
                {['iO', 'niO', 'wiO'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
            {motors.length > 1 && (
              <IconButton size="small" color="error" onClick={() => removeMotor(i)} sx={{ border: 1, borderColor: 'divider' }}>
                <DeleteOutlined fontSize="small" />
              </IconButton>
            )}
          </Box>
        ))}
      </Stack>

      <Stack direction="row" spacing={1.5} sx={{ mt: 3 }}>
        <Button variant="outlined" size="small" startIcon={<AddOutlined />} onClick={addMotor}>
          Motor hinzufügen
        </Button>
        <Button variant="contained" onClick={save} disabled={saving} sx={{ px: 4 }}>
          {saving ? 'Speichern...' : 'Speichern'}
        </Button>
      </Stack>
    </Paper>
  );
}
