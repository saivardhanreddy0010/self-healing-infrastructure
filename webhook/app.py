from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)


@app.route("/alert", methods=["POST"])
def receive_alert():

    alert_data = request.get_json(silent=True) or {}

    print("\n========== ALERT RECEIVED ==========", flush=True)

    recovery_triggered = False

    for alert in alert_data.get("alerts", []):

        alert_name = alert.get("labels", {}).get("alertname")
        status = alert.get("status")
        severity = alert.get("labels", {}).get("severity")
        description = alert.get("annotations", {}).get("description")

        print("Alert Name:", alert_name, flush=True)
        print("Status:", status, flush=True)
        print("Severity:", severity, flush=True)
        print("Description:", description, flush=True)

        if alert_name == "NginxDown" and status == "firing":

            print("\nStarting Ansible self-healing playbook...", flush=True)

            try:
                result = subprocess.run(
                    [
                        "ansible-playbook",
                        "-i", "localhost,",
                        "-c", "local",
                        "/ansible/restart-nginx.yml"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                print(result.stdout, flush=True)

                if result.returncode == 0:
                    print("NGINX recovery successful!", flush=True)
                    recovery_triggered = True

                else:
                    print("Ansible execution failed!", flush=True)
                    print(result.stderr, flush=True)

                    return jsonify({
                        "status": "error",
                        "message": "Ansible playbook failed"
                    }), 500

            except subprocess.TimeoutExpired:

                print("Ansible execution timed out!", flush=True)

                return jsonify({
                    "status": "error",
                    "message": "Ansible execution timed out"
                }), 500

    print("====================================\n", flush=True)

    return jsonify({
        "status": "success",
        "recovery_triggered": recovery_triggered,
        "message": "Alert processed successfully"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)