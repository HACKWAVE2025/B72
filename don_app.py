from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests

app = Flask(__name__)

# Mock Razorpay API URL
MOCK_API = "http://127.0.0.1:5000/mock/v1"

@app.route('/')
def index():
    return '''
    <h2>Disaster Donation Portal</h2>
    <form action="/donate" method="POST">
        <label>Donor Name:</label><br>
        <input type="text" name="name" required><br><br>
        
        <label>Donation Amount (in ₹):</label><br>
        <input type="number" name="amount" required><br><br>
        
        <button type="submit">Donate Now</button>
    </form>
    '''

@app.route('/donate', methods=['POST'])
def donate():
    name = request.form['name']
    amount = int(request.form['amount']) * 100  # Convert ₹ to paise for Razorpay
    
    # Create mock Razorpay order
    order_data = {"amount": amount, "currency": "INR", "notes": {"donor": name}}
    try:
        response = requests.post(f"{MOCK_API}/orders", json=order_data)
        order = response.json()
    except Exception as e:
        return f"<h3>Error connecting to Mock Razorpay API: {str(e)}</h3>"

    if 'id' not in order:
        return f"<h3>Mock order creation failed: {order}</h3>"

    # Create a mock payment link for demonstration
    payment_data = {
        "amount": amount,
        "currency": "INR",
        "customer": {"name": name},
        "notes": {"purpose": "Disaster Donation"}
    }
    pay_response = requests.post(f"{MOCK_API}/payment_links", json=payment_data)
    pay_link = pay_response.json()

    short_url = pay_link.get("short_url", "#")

    return f"""
    <h3>Thank you, {name}!</h3>
    <p>Your donation order has been created.</p>
    <p><b>Order ID:</b> {order['id']}</p>
    <p><b>Mock Payment Link:</b> <a href="{short_url}" target="_blank">{short_url}</a></p>
    """

@app.route('/orders')
def get_orders():
    # Optional: Fetch all mock orders (for debugging)
    try:
        res = requests.get(f"{MOCK_API}/orders")
        return jsonify(res.json())
    except:
        return jsonify({"error": "Cannot connect to mock server"})

if __name__ == "__main__":
    app.run(port=5001, debug=True)
