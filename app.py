import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'garahe_pickleball_secret_key'

# File upload setup
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Admin password setup (Change this to your preferred secure admin code)
ADMIN_PASSWORD = 'garahe_admin_2026'

# In-memory storage for bookings
reservations = []

# Operating hours in 12-Hour format (4:00 PM to 12:00 AM)
SLOTS = [
    "4:00 PM - 5:00 PM",
    "5:00 PM - 6:00 PM",
    "6:00 PM - 7:00 PM",
    "7:00 PM - 8:00 PM",
    "8:00 PM - 9:00 PM",
    "9:00 PM - 10:00 PM",
    "10:00 PM - 11:00 PM",
    "11:00 PM - 12:00 AM"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_rate(date_str):
    """Returns 350 for Fri-Sun, 300 for Mon-Thu"""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    if dt.weekday() >= 4:
        return 350
    return 300

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Garahe Pickleball Court Reservation</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        beige: '#F5F2EB',
                        darkbeige: '#E8E2D5',
                        courtblue: '#1E3A8A',
                        accentsyellow: '#EAB308',
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-beige text-gray-800 font-sans min-h-screen flex flex-col justify-between">

    <!-- Header (Admin link removed for public view) -->
    <header class="bg-courtblue text-white shadow-md">
        <div class="max-w-5xl mx-auto px-6 py-4 flex flex-col sm:flex-row justify-between items-center">
            <div>
                <h1 class="text-2xl font-black tracking-wide text-accentsyellow">GARAHE PICKLEBALL COURT</h1>
                <p class="text-xs text-gray-200">Purok 3, Bamboo Green Village, Cubacub, Mandaue City, 6014</p>
            </div>
            <div class="mt-3 sm:mt-0 flex gap-4 text-sm font-semibold">
                <a href="/" class="hover:text-accentsyellow transition">Book Court</a>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-6 py-8 flex-grow w-full">
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="mb-6 p-4 rounded-lg shadow-sm {{ 'bg-green-100 text-green-800 border border-green-300' if category == 'success' else 'bg-red-100 text-red-800 border border-red-300' }}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-darkbeige p-8">
            <div class="border-b border-gray-100 pb-6 mb-6">
                <h2 class="text-xl font-bold text-courtblue">Court Reservation Form</h2>
                <p class="text-sm text-gray-500 mt-1">Hours: 4:00 PM – 12:00 AM | Rate: ₱300 (Mon–Thu) / ₱350 (Fri–Sun)</p>
            </div>

            <form action="/book" method="POST" enctype="multipart/form-data" class="space-y-6">
                <!-- Date & Slot Selection -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Select Date</label>
                        <input type="date" name="date" id="dateInput" required 
                               class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-courtblue focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Select Time Slot (1 Hour)</label>
                        <select name="slot" id="slotSelect" required class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-courtblue focus:outline-none">
                            <option value="" disabled selected>-- Select a date first --</option>
                        </select>
                    </div>
                </div>

                <!-- Personal Information -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
                        <input type="text" name="name" required placeholder="Juan Dela Cruz"
                               class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-courtblue focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Phone / Mobile Number</label>
                        <input type="text" name="phone" required placeholder="09123456789"
                               class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-courtblue focus:outline-none">
                    </div>
                </div>

                <!-- Payment Method & Receipt Upload Section -->
                <div class="border-t border-b border-gray-200 py-6 my-6 bg-beige/40 rounded-xl p-6">
                    <h3 class="text-lg font-bold text-courtblue mb-2">Payment via GCash</h3>
                    <p class="text-xs text-gray-600 mb-4">Please send payment to GCash before completing your reservation.</p>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                        <!-- GCash Details -->
                        <div class="bg-white p-4 rounded-lg border border-darkbeige shadow-sm">
                            <div class="text-xs text-gray-500 font-semibold uppercase">GCash Account Number</div>
                            <div class="text-xl font-black text-courtblue tracking-wide my-1">0976-364-2944</div>
                            <div class="text-xs text-gray-500 font-semibold uppercase mt-2">Account Name</div>
                            <div class="text-sm font-bold text-gray-800">GARAHE PICKLEBALL COURT</div>
                        </div>

                        <!-- GCash QR Code Placeholder -->
                        <div class="flex flex-col items-center justify-center bg-white p-4 rounded-lg border border-darkbeige shadow-sm">
                            <img src="{{ url_for('static', filename='gcash_qr.png') }}" 
                                alt="GCash QR Code" 
                                class="w-32 h-32 object-contain rounded-md border border-gray-200">
                            <span class="text-xs text-gray-500 mt-2">Scan QR Code to Pay</span>
                        </div>
                    </div>

                    <!-- Receipt Attachment -->
                    <div class="mt-6">
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Attach GCash Payment Receipt (Screenshot)</label>
                        <input type="file" name="receipt" id="receiptInput" accept="image/*" required
                               class="w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-courtblue file:text-white hover:file:bg-blue-900 border border-gray-300 rounded-lg bg-white cursor-pointer">
                        <p class="text-xs text-gray-400 mt-1">Allowed formats: PNG, JPG, JPEG, WEBP</p>
                    </div>
                </div>

                <!-- Submission Controls -->
                <div class="pt-2 flex items-center justify-between border-t border-gray-100">
                    <div>
                        <span class="text-sm text-gray-500">Facility:</span>
                        <span class="font-bold text-courtblue">Garahe Court 1</span>
                    </div>
                    <button type="submit" id="submitBtn" disabled 
                            class="bg-gray-400 text-white font-bold px-8 py-3 rounded-lg shadow cursor-not-allowed transition duration-200">
                        Confirm Reservation
                    </button>
                </div>
            </form>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-courtblue text-gray-300 py-4 text-center text-xs mt-12">
        <p>&copy; 2026 Garahe Pickleball Court &bull; Mandaue City, Cebu</p>
    </footer>

    <script>
        const allSlots = {{ slots | tojson }};
        const dateInput = document.getElementById('dateInput');
        const slotSelect = document.getElementById('slotSelect');
        const receiptInput = document.getElementById('receiptInput');
        const submitBtn = document.getElementById('submitBtn');

        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
        dateInput.value = today;

        receiptInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('bg-gray-400', 'cursor-not-allowed');
                submitBtn.classList.add('bg-courtblue', 'hover:bg-blue-900', 'cursor-pointer', 'hover:-translate-y-0.5');
            } else {
                submitBtn.disabled = true;
                submitBtn.classList.add('bg-gray-400', 'cursor-not-allowed');
                submitBtn.classList.remove('bg-courtblue', 'hover:bg-blue-900', 'cursor-pointer', 'hover:-translate-y-0.5');
            }
        });

        async function updateAvailableSlots() {
            const selectedDate = dateInput.value;
            if (!selectedDate) return;

            slotSelect.innerHTML = '<option value="" disabled selected>Loading available slots...</option>';

            try {
                const response = await fetch(`/api/booked-slots?date=${selectedDate}`);
                const bookedSlots = await response.json();

                slotSelect.innerHTML = '';

                let availableCount = 0;
                allSlots.forEach(slot => {
                    const isBooked = bookedSlots.includes(slot);
                    const option = document.createElement('option');
                    option.value = slot;
                    
                    if (isBooked) {
                        option.textContent = `${slot} (Already Reserved)`;
                        option.disabled = true;
                        option.classList.add('text-red-400', 'bg-gray-100');
                    } else {
                        option.textContent = slot;
                        availableCount++;
                    }
                    slotSelect.appendChild(option);
                });

                if (availableCount > 0) {
                    const defaultOpt = document.createElement('option');
                    defaultOpt.value = "";
                    defaultOpt.disabled = true;
                    defaultOpt.selected = true;
                    defaultOpt.textContent = "-- Choose a time slot --";
                    slotSelect.insertBefore(defaultOpt, slotSelect.firstChild);
                } else {
                    const fullOpt = document.createElement('option');
                    fullOpt.value = "";
                    fullOpt.disabled = true;
                    fullOpt.selected = true;
                    fullOpt.textContent = "All slots are fully booked for this date";
                    slotSelect.insertBefore(fullOpt, slotSelect.firstChild);
                }
            } catch (err) {
                console.error("Failed to fetch slots", err);
            }
        }

        dateInput.addEventListener('change', updateAvailableSlots);
        updateAvailableSlots();
    </script>
