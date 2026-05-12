"""Clean up ui.py: remove all orphan code between render_navbar and page_intro."""
src = open("services/ui.py", encoding="utf-8").read()

# Find end of new render_navbar (ends with the closing of our new function)
marker_end = '    st.markdown("</div></div>", unsafe_allow_html=True)\n\n'
page_intro = '\ndef page_intro('

end_idx   = src.find(marker_end)
intro_idx = src.find(page_intro, end_idx)

if end_idx == -1 or intro_idx == -1:
    print("ERROR finding markers!")
    print("end_idx:", end_idx, "intro_idx:", intro_idx)
    exit(1)

# Everything between end of new render_navbar and page_intro is dead code
dead_start = end_idx + len(marker_end)
dead_end   = intro_idx

dead = src[dead_start:dead_end]
print(f"Removing {len(dead)} chars of dead code ({dead.count(chr(10))} lines):")
print(repr(dead[:200]))

new_src = src[:dead_start] + src[dead_end:]
open("services/ui.py", "w", encoding="utf-8").write(new_src)
print(f"\nDone. File now {new_src.count(chr(10))} lines.")
