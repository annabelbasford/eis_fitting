# syntax and importance of initial guesses detailed in the README
CIRCUITS = {
    "circuit_1": {
        "string": "p(R_1-CPE_1,R_2)",
        "guess": [
            1000,  # R_1 = R_i
            1e-6,  # CPE_1_0 =Q_DL
            0.9,  # CPE_1_1 = alpha_DL
            1e7,  # R_2 = R_e
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
                "compute_conductivity": True,
                "order": 0,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
                "compute_conductivity": True,
                "order": 1,
            },
            "CPE_1_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
        },
    },
    "circuit_2": {
        "string": "R_1-p(R_3-CPE_1,CPE_2,R_2)",
        "guess": [
            100,  # R_1 = R_c
            100,  # R_3 = R_i
            1e-5,  # CPE_1_0 = Q_DL
            0.6,  # CPE_1_1 = alpha_DL
            1e-4,  # CPE_2_0 = Q_g
            0.6,  # CPE_2_1 = alpha_g
            200000,  # R_2 = R_e
        ],
        "mapping": {
            "R_1": {
                "name": "R_c",
                "colour": "#69BC86",
                "order": 2,
            },
            "R_3": {
                "name": "R_i",
                "colour": "#80D4F8",
                "compute_conductivity": True,
                "order": 0,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
                "compute_conductivity": True,
                "order": 1,
            },
            "CPE_1_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_2_0": {
                "name": "Q_g",
                "colour": "#F49A80",
                "order": 1,
            },
            "CPE_1_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_2_1": {
                "name": "alpha_g",
                "colour": "#F49A80",
                "order": 1,
            },
        },
    },
    "circuit_3": {
        "string": "p(R_1,CPE_1)-p(R_2,CPE_2)-CPE_3",
        "guess": [
            100,  # R_1 = R_HF
            1e-6,  # CPE_1_0 = Q_HF
            0.5,  # CPE_1_1 = alpha_HF
            1500,  # R_2 = R_LF
            1e-5,  # CPE_2_0 = Q_LF
            0.6,  # CPE_2_1 = alpha_LF
            1e-4,  # CPE_3_0 = Q_DL
            0.4,  # CPE_3_1 = alpha_DL
        ],
        "mapping": {
            "R_1": {
                "name": "R_HF",
                "colour": "#80D4F8",
                "order": 0,
                "compute_conductivity": True,
            },
            "CPE_1_0": {
                "name": "Q_HF",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_HF",
                "colour": "#7C84C2",
                "order": 0,
            },
            "R_2": {
                "name": "R_LF",
                "colour": "#F37F8C",
                "order": 1,
                "compute_conductivity": True,
            },
            "CPE_2_0": {
                "name": "Q_LF",
                "colour": "#9A8DD8",
                "order": 1,
            },
            "CPE_2_1": {
                "name": "alpha_LF",
                "colour": "#9A8DD8",
                "order": 1,
            },
            "CPE_3_0": {
                "name": "Q_EP",
                "colour": "#9AD3A6",
                "order": 2,
            },
            "CPE_3_1": {
                "name": "alpha_EP",
                "colour": "#9AD3A6",
                "order": 2,
            },
        },
    },
    "circuit_4": {
        "string": "R_1-p(R_2,CPE_1)-p(R_3,CPE_2)-CPE_3",
        "guess": [
            10,  # R_1 = R_s
            100,  # R_2 = R_free
            1e-6,  # CPE_1_0 = Q_free
            0.9,  # CPE_1_1 = alpha_free
            1000,  # R_3 = R_tunnel
            1e-5,  # CPE_2_0 = Q_tunnel
            0.75,  # CPE_2_1 = alpha_tunnel
            1e-5,  # CPE_3_0 = Q_DL
            0.8,  # CPE_3_1 = alpha_DL
        ],
        "mapping": {
            "R_1": {
                "name": "R_s",
                "colour": "#666666",
                "order": 0,
                "use_for_conductivity": False,
            },
            "R_2": {
                "name": "R_free",
                "colour": "#80D4F8",
                "order": 1,
                "use_for_conductivity": True,
                "conductivity_type": "apparent_free_K",
            },
            "CPE_1_0": {
                "name": "Q_free",
                "colour": "#80D4F8",
                "order": 1,
            },
            "CPE_1_1": {
                "name": "alpha_free",
                "colour": "#80D4F8",
                "order": 1,
            },
            "R_3": {
                "name": "R_tunnel",
                "colour": "#7C84C2",
                "order": 2,
                "use_for_conductivity": True,
                "conductivity_type": "apparent_tunnel_K",
            },
            "CPE_2_0": {
                "name": "Q_tunnel",
                "colour": "#7C84C2",
                "order": 2,
            },
            "CPE_2_1": {
                "name": "alpha_tunnel",
                "colour": "#7C84C2",
                "order": 2,
            },
            "CPE_3_0": {
                "name": "Q_DL",
                "colour": "#F37F8C",
                "order": 3,
            },
            "CPE_3_1": {
                "name": "alpha_DL",
                "colour": "#F37F8C",
                "order": 3,
            },
        },
    },
    "circuit_5": {
        "string": "R_1-p(CPE_1,R_2)-p(CPE_2,R_3)",
        "guess": [
            1e2,  # R_1
            1e-4,  # CPE_1_0
            0.8,  # CPE_1_1
            1e3,  # R_2
            1e-3,  # CPE_2_0
            0.8,  # CPE_2_1
            1e4,  # R_3
        ],
        "mapping": {
            "R_1": {
                "name": "R_s",
                "colour": "#69BC86",
                "order": 0,
                "compute_conductivity": False,
            },
            "R_2": {
                "name": "R_1",
                "colour": "#80D4F8",
                "order": 1,
                "compute_conductivity": True,
            },
            "R_3": {
                "name": "R_2",
                "colour": "#F37F8C",
                "order": 2,
                "compute_conductivity": True,
            },
            "CPE_1_0": {"name": "Q_1", "colour": "#7C84C2", "order": 0},
            "CPE_1_1": {"name": "alpha_1", "colour": "#7C84C2", "order": 0},
            "CPE_2_0": {"name": "Q_2", "colour": "#B39DDB", "order": 1},
            "CPE_2_1": {"name": "alpha_2", "colour": "#B39DDB", "order": 1},
        },
    },
    "elec_1": {
        "string": "R_1-p(R_2,CPE_1)-CPE_2",
        "guess": [
            10,  # R_1 = R_i
            1000,  # R_2 = R_e
            1e-4,  # CPE_1_0 = Q_g
            0.3,  # CPE_1_1 = alpha_g
            1e-5,  # CPE_2_0 = Q_DL
            0.9,  # CPE_2_1 = alpha_DL
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
                "order": 0,
                "use_for_conductivity": False,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
                "order": 1,
                "use_for_conductivity": True,
                "compute_conductivity": True,
            },
            "CPE_1_0": {
                "name": "Q_g",
                "colour": "#F49A80",
                "order": 2,
            },
            "CPE_1_1": {
                "name": "alpha_g",
                "colour": "#F49A80",
                "order": 2,
            },
            "CPE_2_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 3,
            },
            "CPE_2_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 3,
            },
        },
    },
    "pseudo_Randles_DL": {
        "string": "p(R_1-p(R_2,CPE_1)-CPE_2,CPE_3)",
        "guess": [
            1e3,  # R_1 = R_i
            1e5,  # R_2 =R_bulk
            1e-8,  # CPE_1_0 = Q_bulk
            0.60,  # CPE_1_1 =alpha_bulk
            1e-7,  # CPE_2_0 = Q_DL
            0.70,  # CPE_2_1 = alpha_DL
            5e-11,  # CPE_3_0 = Q_HF / geometric or stray capacitance
            0.95,  # CPE_3_1 = alpha_HF
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
                "order": 0,
                "compute_conductivity": True,
            },
            "R_2": {
                "name": "R_bulk",
                "colour": "#F37F8C",
                "order": 1,
                "compute_conductivity": True,
            },
            "CPE_1_0": {
                "name": "Q_bulk",
                "colour": "#F49A80",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_bulk",
                "colour": "#F49A80",
                "order": 0,
            },
            "CPE_2_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 1,
            },
            "CPE_2_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 1,
            },
            "CPE_3_0": {
                "name": "Q_HF",
                "colour": "#69BC86",
                "order": 2,
            },
            "CPE_3_1": {
                "name": "alpha_HF",
                "colour": "#69BC86",
                "order": 2,
            },
        },
    },
    "ionic_1": {
        "string": "R_1-p(R_2,CPE_1)-CPE_2",
        "guess": [
            1e2,  # R_1 = R_i
            1e3,  # R_2 = R_bulk
            1e-4,  # CPE_1_0 = Q_bulk
            0.5,  # CPE_1_1 = alpha_bulk
            1e-5,  # CPE_2_0 = Q_DL
            0.9,  # CPE_2_1 = alpha_DL
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
                "order": 0,
                "compute_conductivity": True,
            },
            "R_2": {
                "name": "R_bulk",
                "colour": "#69BC86",
                "order": 1,
            },
            "CPE_1_0": {"name": "Q_bulk", "colour": "#F49A80", "order": 1},
            "CPE_1_1": {"name": "alpha_bulk", "colour": "#F49A80", "order": 1},
            "CPE_2_0": {"name": "Q_DL", "colour": "#7C84C2", "order": 2},
            "CPE_2_1": {"name": "alpha_DL", "colour": "#7C84C2", "order": 2},
        },
    },
    "series_R_CPE": {
        "string": "R_1-CPE_1",
        "guess": [
            1e3,  # R_1 = R_i / transport resistance
            1e-6,  # CPE_1_0 = Q
            0.8,  # CPE_1_1 = alpha
        ],
        "mapping": {
            "R_1": {
                "name": "R_total",
                "colour": "#80D4F8",
                "order": 0,
                "compute_conductivity": True,
            },
            "CPE_1_0": {
                "name": "Q_total",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_total",
                "colour": "#7C84C2",
                "order": 0,
            },
        },
    },
    "circuit_9": {
        "string": "R_1-p(R_2,CPE_1)-CPE_2",
        "guess": [
            50,  # R_1
            2000,  # R_2
            1e-6,  # CPE_1_0
            0.8,  # CPE_1_1
            1e-5,  # CPE_2_0
            0.8,  # CPE_2_1
        ],
        "mapping": {
            "R_1": {
                "name": "R_s",
                "colour": "#B0B0B0",
                "order": 0,
                "compute_conductivity": False,
            },
            "R_2": {
                "name": "R_i",
                "colour": "#80D4F8",
                "order": 1,
                "compute_conductivity": True,
            },
            "CPE_1_0": {
                "name": "Q_i",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_i",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_2_0": {
                "name": "Q_EP",
                "colour": "#F37F8C",
                "order": 1,
            },
            "CPE_2_1": {
                "name": "alpha_EP",
                "colour": "#F37F8C",
                "order": 1,
            },
        },
    },

    "MIEC_R_CPE_Re": {
        # Same topology as circuit_1 (p(R_1-CPE_1,R_2)); only the guess differs.
        "string": "p(R_1-CPE_1,R_2)",
        "guess": [
            600,  # R_1 = R_i, ~R_HF (high-frequency limit is R_i || R_e ~ R_i)
            1.5e-6,  # CPE_1_0 = Q_DL, from the 1 Hz imaginary part
            0.9,  # CPE_1_1 = alpha_DL, from the 1 Hz phase
            1e5,  # R_2 = R_e, ~|Z_LF|: start where chi^2 responds to R_e (not a bound)
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
                "compute_conductivity": True,
                "order": 0,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
                "compute_conductivity": True,
                "order": 1,
            },
            "CPE_1_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
        },
    },
    "Rs_MIEC": {
        # Fig. 5d: R_s in series with p(R_i-CPE_dl, R_e).
        "string": "R_1-p(R_2-CPE_1,R_3)",
        "guess": [
            100,  # R_1 = R_s (arbitrary ~1/6 split of R_HF; data cannot fix it)
            500,  # R_2 = R_i (R_s + R_i ~ R_HF)
            1.5e-6,  # CPE_1_0 = Q_DL
            0.9,  # CPE_1_1 = alpha_DL
            1e5,  # R_3 = R_e, ~|Z_LF|
        ],
        "mapping": {
            "R_1": {
                "name": "R_s",
                "colour": "#B0B0B0",
                "compute_conductivity": False,
                "order": 0,
            },
            "R_2": {
                "name": "R_i",
                "colour": "#80D4F8",
                "compute_conductivity": True,
                "order": 1,
            },
            "R_3": {
                "name": "R_e",
                "colour": "#F37F8C",
                "compute_conductivity": True,
                "order": 2,
            },
            "CPE_1_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
        },
    },
    "Randles_Cdl_W": {
        # Fig. 5c as drawn: ideal C_dl in parallel with R_CT in series with a
        # semi-infinite Warburg element (impedance.py "W", parameter in
        # ohm s^-1/2).
        "string": "R_1-p(C_1,R_2-W_1)",
        "guess": [
            600,  # R_1 = R_s, ~R_HF
            1.3e-6,  # C_1 = C_dl, from the 1 Hz imaginary part
            1e5,  # R_2 = R_CT, ~|Z_LF|
            2e5,  # W_1 = A_W, sets |Z_W(1 Hz)| ~ |Z_LF|
        ],
        "mapping": {
            "R_1": {
                "name": "R_s",
                "colour": "#B0B0B0",
                "compute_conductivity": True,
                "order": 0,
            },
            "C_1": {
                "name": "C_dl",
                "colour": "#9AD3A6",
                "order": 0,
            },
            "R_2": {
                "name": "R_CT",
                "colour": "#F37F8C",
                "compute_conductivity": False,
                "order": 1,
            },
            "W_1": {
                "name": "A_W",
                "colour": "#F49A80",
                "order": 0,
            },
        },
    },
    "Randles_CPE_W": {
        # Variant of Randles_Cdl_W with C_dl replaced by a CPE. Not drawn in
        # the figure; added because every other circuit here uses a CPE and
        # the 1 Hz phase implies alpha ~ 0.9, not 1.
        "string": "R_1-p(CPE_1,R_2-W_1)",
        "guess": [
            600,  # R_1 = R_s, ~R_HF
            1.5e-6,  # CPE_1_0 = Q_DL
            0.9,  # CPE_1_1 = alpha_DL
            1e5,  # R_2 = R_CT, ~|Z_LF|
            2e5,  # W_1 = A_W
        ],
        "mapping": {
            "R_1": {
                "name": "R_s",
                "colour": "#B0B0B0",
                "compute_conductivity": True,
                "order": 0,
            },
            "CPE_1_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "R_2": {
                "name": "R_CT",
                "colour": "#F37F8C",
                "compute_conductivity": False,
                "order": 1,
            },
            "W_1": {
                "name": "A_W",
                "colour": "#F49A80",
                "order": 0,
            },
        },
    },
}
