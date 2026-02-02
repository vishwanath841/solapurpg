// Initialize Supabase correctly without variable shadowing
const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// If we have an auth token, set it in the client
if (typeof AUTH_TOKEN !== 'undefined' && AUTH_TOKEN) {
  // In v2, we set the token manually in headers or use setSession
  sb.auth.setSession({
    access_token: AUTH_TOKEN,
    refresh_token: '' // Not strictly needed for a single session view
  });
}

// Realtime Subscriptions
if (typeof USER_ID !== 'undefined' && USER_ID) {
  const channel = sb
    .channel('db-changes')
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'appointments'
      },
      (payload) => {
        const newRecord = payload.new;

        // If I am a doctor, and this new appointment is for ME
        if (typeof USER_ROLE !== 'undefined' && USER_ROLE === 'doctor') {
          if (newRecord.doctor_id === USER_ID) {
            showNotification("🔔 New Appointment Request Received!");
            refreshDashboard();
          }
        }

        // If I am a patient, and my appointment status changed
        // (This would need a 'UPDATE' listener, let's keep it simple for now as requested)
      }
    )
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'appointments'
      },
      (payload) => {
        const oldRecord = payload.old;
        const newRecord = payload.new;

        if (typeof USER_ROLE !== 'undefined' && USER_ROLE === 'patient') {
          if (newRecord.patient_id === USER_ID && newRecord.status !== oldRecord.status) {
            showNotification(`📅 Appointment status updated to: ${newRecord.status}`);
            refreshDashboard();
          }
        }
      }
    )
    .subscribe();
}

function refreshDashboard() {
  if (window.location.pathname.includes('dashboard')) {
    // Subtle refresh or prompt
    console.log("Data changed, refreshing in 3 seconds...");
    setTimeout(() => window.location.reload(), 3000);
  }
}

function showNotification(message) {
  let area = document.getElementById('notification-area');
  if (!area) {
    area = document.createElement('div');
    area.id = 'notification-area';
    document.body.appendChild(area);
  }

  const toast = document.createElement('div');
  toast.className = 'toast animate-in';
  toast.innerHTML = `<i class="fa-solid fa-circle-info"></i> <span>${message}</span>`;
  area.appendChild(toast);

  // Play a subtle sound if possible or just visual

  setTimeout(() => {
    toast.classList.add('animate-out');
    setTimeout(() => toast.remove(), 500);
  }, 5000);
}

console.log("Supabase Realtime Initialized for", USER_ROLE);
