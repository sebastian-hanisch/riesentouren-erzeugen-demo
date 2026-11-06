"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import rte_constants as C
import rte_evaluation as ev
import rte_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**next(iter(C.PRESETS.values()))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_preset_has_a_distinct_configuration():
    keys = {tuple(sorted(p.items())) for p in C.PRESETS.values()}
    assert len(keys) == len(C.PRESETS)


def test_band_sizes_split_into_exact_and_reference_sizes():
    assert set(C.EXACT_SIZES) < set(C.BAND_SIZES) and set(C.EXACT_SIZES) | {25, 50} == set(C.BAND_SIZES)
    assert max(C.EXACT_SIZES) == C.N_MAX                                      # die Live-Grenze des exakten Lösers ist die größte exakt gebänderte Größe
    assert C.ENUM_MAX < C.N_MAX
