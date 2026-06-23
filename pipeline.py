import pymysql
import os
from config import get_db_connection

def parse_genetic_file(file_path):
    variants = []
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.vcf':
        variants = parse_vcf_file(file_path)
    else:
        variants = parse_txt_file(file_path)
    
    return variants

def parse_txt_file(file_path):
    variants = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    gene = parts[0].strip()
                    mutation = parts[1].strip()
                    variants.append((gene, mutation))
    return variants

def parse_vcf_file(file_path):
    variants = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip header lines
            if line.startswith('#'):
                continue
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 5:
                continue
            
            chrom = parts[0]
            pos = parts[1]
            ref = parts[3]
            alt = parts[4]
            info = parts[7] if len(parts) > 7 else ''
            
            # Try to extract gene name from INFO field
            # Try to extract gene name from INFO field
            gene = None
            for field in info.split(';'):
                field = field.strip()
                if '=' in field:
                    key, val = field.split('=', 1)
                    key = key.strip().upper()
                    if key == 'GENE':
                        gene = val.strip()
                        break
                    elif key == 'GENEINFO':
                        gene = val.split(':')[0].strip()
                        break
            
            # If no gene found in INFO, use chromosome as identifier
            if not gene:
                gene = f"CHR{chrom}"
            
            print(f"Parsed VCF variant: gene={gene}, ref={ref}, alt={alt}")
            
            # Build mutation string in ClinVar-like format
            mutation = f"{ref}>{alt} (pos:{pos})"
            
            variants.append((gene, mutation))
    
    return variants

def match_with_database(variants):
    connection = get_db_connection()
    cursor = connection.cursor()
    results = []
    for gene, mutation in variants:
        cursor.execute(
            "SELECT gene, mutation, disease, clinical_significance, risk_level FROM gene_disease WHERE gene = %s AND mutation LIKE %s",
            (gene, f'%{mutation}%')
        )
        matches = cursor.fetchall()
        
        # If no exact match, try matching by gene only
        if not matches:
            cursor.execute(
                "SELECT gene, mutation, disease, clinical_significance, risk_level FROM gene_disease WHERE gene = %s LIMIT 1",
                (gene,)
            )
            matches = cursor.fetchall()
        
        if matches:
            for match in matches:
                results.append({
                    'gene': match[0],
                    'mutation': match[1],
                    'disease': match[2],
                    'clinical_significance': match[3],
                    'risk_level': match[4]
                })
        else:
            results.append({
                'gene': gene,
                'mutation': mutation,
                'disease': 'No match found in database',
                'clinical_significance': 'Unknown',
                'risk_level': 'LOW'
            })
    cursor.close()
    connection.close()
    return results

def save_results(results, report_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    for result in results:
        cursor.execute(
            "INSERT INTO analysis_results (report_id, gene, mutation, disease, risk_level) VALUES (%s, %s, %s, %s, %s)",
            (report_id, result['gene'], result['mutation'], result['disease'], result['risk_level'])
        )
    connection.commit()
    cursor.close()
    connection.close()

def run_pipeline(file_path, report_id):
    print(f"Running pipeline for report {report_id}")
    ext = os.path.splitext(file_path)[1].lower()
    print(f"File type detected: {ext}")
    variants = parse_genetic_file(file_path)
    print(f"Parsed {len(variants)} variants from file")
    results = match_with_database(variants)
    print(f"Matched {len(results)} results")
    save_results(results, report_id)
    print("Pipeline complete!")
    return results