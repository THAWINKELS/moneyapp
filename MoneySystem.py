from flask import Flask, render_template_string, request, redirect, url_for, session
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATA_FILE = r'D:\Project storage\MoneySystem\data.json'
HISTORY_FILE = r'D:\Project storage\MoneySystem\history.json'
BACKGROUND_URL = 'https://static.vecteezy.com/ti/gratis-vector/p1/11125380-echt-geld-monopoly-achtergrond-vector.jpg'

# ====== DATA LAAD- EN OPSLAGFUNCTIES ======
def load_data():
    default_data = {
        'balances': {str(i): 0.0 for i in range(1, 7)},
        'payments': {str(i): 0.0 for i in range(1, 7)},
        'pins': {str(i): '1234' for i in range(1, 7)}
    }

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)

            # Vul ontbrekende delen aan
            for key in default_data:
                if key not in data:
                    data[key] = default_data[key]
                elif isinstance(default_data[key], dict):
                    for subkey in default_data[key]:
                        if subkey not in data[key]:
                            data[key][subkey] = default_data[key][subkey]

            return data

        except json.JSONDecodeError:
            print("⚠️ Ongeldige JSON. Nieuw bestand wordt aangemaakt.")

    return default_data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def log_transaction(team, amount):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list):  # <-- check!
                    history = []
            except json.JSONDecodeError:
                history = []

    history.append({
        'team': team,
        'amount': amount,
        'timestamp': datetime.now().isoformat()
    })

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)



# ====== INITIELE DATA ======
data = load_data()
team_balances = data['balances']
payment_amounts = data['payments']
team_pins = data['pins']

# Admin login template
ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center px-4">
    <form method="POST" class="bg-white p-6 sm:p-8 rounded-2xl shadow-xl w-full max-w-xs sm:max-w-sm">
        <h2 class="text-2xl font-bold mb-4 text-center">🔐 Admin Login</h2>
        
        <input type="password" name="password" placeholder="Wachtwoord"
               class="w-full px-4 py-2 border rounded-xl mb-4 focus:outline-none focus:ring-2 focus:ring-green-500">
        
        <button type="submit"
                class="w-full bg-green-600 text-white px-4 py-2 rounded-xl hover:bg-green-700 transition">Login</button>
        
        {% if error %}
        <p class="text-red-500 mt-3 text-center text-sm">{{ error }}</p>
        {% endif %}
    </form>
