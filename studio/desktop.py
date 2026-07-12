"""Alis Studio as a native desktop window (pywebview → WKWebView on macOS).

Same local server as the web app, but in its own native window — and dressed like a Mac app,
not a wrapped web page: the title bar is transparent and hidden, the content extends under the
traffic lights (NSFullSizeContentView), the top bar doubles as the window drag region, and a
minimal native View menu drives the app. The web UI detects pywebview and adapts (traffic-light
inset, no text-selection chrome, native context-menu behavior).
"""

from __future__ import annotations

import os

from . import __version__
from .server import start_http


_ABOUT_TARGET = None   # strong ref — ObjC menu targets are weakly referenced


def _app_icon():
    """The bundle icon at runtime: sys.executable lives in Contents/Resources/python/bin/."""
    import sys
    p = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", "AppIcon.icns"))
    if os.path.isfile(p):
        from AppKit import NSImage
        return NSImage.alloc().initWithContentsOfFile_(p)
    return None


def _fix_identity():
    """The process is the bundled python3, so the standard About panel (and dock icon) show the
    interpreter's identity, not the app's. Retarget the About item to a proper panel and set the
    dock icon explicitly. Main thread only."""
    global _ABOUT_TARGET
    from AppKit import NSApplication, NSObject
    icon = _app_icon()
    nsapp = NSApplication.sharedApplication()
    if icon is not None:
        nsapp.setApplicationIconImage_(icon)

    if _ABOUT_TARGET is None:   # the ObjC class may be defined only ONCE per process
        class _AlisAbout(NSObject):
            def showAbout_(self, sender):
                ic = _app_icon()
                opts = {"ApplicationName": "Alis Studio", "ApplicationVersion": __version__,
                        "Version": "", "Copyright": "MIT · github.com/avlp12/alis-studio"}
                if ic is not None:
                    opts["ApplicationIcon"] = ic
                NSApplication.sharedApplication().orderFrontStandardAboutPanelWithOptions_(opts)

        _ABOUT_TARGET = _AlisAbout.alloc().init()
    app_menu = nsapp.mainMenu().itemAtIndex_(0).submenu()
    for i in range(app_menu.numberOfItems()):
        it = app_menu.itemAtIndex_(i)
        if "about" in str(it.title() or "").lower():
            it.setTitle_("About Alis Studio")
            it.setTarget_(_ABOUT_TARGET)
            it.setAction_("showAbout:")
            break


def _nativize(window):
    """macOS: unified-toolbar window chrome. Best-effort — any failure leaves the stock window.
    NSWindow may only be mutated on the main thread; events.shown fires off it, so dispatch."""
    try:
        from PyObjCTools import AppHelper
        from webview.platforms.cocoa import BrowserView

        def apply():
            try:
                ns = BrowserView.instances[window.uid].window   # the NSWindow
                ns.setTitlebarAppearsTransparent_(True)
                ns.setTitleVisibility_(1)                        # hidden title (Mission Control keeps the name)
                ns.setStyleMask_(ns.styleMask() | (1 << 15))     # NSWindowStyleMaskFullSizeContentView
            except Exception as e:
                print(f"[alis] native titlebar styling skipped: {e!r}")
            def fix_id():
                try:
                    _fix_identity()
                except Exception as e:
                    print(f"[alis] app-identity fix skipped: {e!r}")
            fix_id()
            AppHelper.callLater(1.5, fix_id)   # pywebview may rebuild the menubar after shown — re-assert
            AppHelper.callLater(4.0, fix_id)

        AppHelper.callAfter(apply)
    except Exception as e:
        print(f"[alis] native titlebar styling unavailable: {e!r}")


def main():
    import webview
    import webview.menu as wm

    # bind a free loopback port (or honor ALIS_PORT) and run the server in a background thread
    port = int(os.environ.get("ALIS_PORT") or 0)
    server, port = start_http("127.0.0.1", port)
    window = webview.create_window(
        f"Alis Studio {__version__}", f"http://127.0.0.1:{port}/",
        width=1120, height=860, min_size=(840, 600),
    )
    window.events.shown += lambda: _nativize(window)

    def _js(code):
        try:
            window.evaluate_js(code)
        except Exception:
            pass

    menu = [
        wm.Menu("View", [
            wm.MenuAction("Toggle Gallery", lambda: _js("toggleGallery()")),
            wm.MenuAction("Edit an Image…", lambda: _js("document.querySelector('#editImgBtn')?.click()")),
            wm.MenuSeparator(),
            wm.MenuAction("Focus Prompt", lambda: _js("document.querySelector('#prompt')?.focus()")),
        ]),
    ]
    try:
        webview.start(menu=menu)  # runs the native UI loop on the main thread; blocks until close
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
