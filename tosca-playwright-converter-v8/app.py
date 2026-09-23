import gzip
import io
import json
import re
import zipfile
from dataclasses import dataclass
from typing import Any

import streamlit as st

st.set_page_config(page_title="PwC | Tosca → Playwright Converter", page_icon="🔄", layout="wide", initial_sidebar_state="expanded")

# PwC-inspired product UI: charcoal navigation, warm orange actions, white
# workspace and restrained neutral surfaces. Conversion logic is unaffected.
st.markdown(r"""
<style>
:root{--pwc-orange:#E84A18;--pwc-dark:#202428;--pwc-text:#172033;--pwc-muted:#68758A;--pwc-border:#D9DEE6;--pwc-soft:#F7F8FA;}
.stApp{background:#fff;color:var(--pwc-text);} header[data-testid="stHeader"]{background:#fff;border-bottom:1px solid #EEF0F3;}
.block-container{max-width:none;padding:0 3.8rem 2.4rem 3.8rem;}
section[data-testid="stSidebar"]{background:linear-gradient(145deg,#202428 0%,#292D31 70%,#1F2327 100%);border-right:0;min-width:255px;}
section[data-testid="stSidebar"]>div:first-child{padding:0;}
.pwc-brand{height:145px;padding:1.1rem 1.8rem 0;}.pwc-logo{display:flex;flex-direction:column;align-items:flex-start}.pwc-logo-symbol{position:relative;width:72px;height:55px;margin-left:18px}.pwc-logo-symbol span{position:absolute;display:block}.pwc-logo-symbol .b1{width:25px;height:11px;left:27px;top:0;background:#F6A623}.pwc-logo-symbol .b2{width:22px;height:11px;left:41px;top:10px;background:#F68B1F}.pwc-logo-symbol .b3{width:25px;height:11px;left:31px;top:20px;background:#F15A24}.pwc-logo-symbol .b4{width:24px;height:11px;left:15px;top:21px;background:#E84A18}.pwc-logo-symbol .b5{width:18px;height:11px;left:4px;top:31px;background:#D83B14}.pwc-logo-symbol .b6{width:28px;height:11px;left:25px;top:31px;background:#F6A623}.pwc-mark{color:#fff;font-family:Georgia,serif;font-size:2.35rem;font-weight:700;letter-spacing:-2px;line-height:1;margin-top:-2px}.pwc-nav-item{color:#F4F5F6;padding:.78rem 1.3rem;margin:.18rem .8rem;border-radius:6px;font-size:1rem}.pwc-nav-active{background:linear-gradient(90deg,#F04B22,#F05A24);font-weight:700}.pwc-sidebar-footer{position:absolute;bottom:1.5rem;left:1.8rem;right:1.8rem;color:#fff;font-family:Georgia,serif;font-size:1rem;border-top:1px solid #4C5157;padding-top:1rem;line-height:1.15}.pwc-sidebar-footer:before{content:"";display:block;width:42px;height:4px;background:#F6A623;margin-bottom:1rem}
.pwc-topbar{height:58px;margin:0 -3.8rem;padding:0 2.2rem;border-bottom:1px solid #E9ECF0;display:flex;align-items:center;justify-content:space-between;color:#2C3440;font-size:.86rem;background:#fff}.pwc-top-right{display:flex;align-items:center;gap:1rem;color:#5E6A7D}.pwc-env{display:flex;align-items:center;gap:.7rem;padding-right:1rem;border-right:1px solid #E5E7EB}.pwc-env-pill{border:1px solid #DCE1E7;border-radius:8px;padding:.45rem .75rem;color:#283242;background:#fff}.pwc-user{display:flex;align-items:center;gap:.65rem;color:#303744}.pwc-avatar{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#FCE5D9;color:#E84A18;font-weight:700}
.pwc-header{position:relative;margin:2rem 0 1.35rem}.pwc-title{color:#142033;font-size:2.2rem;font-weight:750;letter-spacing:-.7px;margin:0}.pwc-subtitle{color:#5D6C80;font-size:1rem;line-height:1.35;max-width:970px;margin-top:.35rem}.pwc-rule{height:4px;width:40px;background:var(--pwc-orange);margin-top:.8rem}.pwc-hero-art{position:absolute;right:-3.8rem;top:-2rem;width:240px;height:165px;overflow:hidden;pointer-events:none}.pwc-hero-art span{position:absolute;display:block;transform:skewX(-35deg)}.pwc-hero-art .a1{width:105px;height:45px;right:105px;top:0;background:#F8D7A4}.pwc-hero-art .a2{width:110px;height:48px;right:38px;top:0;background:#F59A00}.pwc-hero-art .a3{width:75px;height:80px;right:-8px;top:0;background:#C83B0C}.pwc-hero-art .a4{width:95px;height:58px;right:48px;top:45px;background:#E84A18}.pwc-hero-caption{position:absolute;right:150px;top:78px;width:205px;color:#26303D;font-size:1rem;line-height:1.15}.pwc-hero-caption:before{content:"";display:block;width:38px;height:4px;background:var(--pwc-orange);margin-bottom:.75rem}
.pwc-panel{border:1px solid #DDE2E8;border-radius:9px;background:#fff;padding:1.25rem 1.25rem 1.15rem;box-shadow:0 2px 9px rgba(23,32,51,.035)}.pwc-panel-title{font-size:1.65rem;font-weight:700;color:#20252D;margin-bottom:.2rem}.pwc-panel-sub{font-size:.92rem;color:#7A8493;margin-bottom:1rem}.pwc-upload-card{border:1px solid #DDE2E8;border-radius:10px;background:#fff;padding:1rem;min-height:345px;position:relative}.pwc-upload-head{display:flex;gap:.85rem;align-items:center;margin-bottom:.9rem}.pwc-file-icon{width:78px;height:78px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.9rem;font-weight:800}.pwc-json-icon{background:#FDE6DF;color:#E8441A}.pwc-tsu-icon{background:#FFF0D9;color:#6A4B16}.pwc-upload-title{font-size:1.18rem;font-weight:700;color:#162033}.pwc-upload-desc{font-size:.9rem;color:#778396;margin-top:.15rem}
div[data-testid="stFileUploader"]{background:#fff!important;border:0!important;box-shadow:none!important;padding:0!important;margin:0!important}div[data-testid="stFileUploader"]>label{display:none!important}div[data-testid="stFileUploaderDropzone"]{min-height:220px!important;background:#FCFDFE!important;border:1.5px dashed #CDD5DF!important;border-radius:8px!important;box-shadow:none!important}div[data-testid="stFileUploaderDropzoneInstructions"]{color:#5F6D80!important}div[data-testid="stFileUploaderDropzoneInstructions"] svg{color:#667386!important;width:48px!important;height:48px!important}div[data-testid="stFileUploaderDropzone"] button{background:#fff!important;color:#E84A18!important;border:1.5px solid #E84A18!important;border-radius:7px!important;font-weight:700!important;padding:.48rem 1.8rem!important}div[data-testid="stFileUploaderDropzone"] button:hover{background:#FFF4EF!important}div[data-testid="stFileUploaderFile"]{background:#F7F8FA!important;border-radius:7px!important}
.pwc-ready{display:flex;align-items:center;justify-content:space-between;background:#F7F8FA;border-radius:7px;padding:.6rem .85rem;margin-top:.55rem;color:#667386;font-size:.86rem}.pwc-ready-left{display:flex;align-items:center;gap:.55rem;color:#179A63;font-weight:600}.pwc-check{width:24px;height:24px;border-radius:50%;background:#22A06B;color:#fff;display:flex;align-items:center;justify-content:center;font-size:.8rem}.pwc-language{margin-top:.95rem;margin-bottom:.4rem;color:#243042;font-size:.9rem;font-weight:600}div[role="radiogroup"]{gap:1.1rem!important}div[role="radiogroup"] label{color:#253043!important}
.stButton>button[kind="primary"]{background:linear-gradient(90deg,#F04A1C,#F15A24)!important;border:0!important;color:#fff!important;font-size:1rem!important;font-weight:700!important;height:50px!important;border-radius:6px!important;box-shadow:0 2px 5px rgba(232,74,24,.18)}.stButton>button[kind="primary"]:hover{background:#D94318!important}
.pwc-info-strip{margin-top:1rem;border:1px solid #DCE3EB;border-radius:9px;background:#fff;display:grid;grid-template-columns:1fr 1fr 1fr;overflow:hidden}.pwc-info-item{padding:1rem 1.25rem;display:flex;gap:.8rem;align-items:flex-start}.pwc-info-item+.pwc-info-item{border-left:1px solid #DCE3EB}.pwc-info-icon{color:#E84A18;font-size:1.8rem;line-height:1}.pwc-info-title{font-weight:700;color:#1D2736;font-size:.92rem}.pwc-info-text{color:#7A8493;font-size:.76rem;line-height:1.35;margin-top:.25rem}div[data-testid="stAlert"]{border-radius:8px}[data-testid="stCodeBlock"]{border-left:4px solid var(--pwc-orange);border-radius:5px}[data-testid="stDataFrame"]{border:1px solid #DDE2E8;border-radius:7px}h2,h3{color:var(--pwc-dark)!important}
</style>
""", unsafe_allow_html=True)

