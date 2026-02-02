from flask import Blueprint, render_template, jsonify, g, request
from app.utils import login_required, get_authenticated_client, role_required

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
@role_required('patient')
def dashboard():
    client = get_authenticated_client(g.access_token)
    
    # 1. Fetch upcoming appointments (pending/confirmed)
    appointments = client.table('appointments').select('*, doctors(specialization, profiles(full_name))').eq('patient_id', g.user.id).order('appointment_date').execute()
    
    # 2. Stats Calculation
    # Fetch all completed appointments for spending
    completed = client.table('appointments').select('*, doctors(consultation_fee)').eq('patient_id', g.user.id).eq('status', 'completed').execute()
    total_spent = sum([a['doctors']['consultation_fee'] or 0 for a in completed.data])
    
    # Fetch total prescriptions
    all_appts = client.table('appointments').select('id').eq('patient_id', g.user.id).execute()
    a_ids = [x['id'] for x in all_appts.data]
    rx_count = 0
    if a_ids:
        rx_res = client.table('prescriptions').select('id', count='exact').in_('appointment_id', a_ids).execute()
        rx_count = rx_res.count if rx_res.count is not None else len(rx_res.data)

    return render_template('patient_dashboard.html', 
                           appointments=appointments.data, 
                           user=g.user,
                           total_spent=total_spent,
                           prescriptions_count=rx_count)

@patient_bp.route('/doctors')
@login_required
@role_required('patient')
def view_doctors():
    client = get_authenticated_client(g.access_token)
    
    # Filter out self if logged in as doctor
    doctors = client.table('doctors').select('*, profiles(full_name)').neq('id', g.user.id).execute()
    return render_template('doctors_list.html', doctors=doctors.data)

@patient_bp.route('/appointments/history')
@login_required
@role_required('patient')
def appointment_history():
    client = get_authenticated_client(g.access_token)
    # Fetch all appointments
    history = client.table('appointments').select('*').eq('patient_id', g.user.id).execute()
    return jsonify(history.data)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def profile():
    client = get_authenticated_client(g.access_token)
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        medical_history = request.form.get('medical_history')
        # Check if profile exists, if not insert (upsert)
        data = {
           "id": g.user.id,
           "full_name": full_name,
           "medical_history": medical_history
        }
        client.table('profiles').upsert(data).execute()
        return render_template('patient_profile.html', user=g.user, profile=data, message="Profile updated")

    # GET
    response = client.table('profiles').select('*').eq('id', g.user.id).limit(1).execute()
    profile_data = response.data[0] if response.data else {}
    # If no profile yet, pass empty dict
    return render_template('patient_profile.html', user=g.user, profile=profile_data)

@patient_bp.route('/prescriptions')
@login_required
@role_required('patient')
def prescriptions():
    client = get_authenticated_client(g.access_token)
    data = client.table('prescriptions').select('*, appointments(appointment_date, doctors(profiles(full_name)))').execute()
    return render_template('patient_prescriptions.html', prescriptions=data.data)

@patient_bp.route('/billing')
@login_required
@role_required('patient')
def billing():
    client = get_authenticated_client(g.access_token)
    
    appointments = client.table('appointments').select(
        '*, doctors(consultation_fee, profiles(full_name))'
    ).eq('status', 'completed').eq('patient_id', g.user.id).execute()
    
    total_bill = 0
    billing_items = []
    
    for appt in appointments.data:
        fee = appt['doctors']['consultation_fee'] or 0
        total_bill += fee
        billing_items.append({
            "date": appt['appointment_date'],
            "doctor": appt['doctors']['profiles']['full_name'],
            "fee": fee
        })
        
    return render_template('patient_billing.html', items=billing_items, total=total_bill)
