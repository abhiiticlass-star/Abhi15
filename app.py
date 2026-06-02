from flask import Flask, jsonify, request
from signal_engine import generate_signal

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "name": "ABHI SIGNALS BACKEND"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })

@app.route("/get-signal/<pair>")
def get_signal(pair):

    timeframe = request.args.get("tf", "1")

    try:
        result = generate_signal(
            pair=pair,
            timeframe=timeframe
        )

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "pair": pair,
            "signal": "AVOID",
            "score": 50,
            "trend": "Neutral",
            "trendM5": "Neutral",
            "market": "unknown",
            "error": str(e)
        })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
