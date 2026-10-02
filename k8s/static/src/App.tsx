import { useEffect, useState } from 'react'
import {
  AppBar, Box, Checkbox, Chip, CircularProgress, Container,
  List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  Alert, Toolbar, Typography, LinearProgress,
} from '@mui/material'

interface Step {
  step: number
  ref: string
  phase: number
  title: string
  done: boolean
}

export default function App() {
  const [steps, setSteps] = useState<Step[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/steps')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setSteps)
      .catch((e) => setError(String(e)))
  }, [])

  async function toggle(step: Step) {
    const done = !step.done
    setSteps((s) => s?.map((x) => (x.step === step.step ? { ...x, done } : x)) ?? s)
    try {
      await fetch('/api/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step: step.step, done }),
      })
    } catch {
      setSteps((s) => s?.map((x) => (x.step === step.step ? { ...x, done: !done } : x)) ?? s)
      setError('Failed to save progress — is the app tier reachable?')
    }
  }

  const phases = [...new Set(steps?.map((s) => s.phase) ?? [])]
  const done = steps?.filter((s) => s.done).length ?? 0

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>k8s-tutorial</Typography>
          {steps && <Chip label={`${done}/${steps.length} done`} color={done === steps.length ? 'success' : 'default'} />}
        </Toolbar>
        {steps && <LinearProgress variant="determinate" value={(done / steps.length) * 100} />}
      </AppBar>

      <Container maxWidth="sm" sx={{ py: 4 }}>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {!steps && !error && <CircularProgress />}

        {phases.map((phase) => (
          <Box key={phase}>
            <Typography variant="overline" color="text.secondary">Phase {phase}</Typography>
            <List>
              {steps!.filter((s) => s.phase === phase).map((s) => (
                <ListItem key={s.step} disablePadding>
                  <ListItemButton onClick={() => toggle(s)}>
                    <ListItemIcon>
                      <Checkbox edge="start" checked={s.done} tabIndex={-1} />
                    </ListItemIcon>
                    <ListItemText
                      primary={s.title}
                      secondary={s.ref}
                      sx={s.done ? { textDecoration: 'line-through', opacity: 0.6 } : undefined}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        ))}
      </Container>
    </Box>
  )
}
