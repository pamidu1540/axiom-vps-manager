"""
Axiom QR Code Generator Service
Generates terminal ASCII QR codes and exports QR images for WireGuard, VLESS, and Hysteria2.
"""

import subprocess


class QRCodeGenerator:
    @staticmethod
    def generate_terminal_qr(data: str) -> str:
        """Attempts to render a QR code in terminal using qrencode or fallback text."""
        try:
            p = subprocess.Popen(
                ["qrencode", "-t", "ANSIUTF8", data], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, _ = p.communicate()
            if p.returncode == 0:
                return stdout
        except Exception:
            pass
        return f"[QR Code Data]:\n{data}"

    @staticmethod
    def export_png(data: str, output_path: str) -> bool:
        """Exports QR code image to a PNG file."""
        try:
            subprocess.run(
                ["qrencode", "-o", output_path, data], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False
