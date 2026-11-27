"""Overpull Calculator; original calculation engine preserved."""
from status_bar import CenteredStatusBar
from pathlib import Path
import sys,math
from decimal import Decimal
from PySide6.QtCore import QTimer,QUrl,Qt,QSize,QRegularExpression,QFile,QIODevice,Signal,QSignalBlocker
from PySide6.QtGui import QDesktopServices,QIcon,QRegularExpressionValidator,QShortcut,QKeySequence,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QLabel,QLineEdit,QGroupBox,QVBoxLayout,QHBoxLayout,QGridLayout,QPushButton,QAbstractSpinBox,QDialogButtonBox,QStatusBar,QStyle,QStyleOptionFrame)
from PySide6.QtUiTools import QUiLoader
from dialog_position import exec_centered
from dialog_theme import apply_dialog_theme, ensure_light_scheme, set_settings_identity
from calculator import calculate_overpull_force
HERE=Path(__file__).resolve().parent
from app_info import APP_TITLE,APP_VERSION,GITHUB_URL
from update_checker import UpdateChecker
TITLE=APP_TITLE
VERSION="v"+APP_VERSION
ICONS=HERE/"resources/icons"
STYLE = """
QWidget#surface, QDialog {background:#f3f7fb;color:#1b3452;font-family:'Segoe UI';font-size:12px;}
QLabel {color:#174675;font-weight:normal;}
QLabel#title {color:#123b7c;font-size:19px;font-weight:700;}
QLabel#version, QLabel#muted {color:#6c7e94;font-size:11px;}
QLabel#column {color:#667c94;font-size:11px;font-weight:600;}
QLabel#result {color:#123b7c;font-size:18px;font-weight:700;}
QLabel:disabled {color:#8190b2;}
QGroupBox {background:#ffffff;border:1px solid #d8e4f0;border-radius:6px;margin-top:13px;padding:5px 7px 5px;font-weight:600;color:#174675;}
QGroupBox::title {subcontrol-origin:margin;subcontrol-position:top left;left:10px;top:2px;padding:0 4px;color:#164f8a;}
QAbstractSpinBox {background:white;border:1px solid #b9cce1;border-radius:4px;padding:1px 18px 1px 4px;color:#243d58;}
QAbstractSpinBox QLineEdit {background:transparent;border:0;color:#243d58;selection-background-color:#258aca;}
QAbstractSpinBox:focus {border:2px solid #258aca;padding:0 17px 0 3px;}
QAbstractSpinBox:disabled {background:#e3e8ee;color:#8190b2;border-color:#c4cdd8;}
QAbstractSpinBox:disabled QLineEdit {color:#8190b2;}
QAbstractSpinBox::up-button,QAbstractSpinBox::down-button {subcontrol-origin:border;width:14px;background:transparent;border:none;right:4px;}
QAbstractSpinBox::up-button {subcontrol-position:top right;top:2px;}
QAbstractSpinBox::down-button {subcontrol-position:bottom right;bottom:2px;}
QAbstractSpinBox::up-arrow {image:url(@ICONS@/spin-chevron-up.png);width:12px;height:8px;}
QAbstractSpinBox::down-arrow {image:url(@ICONS@/spin-chevron-down.png);width:12px;height:8px;}
QAbstractSpinBox::up-arrow:disabled {image:url(@ICONS@/spin-chevron-up-disabled.png);}
QAbstractSpinBox::down-arrow:disabled {image:url(@ICONS@/spin-chevron-down-disabled.png);}
QLineEdit#factor {background:white;border:1px solid #b9cce1;border-radius:4px;padding:1px 4px;color:#243d58;}
QLineEdit#factor:focus {border:2px solid #258aca;padding:0 3px;}
QRadioButton {color:#1b3452;spacing:5px;}
QPushButton {background:#eaf3fc;color:#144b83;border:1px solid #9ebfe2;border-radius:5px;min-height:24px;padding:2px 8px;font-weight:600;}
QPushButton:hover {background:#d9ecff;}
QPushButton:pressed {background:#c6def7;}
QPushButton#gear {background:transparent;border:1px solid transparent;padding:0;min-height:0;}
QPushButton#gear:hover {background:#e5f1fc;border-color:#bfd4e9;}
QTabWidget::pane {background:white;border:1px solid #d8e4f0;}
QTabBar::tab {padding:6px 10px;background:#eaf3fc;border:1px solid #d8e4f0;}
QTabBar::tab:selected {background:white;color:#164f8a;}
""".replace("@ICONS@",ICONS.as_posix())
def label(text,name=""):
    w=QLabel(text)
    if name:w.setObjectName(name)
    return w

