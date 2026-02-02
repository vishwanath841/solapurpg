from flask import Blueprint, request, jsonify, g
from app.utils import login_required, get_authenticated_client, role_required

appointment_bp = Blueprint('appointment', __name__)

@appointment_bp.route('/book', methods=['POST'])
@login_required
@role_required('patient')
def book_appointment():
    client = get_authenticated_client(g.access_token)
    data = request.json
    
    doctor_id = data.get('doctor_id')
    appointment_date = data.get('appointment_date') # ISO string
    notes = data.get('notes', '')
    
    if not doctor_id or not appointment_date:
        return jsonify({"error": "Missing details"}), 400

    # Conflict validation
    existing = client.table('appointments').select('id').eq('doctor_id', doctor_id).eq('appointment_date', appointment_date).execute()
    
    if existing.data:
        return jsonify({"error": "Slot unavailable"}), 409

    # Book
    new_appointment = {
        "patient_id": g.user.id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "notes": notes,
        "status": "pending"
    }
    
    res = client.table('appointments').insert(new_appointment).execute()
    
    if res.data:
        return jsonify({"message": "Appointment booked", "data": res.data}), 201
    else:
        return jsonify({"error": "Booking failed. Please ensure you are logged in as a patient."}), 400

@appointment_bp.route('/cancel/<uuid:appointment_id>', methods=['POST'])
@login_required
@role_required('patient')
def cancel_appointment(appointment_id):
    client = get_authenticated_client(g.access_token)
    res = client.table('appointments').update({"status": "cancelled"}).eq('id', str(appointment_id)).execute()
    return jsonify(res.data)

@appointment_bp.route('/reschedule/<uuid:appointment_id>', methods=['POST'])
@login_required
@role_required('patient')
def reschedule_appointment(appointment_id):
    client = get_authenticated_client(g.access_token)
    data = request.json
    new_date = data.get('appointment_date')
    
    if not new_date:
         return jsonify({"error": "New date required"}), 400

    # helper: get doctor_id from appointment to check conflict
    appt = client.table('appointments').select('doctor_id').eq('id', str(appointment_id)).single().execute()
    if not appt.data:
        return jsonify({"error": "Appointment not found"}), 404
        
    doctor_id = appt.data['doctor_id']

    # Check conflict
    existing = client.table('appointments').select('id').eq('doctor_id', doctor_id).eq('appointment_date', new_date).execute()
    if existing.data:
        return jsonify({"error": "Slot unavailable"}), 409

    # Update
    res = client.table('appointments').update({
        "appointment_date": new_date,
        "status": "pending" 
    }).eq('id', str(appointment_id)).execute()
    
    return jsonify(res.data)
