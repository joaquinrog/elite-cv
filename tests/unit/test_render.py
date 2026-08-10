from elitecv.render import latex_escape


def test_latex_escape_handles_reserved_characters():
    value = r"50% & C++_v2 #1 $ {safe} \\ ~ ^"

    escaped = latex_escape(value)

    assert r"50\%" in escaped
    assert r"\&" in escaped
    assert r"C++\_v2" in escaped
    assert r"\#1" in escaped
    assert r"\$" in escaped
    assert r"\{safe\}" in escaped
    assert r"\textbackslash{}" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped
