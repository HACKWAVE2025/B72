# webhook_receiver.py
from flask import Flask, request, jsonify, abort
import hmac, hashlib, json, logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

WEBHOOK_SECRET = "mock_webhook_secret"  # must match mock server's secret

@app.route("/webhook", methods=["POST"])
def webhook():
    body_bytes = request.get_data()
    header_sig = request.headers.get("X-Razorpay-Signature", "")
    computed = hmac.new(WEBHOOK_SECRET.encode(), body_bytes, hashlib.sha256).hexdigest()
    app.logger.debug("received sig: %s computed: %s", header_sig, computed)
    if not hmac.compare_digest(computed, header_sig):
        app.logger.warning("Invalid signature")
        return jsonify({"error":"invalid signature"}), 400
    payload = json.loads(body_bytes)
    app.logger.info("Webhook verified. Payload: %s", json.dumps(payload))
    return jsonify({"status":"ok","received":payload}), 200

if __name__ == "__main__":
    print("Webhook receiver listening on http://127.0.0.1:8000/webhook")
    app.run(host="127.0.0.1", port=8000, debug=True)
