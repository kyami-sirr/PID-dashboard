import hmac
import hashlib
import sys

# Kunci rahasia milikmu (bebas diubah, harus sama dengan di dashboard.py)
SECRET_KEY = b"GantiDenganKunciRahasiaKamu123"

def generate_response(challenge_code: str) -> str:
    h = hmac.new(SECRET_KEY, challenge_code.encode('utf-8'), hashlib.sha256)
    # Mengambil 6 angka unik
    return str(int(h.hexdigest(), 16) % 1000000).zfill(6)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Penggunaan: python3 gen_key.py <KODE_REQUEST>")
        sys.exit(1)
        
    req_code = sys.argv[1].strip()
    resp_code = generate_response(req_code)
    print(f"Kode Request : {req_code}")
    print(f"Kode Balasan : {resp_code}")