</body>
</html>
"""

ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - Garahe Pickleball</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 rounded-xl shadow-md w-full max-w-md border border-gray-200">
        <h2 class="text-xl font-bold text-blue-900 mb-2">Admin Authentication</h2>
        <p class="text-xs text-gray-500 mb-6">Please enter the admin password to view reservations.</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="mb-4 p-3 rounded-lg text-xs bg-red-100 text-red-800 border border-red-300">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form action="/admin/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-xs font-semibold text-gray-600 uppercase mb-1">Admin Password</label>
                <input type="password" name="password" required 
                       class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-800 focus:outline-none">
            </div>
            <button type="submit" class="w-full bg-blue-900 text-white font-bold py-2.5 rounded-lg hover:bg-blue-800 transition">
                Access Dashboard
            </button>
        </form>
        <div class="mt-4 text-center">
            <a href="/" class="text-xs text-blue-600 hover:underline">← Back to Public Booking Page</a>
        </div>
    </div>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Garahe Pickleball</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        beige: '#F5F2EB',
                        darkbeige: '#E8E2D5',
                        courtblue: '#1E3A8A',
                        accentsyellow: '#EAB308',
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-beige text-gray-800 font-sans min-h-screen flex flex-col justify-between">

    <header class="bg-courtblue text-white shadow-md">
        <div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-black tracking-wide text-accentsyellow">GARAHE ADMIN</h1>
                <p class="text-xs text-gray-200">Reservation & Receipt Verification Dashboard</p>
            </div>
            <div class="flex gap-4 text-sm font-semibold items-center">
                <a href="/" class="hover:text-accentsyellow transition">Back to Booking</a>
                <a href="/admin/logout" class="bg-red-600 px-3 py-1.5 rounded text-xs hover:bg-red-700 transition">Logout</a>
            </div>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-6 py-8 flex-grow w-full">
        <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-darkbeige p-6">
            <h2 class="text-xl font-bold text-courtblue mb-4">All Bookings & Payment Verification</h2>
            
            {% if reservations %}
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-100 text-xs uppercase text-gray-600">
                                <th class="p-3">ID</th>
                                <th class="p-3">Name</th>
                                <th class="p-3">Phone</th>
                                <th class="p-3">Date</th>
                                <th class="p-3">Slot</th>
                                <th class="p-3">Rate</th>
                                <th class="p-3">Receipt</th>
                                <th class="p-3 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200 text-sm">
                            {% for r in reservations %}
                            <tr class="hover:bg-gray-50">
                                <td class="p-3 font-mono text-gray-500">#{{ r.id }}</td>
                                <td class="p-3 font-bold text-courtblue">{{ r.name }}</td>
                                <td class="p-3 text-gray-600">{{ r.phone }}</td>
                                <td class="p-3 font-semibold">{{ r.date }}</td>
                                <td class="p-3"><span class="bg-blue-50 text-courtblue px-2 py-1 rounded text-xs font-bold">{{ r.slot }}</span></td>
                                <td class="p-3 font-bold text-green-700">₱{{ r.rate }}</td>
                                <td class="p-3">
                                    {% if r.receipt %}
                                        <a href="/static/uploads/{{ r.receipt }}" target="_blank" class="text-xs font-bold text-blue-600 hover:underline bg-blue-50 px-2 py-1 rounded">View Receipt</a>
                                    {% else %}
                                        <span class="text-xs text-gray-400">No Receipt</span>
                                    {% endif %}
                                </td>
                                <td class="p-3 text-center">
                                    <form action="/cancel/{{ r.id }}" method="POST" class="inline">
                                        <button type="submit" class="text-red-600 hover:text-red-800 text-xs font-bold bg-red-50 hover:bg-red-100 px-3 py-1 rounded transition">Cancel</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <p class="text-gray-500 py-8 text-center">No reservations found yet.</p>
            {% endif %}
        </div>
    </main>

    <footer class="bg-courtblue text-gray-300 py-4 text-center text-xs mt-12">
        <p>&copy; 2026 Garahe Pickleball Court</p>
    </footer>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, slots=SLOTS)

@app.route('/api/booked-slots')
def get_booked_slots():
    date = request.args.get('date')
    booked = [r['slot'] for r in reservations if r['date'] == date]
    return jsonify(booked)

@app.route('/book', methods=['POST'])
def book():
    date = request.form.get('date')
    slot = request.form.get('slot')
    name = request.form.get('name')
    phone = request.form.get('phone')
    
    file = request.files.get('receipt')
    if not file or file.filename == '' or not allowed_file(file.filename):
        flash("Please upload a valid image screenshot of your GCash receipt.", "error")
        return redirect(url_for('index'))

    for r in reservations:
        if r['date'] == date and r['slot'] == slot:
            flash(f"Slot {slot} on {date} was just reserved by another user!", "error")
            return redirect(url_for('index'))
            
    filename = secure_filename(f"{date}_{slot.replace(' ', '')}_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    rate = calculate_rate(date)
    new_id = len(reservations) + 1
    
    reservations.append({
        'id': new_id,
        'date': date,
        'slot': slot,
        'name': name,
        'phone': phone,
        'rate': rate,
        'receipt': filename
    })
    
    flash(f"Reservation submitted for {date} ({slot})! Your payment receipt was received.", "success")
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return render_template_string(ADMIN_LOGIN_TEMPLATE)
    return render_template_string(ADMIN_TEMPLATE, reservations=reservations)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        return redirect(url_for('admin'))
    else:
        flash("Incorrect admin password.", "error")
        return render_template_string(ADMIN_LOGIN_TEMPLATE)

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/cancel/<int:res_id>', methods=['POST'])
def cancel(res_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    
    global reservations
    reservations = [r for r in reservations if r['id'] != res_id]
    flash("Reservation successfully cancelled.", "success")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)