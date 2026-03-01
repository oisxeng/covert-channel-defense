import math
import random
import argparse
import os
from collections import Counter

# Für Text
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

# Für Bilder
from PIL import Image, ImageFilter

# Für Audio & Video
from moviepy.editor import AudioFileClip, VideoFileClip

# --- SETUP ---
def setup_nltk():
    resources = ['punkt', 'wordnet', 'averaged_perceptron_tagger']
    for res in resources:
        try:
            nltk.data.find(f'tokenizers/{res}' if res == 'punkt' else f'corpora/{res}')
        except LookupError:
            nltk.download(res, quiet=True)

setup_nltk()

# --- 1. TEXT PERTURBATION ---
def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'): return wordnet.ADJ
    elif treebank_tag.startswith('V'): return wordnet.VERB
    elif treebank_tag.startswith('N'): return wordnet.NOUN
    elif treebank_tag.startswith('R'): return wordnet.ADV
    return None

def calculate_entropy(text, level='word'):
    if not text: return 0.0
    elements = word_tokenize(text.lower()) if level == 'word' else list(text)
    probabilities = [count / len(elements) for element, count in Counter(elements).items()]
    return round(-sum(p * math.log2(p) for p in probabilities), 4)

def apply_text_perturbation(text, perturbation_rate=0.2):
    tokens = word_tokenize(text)
    tagged_tokens = pos_tag(tokens)
    perturbed_words = []
    
    for word, tag in tagged_tokens:
        if word.isalpha() and random.random() < perturbation_rate:
            wn_tag = get_wordnet_pos(tag)
            if wn_tag:
                synsets = wordnet.synsets(word, pos=wn_tag)
                if synsets:
                    lemmas = [l for s in synsets for l in s.lemma_names() if l.lower() != word.lower() and '_' not in l]
                    if lemmas:
                        chosen = random.choice(lemmas)
                        if word.istitle(): chosen = chosen.capitalize()
                        perturbed_words.append(chosen)
                        continue
        perturbed_words.append(word)
    return " ".join(perturbed_words).replace(" ,", ",").replace(" .", ".").replace(" !", "!")

# --- 2. IMAGE PERTURBATION ---
def apply_image_perturbation(image_path, output_path, quality_reduction=85):
    try:
        img = Image.open(image_path)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=quality_reduction)
        return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

# --- 3. AUDIO PERTURBATION ---
def apply_audio_perturbation(audio_path, output_path, target_bitrate="96k"):
    """
    Re-encoding audio destroys high-frequency and LSB steganography.
    """
    try:
        clip = AudioFileClip(audio_path)
        clip.write_audiofile(output_path, bitrate=target_bitrate, logger=None)
        return True
    except Exception as e:
        print(f"Error processing audio: {e}")
        return False

# --- 4. VIDEO PERTURBATION ---
def apply_video_perturbation(video_path, output_path, v_bitrate="1000k", a_bitrate="96k"):
    """
    Re-encoding video forces frame-recalculation and audio-resampling,
    destroying steganographic payloads across both visual and acoustic channels.
    """
    try:
        clip = VideoFileClip(video_path)
        clip.write_videofile(output_path, bitrate=v_bitrate, audio_bitrate=a_bitrate, logger=None)
        return True
    except Exception as e:
        print(f"Error processing video: {e}")
        return False

# --- MAIN CLI ---
def main():
    parser = argparse.ArgumentParser(description="AI Slop Steganography Defense Toolkit (Fully Multimodal)")
    parser.add_argument("--text", type=str, help="Analyze and sanitize text.")
    parser.add_argument("--image", type=str, help="Path to image for perturbation.")
    parser.add_argument("--audio", type=str, help="Path to audio file (e.g. .wav, .mp3) for perturbation.")
    parser.add_argument("--video", type=str, help="Path to video file (e.g. .mp4) for perturbation.")
    parser.add_argument("--rate", type=float, default=0.25, help="Synonym swap rate (Text only).")
    args = parser.parse_args()

    print("=== 🛡️ AI Slop Steganography Defense Toolkit (Fully Multimodal) ===\n")
    
    # 1. VIDEO MODUS
    if args.video:
        if not os.path.exists(args.video): return print(f"File not found: {args.video}")
        out_name = f"sanitized_{os.path.basename(args.video)}"
        print(f"[1] Video Mode: Processing '{args.video}'")
        print("[2] Applying Video & Audio Re-Encoding (breaking temporal & spatial steganography)...")
        if apply_video_perturbation(args.video, out_name):
            print(f"\n[✓] Sanitized video saved as: {out_name}")

    # 2. AUDIO MODUS
    elif args.audio:
        if not os.path.exists(args.audio): return print(f"File not found: {args.audio}")
        out_name = f"sanitized_{os.path.basename(args.audio)}"
        print(f"[1] Audio Mode: Processing '{args.audio}'")
        print("[2] Applying Audio Re-Encoding (breaking acoustic LSB steganography)...")
        if apply_audio_perturbation(args.audio, out_name):
            print(f"\n[✓] Sanitized audio saved as: {out_name}")

    # 3. IMAGE MODUS
    elif args.image:
        if not os.path.exists(args.image): return print(f"File not found: {args.image}")
        out_name = f"sanitized_{os.path.basename(args.image)}.jpg"
        print(f"[1] Image Mode: Processing '{args.image}'")
        print("[2] Applying Gaussian Blur & JPEG Compression (breaking visual LSB steganography)...")
        if apply_image_perturbation(args.image, out_name):
            print(f"\n[✓] Sanitized image saved as: {out_name}")
            
    # 4. TEXT MODUS (Standard)
    else:
        text = args.text if args.text else (
            "The quick implementation of advanced neural networks completely transforms "
            "digital landscapes. Technology rapidly evolves."
        )
        print("[1] Text Mode: Original Text:")
        print(text)
        print(f"\n[2] Entropy Analysis (Word-Level): {calculate_entropy(text, 'word')} bits/word")
        print(f"\n[3] Applying Semantic Perturbation (Rate: {args.rate * 100}%)...")
        sanitized_text = apply_text_perturbation(text, perturbation_rate=args.rate)
        print("\n[4] Sanitized Output Data:")
        print(sanitized_text)
        print("\n[✓] Fragile steganographic text channels have been disrupted.")

if __name__ == "__main__":
    main()
