from __future__ import annotations

import time
from pathlib import Path

import config

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None


class LCDDisplay:
    """Large 7-inch screen display using the Linux framebuffer.

    This class intentionally keeps the old LCDDisplay interface so that main.py
    can still call lcd.show_lines([...]). Instead of an I2C character LCD, it
    renders large text to /dev/fb0.

    Run with sudo if /dev/fb0 permission is denied:
        sudo ./venv/bin/python main.py
    """

    def __init__(self):
        self.enabled = getattr(config, "LCD_ENABLED", True)
        self.fb_path = getattr(config, "SCREEN_FRAMEBUFFER", "/dev/fb0")
        self.tty_path = getattr(config, "SCREEN_FALLBACK_TTY", "/dev/tty1")
        self.header = getattr(config, "SCREEN_HEADER", "AIoT SMART RECYCLING")
        self.width, self.height = self._get_fb_size()
        self.bpp = self._get_bpp()
        self.console_only = False

        if not self.enabled or Image is None:
            print("[Display] PIL unavailable or display disabled. Console mode.")
            self.console_only = True
            return

        self.font_huge = self._load_font(max(88, int(self.height * 0.13)))
        self.font_big = self._load_font(max(56, int(self.height * 0.075)))
        self.font_mid = self._load_font(max(40, int(self.height * 0.052)))
        self.font_small = self._load_font(max(30, int(self.height * 0.035)))

        print(f"[Display] Using framebuffer {self.fb_path}: {self.width}x{self.height}, {self.bpp}bpp")

    def _get_fb_size(self) -> tuple[int, int]:
        try:
            raw = Path("/sys/class/graphics/fb0/virtual_size").read_text().strip()
            w, h = raw.split(",")
            return int(w), int(h)
        except Exception:
            return 800, 480

    def _get_bpp(self) -> int:
        try:
            return int(Path("/sys/class/graphics/fb0/bits_per_pixel").read_text().strip())
        except Exception:
            return 32

    def _load_font(self, size: int):
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
        for path in candidates:
            if Path(path).exists():
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    def _text_size(self, draw, text: str, font) -> tuple[int, int]:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _center_text(self, draw, text: str, y: int, font, fill=(255, 255, 255)) -> None:
        tw, _ = self._text_size(draw, text, font)
        x = max(0, (self.width - tw) // 2)
        draw.text((x, y), text, fill=fill, font=font)

    def _shorten(self, text: str, limit: int = 36) -> str:
        text = str(text)
        return text if len(text) <= limit else text[: limit - 3] + "..."

    def _classify_screen_state(self, lines: list[str]) -> tuple[str, str]:
        joined = " ".join(lines).lower()
        if "plastic" in joined or "bottle" in joined:
            return "[PLASTIC]", "PLASTIC"
        if "can" in joined:
            return "[CAN]", "CAN"
        if "paper" in joined:
            return "[PAPER]", "PAPER"
        if "full" in joined or "empty bin" in joined or "blocked" in joined:
            return "[FULL]", "FULL"
        if "low" in joined or "again" in joined or "retry" in joined:
            return "[RETRY]", "TRY AGAIN"
        if "ready" in joined or "waiting" in joined:
            return "[READY]", "READY"
        if "motion" in joined or "capturing" in joined:
            return "[SCAN]", "SCANNING"
        return "[INFO]", lines[0] if lines else "INFO"

    def _draw_lines(self, lines: list[str]):
        img = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        header_h = max(70, int(self.height * 0.10))
        draw.rectangle((0, 0, self.width, header_h), fill=(28, 28, 28))
        self._center_text(draw, self.header, int(header_h * 0.23), self.font_small)

        cleaned = [str(line) if line is not None else "" for line in lines]
        icon, main = self._classify_screen_state(cleaned)

        self._center_text(draw, icon, int(self.height * 0.17), self.font_big)
        self._center_text(draw, main.upper(), int(self.height * 0.29), self.font_huge)

        y = int(self.height * 0.56)
        line_gap = max(44, int(self.height * 0.065))
        for line in cleaned[:6]:
            line = line.strip()
            if not line:
                continue
            self._center_text(draw, self._shorten(line, 40), y, self.font_mid)
            y += line_gap

        return img

    def _write_framebuffer(self, img) -> None:
        if self.console_only:
            return

        try:
            if self.bpp == 32:
                data = img.convert("RGBA").tobytes("raw", "BGRA")
            elif self.bpp == 16:
                rgb = img.convert("RGB")
                pixels = rgb.load()
                buf = bytearray(self.width * self.height * 2)
                idx = 0
                for y in range(self.height):
                    for x in range(self.width):
                        r, g, b = pixels[x, y]
                        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                        buf[idx] = value & 0xFF
                        buf[idx + 1] = (value >> 8) & 0xFF
                        idx += 2
                data = bytes(buf)
            else:
                data = img.convert("RGB").tobytes()

            with open(self.fb_path, "wb") as fb:
                fb.write(data)

        except PermissionError:
            print(f"[Display] Permission denied for {self.fb_path}. Run with sudo.")
            self.console_only = True
        except Exception as exc:
            print(f"[Display] framebuffer write failed: {exc}")
            self.console_only = True

    def _write_tty_fallback(self, lines: list[str]) -> None:
        try:
            text = "\033c" + self.header + "\n" + "=" * len(self.header) + "\n\n" + "\n".join(lines) + "\n"
            with open(self.tty_path, "w") as tty:
                tty.write(text)
        except Exception:
            pass

    def show_lines(self, lines: list[str] | tuple[str, ...], hold: float = 0.0) -> None:
        cleaned = [str(line) if line is not None else "" for line in list(lines)]

        if self.console_only or Image is None:
            print("\n[SCREEN]")
            for line in cleaned:
                print(line)
            self._write_tty_fallback(cleaned)
            if hold > 0:
                time.sleep(hold)
            return

        img = self._draw_lines(cleaned)
        self._write_framebuffer(img)

        print("[SCREEN]")
        for line in cleaned:
            print(line)

        if hold > 0:
            time.sleep(hold)

    def clear(self) -> None:
        if Image is None:
            return
        img = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        self._write_framebuffer(img)

    def close(self) -> None:
        pass
