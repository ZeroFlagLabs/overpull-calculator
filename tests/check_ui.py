import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from main import *
from PySide6.QtTest import QTest
from PySide6.QtCore import QPoint,QTimer
app=make_app();w=Window();w.show();w.activateWindow();QTest.qWait(100)
assert w.result.text()=="-"
assert tuple(x.text() for x in w.fields)==("0","","0.000","0.000")
assert w.statusBar().height()==21
assert all(x.size()==QSize(106,30) for x in w.fields)
assert w.reset.size()==QSize(106,30)
results=next(g for g in w.findChildren(QGroupBox) if g.title()=="Results")
assert results.mapTo(w,QPoint(results.width(),0)).x()==w.reset.mapTo(w,QPoint(w.reset.width(),0)).x()

def fill(sy,f,od,id_):
    for field,v in zip(w.fields,(sy,f,od,id_)):field.setText(v)
fill("75000","2/3","6.000","4.000")
assert w.result.text()=="785,398 lbf",w.result.text()

fill("75000","0.67","6","4")
assert w.result.text()==f"{calculate_overpull_force(75000,.67,6,4):,} lbf"
fill("75000","1","6","0")
assert w.result.text()==f"{calculate_overpull_force(75000,1,6,0):,} lbf"
for values in [("0","1","6","0"),("75000","0","6","0"),("75000","2","6","0"),("75000","1/0","6","0"),("75000","1","0","0"),("75000","1","6","6"),("75000","1","6","7"),("75000","nan","6","0"),("75000","1","6","-1"),("75000","1","6","")]:
    fill(*values);assert w.result.text()=="-",values
fill("75000","2/3","6.125","0.000")
for s in (w.yield_strength,w.od,w.id):
    w.factor.setFocus();QTest.qWait(20)
    a=s.unit.mapTo(s,QPoint()).toTuple()
    QTest.mouseClick(s.lineEdit(),Qt.MouseButton.LeftButton,pos=QPoint(12,10));QTest.qWait(20)
    b=s.unit.mapTo(s,QPoint()).toTuple()
    print(s.accessibleName(),a,b)
    assert a==b
    s.lineEdit().selectAll();assert s.lineEdit().selectedText()==s.text()
w.od.clear();w.od.setFocus();QTest.keyClicks(w.od.lineEdit(),"6.123456")
assert w.od.text()=="6.123456",w.od.text()
QTest.keyClicks(w.od.lineEdit(),"7");assert w.od.text()=="6.123456"
w.od.setText("6");QTest.keyClick(w.od,Qt.Key.Key_Up);assert w.od.text()=="6.001"
QTest.keyClick(w.od,Qt.Key.Key_Down);assert w.od.text()=="6.000"
fill("1000000000","1","1000000000","0")
print("maximum",w.result.text(),w.result.fontMetrics().horizontalAdvance(w.result.text()),w.result.width())
assert w.result.fontMetrics().horizontalAdvance(w.result.text())<=w.result.width()

w.reset_fields();assert tuple(x.text() for x in w.fields)==("0","","0.000","0.000") and w.result.text()=="-" and w.statusBar().currentMessage()=="Ready"
d=w.make_settings();d.show();QTest.qWait(50);assert d.settings_tabs.count()==3
assert d.check_now_button.isEnabled()
d.reject();d.deleteLater();QTest.qWait(30)
print("Window",w.width(),w.height())
w.close();print("PASS: engineering results, validation, focus stability, numeric precision, arrows, maximum result, reset and Settings")
