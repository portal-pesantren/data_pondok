import pandas as pd

jateng = "Data_emis/Nasional/jawatengah/pontren.json"
df = pd.read_json(jateng)
df.to_excel("testing/jawatengah/pontren.xlsx")
print("Conversion complete!")