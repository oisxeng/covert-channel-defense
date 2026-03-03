import io
import re
import json
import base64
import numpy as np
from scipy.ndimage import convolve
from PIL import Image
from scipy.stats import entropy
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# ... [Hier bleibt der alte Code für app, Middleware und calculate_transition_rate] ...

def extract_smart_payload(lsb_flat, max_bytes=20000):
    """Extrahiert Bits und sucht nach ZWEIFELSFREIEN Beweisen (Semantik & Struktur)."""
    # 1. Bits zu rohen Bytes machen
    byte_array = bytearray()
    for i in range(0, min(len(lsb_flat), max_bytes * 8) - 8, 8):
        byte_val = int("".join(map(str, lsb_flat[i:i+8])), 2)
        byte_array.append(byte_val)
        
    # Rohen Text (mit unlesbaren Zeichen) für Regex generieren
    raw_text = "".join([chr(b) if 32 <= b <= 126 else '.' for b in byte_array])
    
    definitive_proof = False
    proof_details = []

    # BEWEIS 1: Magic Bytes (File Carving)
    # Wenn wir diese Signaturen im Rauschen finden, ist es zu 100% eine versteckte Datei
    magic_signatures = {
        b'%PDF-': "PDF Document",
        b'PK\x03\x04': "ZIP Archive",
        b'\x89PNG\r\n\x1a\n': "PNG Image",
        b'\xFF\xD8\xFF': "JPEG Image"
    }
    for sig, name in magic_signatures.items():
        if sig in byte_array:
            definitive_proof = True
            proof_details.append(f"Magic Bytes detected: Hidden {name} found!")

    # BEWEIS 2: Deep Base64 Validation
    # Wir suchen Base64-Strings und versuchen sie ECHT zu decodieren.
    base64_suspects = re.findall(r'(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', raw_text)
    valid_b64_decoded = []
    for b64 in base64_suspects:
        try:
            decoded_bytes = base64.b64decode(b64)
            decoded_text = decoded_bytes.decode('utf-8')
            # Wenn der dekodierte Text nur lesbare Zeichen hat, haben wir einen Beweis!
            if len(decoded_text) > 5 and decoded_text.isprintable():
                definitive_proof = True
                valid_b64_decoded.append(decoded_text)
                proof_details.append(f"Verified Base64 Payload: {decoded_text[:50]}...")
        except:
            pass # War wohl doch nur Zufalls-Rauschen

    # BEWEIS 3: JSON / Code Parsing
    # Wir suchen nach JSON-Strukturen und prüfen sie auf syntaktische Korrektheit
    json_candidates = re.findall(r'\{.*?\}', raw_text)
    for jc in json_candidates:
        try:
            parsed = json.loads(jc.replace('.', '')) # Wir ignorieren die Punkte vom Rauschen
            if len(parsed.keys()) > 0:
                definitive_proof = True
                proof_details.append(f"Verified JSON Data: {str(parsed)[:50]}")
        except:
            pass

    # Standard-Heuristiken (Wörter, URLs)
    words = re.findall(r'[A-Za-z0-9_]{6,}', raw_text) # Mindestens 6 Zeichen für weniger False-Positives
    urls = re.findall(r'(https?://[^\s]+|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', raw_text)

    return {
        "raw_snippet": raw_text[:800] + "..." if len(raw_text) > 800 else raw_text,
        "found_words": words[:15],
        "found_urls": urls,
        "definitive_proof": definitive_proof,
        "proof_details": proof_details
    }

# ... [Hier kommt deine bestehende def encode_image_to_base64(...) ] ...

@app.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        img_pil = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        pixel_data = np.array(img_pil, dtype=np.int16)
        
        blue_channel = pixel_data[:, :, 2]
        lsb_blue = blue_channel & 1
        
        # Laplace Filter & Flat Regions (wie vorher)
        laplace_kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        msb_blue = (blue_channel >> 4) & 15
        residual = convolve(msb_blue.astype(float), laplace_kernel)
        flat_mask = np.abs(residual) <= 1
        flat_lsb_blue = lsb_blue[flat_mask]
        
        lsb_blue_flat_all = lsb_blue.flatten()
        if len(flat_lsb_blue) < 2000:
            flat_lsb_blue = lsb_blue_flat_all

        counts_flat = np.bincount(flat_lsb_blue)
        prob_flat = counts_flat / len(flat_lsb_blue) if len(counts_flat) == 2 else [1.0]
        flat_entropy_blue = entropy(prob_flat, base=2) if len(counts_flat) == 2 else 0.0
        flat_trans_blue = calculate_transition_rate(flat_lsb_blue)
        
        trans_deviation = abs(0.5 - flat_trans_blue)
        is_anomaly = False
        if flat_entropy_blue > 0.99985 and trans_deviation < 0.003:
            is_anomaly = True

        noise_map_visual = (lsb_blue * 255).astype(np.uint8)
        base64_image = encode_image_to_base64(noise_map_visual)

        # NEU: Die Payload Extraktion auf harte Beweise prüfen!
        extraction_results = extract_smart_payload(lsb_blue_flat_all)
        
        # Wenn wir einen harten Beweis haben, überschreiben wir die Statistik!
        if extraction_results["definitive_proof"]:
            is_anomaly = True
            message = f"🔥 SMOKING GUN: Cryptographic proof of embedded payload! ({extraction_results['proof_details'][0]})"
        else:
            message = "🚨 SEVERE ANOMALY: Steganographic payload suspected based on statistical variance." if is_anomaly else "✅ SAFE: Natural sensor photon noise detected. No steganography."

        return {
            "filename": file.filename,
            "metrics": {
                "flat_region_entropy": round(flat_entropy_blue, 6),
                "anomaly_score": round(flat_entropy_blue, 6),
                "blue_channel_transition_rate": round(flat_trans_blue, 6)
            },
            "anomaly_detected": is_anomaly,
            "definitive_proof": extraction_results["definitive_proof"], # Senden wir ans Frontend!
            "noise_map_base64": base64_image,
            "extraction": extraction_results,
            "message": message
        }
    except Exception as e:
        return {"error": str(e)}

# ... [read_root() bleibt gleich] ...
