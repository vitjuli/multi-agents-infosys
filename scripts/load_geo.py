import geopandas as gpd
import matplotlib.pyplot as plt

# Path to your GeoJSON file
path = "data/raw/ons_lad_boundaries_dec2024_buc.geojson"

# Load the GeoJSON
gdf = gpd.read_file(path)

# Display basic contents
print(gdf.head())
print()
print("Columns:")
print(gdf.columns)
print()
print("CRS:")
print(gdf.crs)

# Plot the boundaries
gdf.plot(figsize=(8, 8), edgecolor="black", linewidth=0.2)
plt.title("GeoJSON Boundaries")
plt.axis("off")
plt.show()