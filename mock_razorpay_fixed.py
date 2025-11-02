# mock_razorpay_fixed.py
# Mock Razorpay server (runs on http://127.0.0.1:5000)
from flask import Flask, request, jsonify, abort, Blueprint
import uuid, time, hmac, hashlib, json, logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Use Blueprint so all routes are under /mock/v1
mock_api = Blueprint('mock_api', __name__, url_prefix='/mock/v1')

ORDERS = {}
PAYMENT_LINKS = {}
WEBHOOK_SECRET = "mock_webhook_secret"

def make_order_response(order_id, amount, currency="INR", notes=None):
    return {
        "id": order_id,
        "entity": "order",
        "amount": amount,
        "amount_paid": 0,
        "amount_due": amount,
        "currency": currency,
        "receipt": f"rcpt_{order_id}",
        "status": "created",
        "attempts": 0,
        "notes": notes or {}
    }

def make_payment_link_response(link_id, amount, currency="INR", short_url=None, status="created", notes=None):
    return {
        "id": link_id,
        "entity": "payment_link",
        "amount": amount,
        "currency": currency,
        "short_url": short_url or f"https://mock-pay.test/{link_id}",
        "status": status,
        "created_at": int(time.time()),
        "notes": notes or {}
    }

@mock_api.route("/orders", methods=["POST"])
def create_order():
    payload = request.get_json(silent=True)
    app.logger.debug("create_order payload: %s", payload)
    if not payload or "amount" not in payload:
        return jsonify({"error": "amount missing (JSON body required)"}), 400
    amount = payload["amount"]
    order_id = "order_" + uuid.uuid4().hex[:14]
    ORDERS[order_id] = {"amount": amount, "currency": payload.get("currency","INR"), "notes": payload.get("notes",{}), "status":"created"}
    return jsonify(make_order_response(order_id, amount, ORDERS[order_id]["currency"], ORDERS[order_id]["notes"])), 201

@mock_api.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    if order_id not in ORDERS:
        return jsonify({"error":"order not found"}), 404
    d = ORDERS[order_id]
    return jsonify(make_order_response(order_id, d["amount"], d["currency"], d["notes"])), 200

@mock_api.route("/payment_links", methods=["POST"])
def create_payment_link():
    payload = request.get_json(silent=True)
    app.logger.debug("create_payment_link payload: %s", payload)
    if not payload or "amount" not in payload:
        return jsonify({"error": "amount missing (JSON body required)"}), 400
    amount = payload["amount"]
    link_id = "plink_" + uuid.uuid4().hex[:12]
    short_url = f"https://mock-pay.test/p/{link_id}"
    PAYMENT_LINKS[link_id] = {"amount": amount, "currency": payload.get("currency","INR"), "status":"created", "short_url": short_url, "notes": payload.get("notes",{})}
    return jsonify(make_payment_link_response(link_id, amount, payload.get("currency","INR"), short_url, "created", payload.get("notes"))), 201

@mock_api.route("/payment_links/<link_id>", methods=["GET"])
def get_payment_link(link_id):
    if link_id not in PAYMENT_LINKS:
        return jsonify({"error":"payment link not found"}), 404
    d = PAYMENT_LINKS[link_id]
    return jsonify(make_payment_link_response(link_id, d["amount"], d["currency"], d["short_url"], d["status"], d["notes"])), 200

def sign_webhook(body_bytes, secret):
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

@mock_api.route("/send_webhook", methods=["POST"])
def send_webhook():
    body = request.get_json(silent=True) or {}
    target = body.get("target_url")
    event = body.get("event","payment.captured")
    payload = body.get("payload", {"mock":"data"})
    if not target:
        return jsonify({"error":"target_url required"}), 400

    webhook_body = {"event": event, "payload": payload, "created_at": int(time.time())}
    bytes_body = json.dumps(webhook_body).encode("utf-8")
    signature = sign_webhook(bytes_body, WEBHOOK_SECRET)
    # perform the POST (requests is optional; try/except to give helpful error if requests missing)
    try:
        import requests
        headers = {"Content-Type":"application/json", "X-Razorpay-Signature": signature}
        resp = requests.post(target, data=bytes_body, headers=headers, timeout=10)
        return jsonify({"sent_to": target, "status_code": resp.status_code, "response_text": resp.text}), 200
    except Exception as e:
        app.logger.exception("send_webhook failed")
        return jsonify({"error":"failed to POST to target", "exception": str(e), "signature": signature, "body": webhook_body}), 500

# Register blueprint
app.register_blueprint(mock_api)

# Root and health pages
@app.route("/")
def index():
    return """
    <h3>Mock Razorpay server</h3>
    <p>Available endpoints (prefix <code>/mock/v1</code>):</p>
    <ul>
      <li>POST /mock/v1/orders</li>
      <li>GET  /mock/v1/orders/&lt;order_id&gt;</li>
      <li>POST /mock/v1/payment_links</li>
      <li>GET  /mock/v1/payment_links/&lt;link_id&gt;</li>
      <li>POST /mock/v1/send_webhook</li>
    </ul>
    <p>Server is running. Use the exact paths above. Example root URL: <code>http://127.0.0.1:5000</code></p>
    """

# Friendly JSON 404 for unknown paths
@app.errorhandler(404)
def json_404(e):
    return jsonify({"error":"not found", "message": "Check path and HTTP method. Use /mock/v1/..."}), 404

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000
    print(f"Starting Mock Razorpay server at http://{host}:{port}")
    # run on 127.0.0.1 so the link http://127.0.0.1:5000 works exactly as requested
    app.run(host=host, port=port, debug=True)
