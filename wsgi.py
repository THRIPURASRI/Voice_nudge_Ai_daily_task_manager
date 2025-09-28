from voicenudge import create_app
from dotenv import load_dotenv

load_dotenv()  # load .env automatically

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)