</body>
</html>
"""

# ====== AANGEPASTE ADMIN TEMPLATE MET BETAALHISTORIE EN ZONDER LOGOUT ======
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Paneel</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-white p-6 rounded-2xl shadow-xl w-full max-w-4xl">
        <h2 class="text-2xl font-bold mb-4 text-center text-green-800">🛠️ Admin Paneel</h2>
        <p class="text-center text-green-600 mb-6">Beheer snel het saldo en de pincode van elk team</p>

        <form method="POST">
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {% for team, balance in team_balances.items() %}
                <div class="border rounded-xl p-4 bg-green-50 shadow">
                    <h3 class="text-lg font-bold text-green-700 mb-2">Team {{ team }}</h3>
                    <p class="text-green-900 mb-2">Saldo: €{{ '%.2f' | format(balance) }}</p>
                    <input type="number" name="amount_{{ team }}" step="0.01" placeholder="Bedrag" class="w-full px-3 py-1 mb-2 border rounded">
                    <div class="flex gap-2 mb-2">
                        <button type="submit" name="action" value="add_{{ team }}" class="bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600 w-full">➕</button>
                        <button type="submit" name="action" value="sub_{{ team }}" class="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 w-full">➖</button>
                    </div>
                    <div class="flex gap-2 mb-2">
                        <button type="submit" name="action" value="reset_{{ team }}"
                                class="bg-yellow-500 text-white px-2 py-1 rounded hover:bg-yellow-600 w-full"
                                onclick="return confirm('Weet je zeker dat je het saldo van Team {{ team }} wilt resetten?');">🔄 Reset saldo</button>
                    </div>
                    <input type="text" name="pin_{{ team }}" maxlength="4" placeholder="Nieuwe pincode" class="w-full px-3 py-1 border rounded text-center" value="{{ team_pins[team] }}">

                    <a href="{{ url_for('history', team=team) }}" class="block mt-3 text-sm text-blue-600 hover:underline text-center">📜 Betaalhistorie</a>
                </div>
                {% endfor %}
            </div>

            <div class="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                <button type="submit" name="action" value="reset_all"
                        class="bg-red-600 text-white px-6 py-2 rounded-xl hover:bg-red-700 w-full sm:w-auto"
                        onclick="return confirm('Weet je zeker dat je ALLE saldi wilt resetten?');">🔁 Reset alle saldi</button>

                <button type="submit"
                        class="bg-blue-600 text-white px-6 py-2 rounded-xl hover:bg-blue-700 w-full sm:w-auto"
                        onclick="return confirm('Je gaat de gewijzigde pincodes opslaan. Weet je dit zeker?');">💾 Pincodes opslaan</button>

                <a href="{{ url_for('index') }}" class="text-sm text-green-600 hover:underline">⬅ Terug naar overzicht</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

# Index page template
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team Bank Overzicht</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen flex items-center justify-center font-sans" style="background-image: url('{{ background_url }}'); background-size: cover; background-position: center;">
    <div class="bg-white/80 backdrop-blur p-8 rounded-2xl shadow-2xl w-full max-w-lg">
        <h1 class="text-4xl font-bold mb-6 text-center text-green-800">💰 Team Bank 💰</h1>
        <ul class="space-y-3">
            {% for team, balance in team_balances.items() %}
            <li>
                <a href="{{ url_for('team_page', team_number=team) }}" class="block p-4 bg-green-50 rounded-xl shadow hover:bg-green-100 transition">
                    <div class="flex justify-between items-center">
                        <span class="text-lg font-medium text-green-700">Team {{ team }}</span>
                        <span class="text-lg font-semibold text-green-900">€ {{ '%.2f' | format(balance) }}</span>
                    </div>
                </a>
            </li>
            {% endfor %}
        </ul>
        <div class="mt-6 text-center">
            <a href="{{ url_for('admin_login') }}" class="text-sm text-green-600 hover:underline">🔐 Admin Login</a>
        </div>
    </div>
</body>
</html>
"""

# Team page template
TEAM_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team {{ team_number }} Bank</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen flex items-center justify-center font-sans" style="background-image: url('{{ background_url }}'); background-size: cover; background-position: center;">
    <div class="bg-white/80 backdrop-blur p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <h1 class="text-3xl font-bold mb-6 text-center text-green-800">🏦 Team {{ team_number }} Bank</h1>
        <form method="POST" class="mb-4">
            <input type="number" name="amount" placeholder="Bedrag" step="0.01" required class="w-full px-4 py-2 mb-2 border rounded-xl shadow">
            <div class="flex justify-between mt-2">
                <button type="submit" name="action" value="deposit" class="bg-green-500 text-white px-4 py-2 rounded-xl hover:bg-green-600 shadow">Storten</button>
                <button type="submit" name="action" value="withdraw" class="bg-red-500 text-white px-4 py-2 rounded-xl hover:bg-red-600 shadow">Opnemen</button>
            </div>
        </form>
        <form method="POST">
            <input type="number" name="payment" step="0.01" placeholder="Zet betaling klaar" class="w-full px-4 py-2 mb-2 border rounded-xl">
            <button name="action" value="set_payment" class="bg-blue-500 text-white px-4 py-2 rounded-xl hover:bg-blue-600 w-full">💳 Zet betaling klaar</button>
        </form>
        {% if payment_amount != 0 %}
        <div class="mt-4 text-center">
            <a href="{{ url_for('pay_page', team_number=team_number) }}" class="text-blue-600 underline">➡ Betaal €{{ '%.2f' | format(payment_amount) }}</a>
        </div>
        {% endif %}
        <div class="text-center mt-6">
            <p class="text-xl text-green-700">Huidig saldo:</p>
            <p class="text-3xl font-bold text-green-900">€ {{ '%.2f' | format(balance) }}</p>
        </div>
        <div class="mt-6 text-center">
            <a href="{{ url_for('index') }}" class="text-green-600 hover:underline">⬅ Terug naar overzicht</a>
        </div>
    </div>
