landuse_list = [
    "Airports",
    "Arable land (annual crops)",
    "Construction sites",
    "Continuous urban fabric (S.L. : > 80%)",
    "Discontinuous dense urban fabric (S.L. : 50% -  80%)",
    "Discontinuous low density urban fabric (S.L. : 10% - 30%)",
    "Discontinuous medium density urban fabric (S.L. : 30% - 50%)",
    "Discontinuous very low density urban fabric (S.L. : < 10%)",
    "Fast transit roads and associated land",
    "Forests",
    "Green urban areas",
    "Herbaceous vegetation associations (natural grassland, moors...)",
    "Industrial, commercial, public, military and private units",
    "Isolated structures",
    "Land without current use",
    "Mineral extraction and dump sites",
    "Open spaces with little or no vegetation (beaches, dunes, bare rocks, glaciers)",
    "Other roads and associated land",
    "Pastures",
    "Permanent crops (vineyards, fruit trees, olive groves)",
    "Port areas",
    "Railways and associated land",
    "Sports and leisure facilities",
    "Water",
    "Wetlands"
]

similar_map = {
    # --- urban region ---
    "Continuous urban fabric (S.L. : > 80%)": [
        "Discontinuous dense urban fabric (S.L. : 50% -  80%)",
        "Industrial, commercial, public, military and private units",
        "Isolated structures"
    ],
    "Discontinuous dense urban fabric (S.L. : 50% -  80%)": [
        "Continuous urban fabric (S.L. : > 80%)",
        "Discontinuous medium density urban fabric (S.L. : 30% - 50%)",
        "Industrial, commercial, public, military and private units"
    ],
    "Discontinuous medium density urban fabric (S.L. : 30% - 50%)": [
        "Discontinuous dense urban fabric (S.L. : 50% -  80%)",
        "Discontinuous low density urban fabric (S.L. : 10% - 30%)",
        "Isolated structures"
    ],
    "Discontinuous low density urban fabric (S.L. : 10% - 30%)": [
        "Discontinuous medium density urban fabric (S.L. : 30% - 50%)",
        "Discontinuous very low density urban fabric (S.L. : < 10%)",
        "Isolated structures"
    ],
    "Discontinuous very low density urban fabric (S.L. : < 10%)": [
        "Discontinuous low density urban fabric (S.L. : 10% - 30%)",
        "Isolated structures",
        "Land without current use"
    ],
    "Industrial, commercial, public, military and private units": [
        "Continuous urban fabric (S.L. : > 80%)",
        "Discontinuous dense urban fabric (S.L. : 50% -  80%)",
        "Construction sites"
    ],
    "Isolated structures": [
        "Discontinuous very low density urban fabric (S.L. : < 10%)",
        "Discontinuous low density urban fabric (S.L. : 10% - 30%)",
        "Land without current use"
    ],
    "Construction sites": [
        "Industrial, commercial, public, military and private units",
        "Isolated structures",
        "Land without current use"
    ],
    "Sports and leisure facilities": [
        "Green urban areas",
        "Isolated structures",
        "Discontinuous medium density urban fabric (S.L. : 30% - 50%)"
    ],
    "Green urban areas": [
        "Sports and leisure facilities",
        "Discontinuous very low density urban fabric (S.L. : < 10%)",
        "Pastures"
    ],
    # --- nature land cover ---
    "Forests": [
        "Herbaceous vegetation associations (natural grassland, moors...)",
        "Pastures",
        "Permanent crops (vineyards, fruit trees, olive groves)"
    ],
    "Herbaceous vegetation associations (natural grassland, moors...)": [
        "Forests",
        "Pastures",
        "Arable land (annual crops)"
    ],
    "Pastures": [
        "Herbaceous vegetation associations (natural grassland, moors...)",
        "Arable land (annual crops)",
        "Permanent crops (vineyards, fruit trees, olive groves)"
    ],
    "Arable land (annual crops)": [
        "Pastures",
        "Permanent crops (vineyards, fruit trees, olive groves)",
        "Herbaceous vegetation associations (natural grassland, moors...)"
    ],
    "Permanent crops (vineyards, fruit trees, olive groves)": [
        "Arable land (annual crops)",
        "Pastures",
        "Forests"
    ],
    "Water": [
        "Wetlands",
        "Port areas",
        "Open spaces with little or no vegetation (beaches, dunes, bare rocks, glaciers)"
    ],
    "Wetlands": [
        "Water",
        "Forests",
        "Herbaceous vegetation associations (natural grassland, moors...)"
    ],
    # --- build up ---
    "Airports": [
        "Industrial, commercial, public, military and private units",
        "Fast transit roads and associated land",
        "Railways and associated land"
    ],
    "Port areas": [
        "Water",
        "Industrial, commercial, public, military and private units",
        "Railways and associated land"
    ],
    "Railways and associated land": [
        "Fast transit roads and associated land",
        "Other roads and associated land",
        "Industrial, commercial, public, military and private units"
    ],
    "Fast transit roads and associated land": [
        "Other roads and associated land",
        "Railways and associated land",
        "Airports"
    ],
    "Other roads and associated land": [
        "Fast transit roads and associated land",
        "Railways and associated land",
        "Construction sites"
    ],
    # --- bare land ---
    "Land without current use": [
        "Isolated structures",
        "Construction sites",
        "Open spaces with little or no vegetation (beaches, dunes, bare rocks, glaciers)"
    ],
    "Mineral extraction and dump sites": [
        "Construction sites",
        "Land without current use",
        "Open spaces with little or no vegetation (beaches, dunes, bare rocks, glaciers)"
    ],
    "Open spaces with little or no vegetation (beaches, dunes, bare rocks, glaciers)": [
        "Land without current use",
        "Mineral extraction and dump sites",
        "Water"
    ]
}
