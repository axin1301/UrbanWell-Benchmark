import pandas as pd
import json

with open("europe-cities-by-population-2025.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

df_max = df.loc[df.groupby("country")["population"].idxmax()].reset_index(drop=True)

df_max.to_csv("outputs/city_selection/largest_city_per_country.csv", index=False, encoding="utf-8")

print(df_max)
