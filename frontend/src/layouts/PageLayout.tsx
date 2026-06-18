import { Box, Tabs, Tab, useMediaQuery, useTheme } from '@mui/material';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { MBAppBar, MBFooter } from '@mercedes-benz/mbui-comps';
import ThemeToggleButton from '../components/ThemeToggleButton';
import ProfileSelector from '../components/ProfileSelector';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Meine Abholungen', path: '/mine' },
  { label: 'Angefordert', path: '/requested' },
  { label: 'Abgeschlossen', path: '/completed' },
  { label: 'Einstellungen', path: '/settings' },
];

export default function PageLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const currentTab = location.hash.replace('#', '') || '/dashboard';

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <MBAppBar
        position="static"
        leftContent={
          <Tabs
            value={currentTab}
            textColor="inherit"
            TabIndicatorProps={{ sx: { bgcolor: 'common.white', height: 3 } }}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              minHeight: 48,
              '& .MuiTab-root': {
                minHeight: 48,
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '0.875rem',
                color: 'rgba(255,255,255,0.7)',
                '&.Mui-selected': { color: 'common.white' },
              },
            }}
          >
            {NAV_ITEMS.map((item) => (
              <Tab
                key={item.path}
                label={item.label}
                value={item.path}
                onClick={() => navigate(item.path)}
              />
            ))}
          </Tabs>
        }
        rightContent={
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 1.5 }}>
            {!isMobile && <ProfileSelector />}
            <ThemeToggleButton />
          </Box>
        }
        logoOnClick={() => navigate('/dashboard')}
      />

      {isMobile && (
        <Box sx={{ px: 2, py: 1.5, bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
          <ProfileSelector />
        </Box>
      )}

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          px: { xs: 2, sm: 3, md: 4 },
          py: 3,
          bgcolor: 'background.default',
          maxWidth: 1440,
          width: '100%',
          mx: 'auto',
        }}
      >
        <Outlet />
      </Box>

      <MBFooter
        privacyProtectionInfoLink="#"
        legalNoticeInfoLink="#"
        providerInfoLink="#"
        lang="de"
      />
    </Box>
  );
}