st.markdown(r"""<style>
/* V6.1 UI corrections: visual-only, no conversion logic changes */
section[data-testid="stSidebar"]{min-width:255px!important;max-width:255px!important;}
.pwc-brand{height:155px!important;padding-top:1.0rem!important;}
.pwc-nav-item{display:block!important;box-sizing:border-box!important;height:50px!important;line-height:34px!important;margin:.2rem .75rem!important;padding:.48rem 1.15rem!important;font-size:1rem!important;}
.pwc-sidebar-footer{position:fixed!important;left:1.8rem!important;bottom:1.5rem!important;width:185px!important;right:auto!important;font-size:.98rem!important;line-height:1.15!important;z-index:10!important;}
.pwc-header{margin:1.25rem 0 1.2rem!important;min-height:170px!important;position:relative!important;z-index:1!important;isolation:isolate!important;}
.pwc-title{font-size:2.05rem!important;position:relative!important;z-index:9999!important;display:block!important;visibility:visible!important;opacity:1!important;color:#142033!important;background:transparent!important;width:max-content!important;max-width:calc(100% - 320px)!important;}
.pwc-subtitle{max-width:900px!important;font-size:.98rem!important;}
.pwc-hero-art{right:0!important;top:-.4rem!important;width:300px!important;height:155px!important;z-index:0!important;}
.pwc-hero-caption{right:155px!important;top:76px!important;width:140px!important;font-size:.93rem!important;}
/* No artificial empty panel / spacer */
.pwc-panel-title{margin-top:.2rem!important;}
.pwc-upload-head{min-height:86px!important;margin-bottom:.65rem!important;}
.pwc-file-icon{width:78px!important;height:78px!important;flex:0 0 78px!important;}
div[data-testid="stFileUploaderDropzone"]{min-height:220px!important;}
.pwc-info-strip{margin-top:1rem!important;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div class="pwc-brand">
      <div class="pwc-logo" aria-label="PwC">
        <div class="pwc-logo-symbol">
          <span class="b1"></span><span class="b2"></span><span class="b3"></span>
          <span class="b4"></span><span class="b5"></span><span class="b6"></span>
        </div>
        <div class="pwc-mark">pwc</div>
      </div>
    </div>
    <div class="pwc-nav-item pwc-nav-active">⌂ &nbsp;&nbsp; Home</div>
    <div class="pwc-nav-item">⇄ &nbsp;&nbsp; Convert</div>
    <div class="pwc-nav-item">◷ &nbsp;&nbsp; History</div>
    <div class="pwc-nav-item">⚙ &nbsp;&nbsp; Settings</div>
    <div class="pwc-nav-item">? &nbsp;&nbsp; Help</div>
    <div class="pwc-sidebar-footer">Build trust<br>in a changing<br>world</div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="
  display:block !important;
  visibility:visible !important;
  opacity:1 !important;
  color:#142033 !important;
  font-family:Arial,Helvetica,sans-serif !important;
  font-size:2.05rem !important;
  font-weight:750 !important;
  line-height:1.2 !important;
  letter-spacing:-.7px !important;
  margin:1.25rem 0 1rem 0 !important;
  padding:0 !important;
  position:relative !important;
  z-index:999999 !important;">
  Tosca → Playwright Converter
</div>
""", unsafe_allow_html=True)


