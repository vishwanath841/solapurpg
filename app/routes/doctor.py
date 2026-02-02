from flask import Blueprint, render_template, g, request, jsonify
from app.utils import login_required, get_authenticated_client, role_required
import datetime

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@login_required
@role_required('doctor')
def dashboard():
    client = get_authenticated_client(g.access_token)
    
    # Fetch assigned appointments
    appointments = client.table('appointments').select('*, profiles(full_name, medical_history)').eq('doctor_id', g.user.id).order('appointment_date', desc=True).execute()
    
    # Fetch Doctor Fee for Calculations
    doc_res = client.table('doctors').select('consultation_fee').eq('id', g.user.id).limit(1).execute()
    fee = doc_res.data[0]['consultation_fee'] if doc_res.data else 0
    
    # Calculate Realtime Analytics
    total_earnings = 0
    monthly_income = [0] * 12

    for appt in appointments.data:
        if appt['status'] == 'completed':
            total_earnings += fee
            # Parse Date
            try:
                dt_str = appt['appointment_date'].replace('Z', '+00:00')
                dt = datetime.datetime.fromisoformat(dt_str)
                monthly_income[dt.month - 1] += fee
            except:
                pass

    return render_template('doctor_dashboard.html', 
                           appointments=appointments.data, 
                           user=g.user,
                           earnings=total_earnings,
                           monthly_income=monthly_income)

@doctor_bp.route('/patients')
@login_required
@role_required('doctor')
def patients():
    client = get_authenticated_client(g.access_token)
    # Get unique patients from appointments
    # Supabase doesn't support 'distinct' easy via API sometimes, so we process in python
    appts = client.table('appointments').select('*, profiles(full_name, medical_history)').eq('doctor_id', g.user.id).execute()
    
    patients = {}
    for a in appts.data:
        pid = a['patient_id']
        if pid not in patients:
            patients[pid] = {
                'id': pid,
                'name': a['profiles']['full_name'],
                'history': a['profiles']['medical_history'],
                'last_visit': a['appointment_date']
            }
        else:
            # Update last visit if newer
            if a['appointment_date'] > patients[pid]['last_visit']:
                patients[pid]['last_visit'] = a['appointment_date']
    
    return render_template('doctor_patients.html', patients=list(patients.values()))

@doctor_bp.route('/patients/<uuid:patient_id>')
@login_required
@role_required('doctor')
def patient_details(patient_id):
    client = get_authenticated_client(g.access_token)
    
    # 1. Fetch Basic Profile
    profile = client.table('profiles').select('*').eq('id', str(patient_id)).single().execute()
    
    # 2. Fetch Appointment History with this Doctor
    appointments = client.table('appointments').select('*').eq('doctor_id', g.user.id).eq('patient_id', str(patient_id)).order('appointment_date', desc=True).execute()
    
    # 3. Fetch Prescriptions (linked to appointments with this doctor)
    # We can get prescriptions where appointment.patient_id = patient_id and appointment.doctor_id = current_doctor
    # Easier: Fetch all prescriptions for appointments in step 2
    appt_ids = [a['id'] for a in appointments.data]
    prescriptions = []
    if appt_ids:
        res = client.table('prescriptions').select('*').in_('appointment_id', appt_ids).execute()
        prescriptions = res.data

    return render_template('doctor_patient_details.html', 
                           patient=profile.data, 
                           appointments=appointments.data, 
                           prescriptions=prescriptions)

@doctor_bp.route('/transactions')
@login_required
@role_required('doctor')
def transactions():
    client = get_authenticated_client(g.access_token)
    doc_res = client.table('doctors').select('consultation_fee').eq('id', g.user.id).limit(1).execute()
    fee = doc_res.data[0]['consultation_fee'] if doc_res.data else 0

    # Get completed appointments
    appts = client.table('appointments').select('*, profiles(full_name)').eq('doctor_id', g.user.id).eq('status', 'completed').order('appointment_date', desc=True).execute()
    
    return render_template('doctor_transactions.html', transactions=appts.data, fee=fee)

@doctor_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
@role_required('doctor')
def schedule():
    client = get_authenticated_client(g.access_token)
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        specialization = request.form.get('specialization')
        start = request.form.get('start_time') or None
        end = request.form.get('end_time') or None
        fees_str = request.form.get('fee')
        fee = int(fees_str) if fees_str else None
        days = request.form.getlist('days')
        
        data = {
            "id": g.user.id,
            "specialization": specialization,
            "consultation_fee": fee,
            "available_days": days,
            "start_time": start,
            "end_time": end
        }
        
        
        # 1. Ensure Profile Exists (Fix for FK Error)
        client.table('profiles').upsert({
            "id": g.user.id,
            "full_name": full_name,
            "role": "doctor" 
        }).execute()

        # 2. Upsert Doctor
        client.table('doctors').upsert(data).execute()
        return render_template('doctor_schedule.html', message="Schedule Updated!", doctor=data)

    # GET
    response = client.table('doctors').select('*, profiles(full_name)').eq('id', g.user.id).limit(1).execute()
    doctor_data = response.data[0] if response.data else {}
    return render_template('doctor_schedule.html', doctor=doctor_data)

@doctor_bp.route('/appointment/<uuid:appointment_id>/status', methods=['POST'])
@login_required
@role_required('doctor')
def update_status(appointment_id):
    client = get_authenticated_client(g.access_token)
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['confirmed', 'cancelled']:
        return jsonify({"error": "Invalid status"}), 400

    # RLS ensures doctor can only update assigned appointments
    try:
        res = client.table('appointments').update({"status": new_status}).eq('id', str(appointment_id)).execute()
        if hasattr(res, 'error') and res.error:
            print(f"Update Error: {res.error}")
            return jsonify({"error": str(res.error)}), 400
        print(f"Update Success: {res.data}")
        return jsonify(res.data)
    except Exception as e:
        print(f"Update Exception: {e}")
        return jsonify({"error": str(e)}), 500

@doctor_bp.route('/prescribe/<uuid:appointment_id>', methods=['POST'])
@login_required
@role_required('doctor')
def create_prescription(appointment_id):
    client = get_authenticated_client(g.access_token)
    data = request.json
    
    diagnosis = data.get('diagnosis')
    medicines = data.get('medicines') # List of objects
    
    try:
        # 1. Update Appointment to Completed
        client.table('appointments').update({"status": "completed"}).eq('id', str(appointment_id)).execute()
        
        # 2. Insert Prescription
        prescription_data = {
            "appointment_id": str(appointment_id),
            "diagnosis": diagnosis,
            "medicines": medicines
        }
        
        res = client.table('prescriptions').insert(prescription_data).execute()
        return jsonify(res.data)
    except Exception as e:
        print(f"Prescription Error: {e}")
        return jsonify({"error": str(e)}), 500