</body>
</html>
"""

# Pincode betalingspagina
PAY_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pincode Invoeren</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-white p-6 rounded-2xl shadow-xl w-full max-w-xs text-center">
        <h2 class="text-xl font-bold mb-2">Voer pincode in</h2>
        <p class="text-md mb-4 text-green-700 font-semibold">Te betalen: €{{ '%.2f' | format(payment_amount) }}</p>

        <form method="POST" class="flex flex-col items-center">
            <input type="password" name="pin" id="pin-input" maxlength="4" readonly
                   class="text-center text-2xl tracking-widest mb-4 bg-gray-100 border border-gray-300 rounded-xl px-4 py-2 w-full" placeholder="●●●●">

            <div class="grid grid-cols-3 gap-3 mb-4 w-full">
                {% for num in range(1, 10) %}
                <button type="button" class="bg-gray-200 text-xl py-4 rounded-xl shadow hover:bg-gray-300" onclick="appendPin('{{ num }}')">{{ num }}</button>
                {% endfor %}
                <button type="button" class="bg-red-200 text-xl py-4 rounded-xl shadow hover:bg-red-300" onclick="resetPin()">Reset</button>
                <button type="button" class="bg-gray-200 text-xl py-4 rounded-xl shadow hover:bg-gray-300" onclick="appendPin('0')">0</button>
                <button type="button" class="bg-yellow-200 text-xl py-4 rounded-xl shadow hover:bg-yellow-300" onclick="deletePin()">⌫</button>
            </div>

            <button type="submit" class="bg-green-600 text-white px-4 py-2 rounded-xl w-full hover:bg-green-700">Bevestig</button>
        </form>

        {% if error %}
        <p class="text-red-600 mt-3 font-semibold">{{ error }}</p>
        {% endif %}
    </div>

    <script>
        function appendPin(digit) {
            const input = document.getElementById('pin-input');
            if (input.value.length < 4) {
                input.value += digit;
            }
        }
        function deletePin() {
            const input = document.getElementById('pin-input');
            input.value = input.value.slice(0, -1);
        }
        function resetPin() {
            document.getElementById('pin-input').value = '';
        }
    </script>
</body>
</html>
"""

HISTORY_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Betaalhistorie - Team {{ team }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center px-4">
    <div class="bg-white w-full max-w-2xl p-6 rounded-2xl shadow-xl">
        <h2 class="text-xl sm:text-2xl font-bold mb-4 text-green-700 text-center">📜 Betaalhistorie voor Team {{ team }}</h2>

        {% if history %}
        <ul class="divide-y divide-gray-200">
            {% for entry in history %}
            <li class="py-3 flex flex-col sm:flex-row sm:justify-between sm:items-center text-sm sm:text-base">
                <span class="text-green-800 font-medium">💶 €{{ '%.2f'|format(entry.amount) }}</span>
                <span class="text-gray-500">{{ entry.timestamp }}</span>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="text-gray-600 text-center">Geen transacties gevonden.</p>
        {% endif %}

        <div class="mt-6 text-center">
            <a href="{{ url_for('admin_login') }}" class="text-green-600 hover:underline">⬅ Terug naar admin</a>
        </div>
    </div>
</body>
</html>
"""

# Team page template
TEAM_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team {{ team_number }} Bank</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen flex items-center justify-center font-sans" style="background-image: url('{{ background_url }}'); background-size: cover; background-position: center;">
    <div class="bg-white/80 backdrop-blur p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <h1 class="text-3xl font-bold mb-6 text-center text-green-800">🏦 Team {{ team_number }} Bank</h1>
        <form method="POST" class="mb-4">
            <input type="number" name="amount" placeholder="Bedrag" step="0.01" required class="w-full px-4 py-2 mb-2 border rounded-xl shadow">
            <div class="flex justify-between mt-2">
                <button type="submit" name="action" value="deposit" class="bg-green-500 text-white px-4 py-2 rounded-xl hover:bg-green-600 shadow">Storten</button>
                <button type="submit" name="action" value="withdraw" class="bg-red-500 text-white px-4 py-2 rounded-xl hover:bg-red-600 shadow">Opnemen</button>
            </div>
        </form>
        <form method="POST">
            <input type="number" name="payment" step="0.01" placeholder="Zet betaling klaar" class="w-full px-4 py-2 mb-2 border rounded-xl">
            <button name="action" value="set_payment" class="bg-blue-500 text-white px-4 py-2 rounded-xl hover:bg-blue-600 w-full">💳 Zet betaling klaar</button>
        </form>
        {% if payment_amount != 0 %}
        <div class="mt-4 text-center">
            <a href="{{ url_for('pay_page', team_number=team_number) }}" class="text-blue-600 underline">➡ Betaal €{{ '%.2f' | format(payment_amount) }}</a>
        </div>
        {% endif %}
        <div class="text-center mt-6">
            <p class="text-xl text-green-700">Huidig saldo:</p>
            <p class="text-3xl font-bold text-green-900">€ {{ '%.2f' | format(balance) }}</p>
        </div>
        <div class="mt-6 text-center">
            <a href="{{ url_for('index') }}" class="text-green-600 hover:underline">⬅ Terug naar overzicht</a>
        </div>
    </div>
</body>
</html>
"""



# ====== ROUTES ======

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE, team_balances=team_balances, background_url=BACKGROUND_URL)