@dataclass
class ModuleControl:
    name: str
    business_type: str = ""
    engine: str = ""
    tag: str = ""
    technical_id: str = ""
    module_surrogate: str = ""
    properties: dict[str, str] | None = None

def clean(v):
    return "" if v is None else str(v).strip()

def parse_tsu(uploaded_bytes: bytes):
    """Parse Tosca .tsu. Tosca subset exports may be gzip-compressed JSON."""
    raw = uploaded_bytes

    # 1) Tosca .tsu seen in the provided file: gzip-compressed JSON
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)

    # 2) Also tolerate ZIP containers
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            candidates = [n for n in z.namelist() if n.lower().endswith((".json", ".xml", ".tsu"))]
            if not candidates:
                raise ValueError("No JSON/XML content found inside TSU archive.")
            raw = z.read(candidates[0])
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)

    text = raw.decode("utf-8-sig", errors="strict")
    data = json.loads(text)

    entities = data.get("Entities", [])
    by_id = {clean(e.get("Surrogate")): e for e in entities}
    controls: dict[str, list[ModuleControl]] = {}

    # Actual Tosca export structure:
    # XModuleAttribute -> Assocs.Properties -> XParam(Name/Value)
    for entity in entities:
        if entity.get("ObjectClass") != "XModuleAttribute":
            continue

        attrs = entity.get("Attributes", {})
        name = clean(attrs.get("Name"))
        if not name:
            continue

        props = {}
        for prop_id in entity.get("Assocs", {}).get("Properties", []):
            p = by_id.get(clean(prop_id))
            if not p or p.get("ObjectClass") != "XParam":
                continue
            pa = p.get("Attributes", {})
            props[clean(pa.get("Name")).lower()] = clean(pa.get("Value"))

        control = ModuleControl(
            name=name,
            business_type=clean(attrs.get("BusinessType")),
            engine=props.get("engine", ""),
            tag=props.get("tag", ""),
            technical_id=props.get("id", ""),
            module_surrogate=clean(entity.get("Surrogate")),
            properties=props,
        )
        controls.setdefault(name.lower(), []).append(control)

    if not controls:
        raise ValueError("No XModuleAttribute controls were found in the TSU export.")

    return controls, len(entities)

def _extract_test_value(line):
    """Read the test-step value from common Tosca JSON export column names.

    Different Tosca exports can put the value in different columns. The old
    converter only read unnamed_1, which can be empty for a SELECT/ComboBox
    even though the selected value (for example Suzuki) is present elsewhere
    in the row.
    """
    preferred = [
        "unnamed_1", "value", "Value", "ValueString", "valueString",
        "InputValue", "inputValue", "TestValue", "testValue",
        "ActionValue", "actionValue", "SelectedValue", "selectedValue",
        "StringValue", "stringValue"
    ]
    for key in preferred:
        if key in line and line.get(key) not in (None, ""):
            return line.get(key)

    # Last resort: find a non-empty scalar column other than element/action
    # columns. This is deliberately conservative so we don't use metadata.
    ignored = {
        "unnamed_0", "unnamed_2", "unnamed_3", "unnamed_4",
        "element", "name", "action", "Action", "Control", "control"
    }
    for key, val in line.items():
        if key in ignored or val in (None, "") or isinstance(val, (dict, list)):
            continue
        if isinstance(val, (str, int, float, bool)):
            text = clean(val)
            if text and text.lower() not in {"input", "select", "verify", "click", "x"}:
                return val
    return ""


def get_test_steps(data):
    pages = data.get("Document", {}).get("Pages", [])
    steps = []
    section = "General"

    for page in pages:
        for table in page.get("Tables", []):
            label = table.get("Label", "")
            for line in table.get("BodyLines", []):
                if label == "ExecutionTestStepLog":
                    section = clean(line.get("unnamed_0")) or section
                    msg = clean(line.get("unnamed_1"))
                    m = re.search(r"https?://[^\s]+", msg)
                    if m:
                        steps.append({"action": "navigate", "element": "", "value": m.group(0), "section": section})

                elif label == "ExecutionTestStepValueLog":
                    element = clean(line.get("unnamed_0"))
                    value = _extract_test_value(line)
                    action = clean(line.get("unnamed_2")).lower()
                    if not element:
                        continue

                    if action == "verify":
                        mapped = "verify"
                    elif action == "select":
                        mapped = "select"
                    elif action == "input" and clean(value).lower() == "x":
                        mapped = "click"
                    elif action == "input" and isinstance(value, bool):
                        mapped = "check" if value else "uncheck"
                    elif action == "input":
                        mapped = "input"
                    else:
                        mapped = action or "unknown"

                    # Keep the original row so SELECT handling can recover a
                    # selected value if this Tosca export stored it in another
                    # column.
                    steps.append({"action": mapped, "element": element, "value": value,
                                  "section": section, "raw": line})
    return steps

def _prop(c: ModuleControl, *names: str) -> str:
    props = c.properties or {}
    for name in names:
        v = clean(props.get(name.lower(), ""))
        if v:
            return v
    return ""


def _bool_prop(c: ModuleControl, *names: str) -> bool | None:
    v = _prop(c, *names).lower()
    if v in {"true", "yes", "1", "y"}:
        return True
    if v in {"false", "no", "0", "n"}:
        return False
    return None


def _exact_options(c: ModuleControl, element: str) -> str:
    exact = _bool_prop(c, "exact", "exactmatch", "exact match")
    return f", exact: {str(exact).lower()}" if exact is not None else ""


def _display_name(c: ModuleControl, element: str) -> str:
    # Tosca Text is the strongest semantic name when present; otherwise use the
    # test-step element name. Do not use the selected dropdown value as the control name.
    return _prop(c, "text", "label", "aria-label", "accessible name") or element


def _locator_name(c: ModuleControl, element: str) -> str:
    return json.dumps(_display_name(c, element))


