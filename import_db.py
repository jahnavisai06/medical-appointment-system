import pymysql
import pandas as pd

conn = pymysql.connect(
    host='shuttle.proxy.rlwy.net',
    port=55435,
    user='root',
    password='URtjxXFbMPUmEKdkFnBpTQukeZfMHrSI',
    database='railway',
    connect_timeout=60,
    read_timeout=300,
    write_timeout=300
)
cursor = conn.cursor()

df = pd.read_csv('clinvar_500.csv')
print(f"Importing {len(df)} rows...")

for i, row in df.iterrows():
    try:
        cursor.execute(
            "INSERT INTO gene_disease (gene, mutation, disease, clinical_significance, risk_level) VALUES (%s, %s, %s, %s, %s)",
            (str(row['GeneSymbol'])[:50], str(row['Name'])[:255], str(row['PhenotypeList'])[:255], str(row['ClinicalSignificance'])[:50], str(row['risk_level'])[:10])
        )
        if i % 50 == 0:
            conn.commit()
            print(f"Progress: {i}/500")
    except Exception as e:
        print(f"Failed row {i}: {e}")

conn.commit()
cursor.close()
conn.close()
print("Done!")