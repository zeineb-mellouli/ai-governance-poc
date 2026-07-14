import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# ARCH-12 violation 1: reads from bronze (good), but will write output
# back into the same bronze folder (overwrites immutable source layer)
df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")
print("Data loaded:")
print(df)
print("Shape:", df.shape)

# Also load customer data for enrichment
customers = pd.read_csv("data/customers.csv")
print("\nCustomer list:")
print(customers)

# Connect to database - password hardcoded directly in script
connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"
api_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"

# No quality checks before processing (DQ-1 + ARCH-12 violations)
avg_price = df["val"].mean()
print("\nAverage price:", avg_price)

total_vol = df["vol"].sum()
print("Total volume:", total_vol)

# Train a model - no random_state set anywhere (REPRO-6 violation)
X = df[["id", "vol"]].values
y = df["val"].values

X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!

model = LinearRegression()
model.fit(X_train, y_train)
print("\nModel trained")
print("Score:", model.score(X_test, y_test))

df["predicted_val"] = model.predict(X)

# ARCH-12 violation 1: writing processed output BACK to bronze (must be immutable)
df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)
print("Saved back to bronze (overwrote raw source!)")

# ARCH-12 violation 2: no silver layer exists anywhere -- bronze jumps straight
# to a reporting dump with zero validation or aggregation in between
df.to_csv("data/output final.csv")
print("\nDone! Results saved to data/ (no gold layer, no silver layer).")