def _technical_locator(c: ModuleControl):
    """Tosca technical locator priority: ID first, then Class."""
    if c.technical_id:
        return f"page.locator({json.dumps('#' + c.technical_id)})", f"technical ID: #{c.technical_id}"

    class_value = _prop(c, "class", "classname", "class name", "cssclass")
    if class_value:
        classes = [x for x in re.split(r"\s+", class_value.strip()) if x]
        if classes:
            selector = "".join(f"[class~={json.dumps(cls)}]" for cls in classes)
            return f"page.locator({json.dumps(selector)})", f"technical class: {class_value}"
    return None, ""



def _module_path(c: ModuleControl | None) -> str:
    if not c:
        return ""
    return _prop(c, "nodepath", "node path", "path")


def _is_table_control(c: ModuleControl | None) -> bool:
    if not c:
        return False
    bt = c.business_type.strip().lower()
    tag = c.tag.upper()
    # Only an actual TABLE control starts table context. Do not classify
    # TableRow/TableCell/TableColumn children as the table itself.
    return tag == "TABLE" or bt in {"table", "datatable", "data table"}


def _is_descendant_of(child: ModuleControl | None, parent: ModuleControl | None) -> bool:
    """Use Tosca NodePath when available to determine table hierarchy.

    This is a preferred signal only. Table execution mapping must still work
    when a row/cell does not carry a usable NodePath in the module export.
    """
    child_path = _module_path(child).rstrip("/")
    parent_path = _module_path(parent).rstrip("/")
    if not child_path or not parent_path or child is parent:
        return False
    return child_path.startswith(parent_path + "/")


def _table_locator(c: ModuleControl) -> tuple[str, str]:
    """Build the table locator from the TABLE module's own technical properties."""
    technical_loc, technical_reason = _technical_locator(c)
    if technical_loc:
        return technical_loc, f"table {technical_reason}"
    name = _locator_name(c, c.name)
    exact = _exact_options(c, c.name)
    return f"page.getByRole('table', {{ name: {name}{exact} }})", "table role"


def _table_cell_locator(table_loc: str, row_name: str, column_name: str) -> str:
    """Scope a table cell to the JSON row and column.

    The table locator comes only from the module technical properties. The row
    and column names come from the Test Case JSON sequence.
    """
    row = f"{table_loc}.locator('tr', {{ hasText: {json.dumps(row_name)} }})"
    return f"{row}.locator('td[data-label={json.dumps(column_name)}]')"


def _table_control_locator(table_loc: str, control: ModuleControl | None,
                           element: str, value: Any = "") -> str:
    """Locate an actual interactive control inside a table.

    Prefer the module technical ID/class, scoped to the table. For radio/select
    controls where the JSON supplies the selected value, use that value as a
    stable table-scoped attribute when possible.
    """
    if control:
        bt = control.business_type.lower()
        tag = control.tag.upper()
        # A radio group such as Options -> Ultimate is best addressed by the
        # actual radio value from the Test Case JSON, scoped to this table.
        if ("radio" in bt or "radiobutton" in bt or tag == "RADIO") and value not in (None, ""):
            return f"{table_loc}.locator('input[type=\"radio\"][value={json.dumps(str(value))}]')"
        technical_loc, _ = _technical_locator(control)
        if technical_loc and technical_loc.startswith("page.locator("):
            selector = technical_loc[len("page.locator("):-1]
            return f"{table_loc}.locator({selector})"
    return f"{table_loc}.getByText({json.dumps(element)})"


def _is_interactive_table_control(c: ModuleControl | None) -> bool:
    if not c:
        return False
    bt = c.business_type.lower()
    tag = c.tag.upper()
    return any(x in bt for x in ("radio", "checkbox", "button", "textbox", "combobox", "dropdown", "listbox")) \
        or tag in {"INPUT", "SELECT", "BUTTON", "TEXTAREA", "RADIO", "CHECKBOX"}


def choose_locator(c: ModuleControl | None, element: str, action: str = ""):
    if not c:
        return f"page.getByText({json.dumps(element)})", "UNRESOLVED — module control not found", "generic"

    bt = c.business_type.lower()
    tag = c.tag.upper()
    exact = _exact_options(c, element)
    name = _locator_name(c, element)
    technical_loc, technical_reason = _technical_locator(c)

    # Keep the existing SELECT/dropdown handling. Only the locator priority is
    # changed: Tosca ID > Tosca Class > semantic Playwright locator.
    if tag == "TABLE" or "table" in bt:
        if technical_loc:
            return technical_loc, f"table {technical_reason}", "table"
        return f"page.getByRole('table', {{ name: {name}{exact} }})", "role=table", "table"

    if tag == "SELECT" or "select" in bt or ("dropdown" in bt and "combo" not in bt):
        if technical_loc:
            return technical_loc, f"native-select {technical_reason}", "native_select"
        return f"page.getByRole('combobox', {{ name: {name}{exact} }})", "native-select role=combobox", "native_select"

    if "combo" in bt or "dropdown" in bt or "listbox" in bt:
        if technical_loc:
            return technical_loc, f"custom-dropdown {technical_reason}", "custom_dropdown"
        return f"page.getByRole('combobox', {{ name: {name}{exact} }})", "custom-dropdown role=combobox", "custom_dropdown"

    # Checkbox/radio controls should use their accessible label, even when
    # Tosca also provides an ID/class. This keeps the generated Playwright
    # locator aligned with the control label, e.g. getByLabel('Male').
    if "checkbox" in bt or tag == "CHECKBOX":
        return f"page.getByLabel({name}{exact})", "role=label checkbox", "checkbox"
    if "radio" in bt or "radiobutton" in bt or tag == "RADIO":
        return f"page.getByLabel({name}{exact})", "role=label radio", "radio"

    # For every other control, preserve Tosca's ID/class when available.
    if technical_loc:
        kind = "generic"
        if "button" in bt or tag == "BUTTON":
            kind = "button"
        elif "link" in bt or tag == "A":
            kind = "link"
        elif "textbox" in bt or tag in {"INPUT", "TEXTAREA"}:
            kind = "textbox"
        return technical_loc, technical_reason, kind

    if "button" in bt or tag == "BUTTON":
        return f"page.getByRole('button', {{ name: {name}{exact} }})", "role=button", "button"
    if "link" in bt or tag == "A":
        return f"page.getByRole('link', {{ name: {name}{exact} }})", "role=link", "link"
    if "checkbox" in bt:
        return f"page.getByLabel({name}{exact})", "role=label checkbox", "checkbox"
    if "radio" in bt or "radiobutton" in bt:
        return f"page.getByLabel({name}{exact})", "role=label radio", "radio"
    if "textbox" in bt or tag in {"INPUT", "TEXTAREA"}:
        return f"page.getByRole('textbox', {{ name: {name}{exact} }})", "role=textbox", "textbox"

    return f"page.getByText({name}{exact})", "fallback=text", "generic"