class NumericSpin(QAbstractSpinBox):
    textChanged=Signal(str)
    def __init__(self,unit,step):
        super().__init__()
        self.maximum=1e9
        self.step=step
        self.minimum_decimals=3 if unit=="in" else 0
        self.setFixedSize(106,30)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        e=self.lineEdit()
        self.unit=QLabel(" "+unit,e)
        self.unit.setStyleSheet("color:#243d58;background:transparent;border:0;padding:0;")
        self.unit.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.unit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        e.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]{0,10}(?:\.[0-9]{0,6})?"),self))
        self.position_unit()
        e.textChanged.connect(self.position_unit)
        e.cursorPositionChanged.connect(self.position_unit)
        e.textChanged.connect(self.textChanged)
        self.setKeyboardTracking(True)
    def position_unit(self,*_):
        e=self.lineEdit();self.unit.setFont(e.font());fm=e.fontMetrics()
        self.unit.adjustSize()
        reserve=self.unit.width()+2
        if e.textMargins().left()!=4 or e.textMargins().right()!=reserve:
            e.setTextMargins(4,0,reserve,0)
        opt=QStyleOptionFrame();e.initStyleOption(opt)
        area=e.style().subElementRect(QStyle.SubElement.SE_LineEditContents,opt,e)
        left=area.left()+4
        right=area.right()-self.unit.width()-1
        end=left+2+fm.horizontalAdvance(e.text())
        if end>right:
            caret=e.inputMethodQuery(Qt.InputMethodQuery.ImCursorRectangle)
            end=caret.x()+caret.width()//2+fm.horizontalAdvance(e.text()[e.cursorPosition():])
        self.unit.move(min(max(left,end),right),(e.height()-self.unit.height())//2)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,"unit"):self.position_unit()
    def focusInEvent(self,event):
        super().focusInEvent(event);self.position_unit()
    def focusOutEvent(self,event):
        super().focusOutEvent(event);self.position_unit()
    def setText(self,t):self.lineEdit().setText(str(t))
    def clear(self):self.lineEdit().clear()
    def number(self):
        t=self.text().strip()
        if not t:return None
        if not self.lineEdit().hasAcceptableInput():raise ValueError
        n=float(t)
        if not math.isfinite(n) or not 0<=n<=self.maximum:raise ValueError
        return n
    def stepEnabled(self):
        try:n=self.number()
        except ValueError:n=None
        f=QAbstractSpinBox.StepEnabledFlag.StepNone
        if n is None or n<self.maximum:f|=QAbstractSpinBox.StepEnabledFlag.StepUpEnabled
        if n is not None and n>0:f|=QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
        return f
    def stepBy(self,steps):
        try:n=self.number()
        except ValueError:n=None
        n=max(Decimal(0),min(Decimal(str(self.maximum)),Decimal(str(n or 0))+steps*Decimal(str(self.step))))
        t=format(n,".6f").rstrip("0").rstrip(".")
        if self.minimum_decimals:
            a,_,b=t.partition(".");t=a+"."+b.ljust(self.minimum_decimals,"0")
        self.setText(t)
    def wheelEvent(self,event):event.ignore()

def group(title):
    g=QGroupBox(title);l=QVBoxLayout(g);l.setContentsMargins(8,7,8,7);l.setSpacing(5)
    return g,l

def parse_factor(t):
    t=t.strip()
    if not t:return None
    parts=t.split("/")
    if len(parts)==1:v=float(parts[0])
    elif len(parts)==2:v=float(parts[0])/float(parts[1])
    else:raise ValueError
    if not math.isfinite(v) or not 0<v<=1:raise ValueError
    return v

class Window(QMainWindow):
    def __init__(self):
        ensure_light_scheme()
        super().__init__()
        self.update_checker=UpdateChecker(self)
        self.setWindowTitle(TITLE)
        self.setWindowIcon(QIcon(str(ICONS/"icon.ico")))
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint,False)
        surface=QWidget(objectName="surface");surface.setStyleSheet(STYLE);self.setCentralWidget(surface)
        root=QVBoxLayout(surface);root.setContentsMargins(10,8,10,8);root.setSpacing(6)
        h=QHBoxLayout();h.addWidget(label(TITLE,"title"));h.addStretch();h.addWidget(label(VERSION,"version"))
        self.gear=QPushButton(objectName="gear");self.gear.setIcon(QIcon(str(ICONS/"settings-gear.png")));self.gear.setIconSize(QSize(18,18));self.gear.setFixedSize(28,28);self.gear.setToolTip("Settings (Ctrl+,)");self.gear.setFocusPolicy(Qt.FocusPolicy.NoFocus);self.gear.clicked.connect(self.settings);h.addWidget(self.gear);root.addLayout(h)
        g,l=group("Inputs");grid=QGridLayout();grid.setHorizontalSpacing(10);grid.setVerticalSpacing(5)
        self.yield_strength=NumericSpin("psi",1000)
        self.factor=QLineEdit(objectName="factor");self.factor.setFixedSize(106,30);self.factor.setTextMargins(4,0,0,0);self.factor.setPlaceholderText("e.g. 2/3");self.factor.setMaxLength(40)
        self.factor.setToolTip("Allowable fraction of yield strength, greater than zero and no greater than 1. Enter a decimal or fraction.")
        self.od=NumericSpin("in",0.001);self.id=NumericSpin("in",0.001)
        self.fields=[self.yield_strength,self.factor,self.od,self.id]
        for i,(name,field) in enumerate(zip(("Material yield strength","Design factor","Outer diameter (min)","Inner diameter (max)"),self.fields)):
            lab=label(name);lab.setBuddy(field);field.setAccessibleName(name);grid.addWidget(lab,i,0);grid.addWidget(field,i,1)
            field.textChanged.connect(self.calculate)
        grid.setColumnStretch(0,1);l.addLayout(grid);root.addWidget(g)
        g,l=group("Results");l.addWidget(label("Maximum overpull"))
        self.result=label("-","result");self.result.setAlignment(Qt.AlignmentFlag.AlignRight);self.result.setMinimumWidth(0)
        from PySide6.QtWidgets import QSizePolicy
        self.result.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
        l.addWidget(self.result);root.addWidget(g)
        h=QHBoxLayout();h.addStretch();self.reset=QPushButton("Reset");self.reset.setFixedSize(106,30);self.reset.clicked.connect(self.reset_fields);h.addWidget(self.reset);root.addLayout(h)
        self.setStatusBar(CenteredStatusBar(self))
        self.status=self.statusBar()
        self.reset.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for a,b in zip(self.fields,self.fields[1:]):QWidget.setTabOrder(a,b)
        QWidget.setTabOrder(self.id,self.yield_strength)
        self.shortcuts=[QShortcut(QKeySequence("Ctrl+R"),self,activated=self.reset_fields),QShortcut(QKeySequence("Ctrl+,"),self,activated=self.settings)]
        self.reset_fields()
        self.adjustSize();self.setFixedSize(self.sizeHint().expandedTo(QSize(320,0)))
        self.yield_strength.setFocus()
    def reset_fields(self):
        blockers=[QSignalBlocker(f) for f in self.fields]
        for f,v in zip(self.fields,("0","","0.000","0.000")):f.setText(v)
        del blockers
        self.calculate();self.yield_strength.setFocus()
    def calculate(self,*_):
        if not hasattr(self,"result"):return
        self.result.setStyleSheet("")
        self.result.setText("-")
        names=["Material yield strength","Design factor","Outer diameter (min)","Inner diameter (max)"]
        values=[]
        for name,field in zip(names,self.fields):
            try:v=parse_factor(field.text()) if field is self.factor else field.number()
            except (ValueError,ZeroDivisionError,OverflowError):
                self.status.showMessage("Invalid "+name.lower()+".");return
            values.append(v)
        sy,f,od,id_=values
        if sy==0 and f is None and od==0 and id_==0:self.status.showMessage("Ready");return
        if sy is not None and sy<=0:self.status.showMessage("Enter positive yield strength.");return
        if od is not None and od<=0:self.status.showMessage("Enter positive outer diameter.");return
        if od is not None and id_ is not None and id_>=od:self.status.showMessage("Inner diameter must be less than outer.");return
        if any(v is None for v in values):self.status.showMessage("Enter all four inputs.");return
        result=calculate_overpull_force(sy,f,od,id_)
        self.result.setText(f"{result:,} lbf")
        # Retain the full rounded integer even for legacy extreme input values.
        size=18
        while size>9:
            font=QFont(self.result.font());font.setPixelSize(size);font.setBold(True)
            from PySide6.QtGui import QFontMetrics
            if QFontMetrics(font).horizontalAdvance(self.result.text())<=self.result.width()-2:break
            size-=1
        if size!=18:self.result.setStyleSheet(f"font-size:{size}px;")
        self.status.showMessage("Calculated")
    def make_settings(self):
        f=QFile(str(HERE/"ui/settings_dialog.ui"))
        if not f.open(QIODevice.OpenModeFlag.ReadOnly):raise RuntimeError("Settings form missing")
        try:d=QUiLoader().load(f,self)
        finally:f.close()
        d.setWindowIcon(self.windowIcon());d.resize(526,500)
        d.setStyleSheet("""
            QPushButton {background:#eaf3fc;color:#144b83;border:1px solid #9ebfe2;border-radius:5px;min-height:24px;padding:2px 8px;font-weight:600;}
            QPushButton:disabled {color:#8795a5;background:#eff2f5;}
            QTabWidget::pane {background:white;border:1px solid #e7e7e7;border-radius:4px;}
            QTabBar::tab {background:#f1f1f1;border:1px solid #e5e5e5;padding:4px 11px;color:#344556;}
            QTabBar::tab:selected {background:white;color:#1b3452;border-bottom-color:white;}
        """)
        d.setWindowModality(Qt.WindowModality.ApplicationModal)
        d.buttons.button(QDialogButtonBox.StandardButton.Close).setFixedSize(106,30)
        d.buttons.rejected.connect(d.reject)
        checker=self.update_checker
        d.check_on_launch.setChecked(checker.enabled())
        d.check_on_launch.toggled.connect(checker.set_enabled)
        d.check_now_button.clicked.connect(checker.check)
        set_settings_identity(d, APP_TITLE, APP_VERSION, 'Estimates the allowable axial overpull of a uniform annular cross-section.')
        d.github_link.setText(f'<a href="{GITHUB_URL}">Project on GitHub</a>')
        d.github_link.setOpenExternalLinks(True)
        def refresh():
            d.update_status.setText(checker.status)
            d.check_now_button.setEnabled(checker._reply is None)
            d.open_release_button.setEnabled(checker.release_url is not None)
        def open_release():
            if checker.release_url:QDesktopServices.openUrl(QUrl(checker.release_url))
        def disconnect(*_):
            try:checker.state_changed.disconnect(refresh)
            except (RuntimeError,TypeError):pass
        d.open_release_button.clicked.connect(open_release)
        checker.state_changed.connect(refresh);d.finished.connect(disconnect);refresh()
        apply_dialog_theme(d)
        return d
    def settings(self):
        d=self.make_settings()
        try:exec_centered(d,self)
        finally:d.deleteLater()

def make_app():
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setWindowIcon(QIcon(str(ICONS/"icon.ico")));return app

if __name__=="__main__":
    app=make_app()
    if "--dialogue-test" in sys.argv:
        from dialogue_acceptance import prepare_scheme
        prepare_scheme(app)
    w=Window();w.show()
    if "--dialogue-test" in sys.argv:
        from dialogue_acceptance import run_for_window
        sys.exit(run_for_window(app,w))
    if "--self-test" in sys.argv:
        from runtime_check import run
        sys.exit(run(app,w))
    QTimer.singleShot(0,w.update_checker.check_on_launch)
    sys.exit(app.exec())