@app.route('/team/<team_number>', methods=['GET', 'POST'])
def team_page(team_number):
    if team_number not in team_balances:
        return redirect(url_for('index'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action in ['deposit', 'withdraw']:
            try:
                amount = float(request.form.get('amount', '0'))
                if action == 'deposit':
                        team_balances[team_number] += amount
                    elif action == 'withdraw':
                        team_balances[team_number] -= amount
            except ValueError:
                pass
        elif action == 'set_payment':
            try:
                payment = float(request.form.get('payment', '0'))
                payment_amounts[team_number] = payment
            except ValueError:
                pass

        save_data(data)

    return render_template_string(
        TEAM_TEMPLATE,
        team_number=team_number,
        balance=team_balances[team_number],
        payment_amount=payment_amounts[team_number],
        background_url="https://images.unsplash.com/photo-1605902711622-cfb43c4437b2"  # voorbeeldafbeelding
    )

@app.route('/team/<team_number>/pay', methods=['GET', 'POST'])
def pay_page(team_number):
    if team_number not in team_balances:
        return redirect(url_for('index'))

    error = None

    if request.method == 'POST':
        if request.form.get('pin') == team_pins[team_number]:
            payment = payment_amounts[team_number]

            # Positief = bijschrijven, negatief = afschrijven
            team_balances[team_number] += payment

            # Sla de transactie op met hetzelfde teken
            log_transaction(team_number, payment)

            # Betaling wissen
            payment_amounts[team_number] = 0.0
            save_data(data)

            return redirect(url_for('team_page', team_number=team_number))
        else:
            error = 'Onjuiste pincode'

    return render_template_string(
        PAY_TEMPLATE,
        team_number=team_number,
        payment_amount=payment_amounts[team_number],
        error=error
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == '123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = 'Onjuist wachtwoord'
    return render_template_string(ADMIN_LOGIN_TEMPLATE, error=error)


@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')

        for team in team_balances.keys():
            if action in [f'add_{team}', f'sub_{team}']:
                try:
                    amount = float(request.form.get(f'amount_{team}', '0'))
                    if action.startswith('add'):
                        team_balances[team] += amount
                        log_transaction(team, amount)
                    elif action.startswith('sub'):
                        team_balances[team] -= amount
                        log_transaction(team, -amount)
                except ValueError:
                    pass

            elif action == f'reset_{team}':
                log_transaction(team, -team_balances[team])
                team_balances[team] = 0.0

        if action == 'reset_all':
            for t in team_balances:
                log_transaction(t, -team_balances[t])
                team_balances[t] = 0.0

            # Leeg de geschiedenis
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'w') as f:
                    json.dump([], f)

        for team in team_pins:
            nieuwe_pin = request.form.get(f'pin_{team}')
            if nieuwe_pin and len(nieuwe_pin) == 4 and nieuwe_pin.isdigit():
                team_pins[team] = nieuwe_pin

        save_data(data)

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)

    return render_template_string(ADMIN_TEMPLATE, team_balances=team_balances, team_pins=team_pins, history=history)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route("/history/<team>")
def history(team):
    all_history = load_history()
    team_history = [entry for entry in all_history if entry.get("team") == team]

    team_history.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template_string(HISTORY_TEMPLATE, team=team, history=team_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