def resolve_control(controls: dict[str, list[ModuleControl]], element: str):
    candidates = controls.get(element.lower(), [])
    if not candidates:
        return None, "UNRESOLVED — module control not found"
    if len(candidates) == 1:
        return candidates[0], ""

    # Tosca exports can contain the same module control more than once (for example
    # the same SELECT/ComboBox may appear in multiple exported module references).
    # If all duplicates describe the same technical control, collapse them instead
    # of incorrectly marking the test step as AMBIGUOUS.
    signatures = {
        (
            c.technical_id.strip().lower(),
            c.tag.strip().lower(),
            c.business_type.strip().lower(),
            c.engine.strip().lower(),
        )
        for c in candidates
    }
    if len(signatures) == 1:
        return candidates[0], ""

    # Prefer a candidate whose Tosca Text/Label matches the test-step element exactly.
    exact_matches = []
    for c in candidates:
        txt = _prop(c, "text", "label", "aria-label", "accessible name")
        if txt and txt.strip().lower() == element.strip().lower():
            exact_matches.append(c)
    if len(exact_matches) == 1:
        return exact_matches[0], ""

    # If candidates really differ, do not silently choose one.
    details = ", ".join(
        f"id={c.technical_id or '-'} tag={c.tag or '-'} type={c.business_type or '-'}"
        for c in candidates
    )
    return None, f"AMBIGUOUS — {len(candidates)} Tosca controls named '{element}': {details}"

def _select_value_for_step(step, control):
    """Return the actual option selected by a Tosca SELECT control.

    Tosca can export a SELECT row with action=Input and an empty primary value.
    In that case inspect the original row for another value column. Never use
    the control name (Make) or the module ValueRange as the selected option.
    """
    value = step.get("value")
    if value not in (None, ""):
        return value

    raw = step.get("raw") or {}
    value = _extract_test_value(raw)
    if value not in (None, ""):
        return value

    return ""


def dynamic_date(value):
    if not isinstance(value, str):
        return None
    m = re.match(r"^\{DATE\[.*?\]\[([+-]?\d+)([MYDmyd])\]\[(.+)\]\}$", value)
    if not m:
        return None
    unit = {"d": "day", "m": "month", "y": "year"}[m.group(2).lower()]
    fmt = m.group(3).replace("''", "'")
    return int(m.group(1)), unit, fmt


def _python_locator(c: ModuleControl | None, element: str, action: str = ""):
    """Python equivalent of the existing TypeScript locator strategy.

    This mirrors the current BusinessType rules; it does not alter the
    TypeScript generator or Tosca mapping behavior.
    """
    if not c:
        return f"page.get_by_text({json.dumps(element)})", "UNRESOLVED — module control not found", "generic"

    bt = c.business_type.lower()
    tag = c.tag.upper()
    exact = _bool_prop(c, "exact", "exactmatch", "exact match")
    name = json.dumps(_display_name(c, element))

    if c.technical_id:
        technical_loc = f"page.locator({json.dumps('#' + c.technical_id)})"
        technical_reason = f"technical ID: #{c.technical_id}"
    else:
        class_value = _prop(c, "class", "classname", "class name", "cssclass")
        if class_value:
            classes = [x for x in re.split(r"\s+", class_value.strip()) if x]
            selector = "".join(f"[class~={json.dumps(cls)}]" for cls in classes)
            technical_loc = f"page.locator({json.dumps(selector)})"
            technical_reason = f"technical class: {class_value}"
        else:
            technical_loc = None
            technical_reason = ""

    exact_py = f", exact=True" if exact is True else (", exact=False" if exact is False else "")

    if tag == "TABLE" or "table" in bt:
        if technical_loc:
            return technical_loc, f"table {technical_reason}", "table"
        return f"page.get_by_role('table', name={name}{exact_py})", "role=table", "table"

    if tag == "SELECT" or "select" in bt or ("dropdown" in bt and "combo" not in bt):
        if technical_loc:
            return technical_loc, f"native-select {technical_reason}", "native_select"
        return f"page.get_by_role('combobox', name={name}{exact_py})", "native-select role=combobox", "native_select"

    if "combo" in bt or "dropdown" in bt or "listbox" in bt:
        if technical_loc:
            return technical_loc, f"custom-dropdown {technical_reason}", "custom_dropdown"
        return f"page.get_by_role('combobox', name={name}{exact_py})", "custom-dropdown role=combobox", "custom_dropdown"

    if "checkbox" in bt or tag == "CHECKBOX":
        return f"page.get_by_label({name}{exact_py})", "role=label checkbox", "checkbox"
    if "radio" in bt or "radiobutton" in bt or tag == "RADIO":
        return f"page.get_by_label({name}{exact_py})", "role=label radio", "radio"

    if technical_loc:
        kind = "generic"
        if "button" in bt or tag == "BUTTON": kind = "button"
        elif "link" in bt or tag == "A": kind = "link"
        elif "textbox" in bt or tag in {"INPUT", "TEXTAREA"}: kind = "textbox"
        return technical_loc, technical_reason, kind

    if "button" in bt or tag == "BUTTON":
        return f"page.get_by_role('button', name={name}{exact_py})", "role=button", "button"
    if "link" in bt or tag == "A":
        return f"page.get_by_role('link', name={name}{exact_py})", "role=link", "link"
    if "textbox" in bt or tag in {"INPUT", "TEXTAREA"}:
        return f"page.get_by_role('textbox', name={name}{exact_py})", "role=textbox", "textbox"
    return f"page.get_by_text({name}{exact_py})", "fallback=text", "generic"


