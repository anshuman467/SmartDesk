"""One-shot script: replaces render_navbar in services/ui.py with the clean version."""
import re

NEW_NAVBAR = '''
def render_navbar(authenticated: bool = False) -> None:
    """Responsive navbar via components.html – CSS/JS run in their own iframe."""
    import streamlit.components.v1 as components

    if authenticated:
        links_html = (
            "<a class=nl onclick=\\"nav(\\'home\\')\\" >Home</a>"
            "<a class=nl onclick=\\"nav(\\'upload\\')\\" >Upload</a>"
            "<a class=nl onclick=\\"nav(\\'ipdr\\')\\" >IPDR</a>"
            "<a class=nl onclick=\\"nav(\\'map\\')\\" >Map View</a>"
            "<a class=nl onclick=\\"nav(\\'reports\\')\\" >Reports</a>"
        )
        cta_html   = "<a class=cta onclick=\\"nav(\\'logout\\')\\">Log Out</a>"
        mob_extra  = "<a class='nl mob-cta' onclick=\\"nav(\\'logout\\')\\">Log Out</a>"
    else:
        links_html = (
            "<a class=nl onclick=\\"nav(\\'features\\')\\" >Features</a>"
            "<a class=nl onclick=\\"nav(\\'analysis\\')\\" >Analysis</a>"
            "<a class=nl onclick=\\"nav(\\'map\\')\\" >Map View</a>"
            "<a class=nl onclick=\\"nav(\\'reports\\')\\" >Reports</a>"
        )
        cta_html  = "<a class=cta onclick=\\"nav(\\'login\\')\\">Log In / Sign Up</a>"
        mob_extra = "<a class='nl mob-cta' onclick=\\"nav(\\'login\\')\\">Log In / Sign Up</a>"

    CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:transparent;overflow:hidden;margin:0}
nav{display:flex;align-items:center;justify-content:space-between;padding:.7rem 2rem;gap:1rem;
    background:rgba(17,25,40,.84);backdrop-filter:blur(20px);
    border-bottom:1px solid rgba(255,255,255,.08);font-family:Inter,sans-serif;position:relative}
.brand{display:flex;align-items:center;gap:.55rem;cursor:pointer;text-decoration:none}
.badge{width:32px;height:32px;border-radius:9px;flex-shrink:0;
       background:linear-gradient(135deg,#7c3aed,#06b6d4);
       display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:1rem}
.bname{color:#f1f5f9;font-size:.95rem;font-weight:700;line-height:1.1}
.bsub{color:#64748b;font-size:.5rem;letter-spacing:.12em;font-weight:500}
.links{display:flex;align-items:center;gap:.15rem;flex:1;justify-content:center}
.nl{color:#94a3b8;font-size:.85rem;font-weight:500;padding:.4rem .85rem;border-radius:8px;
    cursor:pointer;white-space:nowrap;text-decoration:none;border:1px solid transparent;
    transition:color .18s,background .18s}
.nl:hover{color:#f1f5f9;background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.1)}
.cta{background:linear-gradient(135deg,#7c3aed,#06b6d4);color:#fff;font-size:.85rem;font-weight:600;
     padding:.45rem 1.1rem;border-radius:999px;cursor:pointer;white-space:nowrap;text-decoration:none;
     transition:opacity .18s,transform .15s;display:inline-block}
.cta:hover{opacity:.85;transform:translateY(-1px)}
.ham{display:none;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);
     color:#f1f5f9;font-size:1.2rem;width:38px;height:38px;border-radius:9px;cursor:pointer;
     align-items:center;justify-content:center;flex-shrink:0}
.mob{display:none;flex-direction:column;gap:.2rem;padding:.6rem 1.5rem .9rem;
     background:rgba(17,25,40,.97);border-top:1px solid rgba(255,255,255,.06);
     position:absolute;top:100%;left:0;right:0;z-index:9999}
.mob.open{display:flex}
.mob .nl{font-size:.95rem;padding:.6rem .5rem;border-bottom:1px solid rgba(255,255,255,.05);border-radius:0}
.mob-cta{margin-top:.4rem;background:linear-gradient(135deg,#7c3aed,#06b6d4)!important;
         color:#fff!important;text-align:center;font-weight:600!important;
         padding:.65rem!important;border-radius:10px!important;border:none!important}
@media(max-width:900px){.links,.cta{display:none!important}.ham{display:flex!important}}
@media(min-width:901px){.ham{display:none!important}.mob{display:none!important}}
"""

    JS = """
function toggleMenu(){document.getElementById('mm').classList.toggle('open')}
document.addEventListener('click',function(e){
  var n=document.getElementById('nb'),m=document.getElementById('mm');
  if(m&&n&&!n.contains(e.target)&&!m.contains(e.target))m.classList.remove('open')
})
function nav(a){window.parent.postMessage({type:'streamlit:setComponentValue',value:a},'*')}
"""

    html = f"""<!DOCTYPE html><html><head>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>{CSS}</style></head><body>
<nav id=nb>
  <a class=brand onclick="nav(\'home\')">
    <div class=badge>⇡</div>
    <div><div class=bname>SignalDesk</div><div class=bsub>TELECOM INVESTIGATION SIMPLIFIED</div></div>
  </a>
  <div class=links>{links_html}</div>
  {cta_html}
  <button class=ham onclick=toggleMenu()>☰</button>
</nav>
<div class=mob id=mm>{links_html}{mob_extra}</div>
<script>{JS}</script></body></html>"""

    action = components.html(html, height=62, scrolling=False)

    if action:
        if not authenticated:
            if action == "features":
                st.session_state.landing_section = "features"; st.rerun()
            elif action == "analysis":
                st.session_state.landing_section = "analysis"; st.rerun()
            elif action == "map":
                st.session_state.landing_section = "map"; st.rerun()
            elif action == "reports":
                st.session_state.landing_section = "reports"; st.rerun()
            elif action == "login":
                st.session_state.auth_dialog_open = True; st.rerun()
        else:
            if action == "home":
                st.switch_page("app.py")
            elif action == "upload":
                st.switch_page("pages/upload.py")
            elif action == "ipdr":
                st.switch_page("pages/idpr_analysis.py")
            elif action == "map":
                st.switch_page("pages/map_view.py")
            elif action == "reports":
                st.switch_page("pages/report_center.py")
            elif action == "logout":
                from services.auth import logout
                logout(); st.rerun()

'''

src = open("services/ui.py", encoding="utf-8").read()

# Find boundaries
nav_start = src.find("\ndef render_navbar(")
page_intro_start = src.find("\ndef page_intro(", nav_start)

if nav_start == -1 or page_intro_start == -1:
    print("ERROR: Could not find boundaries!")
    exit(1)

new_src = src[:nav_start] + NEW_NAVBAR + src[page_intro_start:]
open("services/ui.py", "w", encoding="utf-8").write(new_src)
print(f"Done. render_navbar replaced. New file: {new_src.count(chr(10))} lines.")
