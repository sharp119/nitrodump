"""macOS Menu Bar Application for Nitrodump."""

import datetime
import rumps

from nitrodump.client import CodeiumClient
from nitrodump.menubar_manager import stop as stop_agent


def _noop(_):
    """No-op callback so macOS renders items with full contrast."""
    pass


class NitrodumpMenuBarApp(rumps.App):

    def __init__(self):
        super(NitrodumpMenuBarApp, self).__init__("⚡️ Nd", quit_button=None)
        self.client = CodeiumClient()

        self.user_item = rumps.MenuItem("👤  Loading...", callback=_noop)
        self.plan_item = rumps.MenuItem("💎  Loading...", callback=_noop)
        self.menu.add(self.user_item)
        self.menu.add(self.plan_item)
        self.menu.add(rumps.separator)

        self.dynamic_items = []
        self.quit_key = None

        self._fetch_and_update()

    def _on_quit(self, _):
        """Unload the launchd agent and quit the app."""
        try:
            stop_agent()
        except Exception:
            pass
        rumps.quit_application()

    # ── helpers ──────────────────────────────────

    def _bar(self, pct, w=8):
        f = round(pct / 100 * w)
        return "▓" * f + "░" * (w - f)

    def _relative(self, iso):
        try:
            dt = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            m = int((dt - now).total_seconds() / 60)
            if m < 0:
                return "now"
            if m < 60:
                return f"{m}m"
            h, r = divmod(m, 60)
            return f"{h}h {r}m" if r else f"{h}h"
        except Exception:
            return "—"

    def _absolute(self, iso):
        try:
            dt = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
            local = dt.astimezone()
            return local.strftime("%b %d, %H:%M")
        except Exception:
            return "—"

    def _short(self, label):
        m = {
            "Claude Opus 4.6 (Thinking)":   "Opus 4.6",
            "Claude Sonnet 4.6 (Thinking)": "Sonnet 4.6",
            "GPT-OSS 120B (Medium)":        "GPT-OSS 120B",
            "Gemini 3 Flash":               "3 Flash",
            "Gemini 3 Pro (High)":          "3 Pro ↑",
            "Gemini 3 Pro (Low)":           "3 Pro ↓",
            "Gemini 3.1 Pro (High)":        "3.1 Pro ↑",
            "Gemini 3.1 Pro (Low)":         "3.1 Pro ↓",
        }
        return m.get(label, label[:18])

    def _classify(self, label):
        if "Gemini" in label:
            return "Gemini"
        if "Claude" in label or "Opus" in label or "Sonnet" in label:
            return "Claude"
        return "Other"

    # ── dynamic menu ─────────────────────────────

    def _clear(self):
        for t in self.dynamic_items:
            try:
                del self.menu[t]
            except KeyError:
                pass
        self.dynamic_items.clear()
        # Also remove tracked quit button
        if self.quit_key:
            try:
                del self.menu[self.quit_key]
            except KeyError:
                pass
            self.quit_key = None

    def _add(self, title):
        self.menu.add(rumps.MenuItem(title, callback=_noop))
        self.dynamic_items.append(title)

    def _add_quit(self):
        """Add Quit at the very bottom."""
        key = "Quit"
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem(key, callback=self._on_quit))
        self.quit_key = key

    # ── fetch ────────────────────────────────────

    @rumps.timer(30)
    def _tick(self, _):
        self._fetch_and_update()

    def _fetch_and_update(self):
        try:
            resp = self.client.get_user_status()
            if not resp or not resp.user_status:
                self.user_item.title = "⚠️  Could not fetch"
                return

            s = resp.user_status
            plan = "Unknown"
            if s.plan_status and s.plan_status.plan_info:
                plan = s.plan_status.plan_info.plan_name
            self.user_item.title = f"👤  {s.name}"
            self.plan_item.title = f"💎  {plan}"

            self._clear()

            if not (s.cascade_model_config_data and s.cascade_model_config_data.client_model_configs):
                self._add("No models available")
                return

            # Group configs by provider
            groups = {}
            for c in s.cascade_model_config_data.client_model_configs:
                g = self._classify(c.label)
                groups.setdefault(g, []).append(c)

            order = ["Gemini", "Claude", "Other"]
            icons = {"Gemini": "☁️", "Claude": "🤖", "Other": "⚙️"}

            for g in order:
                if g not in groups:
                    continue
                models = groups[g]

                # Group header
                self._add(f"{icons.get(g, '')}  ── {g} ──")

                # Individual models with bar
                for c in models:
                    name = self._short(c.label)
                    pct = int(c.quota_info.remaining_fraction * 100)
                    bar = self._bar(pct)
                    self._add(f"  {name:<12} {bar} {pct}%")

                # Shared reset info (from first model in group)
                rep = models[0]
                abs_t = self._absolute(rep.quota_info.reset_time)
                rel_t = self._relative(rep.quota_info.reset_time)
                self._add(f"  {g} resets: {abs_t}")
                self._add(f"  {g} reset in: {rel_t}")

            self._add_quit()

        except Exception:
            self.user_item.title = "👤  —"
            self.plan_item.title = "⚠️  Offline"
            self._clear()
            self._add("  Language server unreachable")
            self._add_quit()


def run_menubar_app():
    app = NitrodumpMenuBarApp()
    app.run()