def _python_table_locator(c: ModuleControl) -> tuple[str, str]:
    # _python_locator returns (locator, reason, kind). For table context we
    # only need the locator and reason; keep the existing mapping logic intact.
    technical_loc, technical_reason, _ = _python_locator(c, c.name)
    if technical_loc:
        return technical_loc, f"table {technical_reason}"
    return f"page.get_by_role('table', name={json.dumps(_display_name(c, c.name))})", "table role"


def _python_table_cell_locator(table_loc: str, row_name: str, column_name: str) -> str:
    row = f"{table_loc}.locator('tr', has_text={json.dumps(row_name)})"
    return f"{row}.locator('td[data-label={json.dumps(column_name)}]')"


def _python_table_control_locator(table_loc: str, control: ModuleControl | None, element: str, value: Any = "") -> str:
    if control:
        bt = control.business_type.lower()
        tag = control.tag.upper()
        if ("radio" in bt or "radiobutton" in bt or tag == "RADIO") and value not in (None, ""):
            return f"{table_loc}.locator('input[type=\"radio\"][value={json.dumps(str(value))}]')"
        if control.technical_id:
            return f"{table_loc}.locator({json.dumps('#' + control.technical_id)})"
        class_value = _prop(control, "class", "classname", "class name", "cssclass")
        if class_value:
            classes = [x for x in re.split(r"\s+", class_value.strip()) if x]
            selector = "".join(f"[class~={json.dumps(cls)}]" for cls in classes)
            return f"{table_loc}.locator({json.dumps(selector)})"
    return f"{table_loc}.get_by_text({json.dumps(element)})"


def generate_python(test_data, controls):
    """Generate Playwright Python using the same mapping decisions as V4 TS."""
    steps = get_test_steps(test_data)
    lines = [
        "import re",
        "from playwright.sync_api import Page, expect",
        "",
        "def test_tosca_migrated(page: Page):",
        ""
    ]
    report = []
    current_table = None
    current_table_loc = None
    current_row_name = None
    current_table_section = None

    for s in steps:
        action, element, value = s["action"], s["element"], s["value"]
        section = s.get("section", "")
        if action == "navigate":
            current_table = current_table_loc = current_row_name = current_table_section = None
            lines.append(f"    page.goto({json.dumps(str(value))})")
            report.append({"Element": value, "Action": "navigate", "Locator": "URL"})
            lines.append("")
            continue

        if current_table is not None and current_table_section != section:
            current_table = current_table_loc = current_row_name = current_table_section = None

        control, resolve_reason = resolve_control(controls, element)
        if _is_table_control(control):
            current_table = control
            current_table_loc, table_reason = _python_table_locator(control)
            current_row_name = None
            current_table_section = section
            report.append({"Element": element, "Action": "table-context", "Locator": table_reason})
            continue

        effective_action = action
        if control and control.tag.upper() == "SELECT" and action == "input":
            effective_action = "select"

        if current_table is not None and current_row_name is None:
            current_row_name = element
            report.append({"Element": element, "Action": "table-row-context", "Locator": f"table={current_table.name}; row={element}"})
            continue

        is_descendant = current_table is not None and _is_descendant_of(control, current_table)
        is_interactive = _is_interactive_table_control(control)
        if current_table is not None and control is not None and is_descendant and ("row" in control.business_type.lower() or control.tag.upper() == "TR"):
            current_row_name = element
            report.append({"Element": element, "Action": "table-row-context", "Locator": f"table={current_table.name}; row={element}"})
            continue

        leave_table = current_table is not None and ((control is not None and not is_descendant and effective_action == "click") or (control is None and effective_action == "verify" and isinstance(value, bool)))
        if leave_table:
            current_table = current_table_loc = current_row_name = current_table_section = None
            table_active = False
        else:
            table_active = current_table is not None and current_table_loc is not None

        is_table_interactive = table_active and ((is_descendant and is_interactive) or (is_interactive and effective_action in {"input","check","uncheck","select"}))
        if table_active and is_table_interactive:
            loc = _python_table_control_locator(current_table_loc, control, element, value)
            locator_reason = f"table={current_table.name}; control={element}"
            control_kind = "table_control"
            if control and ("radio" in control.business_type.lower() or control.tag.upper() == "RADIO") and effective_action == "input":
                effective_action = "check"
        elif table_active and current_row_name is not None:
            loc = _python_table_cell_locator(current_table_loc, current_row_name, element)
            locator_reason = f"table={current_table.name}; row={current_row_name}; column={element}"
            control_kind = "table_cell"
        else:
            loc, locator_reason, control_kind = _python_locator(control, element, effective_action)

        reason = locator_reason if control_kind in {"table_cell","table_control"} else (resolve_reason or locator_reason)
        report.append({"Element": element, "Action": effective_action, "Locator": reason})
        if "UNRESOLVED" in reason or "AMBIGUOUS" in reason:
            lines.append(f"    # TODO: {reason}")

        if effective_action == "click":
            lines.append(f"    {loc}.click()")
        elif effective_action == "input":
            d = dynamic_date(value)
            if d:
                amount, unit, fmt = d
                lines.append(f"    # TODO: Tosca dynamic date: {amount} {unit}(s), format {fmt}")
                lines.append(f"    {loc}.fill(\"\")")
            else:
                lines.append(f"    {loc}.fill({json.dumps(str(value))})")
        elif effective_action == "select":
            select_value = _select_value_for_step(s, control)
            if control_kind == "native_select":
                if select_value not in (None, ""):
                    lines.append(f"    {loc}.select_option({json.dumps(str(select_value))})")
                else:
                    lines.append("    # TODO: SELECT control found, but selected option value is empty in the Test Case export.")
            elif control_kind == "custom_dropdown":
                option_name = json.dumps(str(select_value))
                lines.append(f"    {loc}.click()")
                lines.append(f"    page.get_by_role('option', name={option_name}).click()")
            elif control_kind == "table_control":
                if control and ("radio" in control.business_type.lower() or control.tag.upper() == "RADIO"):
                    lines.append(f"    {loc}.check(force=True)")
                else:
                    lines.append(f"    {loc}.click()")
            elif control_kind == "table_cell":
                lines.append(f"    {loc}.click()")
            else:
                lines.append(f"    # TODO: dropdown type could not be determined; select '{str(select_value)}' manually")
                lines.append(f"    {loc}.click()")
                lines.append(f"    page.get_by_role('option', name={json.dumps(str(select_value))}, exact=True).click()")
        elif effective_action == "check":
            lines.append(f"    {loc}.check(force=True)" if control_kind == "table_control" else f"    {loc}.check()")
        elif effective_action == "uncheck":
            lines.append(f"    {loc}.uncheck(force=True)" if control_kind == "table_control" else f"    {loc}.uncheck()")
        elif effective_action == "verify":
            lines.append(f"    expect({loc}).to_have_text({json.dumps(str(value))})")
        else:
            lines.append(f"    # TODO: unsupported Tosca action '{effective_action}' on '{element}'")
        lines.append("")

    return "\n".join(lines), report, steps

