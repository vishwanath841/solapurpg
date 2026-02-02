const supabase = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// Realtime Subscriptions
// We listen to changes in 'appointments' table
const channel = supabase
  .channel('public:appointments')
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'appointments' },
    (payload) => {
      console.log('Change received!', payload);
      handleRealtimeUpdate(payload);
    }
  )
  .subscribe();

function handleRealtimeUpdate(payload) {
    const eventType = payload.eventType;
    const newRecord = payload.new;
    
    // Show notification
    showNotification(`Appointment ${eventType}: ID ${newRecord.id || 'N/A'}`);
    
    // Reload page if on dashboard (simple way to refresh data)
    // In a SPA (React/Vue/Angular), we would update state. 
    // Here, we can reload or use specific DOM manipulation.
    // For "Real-time" feel without reload, we need to manipulate DOM.
    // But since we use server-side rendering for the list, reload is easiest for this scope.
    if (window.location.pathname.includes('dashboard')) {
        setTimeout(() => window.location.reload(), 2000); // Wait for user to read toast
    }
}

function showNotification(message) {
    const area = document.getElementById('notification-area');
    if (!area) {
        const div = document.createElement('div');
        div.id = 'notification-area';
        document.body.appendChild(div);
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerText = message;
    document.getElementById('notification-area').appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

console.log("Supabase Realtime Initialized");
