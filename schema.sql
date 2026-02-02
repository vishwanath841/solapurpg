-- Create a specific table for user profiles to store role and metadata
-- This triggers on auth.users creation usually, but we will handle it via API or Trigger
-- For simplicity in this script, we assume a trigger approach or manual handling.

create table public.profiles (
  id uuid references auth.users not null primary key,
  full_name text,
  role text check (role in ('patient', 'doctor', 'admin')) default 'patient',
  medical_history text, -- For patients
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Turn on RLS
alter table public.profiles enable row level security;

-- Policies for profiles
create policy "Public profiles are viewable by everyone"
  on public.profiles for select
  using ( true );

create policy "Users can insert their own profile"
  on public.profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile"
  on public.profiles for update
  using ( auth.uid() = id );

-- Doctors Table (Extension of profiles for doctor specific details)
create table public.doctors (
  id uuid references public.profiles(id) not null primary key,
  specialization text not null,
  available_days text[], -- e.g. ['Monday', 'Tuesday']
  start_time time,
  end_time time,
  consultation_fee numeric,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.doctors enable row level security;

create policy "Doctors are viewable by everyone"
  on public.doctors for select
  using ( true );

create policy "Doctors can update their own info"
  on public.doctors for update
  using ( auth.uid() = id );

create policy "Doctors can insert their own info"
  on public.doctors for insert
  with check ( auth.uid() = id );

-- Appointments
create table public.appointments (
  id uuid default uuid_generate_v4() primary key,
  patient_id uuid references public.profiles(id) not null,
  doctor_id uuid references public.doctors(id) not null,
  appointment_date timestamp with time zone not null,
  status text check (status in ('pending', 'confirmed', 'cancelled', 'completed')) default 'pending',
  notes text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.appointments enable row level security;

create policy "Patients can view own appointments"
  on public.appointments for select
  using ( auth.uid() = patient_id );

create policy "Doctors can view assigned appointments"
  on public.appointments for select
  using ( auth.uid() = doctor_id );

create policy "Patients can create appointments"
  on public.appointments for insert
  with check ( auth.uid() = patient_id );

create policy "Doctors can update status of assigned appointments"
  on public.appointments for update
  using ( auth.uid() = doctor_id );

create policy "Patients can cancel (update) own appointments"
  on public.appointments for update
  using ( auth.uid() = patient_id );

-- Prescriptions
create table public.prescriptions (
  id uuid default uuid_generate_v4() primary key,
  appointment_id uuid references public.appointments(id) not null,
  medicines jsonb, -- Array of objects: {name, dosage, frequency}
  diagnosis text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.prescriptions enable row level security;

create policy "Patients can view their prescriptions"
  on public.prescriptions for select
  using ( exists (
    select 1 from public.appointments
    where appointments.id = prescriptions.appointment_id
    and appointments.patient_id = auth.uid()
  ));

create policy "Doctors can create prescriptions"
  on public.prescriptions for insert
  with check ( exists (
    select 1 from public.appointments
    where appointments.id = prescriptions.appointment_id
    and appointments.doctor_id = auth.uid()
  ));

-- Realtime publication
-- Supabase Realtime is enabled by adding tables to the publication
-- This typically is done in the UI or via SQL:
alter publication supabase_realtime add table public.appointments;
alter publication supabase_realtime add table public.doctors;