def generate(test_data, controls):
    steps = get_test_steps(test_data)
    lines = [
        "import { test, expect } from '@playwright/test';",
        "",
        "test('Tosca migrated test', async ({ page }) => {",
        ""
    ]
    report = []
    current_table = None
    current_table_loc = None
    current_row_name = None
    current_table_section = None

    for s in steps:
        action, element, value = s["action"], s["element"], s["value"]
        section = s.get("section", "")

        if action == "navigate":
            current_table = None
            current_table_loc = None
            current_row_name = None
            current_table_section = None
            lines.append(f"  await page.goto({json.dumps(str(value))});")
            report.append({"Element": value, "Action": "navigate", "Locator": "URL"})
            lines.append("")
            continue

        # A Tosca execution section is a reliable boundary for table context.
        # The Price Option JSON section, for example, contains priceTable,
        # Price per Year ($), Silver/Gold/Platinum/Ultimate and Options.
        if current_table is not None and current_table_section != section:
            current_table = None
            current_table_loc = None
            current_row_name = None
            current_table_section = None

        control, resolve_reason = resolve_control(controls, element)

        # TABLE START -------------------------------------------------------
        # The table name comes from the Test Case JSON (e.g. priceTable), but
        # the actual locator comes ONLY from the matching TABLE module's ID or
        # class. Never generate #priceTable merely because the JSON says so.
        if _is_table_control(control):
            current_table = control
            current_table_loc, table_reason = _table_locator(control)
            current_row_name = None
            current_table_section = section
            report.append({
                "Element": element,
                "Action": "table-context",
                "Locator": table_reason,
            })
            continue

        # If the JSON table name did not resolve by exact name, do not invent a
        # CSS selector from the JSON. We only enter table mode from a real TABLE
        # module control. This preserves the existing non-table behavior.
        effective_action = action
        if control and control.tag.upper() == "SELECT" and action == "input":
            effective_action = "select"

        # TABLE ROW ---------------------------------------------------------
        # The first execution item after the TABLE marker is the row name from
        # the JSON. It is context, not a browser action. This intentionally does
        # not require the row to resolve as an independent ModuleControl.
        if current_table is not None and current_row_name is None:
            current_row_name = element
            report.append({
                "Element": element,
                "Action": "table-row-context",
                "Locator": f"table={current_table.name}; row={element}",
            })
            continue

        # TABLE CONTENT -----------------------------------------------------
        is_descendant = current_table is not None and _is_descendant_of(control, current_table)
        is_interactive = _is_interactive_table_control(control)

        # If Tosca explicitly exposes another table-row node, allow a new row
        # context. Otherwise the JSON sequence keeps the current row name.
        if (current_table is not None and control is not None and is_descendant
                and ("row" in control.business_type.lower() or control.tag.upper() == "TR")):
            current_row_name = element
            report.append({
                "Element": element,
                "Action": "table-row-context",
                "Locator": f"table={current_table.name}; row={element}",
            })
            continue

        # A known control with a click action and no table hierarchy is a
        # section/page control (for example Next »), not a table cell. A boolean
        # Verify immediately after a table radio/control is also normally a
        # separate page control (View Quote / Download Quote in the sample JSON).
        leave_table = (
            current_table is not None
            and ((control is not None and not is_descendant and effective_action == "click")
                 or (control is None and effective_action == "verify" and isinstance(value, bool)))
        )
        if leave_table:
            current_table = None
            current_table_loc = None
            current_row_name = None
            current_table_section = None
            table_active = False
        else:
            table_active = current_table is not None and current_table_loc is not None

        is_table_interactive = table_active and (
            (is_descendant and is_interactive) or
            (is_interactive and effective_action in {"input", "check", "uncheck", "select"})
        )

        if table_active and is_table_interactive:
            loc = _table_control_locator(current_table_loc, control, element, value)
            locator_reason = f"table={current_table.name}; control={element}"
            control_kind = "table_control"
            if control and ("radio" in control.business_type.lower() or control.tag.upper() == "RADIO") and effective_action == "input":
                effective_action = "check"

        elif table_active and current_row_name is not None:
            # For Verify rows such as:
            #   Price per Year ($) -> Silver -> 103.00 -> Verify
            # the row and column are taken directly from the JSON sequence.
            # The table locator itself still comes from the Module.
            loc = _table_cell_locator(current_table_loc, current_row_name, element)
            locator_reason = f"table={current_table.name}; row={current_row_name}; column={element}"
            control_kind = "table_cell"

        else:
            loc, locator_reason, control_kind = choose_locator(control, element, effective_action)

        # Once table mapping succeeds, do not carry an unresolved module-name
        # warning into the report: row/column mapping intentionally comes from
        # the Test Case JSON.
        if control_kind in {"table_cell", "table_control"}:
            reason = locator_reason
        else:
            reason = resolve_reason or locator_reason
        report.append({"Element": element, "Action": effective_action, "Locator": reason})

        if "UNRESOLVED" in reason or "AMBIGUOUS" in reason:
            lines.append(f"  // TODO: {reason}")

        if effective_action == "click":
            lines.append(f"  await {loc}.click();")
        elif effective_action == "input":
            d = dynamic_date(value)
            if d:
                amount, unit, fmt = d
                lines.append(f"  // TODO: Tosca dynamic date: {amount} {unit}(s), format {fmt}")
                lines.append(f"  await {loc}.fill('');")
            else:
                lines.append(f"  await {loc}.fill({json.dumps(str(value))});")
        elif effective_action == "select":
            # Existing dropdown logic is intentionally unchanged.
            select_value = _select_value_for_step(s, control)
            if control_kind == "native_select":
                if select_value not in (None, ""):
                    lines.append(f"  await {loc}.selectOption({json.dumps(str(select_value))});")
                else:
                    lines.append("  // TODO: SELECT control found, but the selected option value is empty in the Test Case export.")
            elif control_kind == "custom_dropdown":
                exact = _exact_options(control, element) if control else ""
                option_name = json.dumps(str(select_value))
                lines.append(f"  await {loc}.click();")
                lines.append(f"  await page.getByRole('option', {{ name: {option_name}{exact} }}).click();")
            elif control_kind == "table_control":
                # Table radio/select controls are scoped by _table_control_locator.
                if control and ("radio" in control.business_type.lower() or control.tag.upper() == "RADIO"):
                    lines.append(f"  await {loc}.check({{ force: true }});")
                else:
                    lines.append(f"  await {loc}.click();")
            elif control_kind == "table_cell":
                lines.append(f"  await {loc}.click();")
            else:
                lines.append(f"  // TODO: dropdown type could not be determined; select '{str(select_value)}' manually")
                lines.append(f"  await {loc}.click();")
                lines.append(f"  await page.getByRole('option', {{ name: {json.dumps(str(select_value))}, exact: true }}).click();")
        elif effective_action == "check":
            lines.append(f"  await {loc}.check({{ force: true }});") if control_kind == "table_control" else lines.append(f"  await {loc}.check();")
        elif effective_action == "uncheck":
            lines.append(f"  await {loc}.uncheck({{ force: true }});") if control_kind == "table_control" else lines.append(f"  await {loc}.uncheck();")
        elif effective_action == "verify":
            lines.append(f"  await expect({loc}).toHaveText({json.dumps(str(value))});")
        else:
            lines.append(f"  // TODO: unsupported Tosca action '{effective_action}' on '{element}'")
        lines.append("")

    lines.append("});")
    return "\n".join(lines), report, steps

st.markdown('<div class="pwc-panel-title">Conversion inputs</div>', unsafe_allow_html=True)
st.markdown('<div class="pwc-panel-sub">Provide the Tosca execution JSON and the exported Modules .tsu. The converter keeps module technical properties as the source of truth for locators.</div>', unsafe_allow_html=True)

upload_col1, upload_col2 = st.columns(2, gap="large")
with upload_col1:
    st.markdown('<div class="pwc-upload-head"><div class="pwc-file-icon pwc-json-icon">▤</div><div><div class="pwc-upload-title">Tosca Test Case JSON</div><div class="pwc-upload-desc">Upload the Tosca execution JSON file</div></div></div>', unsafe_allow_html=True)
    test_file = st.file_uploader("Tosca Test Case JSON", type=["json"], key="test_json")
with upload_col2:
    st.markdown('<div class="pwc-upload-head"><div class="pwc-file-icon pwc-tsu-icon">TSU</div><div><div class="pwc-upload-title">Tosca Modules export (.tsu)</div><div class="pwc-upload-desc">Upload the exported Tosca Modules file</div></div></div>', unsafe_allow_html=True)
    module_file = st.file_uploader("Tosca Modules export (.tsu)", type=["tsu"], key="modules_tsu")

st.markdown('<div class="pwc-language">Target language</div>', unsafe_allow_html=True)
lang_col, _ = st.columns([1.6, 2.4])
with lang_col:
    target_language = st.radio("Target language", ["TypeScript", "Python"], horizontal=True, key="target_language", label_visibility="collapsed")

st.markdown('<div style="height:.45rem"></div>', unsafe_allow_html=True)
convert_clicked = st.button("✨  Convert to Playwright  →", type="primary", use_container_width=True)
st.markdown("""<div class="pwc-info-strip"><div class="pwc-info-item"><div class="pwc-info-icon">⚙</div><div><div class="pwc-info-title">What happens next?</div><div class="pwc-info-text">The converter processes the input files, reads module technical properties, and generates Playwright test scripts with locators and best practices.</div></div></div><div class="pwc-info-item"><div class="pwc-info-icon">▤</div><div><div class="pwc-info-title">Output</div><div class="pwc-info-text">Download Playwright test files (.spec.ts or .py) with page objects, locators and test data mapping.</div></div></div><div class="pwc-info-item"><div class="pwc-info-icon">♡</div><div><div class="pwc-info-title">Your data stays secure</div><div class="pwc-info-text">Files are processed within PwC's secure environment and are not stored permanently.</div></div></div></div>""", unsafe_allow_html=True)
if convert_clicked:
    if not (test_file and module_file):
        st.error("Please upload both the Tosca Test Case JSON and the Tosca Modules .tsu file.")
    else:
        try:
            test_data = json.load(test_file)
            controls, entity_count = parse_tsu(module_file.read())
            if target_language == "Python":
                code, report, steps = generate_python(test_data, controls)
                code_language = "python"
                file_name = "test_tosca_migration.py"
                download_label = "⬇️ Download test_tosca_migration.py"
            else:
                code, report, steps = generate(test_data, controls)
                code_language = "typescript"
                file_name = "playwright.spec.ts"
                download_label = "⬇️ Download playwright.spec.ts"

            unresolved = sum(("UNRESOLVED" in x["Locator"] or "AMBIGUOUS" in x["Locator"]) for x in report)
            st.success(f"Loaded {sum(len(v) for v in controls.values())} Tosca controls from Modules.tsu and processed {len(steps)} test steps.")

            if unresolved:
                st.warning(f"{unresolved} test controls could not be matched to the module export. Check the Mapping Report.")
            else:
                st.success("All test controls were mapped successfully.")

            st.subheader(f"Generated Playwright — {target_language}")
            st.code(code, language=code_language)
            st.download_button(download_label, code, file_name, "text/plain", use_container_width=True)

            st.subheader("Mapping Report")
            st.dataframe(report, use_container_width=True)
        except Exception as e:
            st.error(f"Conversion failed: {e}")
