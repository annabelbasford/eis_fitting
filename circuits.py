CIRCUITS = {
    "circuit_1": {
        "string": "p(R_1-CPE_1,R_2)",
        "guess": [
            100,
            1e-6,
            0.9,
            1000,
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
                "order": 0,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
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
            20,
            750,
            1e-5,
            0.9,
            1e-4,
            0.7,
            200,
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
                "order": 0,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
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
    "elec_1": {
        "string": "R_1-p(R_2,CPE_1)-CPE_2",
        "guess": [
            10,  # R_1 = R_i
            1000,  # R_2 = R_PEDOT
            1e-6,  # CPE_1_0 = Q_g
            0.8,  # CPE_1_1 = alpha_g
            1e-5,  # CPE_2_0 = Q_DL
            0.7,  # CPE_2_1 = alpha_DL
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#666666",
                "order": 0,
                "use_for_conductivity": False,
            },
            "R_2": {
                "name": "R_PEDOT",
                "colour": "#F37F8C",
                "order": 1,
                "use_for_conductivity": True,
                "conductivity_type": "apparent_PEDOT_network",
            },
            "CPE_1_0": {
                "name": "Q_g",
                "colour": "#7C84C2",
                "order": 2,
            },
            "CPE_1_1": {
                "name": "alpha_g",
                "colour": "#7C84C2",
                "order": 2,
            },
            "CPE_2_0": {
                "name": "Q_DL",
                "colour": "#B68D40",
                "order": 3,
            },
            "CPE_2_1": {
                "name": "alpha_DL",
                "colour": "#B68D40",
                "order": 3,
            },
        },
    },
    "ionic_1": {
        "string": "R_1-p(R_2,CPE_1)-CPE_2",
        "guess": [
            10,  # R_1 = R_s
            1e4,  # R_2 = R_i
            1e-9,  # CPE_1_0 = Q_bulk
            0.9,  # CPE_1_1 = alpha_bulk
            1e-5,  # CPE_2_0 = Q_DL
            0.8,  # CPE_2_1 = alpha_DL
        ],
        "mapping": {
            "R_1": {"name": "R_s", "colour": "#666666", "order": 0},
            "R_2": {"name": "R_i", "colour": "#7C84C2", "order": 1},
            "CPE_1_0": {"name": "Q_bulk", "colour": "#80D4F8", "order": 1},
            "CPE_1_1": {"name": "alpha_bulk", "colour": "#80D4F8", "order": 1},
            "CPE_2_0": {"name": "Q_ep", "colour": "#F37F8C", "order": 2},
            "CPE_2_1": {"name": "alpha_ep", "colour": "#F37F8C", "order": 2},
        },
    },
    "pseudo_randles_DL": {
        "string": "R_1-p(CPE_1,R_2-CPE_2)-p(CPE_3,R_3)",
        "guess": [
            20,  # R_1
            1e-5,  # CPE_1_0
            0.9,  # CPE_1_1
            1000,  # R_2
            1e-4,  # CPE_2_0
            0.6,  # CPE_2_1
            1e-5,  # CPE_3_0
            0.9,  # CPE_3_1
            1000,  # R_3
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
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
                "name": "R_T",
                "colour": "#F37F8C",
                "order": 1,
            },
            "CPE_2_0": {
                "name": "Q_T",
                "colour": "#B39DDB",
                "order": 1,
            },
            "CPE_2_1": {
                "name": "alpha_T",
                "colour": "#B39DDB",
                "order": 1,
            },
            "CPE_3_0": {
                "name": "Q_LF",
                "colour": "#9AD0A3",
                "order": 2,
            },
            "CPE_3_1": {
                "name": "alpha_LF",
                "colour": "#9AD0A3",
                "order": 2,
            },
            "R_3": {
                "name": "R_LF",
                "colour": "#F4A261",
                "order": 2,
            },
        },
    },
}
