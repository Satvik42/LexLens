from app.services.model_cooldown import ModelCooldown


def test_mark_hides_a_model_until_the_clock_passes():
    now = {"t": 100.0}
    cooldown = ModelCooldown(clock=lambda: now["t"])
    assert cooldown.allow("gemini-3.7-flash") is True
    cooldown.mark("gemini-3.7-flash", 60)
    assert cooldown.allow("gemini-3.7-flash") is False
    now["t"] = 160.0
    assert cooldown.allow("gemini-3.7-flash") is True


def test_soonest_is_the_model_whose_cooldown_ends_first():
    now = {"t": 0.0}
    cooldown = ModelCooldown(clock=lambda: now["t"])
    cooldown.mark("gemini-3.7-flash", 60)
    cooldown.mark("gemini-3.8-flash", 20)
    assert cooldown.soonest(["gemini-3.7-flash", "gemini-3.8-flash"]) == "gemini-3.8-flash"
