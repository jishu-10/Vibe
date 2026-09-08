"""Canonical, versioned Campus Chemistry Vibe Engine V1 configuration.

All values in this module are copied from the locked V1 build contract. Business
logic consumes this configuration; it does not embed weights, thresholds, or
matrices in calculation functions.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

QUESTIONNAIRE_VERSION = "1.0"
SIGNAL_MODEL_VERSION = "1.0"
DIMENSION_MODEL_VERSION = "1.0"
SCORING_MODEL_VERSION = "1.2.0"
NARRATIVE_PROMPT_VERSION = "1.0"
COMPLETION_AMENDMENT_VERSION = "1.0"
WILDCARD_SCORING_CONFIG_VERSION = "1.0"

VERSIONS = MappingProxyType(
    {
        "questionnaire": QUESTIONNAIRE_VERSION,
        "signal_model": SIGNAL_MODEL_VERSION,
        "dimension_model": DIMENSION_MODEL_VERSION,
        "scoring_model": SCORING_MODEL_VERSION,
        "narrative_prompt": NARRATIVE_PROMPT_VERSION,
        "completion_amendment": COMPLETION_AMENDMENT_VERSION,
    }
)

QUESTION_WEIGHTS = MappingProxyType(
    {
        "Q1": 1.15,
        "Q2": 1.15,
        "Q3": 0.90,
        "Q4": 0.90,
        "Q5": 0.60,
        "Q6": 1.10,
        "Q7": 1.15,
        "Q8": 1.15,
        "Q9": 1.00,
        "Q10": 0.95,
    }
)

GLOBAL_COMPONENT_WEIGHTS = MappingProxyType(
    {"alignment": 0.50, "complementarity": 0.25, "friction": 0.60}
)

THRESHOLDS = MappingProxyType(
    {
        "alignment": 0.50,
        "high_conf_alignment": 0.65,
        "complementarity": 0.25,
        "soft_friction": -0.01,
        "meaningful_friction": -0.35,
        "hard_friction": -0.50,
    }
)

CHEMISTRY_THRESHOLDS = MappingProxyType(
    {
        "natural_final": 0.65,
        "natural_alignment": 0.55,
        "natural_friction_max_exclusive": 0.35,
        "interesting_final": 0.45,
        "interesting_complementarity": 0.35,
        "interesting_friction_max_exclusive": 0.50,
    }
)

PHASE_ADJUSTMENT = MappingProxyType(
    {"same": 0.05, "compatible": 0.025, "neutral": 0.0, "conflicting": -0.025}
)

NARRATIVE_LIMITS = MappingProxyType(
    {"positive_findings": 3, "friction_findings": 1, "max_evidence": 4}
)

INDIVIDUAL_THRESHOLDS = MappingProxyType(
    {
        "social_energy": (0.25, 0.45, 0.65, 0.80),
        "social_density": (0.30, 0.60),
        "social_selectivity": (0.35, 0.65),
        "humor_connection": (0.35, 0.65, 0.80),
        "introspection": (0.30, 0.60),
        "connection_mode_qualifying": 0.65,
        "pace_variable": 0.70,
        "pace_action_orientation": 0.75,
        "pace_action_delay_max": 0.45,
        "pace_process_delay": 0.75,
        "pace_introspection": 0.60,
        "pace_observation": 0.70,
        "pace_warmup_observation_max": 0.60,
        "pace_openness": 0.75,
        "pace_warmup_immediate": 0.75,
        "energy_secondary_score": 0.65,
        "energy_secondary_delta": 0.10,
        "rhythm_warm_fast": 0.75,
        "rhythm_warm_moderate": 0.45,
        "rhythm_peak_humor": 0.70,
        "rhythm_peak_social": 0.65,
        "rhythm_peak_depth": 0.70,
        "rhythm_peak_attention": 0.70,
        "rhythm_peak_relaxed": 0.70,
    }
)

PAIR_POLICY_THRESHOLDS = MappingProxyType(
    {
        "d2_shared_alignment": 0.70,
        "d2_productive_gap": 0.30,
        "d2_interference_gap": 0.60,
        "d2_hard_gap": 0.80,
        "d4_high_social": 0.65,
        "d4_high_density": 0.60,
        "d4_fast_warm": 0.75,
        "d4_interference_energy_a": 0.75,
        "d4_interference_energy_b": 0.45,
        "d4_interference_replenishment_high": 0.70,
        "d4_interference_recovery_low": 0.30,
        "d5_direct_gap": 0.55,
        "d5_delay_gap": 0.50,
        "d5_high_direct": 0.70,
        "d5_productive_gap_min": 0.30,
        "d5_productive_gap_max": 0.50,
        "d5_alignment_gap_1": 0.15,
        "d5_alignment_gap_2": 0.30,
        "d5_hard_gap": 0.70,
        "d8_hard_gap": 0.60,
        "d8_productive_gap_min": 0.30,
        "d8_productive_gap_max": 0.70,
        "d9_energy_gap": 0.50,
        "d9_hard_gap": 0.60,
        "generic_gap_1": 0.15,
        "generic_gap_2": 0.30,
        "generic_gap_3": 0.70,
    }
)

WILDCARD_THRESHOLDS = MappingProxyType(
    {"difference": 0.30, "complementarity": 0.35, "friction_exclusive": 0.35, "hard_friction_count": 0}
)

# Wildcard is an individual-profile operation.  It uses the stable profile
# dimension priorities from the canonical contrast contract, with no DATE,
# FRIEND, or HANGOUT mode inheritance.
WILDCARD_DIMENSION_ORDER = tuple(f"D{i}" for i in range(1, 10))
WILDCARD_BASE_WEIGHTS = MappingProxyType(
    {"D1": 1.10, "D2": 1.20, "D3": 1.00, "D4": 1.20, "D5": 1.00, "D6": 0.90, "D7": 1.00, "D8": 0.90, "D9": 1.00}
)
WILDCARD_MULTIPLIERS = MappingProxyType({dimension: 1.0 for dimension in WILDCARD_DIMENSION_ORDER})
WILDCARD_EFFECTIVE_WEIGHTS = MappingProxyType(
    {dimension: WILDCARD_BASE_WEIGHTS[dimension] * WILDCARD_MULTIPLIERS[dimension] for dimension in WILDCARD_DIMENSION_ORDER}
)
WILDCARD_WEIGHT_DENOMINATOR = 10.30
WILDCARD_NORMALIZED_WEIGHTS = MappingProxyType(
    {dimension: WILDCARD_EFFECTIVE_WEIGHTS[dimension] / WILDCARD_WEIGHT_DENOMINATOR for dimension in WILDCARD_DIMENSION_ORDER}
)
WILDCARD_D10_PARTICIPATES = False

WILDCARD_DELTAS = MappingProxyType(
    {
        "HIGHER_ENERGY": MappingProxyType({"social_energy": 0.30, "energy_contribution": 0.15, "social_presence": 0.15}),
        "MORE_DIRECT": MappingProxyType({"direct_expression": 0.30, "direct_affection": 0.15, "initial_openness": 0.15}),
        "MORE_SPONTANEOUS": MappingProxyType({"spontaneity": 0.30, "flexibility": 0.15, "structure_preference": -0.15}),
        "MORE_STRUCTURED": MappingProxyType({"structure_preference": 0.30, "predictability": 0.15, "spontaneity": -0.15}),
        "MORE_SOCIAL": MappingProxyType({"social_density": 0.30, "social_energy": 0.15, "group_orientation": 0.15, "solitude_preference": -0.15}),
        "MORE_TUNED_IN": MappingProxyType({"attentional_presence": 0.30, "attentional_affection": 0.15, "introspection": 0.15}),
    }
)

CONTINUOUS_SIGNAL_NAMES = (
    "social_energy", "social_density", "group_orientation", "one_to_one_preference", "solitude_preference", "external_stimulation",
    "intellectual_depth", "emotional_depth", "humor_connection", "conversation_ease", "initial_openness", "warmup_speed", "social_selectivity", "initial_observation", "initial_social_friction",
    "social_presence", "energy_contribution", "relaxed_presence", "humor_presence", "attentional_presence",
    "direct_expression", "processing_delay", "action_response", "context_sensitivity",
    "direct_affection", "verbal_expression", "behavioral_expression", "reliability_affection", "playful_affection", "humor_affection", "attentional_affection", "listening", "memory_for_detail",
    "structure_preference", "flexibility", "spontaneity", "predictability", "planning_variability",
    "social_replenishment", "solitary_recovery", "people_dependency", "mixed_recovery",
    "introspection", "reflection", "action_orientation", "processing_variability",
)

QUESTIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "Q1",
        "title": "UNSTRUCTURED SOCIAL ENERGY",
        "text": "It's Friday night with no plans. What actually sounds good?",
        "options": {
            "Q1_A": "Going out - find where the energy is",
            "Q1_B": "Small gathering - close people, good conversation",
            "Q1_C": "One person, deep hangout - proper time with someone I actually like",
            "Q1_D": "Honestly, staying in sounds perfect right now",
        },
    },
    {
        "id": "Q2",
        "title": "CONVERSATION / CONNECTION PREFERENCE",
        "text": "What kind of conversation actually does it for you?",
        "options": {
            "Q2_A": "Going deep on ideas - opinions, what things actually mean, why things are the way they are",
            "Q2_B": "Getting real and personal - actual feelings, actual lives, the stuff people don't usually say",
            "Q2_C": "Funny and sharp - wit, banter, making each other laugh without trying too hard",
            "Q2_D": "Easy and effortless - no performance, just comfortable silence and flow",
        },
    },
    {
        "id": "Q3",
        "title": "FIRST-CONTACT STYLE",
        "text": "How do you usually show up when you first meet someone?",
        "options": {
            "Q3_A": "Pretty open - I talk easily, I warm up fast",
            "Q3_B": "Selectively warm - I'm friendly but I take time to actually let people in",
            "Q3_C": "Quiet at first - I observe before I engage, but once I'm comfortable it changes",
            "Q3_D": "A little awkward at first - I need time to find my rhythm",
        },
    },
    {
        "id": "Q4",
        "title": "SOCIAL ENERGY SIGNATURE",
        "text": "When you're with people you really like, what's most like you?",
        "options": {
            "Q4_A": "I bring the energy",
            "Q4_B": "I keep things relaxed",
            "Q4_C": "I keep everyone laughing",
            "Q4_D": "I get quieter and really tuned-in",
        },
    },
    {
        "id": "Q5",
        "title": "CURRENT LIFE PULSE",
        "text": "Where are you at right now - honestly?",
        "options": {
            "Q5_A": "Figuring things out - a lot is uncertain and I'm mostly okay with that",
            "Q5_B": "Building something - I have a direction and I'm moving toward it",
            "Q5_C": "Enjoying the ride - not thinking too far ahead, present in what's happening",
            "Q5_D": "Feeling the weight of it - expectations, future, a lot sitting on me",
        },
    },
    {
        "id": "Q6",
        "title": "EMOTIONAL PROCESSING",
        "text": "When something's bothering you, what do you usually do?",
        "options": {
            "Q6_A": "Bring it up - I'd rather say it than let it sit",
            "Q6_B": "Sit with it first - I need to process before I can talk about it",
            "Q6_C": "Distract myself and move on - overthinking doesn't help",
            "Q6_D": "Depends on who it involves and how much it matters",
        },
    },
    {
        "id": "Q7",
        "title": "AFFECTION / WARMTH STYLE",
        "text": "When you like someone - friend or more - how do you show it?",
        "options": {
            "Q7_A": "I tell them or make it pretty obvious",
            "Q7_B": "I show up for them - I'm there when it actually matters",
            "Q7_C": "I tease them - banter and humor is how I show I'm comfortable",
            "Q7_D": "I give them real attention - I listen, I remember, I notice",
        },
    },
    {
        "id": "Q8",
        "title": "PLANNING RHYTHM",
        "text": "How do you feel about plans?",
        "options": {
            "Q8_A": "I like knowing what's happening - I function better with some structure",
            "Q8_B": "Loose plans are fine - general idea, room to change",
            "Q8_C": "Spontaneous is better - figure it out as you go",
            "Q8_D": "Depends on my mood and energy that day",
        },
    },
    {
        "id": "Q9",
        "title": "SOCIAL RECHARGE",
        "text": "After a lot of social interaction, what do you actually need?",
        "options": {
            "Q9_A": "More people",
            "Q9_B": "Some alone time",
            "Q9_C": "Depends on people",
            "Q9_D": "A mix",
        },
    },
    {
        "id": "Q10",
        "title": "INTERNAL PROCESSING",
        "text": "Honestly - how much are you in your own head?",
        "options": {
            "Q10_A": "A lot",
            "Q10_B": "Somewhat",
            "Q10_C": "Not really",
            "Q10_D": "Comes in waves",
        },
    },
)

# Each mapping contains continuous signals and, where specified, a controlled
# categorical value. The mapping is immutable by convention and validated at
# import time by the configuration validator.
SIGNAL_MAP: dict[str, dict[str, dict[str, Any]]] = {
    "Q1": {
        "Q1_A": {"category": "HIGH_SOCIAL_STIMULATION", "signals": {"social_energy": 1.00, "social_density": 1.00, "group_orientation": 1.00, "one_to_one_preference": 0.25, "solitude_preference": 0.00, "external_stimulation": 1.00}},
        "Q1_B": {"category": "SMALL_GROUP_SOCIAL", "signals": {"social_energy": 0.70, "social_density": 0.60, "group_orientation": 0.75, "one_to_one_preference": 0.60, "solitude_preference": 0.15, "external_stimulation": 0.65}},
        "Q1_C": {"category": "ONE_TO_ONE_SOCIAL", "signals": {"social_energy": 0.40, "social_density": 0.15, "group_orientation": 0.05, "one_to_one_preference": 1.00, "solitude_preference": 0.20, "external_stimulation": 0.30}},
        "Q1_D": {"category": "LOW_SOCIAL_STIMULATION", "signals": {"social_energy": 0.10, "social_density": 0.00, "group_orientation": 0.00, "one_to_one_preference": 0.10, "solitude_preference": 1.00, "external_stimulation": 0.05}},
    },
    "Q2": {
        "Q2_A": {"category": "INTELLECTUAL", "signals": {"intellectual_depth": 1.00, "emotional_depth": 0.40, "humor_connection": 0.25, "conversation_ease": 0.40}},
        "Q2_B": {"category": "EMOTIONAL", "signals": {"intellectual_depth": 0.50, "emotional_depth": 1.00, "humor_connection": 0.25, "conversation_ease": 0.50}},
        "Q2_C": {"category": "PLAYFUL", "signals": {"intellectual_depth": 0.35, "emotional_depth": 0.20, "humor_connection": 1.00, "conversation_ease": 0.85}},
        "Q2_D": {"category": "AMBIENT_COMFORT", "signals": {"intellectual_depth": 0.30, "emotional_depth": 0.35, "humor_connection": 0.45, "conversation_ease": 1.00}},
    },
    "Q3": {
        "Q3_A": {"category": "IMMEDIATE_OPEN", "signals": {"initial_openness": 1.00, "warmup_speed": 1.00, "social_selectivity": 0.25, "initial_observation": 0.20}},
        "Q3_B": {"category": "SELECTIVE_OPEN", "signals": {"initial_openness": 0.70, "warmup_speed": 0.55, "social_selectivity": 0.90, "initial_observation": 0.60}},
        "Q3_C": {"category": "OBSERVATIONAL", "signals": {"initial_openness": 0.30, "warmup_speed": 0.30, "social_selectivity": 0.65, "initial_observation": 1.00}},
        "Q3_D": {"category": "SLOW_START", "signals": {"initial_openness": 0.25, "warmup_speed": 0.20, "social_selectivity": 0.50, "initial_observation": 0.55, "initial_social_friction": 0.80}},
    },
    "Q4": {
        "Q4_A": {"category": "ENERGIZER", "signals": {"social_presence": 1.00, "energy_contribution": 1.00, "relaxed_presence": 0.30, "humor_presence": 0.35, "attentional_presence": 0.40}},
        "Q4_B": {"category": "REGULATOR", "signals": {"social_presence": 0.45, "energy_contribution": 0.30, "relaxed_presence": 1.00, "humor_presence": 0.30, "attentional_presence": 0.50}},
        "Q4_C": {"category": "PLAYMAKER", "signals": {"social_presence": 0.75, "energy_contribution": 0.65, "relaxed_presence": 0.45, "humor_presence": 1.00, "attentional_presence": 0.55}},
        "Q4_D": {"category": "TUNED_IN", "signals": {"social_presence": 0.30, "energy_contribution": 0.20, "relaxed_presence": 0.55, "humor_presence": 0.20, "attentional_presence": 1.00}},
    },
    "Q5": {
        "Q5_A": {"category": "EXPLORING", "signals": {"life_phase": "EXPLORING", "uncertainty": "HIGH", "direction": "LOW", "future_pressure": "MODERATE", "present_orientation": "MODERATE"}},
        "Q5_B": {"category": "BUILDING", "signals": {"life_phase": "BUILDING", "uncertainty": "MODERATE", "direction": "HIGH", "future_orientation": "HIGH", "present_orientation": "MODERATE"}},
        "Q5_C": {"category": "PRESENT", "signals": {"life_phase": "PRESENT", "uncertainty": "MODERATE", "direction": "LOW", "future_orientation": "LOW", "present_orientation": "HIGH"}},
        "Q5_D": {"category": "PRESSURED", "signals": {"life_phase": "PRESSURED", "uncertainty": "MODERATE", "direction": "MODERATE", "future_orientation": "HIGH", "future_pressure": "HIGH", "mental_load": "HIGH"}},
    },
    "Q6": {
        "Q6_A": {"category": "DIRECT_PROCESSOR", "signals": {"direct_expression": 1.00, "processing_delay": 0.10, "action_response": 0.55, "context_sensitivity": 0.40}},
        "Q6_B": {"category": "PROCESS_THEN_TALK", "signals": {"direct_expression": 0.35, "processing_delay": 1.00, "action_response": 0.35, "context_sensitivity": 0.50}},
        "Q6_C": {"category": "ACTION_RESPONSE", "signals": {"direct_expression": 0.20, "processing_delay": 0.30, "action_response": 1.00, "context_sensitivity": 0.30}},
        "Q6_D": {"category": "CONTEXTUAL_PROCESSOR", "signals": {"direct_expression": 0.50, "processing_delay": 0.50, "action_response": 0.50, "context_sensitivity": 1.00}},
    },
    "Q7": {
        "Q7_A": {"category": "DIRECT", "signals": {"direct_affection": 1.00, "verbal_expression": 1.00, "behavioral_expression": 0.45}},
        "Q7_B": {"category": "PRESENCE", "signals": {"direct_affection": 0.45, "reliability_affection": 1.00, "behavioral_expression": 1.00}},
        "Q7_C": {"category": "PLAYFUL", "signals": {"direct_affection": 0.35, "reliability_affection": 0.25, "playful_affection": 1.00, "humor_affection": 1.00}},
        "Q7_D": {"category": "ATTENTIVE", "signals": {"direct_affection": 0.35, "attentional_affection": 1.00, "listening": 1.00, "memory_for_detail": 1.00}},
    },
    "Q8": {
        "Q8_A": {"category": "STRUCTURED", "signals": {"structure_preference": 1.00, "flexibility": 0.35, "spontaneity": 0.20, "predictability": 1.00}},
        "Q8_B": {"category": "FLEXIBLE", "signals": {"structure_preference": 0.55, "flexibility": 0.85, "spontaneity": 0.65, "predictability": 0.50}},
        "Q8_C": {"category": "SPONTANEOUS", "signals": {"structure_preference": 0.15, "flexibility": 0.75, "spontaneity": 1.00, "predictability": 0.20}},
        "Q8_D": {"category": "VARIABLE", "signals": {"structure_preference": 0.40, "flexibility": 0.55, "spontaneity": 0.50, "planning_variability": 1.00}},
    },
    "Q9": {
        "Q9_A": {"category": "SOCIAL_RECHARGE", "signals": {"social_replenishment": 1.00, "solitary_recovery": 0.00, "people_dependency": 0.90, "mixed_recovery": 0.20}},
        "Q9_B": {"category": "SOLITARY_RECHARGE", "signals": {"social_replenishment": 0.10, "solitary_recovery": 1.00, "people_dependency": 0.10, "mixed_recovery": 0.20}},
        "Q9_C": {"category": "PEOPLE_DEPENDENT", "signals": {"social_replenishment": 0.50, "solitary_recovery": 0.40, "people_dependency": 1.00, "mixed_recovery": 0.65}},
        "Q9_D": {"category": "MIXED_RECHARGE", "signals": {"social_replenishment": 0.55, "solitary_recovery": 0.65, "people_dependency": 0.50, "mixed_recovery": 1.00}},
    },
    "Q10": {
        "Q10_A": {"category": "DEEP_PROCESSING", "signals": {"introspection": 1.00, "reflection": 1.00, "action_orientation": 0.20, "processing_variability": 0.30}},
        "Q10_B": {"category": "MODERATE_PROCESSING", "signals": {"introspection": 0.65, "reflection": 0.70, "action_orientation": 0.50, "processing_variability": 0.25}},
        "Q10_C": {"category": "ACTION_ORIENTED", "signals": {"introspection": 0.15, "reflection": 0.20, "action_orientation": 1.00, "processing_variability": 0.20}},
        "Q10_D": {"category": "VARIABLE_PROCESSING", "signals": {"introspection": 0.65, "reflection": 0.65, "action_orientation": 0.55, "processing_variability": 1.00}},
    },
}

VERSIONED_SIGNAL_MAP = {
    (QUESTIONNAIRE_VERSION, SIGNAL_MODEL_VERSION): SIGNAL_MAP,
}

D1_MATRIX = {
    "INTELLECTUAL": {"INTELLECTUAL": 0.90, "EMOTIONAL": 0.45, "PLAYFUL": 0.35, "AMBIENT_COMFORT": -0.55},
    "EMOTIONAL": {"INTELLECTUAL": 0.45, "EMOTIONAL": 0.90, "PLAYFUL": 0.30, "AMBIENT_COMFORT": -0.40},
    "PLAYFUL": {"INTELLECTUAL": 0.35, "EMOTIONAL": 0.30, "PLAYFUL": 0.95, "AMBIENT_COMFORT": 0.45},
    "AMBIENT_COMFORT": {"INTELLECTUAL": -0.55, "EMOTIONAL": -0.40, "PLAYFUL": 0.45, "AMBIENT_COMFORT": 0.90},
}

D3_MATRIX = {
    "DIRECT": {"DIRECT": 0.90, "PRESENCE": 0.45, "PLAYFUL": 0.50, "ATTENTIVE": 0.40},
    "PRESENCE": {"DIRECT": 0.45, "PRESENCE": 0.90, "PLAYFUL": 0.30, "ATTENTIVE": 0.55},
    "PLAYFUL": {"DIRECT": 0.50, "PRESENCE": 0.30, "PLAYFUL": 0.95, "ATTENTIVE": 0.40},
    "ATTENTIVE": {"DIRECT": 0.40, "PRESENCE": 0.55, "PLAYFUL": 0.40, "ATTENTIVE": 0.90},
}

D6_MATRIX = {
    "STRUCTURED": {"STRUCTURED": 0.90, "FLEXIBLE": 0.45, "SPONTANEOUS": -0.80, "VARIABLE": -0.20},
    "FLEXIBLE": {"STRUCTURED": 0.45, "FLEXIBLE": 0.90, "SPONTANEOUS": 0.55, "VARIABLE": 0.30},
    "SPONTANEOUS": {"STRUCTURED": -0.80, "FLEXIBLE": 0.55, "SPONTANEOUS": 0.90, "VARIABLE": 0.40},
    "VARIABLE": {"STRUCTURED": -0.20, "FLEXIBLE": 0.30, "SPONTANEOUS": 0.40, "VARIABLE": 0.80},
}

D7_MATRIX = {
    "SOCIAL_RECHARGE": {"SOCIAL_RECHARGE": 0.90, "SOLITARY_RECHARGE": -0.60, "PEOPLE_DEPENDENT": 0.20, "MIXED_RECHARGE": 0.30},
    "SOLITARY_RECHARGE": {"SOCIAL_RECHARGE": -0.60, "SOLITARY_RECHARGE": 0.90, "PEOPLE_DEPENDENT": -0.45, "MIXED_RECHARGE": 0.35},
    "PEOPLE_DEPENDENT": {"SOCIAL_RECHARGE": 0.20, "SOLITARY_RECHARGE": -0.45, "PEOPLE_DEPENDENT": 0.80, "MIXED_RECHARGE": 0.55},
    "MIXED_RECHARGE": {"SOCIAL_RECHARGE": 0.30, "SOLITARY_RECHARGE": 0.35, "PEOPLE_DEPENDENT": 0.55, "MIXED_RECHARGE": 0.85},
}

D10_MATRIX = {
    "EXPLORING": {"EXPLORING": 0.050, "BUILDING": 0.025, "PRESENT": 0.000, "PRESSURED": -0.025},
    "BUILDING": {"EXPLORING": 0.025, "BUILDING": 0.050, "PRESENT": 0.025, "PRESSURED": -0.025},
    "PRESENT": {"EXPLORING": 0.000, "BUILDING": 0.025, "PRESENT": 0.050, "PRESSURED": -0.025},
    "PRESSURED": {"EXPLORING": -0.025, "BUILDING": -0.025, "PRESENT": -0.025, "PRESSURED": 0.050},
}

MODE_BASE_WEIGHTS = MappingProxyType(
    {"D1": 1.20, "D2": 1.15, "D3": 1.10, "D4": 1.10, "D5": 1.10, "D6": 1.05, "D7": 1.00, "D8": 0.90, "D9": 0.90, "D10": 0.50}
)
MODE_MULTIPLIERS = {
    "DATE": {"D1": 1.25, "D2": 1.20, "D3": 1.15, "D4": 1.00, "D5": 1.15, "D6": 0.90, "D7": 0.85, "D8": 0.85, "D9": 0.85, "D10": 0.50},
    "FRIEND": {"D1": 1.10, "D2": 1.00, "D3": 0.75, "D4": 1.20, "D5": 0.90, "D6": 1.00, "D7": 1.15, "D8": 0.85, "D9": 1.00, "D10": 0.40},
    "HANGOUT": {"D1": 1.00, "D2": 0.85, "D3": 0.45, "D4": 1.25, "D5": 0.55, "D6": 1.20, "D7": 1.15, "D8": 0.80, "D9": 1.10, "D10": 0.35},
}

FRICTION_MULTIPLIERS = MappingProxyType(
    {"D1": 1.05, "D2": 1.05, "D3": 1.00, "D4": 1.00, "D5": 1.15, "D6": 1.15, "D7": 1.10, "D8": 1.00, "D9": 0.95}
)
COMPLEMENTARITY_MULTIPLIERS = MappingProxyType(
    {"D1": 0.95, "D2": 1.00, "D3": 0.95, "D4": 1.05, "D5": 0.90, "D6": 1.05, "D7": 0.95, "D8": 1.10, "D9": 1.15}
)

D4_FEATURE_WEIGHTS = MappingProxyType({"social_energy": 0.30, "social_density": 0.20, "initial_openness": 0.15, "warmup_speed": 0.15, "energy_contribution": 0.10, "social_replenishment": 0.10})
D5_FEATURE_WEIGHTS = MappingProxyType({"direct_expression": 0.30, "processing_delay": 0.35, "action_response": 0.15, "context_sensitivity": 0.20})
D8_FEATURE_WEIGHTS = MappingProxyType({"initial_openness": 0.25, "warmup_speed": 0.25, "processing_delay": 0.25, "introspection": 0.15, "action_orientation": 0.10})
D9_FEATURE_WEIGHTS = MappingProxyType({"social_presence": 0.25, "energy_contribution": 0.25, "relaxed_presence": 0.20, "humor_presence": 0.15, "attentional_presence": 0.15})

D2_PRODUCTIVE_PAIRS = frozenset({frozenset({"HUMOR_LED", "EASE_LED"}), frozenset({"HUMOR_LED", "ATTENTION_LED"}), frozenset({"DEPTH_LED", "EMOTION_LED"}), frozenset({"DEPTH_LED", "ATTENTION_LED"}), frozenset({"PRESENCE_LED", "ATTENTION_LED"}), frozenset({"DIRECT", "PRESENCE_LED"}), frozenset({"DIRECT", "EMOTION_LED"})})
D2_INTERFERENCE_PAIRS = frozenset({frozenset({"DEPTH_LED", "EASE_LED"}), frozenset({"EMOTION_LED", "EASE_LED"}), frozenset({"DIRECT", "EASE_LED"})})
D4_PRODUCTIVE_CATEGORIES = frozenset({"HIGH_SOCIAL_ENERGY", "HIGH_SOCIAL_DENSITY", "FAST_WARMUP"})
D5_PRODUCTIVE_PAIRS = frozenset({frozenset({"DIRECT_PROCESSOR", "CONTEXTUAL_PROCESSOR"}), frozenset({"PROCESS_THEN_TALK", "CONTEXTUAL_PROCESSOR"}), frozenset({"ACTION_RESPONSE", "CONTEXTUAL_PROCESSOR"})})
D8_PRODUCTIVE_PAIRS = frozenset({frozenset({"IMMEDIATE", "GRADUAL"}), frozenset({"IMMEDIATE", "OBSERVATIONAL"}), frozenset({"ACTION_FIRST", "PROCESS_FIRST"})})
D8_HARD_PAIRS = frozenset({frozenset({"IMMEDIATE", "PROCESS_FIRST"}), frozenset({"ACTION_FIRST", "PROCESS_FIRST"})})
D9_PRODUCTIVE_PAIRS = frozenset({frozenset({"ENERGIZER", "RELAXED"}), frozenset({"ENERGIZER", "TUNED_IN"}), frozenset({"PLAYMAKER", "RELAXED"}), frozenset({"SOCIAL_CATALYST", "UNDERSTATED"}), frozenset({"INTENSE", "RELAXED"})})

D2_TIE_ORDER = ("ATTENTION_LED", "HUMOR_LED", "PRESENCE_LED", "DEPTH_LED", "DIRECT", "EASE_LED", "EMOTION_LED")
D9_TIE_ORDER = ("PLAYFUL", "ENERGIZER", "SOCIAL_CATALYST", "TUNED_IN", "RELAXED", "INTENSE", "UNDERSTATED")
CONTRAST_TIE_ORDER = ("D4", "D1", "D6", "D7", "D8", "D9", "D5", "D2", "D3")
WILDCARD_ORDER = ("HIGHER_ENERGY", "MORE_DIRECT", "MORE_SPONTANEOUS", "MORE_STRUCTURED", "MORE_SOCIAL", "MORE_TUNED_IN")
DIMENSION_ORDER = tuple(f"D{i}" for i in range(1, 10))

PULL_LIBRARY = {
    "BANTER_WITHOUT_FORCING": lambda s: s["humor_connection"] >= 0.70 and s["playful_affection"] >= 0.65,
    "REAL_CONVERSATION": lambda s: s["emotional_depth"] >= 0.65 or s["intellectual_depth"] >= 0.80,
    "EASY_FLOW": lambda s: s["conversation_ease"] >= 0.80,
    "ATTENTIVE_PEOPLE": lambda s: s["attentional_affection"] >= 0.70,
    "PATIENT_ENTRY": lambda s: s["social_selectivity"] >= 0.65 or s["warmup_speed"] <= 0.45,
    "PLAYFUL_WARMTH": lambda s: s["humor_connection"] >= 0.65 and s["social_presence"] >= 0.45,
    "SPACE_WITH_PRESENCE": lambda s: s["solitary_recovery"] >= 0.65 and s["attentional_presence"] >= 0.60,
    "FLEXIBLE_PLANNING": lambda s: s["flexibility"] >= 0.75 and s["spontaneity"] >= 0.60,
}
DRAIN_LIBRARY = {
    "CONSTANT_SOCIAL_DEMAND": lambda s: s["social_energy"] <= 0.44 and s["solitary_recovery"] >= 0.65,
    "FORCED_OPENING": lambda s: s["social_selectivity"] >= 0.65 and s["warmup_speed"] <= 0.60,
    "LAST_MINUTE_CHANGE": lambda s: s["structure_preference"] >= 0.70,
    "OVERLY_CONTROLLED_PLANS": lambda s: s["spontaneity"] >= 0.75,
    "LIGHT_TALK_ONLY": lambda s: s["connection_depth"] >= 0.70,
    "NO_BANTER": lambda s: s["humor_connection"] >= 0.70 and s["conversation_ease"] < 0.70,
    "IMMEDIATE_EMOTIONAL_DEMAND": lambda s: s["processing_delay"] >= 0.75 or s["Q6_category"] == "PROCESS_THEN_TALK",
}

CONTRAST_PROTOTYPES = {
    "HIGH_ENERGY": ("Q1_A", "Q2_C", "Q3_A", "Q4_A", "Q5_B", "Q6_A", "Q7_C", "Q8_C", "Q9_A", "Q10_C"),
    "VERY_QUIET": ("Q1_D", "Q2_D", "Q3_C", "Q4_D", "Q5_A", "Q6_B", "Q7_D", "Q8_B", "Q9_B", "Q10_A"),
    "HIGHLY_STRUCTURED": ("Q1_B", "Q2_A", "Q3_B", "Q4_B", "Q5_B", "Q6_A", "Q7_B", "Q8_A", "Q9_D", "Q10_B"),
    "HIGHLY_SPONTANEOUS": ("Q1_A", "Q2_C", "Q3_A", "Q4_C", "Q5_C", "Q6_C", "Q7_C", "Q8_C", "Q9_A", "Q10_C"),
}

CONTRAST_WEIGHTS = MappingProxyType(
    {"D1": 1.10, "D2": 1.20, "D3": 1.00, "D4": 1.20, "D5": 1.00, "D6": 0.90, "D7": 1.00, "D8": 0.90, "D9": 1.00}
)
CONTRAST_WEIGHT_DENOMINATOR = 10.30
CONTRAST_NORMALIZED_WEIGHTS = MappingProxyType(
    {dimension: weight / CONTRAST_WEIGHT_DENOMINATOR for dimension, weight in CONTRAST_WEIGHTS.items()}
)

PROFILE_WEIGHTS = MappingProxyType(
    {"D1": 1.10, "D2": 1.20, "D3": 1.00, "D4": 1.20, "D5": 1.00, "D6": 0.90, "D7": 1.00, "D8": 0.90, "D9": 1.00, "D10": 0.50}
)

APPROVED_LANGUAGE = ("You tend to", "You probably", "You may", "The interesting part is", "This could feel", "You might find", "The thing to watch is")
FORBIDDEN_CLAIMS = ("attachment style", "trauma", "mental health diagnosis", "clinical personality", "avoidant", "anxious", "soulmate", "destiny", "guaranteed chemistry", "guaranteed attraction", "relationship success", "IQ", "intelligence claim", "social anxiety")

# The narrative boundary accepts natural wording only inside this deterministic
# vocabulary.  These are semantic anchors, not additional traits or scoring
# inputs; unsupported terms remain outside the claim envelope.
NARRATIVE_GENERIC_TERMS = frozenset(
    {
        "a", "an", "and", "are", "around", "as", "at", "be", "between", "both", "can", "could", "evidence",
        "feel", "feels", "for", "from", "here", "in", "is", "it", "may", "might", "of", "on", "or", "pattern",
        "patterns", "share", "shared", "shows", "show", "supports", "supported", "tend", "tends", "the", "their", "grounded",
        "this", "to", "two", "we", "with", "you", "your",
    }
)
NARRATIVE_CLAIM_TERMS = MappingProxyType(
    {
        "D1": frozenset({"conversation", "connection", "conversations", "ideas", "meaning", "emotional", "humor", "flow", "depth", "intellectual", "alignment", "aligned", "overlap"}),
        "D2": frozenset({"direct", "process", "processing", "action", "context", "talk", "talking", "affection", "expression", "communication", "pace", "alignment", "aligned", "overlap"}),
        "D3": frozenset({"openness", "open", "warmth", "warm", "selective", "observation", "observational", "start", "beginning", "connection", "alignment", "aligned", "overlap"}),
        "D4": frozenset({"energy", "social", "presence", "warming", "warm", "peak", "recovery", "rhythm", "recharge", "alignment", "aligned", "overlap"}),
        "D5": frozenset({"directness", "direct", "delay", "processing", "response", "respond", "friction", "difference", "alignment", "aligned", "overlap"}),
        "D6": frozenset({"affection", "attention", "attentive", "listening", "memory", "detail", "presence", "warmth", "difference", "alignment", "aligned", "overlap"}),
        "D7": frozenset({"structure", "flexibility", "spontaneity", "planning", "predictability", "organized", "difference", "alignment", "aligned", "overlap"}),
        "D8": frozenset({"recovery", "social", "solitary", "people", "recharge", "energy", "difference", "alignment", "aligned", "overlap"}),
        "D9": frozenset({"reflection", "introspection", "action", "depth", "processing", "energy", "difference", "alignment", "aligned", "overlap"}),
        "D10": frozenset({"phase", "present", "building", "exploring", "pressured", "context", "difference", "alignment", "aligned", "overlap"}),
    }
)


def engine_versions() -> dict[str, str]:
    return dict(VERSIONS)
