import { IconButton, Tooltip } from '@mui/material';
import { LightModeOutlined, DarkModeOutlined } from '@mui/icons-material';
import { useThemeContext } from '../context/ThemeContext';

export default function ThemeToggleButton() {
  const { mode, toggleTheme } = useThemeContext();
  return (
    <Tooltip title={mode === 'light' ? 'Dark Mode aktivieren' : 'Light Mode aktivieren'}>
      <IconButton onClick={toggleTheme} color="inherit" aria-label="Theme wechseln">
        {mode === 'light' ? <DarkModeOutlined /> : <LightModeOutlined />}
      </IconButton>
    </Tooltip>
  );
}
