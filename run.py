from app import create_app
from config import HOST, PORT, DEBUG

app = create_app()

if __name__ == '__main__':
    print(f"""
    ╔══════════════════════════════════════════╗
    ║   Email Extractor Platform Started!     ║
    ╠══════════════════════════════════════════╣
    ║  Open: http://{HOST}:{PORT}           ║
    ╚══════════════════════════════════════════╝
    """)
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
