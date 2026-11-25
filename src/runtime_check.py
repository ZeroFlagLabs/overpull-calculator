import sys,json,traceback
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtCore import QSize,QSettings,QEventLoop,QTimer
from PySide6.QtWidgets import QDialogButtonBox
from app_info import APP_VERSION
from calculator import calculate_overpull_force
def run(app,w):
    out=Path(sys.argv[sys.argv.index("--self-test-output")+1]) if "--self-test-output" in sys.argv else None
    report={}
    try:
        app.processEvents()
        assert (w.width(),w.height())==(320,369)
        assert not w.windowIcon().isNull()
        assert tuple(f.text() for f in w.fields)==("0","","0.000","0.000")
        assert w.result.text()=="-"
        assert all(f.size()==QSize(106,30) for f in w.fields) and w.reset.size()==QSize(106,30)
        for vals in (("75000","2/3","6.000","4.000"),("75000","1","6","0"),("75000","0.67","6","4")):
            for f,v in zip(w.fields,vals):f.setText(v)
            a,b,c,d=vals;factor=2/3 if b=="2/3" else float(b)
            assert w.result.text()==f"{calculate_overpull_force(float(a),factor,float(c),float(d)):,} lbf"
        w.id.setText("7");assert w.result.text()=="-"
        w.reset_fields();assert tuple(f.text() for f in w.fields)==("0","","0.000","0.000")
        with TemporaryDirectory() as t:
            w.update_checker.prefs=QSettings(str(Path(t)/"prefs.ini"),QSettings.Format.IniFormat)
            d=w.make_settings();d.show();app.processEvents()
            assert d.buttons.button(QDialogButtonBox.StandardButton.Close).size()==QSize(106,30)
            assert d.settings_tabs.count()==3
            assert d.current_version.text()=="Current version: v"+APP_VERSION
            assert "MIT Licence" in d.about_text.text()
            assert d.github_link.openExternalLinks()
            d.reject()
            if "--live-update-test" in sys.argv:
                loop=QEventLoop()
                w.update_checker.state_changed.connect(lambda:loop.quit() if w.update_checker._reply is None else None)
                w.update_checker.check();QTimer.singleShot(15000,loop.quit)
                if w.update_checker._reply is not None:loop.exec()
                report["live_update"]=w.update_checker.status
                assert w.update_checker.status in ("Up to date.","No published GitHub release found yet."),w.update_checker.status
        report["result"]="passed";return 0
    except Exception:
        report["result"]="failed";report["traceback"]=traceback.format_exc();return 1
    finally:
        if out:out.write_text(json.dumps(report,indent=2),encoding="utf8")
        print(json.dumps(report),flush=True);w.close()
