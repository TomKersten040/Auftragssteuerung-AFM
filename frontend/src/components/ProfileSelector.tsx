import { useState, useEffect } from 'react';
import { Select, MenuItem, FormControl, Box, Typography, Chip } from '@mui/material';
import { PersonOutlined } from '@mui/icons-material';

export default function ProfileSelector() {
  const [persons, setPersons] = useState<string[]>([]);
  const [profile, setProfileState] = useState<string>('');

  useEffect(() => {
    fetch('/api/profile')
      .then((r) => r.json())
      .then((d) => {
        setProfileState(d.profile ?? '');
        setPersons(d.persons ?? []);
      })
      .catch(() => {});
  }, []);

  const handleChange = async (name: string) => {
    setProfileState(name);
    await fetch('/api/profile', {
      method: 'POST',
      body: new URLSearchParams({ profile_name: name }),
    });
    window.location.reload();
  };

  if (persons.length === 0) return null;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      {profile && (
        <Chip
          icon={<PersonOutlined />}
          label={profile}
          size="small"
          sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: 'inherit', '& .MuiChip-icon': { color: 'inherit' } }}
        />
      )}
      <FormControl size="small" sx={{ minWidth: 140 }}>
        <Select
          value={profile}
          onChange={(e) => handleChange(e.target.value)}
          displayEmpty
          sx={{
            color: 'inherit',
            fontSize: '0.8125rem',
            '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
            '& .MuiSelect-icon': { color: 'inherit' },
          }}
          renderValue={(v) => v || 'Profil wählen...'}
        >
          <MenuItem value="" disabled>
            <Typography variant="body2" color="text.secondary">Profil wählen</Typography>
          </MenuItem>
          {persons.map((name) => (
            <MenuItem key={name} value={name}>{name}</MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
