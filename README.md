# Covert Channel & Synthetic Media Detector

**An open-source proof-of-concept toolkit for detecting steganographic payloads and covert AI-to-AI communication in synthetic visual media.**

This repository accompanies the position paper:  
**"Synthetic Media as Covert Infrastructure: A Position on Defending Open AI Ecosystems from Decentralized Misalignment Risks"**  
by Michael Hackl and Leander Kühnel (February 2026).

## Purpose

The detector serves as a practical demonstration that hidden structures in AI-generated content can already be identified with current techniques. It combines statistical noise analysis with semantic validation to provide empirical support for the paper’s proposed mitigation strategies.

## Live Demo
Test the detector here: [https://covert-channel-detector.netlify.app/](https://covert-channel-detector.netlify.app/)

## Technical Features

- RGB channel isolation (focused on Blue channel LSB)
- High-Pass Residual Filtering using 3×3 Laplacian kernel
- Spatial Transition Rate Analysis (bit-flip probability)
- Semantic "Smoking Gun" validation:
  - Magic byte detection (PDF, ZIP, PNG, JPEG signatures)
  - Real-time Base64 decoding to readable text
  - JSON structure recognition

## Installation & Local Deployment

```bash
git clone https://github.com/oisxeng/covert-channel-defense.git
cd covert-channel-defense
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000
