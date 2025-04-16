# app.py - Flask web application for variant annotation pipeline
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import subprocess
import pandas as pd
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "variant_annotation_secret_key"

# Create necessary directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

ALLOWED_EXTENSIONS = {'fastq', 'fastq.gz', 'fq', 'fq.gz'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS or \
           filename.endswith('.fastq.gz') or filename.endswith('.fq.gz')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if files were uploaded
        if 'fastq_files' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        files = request.files.getlist('fastq_files')
        
        # Check if file selection is empty
        if not files or files[0].filename == '':
            flash('No selected files')
            return redirect(request.url)
        
        # Process each file
        file_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                file.save(file_path)
                file_paths.append(file_path)
            else:
                flash(f'Invalid file type: {file.filename}. Only FASTQ files are allowed.')
                return redirect(request.url)
        
        # Generate a unique ID for this run
        run_id = f"run_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        result_dir = os.path.join('results', run_id)
        os.makedirs(result_dir, exist_ok=True)
        
        try:
            # Run the variant calling pipeline
            result_file = run_variant_pipeline(file_paths, result_dir)
            
            # Return the annotated Excel file
            return send_file(
                result_file,
                as_attachment=True,
                download_name=f"annotated_variants_{run_id}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            flash(f"Error processing files: {str(e)}")
            return redirect(request.url)
    
    return render_template('index.html')

def clean_annovar_csv(input_csv, output_csv):
    """Clean Annovar CSV file by removing VCF header lines."""
    with open(input_csv, 'r') as infile, open(output_csv, 'w') as outfile:
        # Get the header line
        header = infile.readline()
        outfile.write(header)
        
        # Process the rest of the file
        for line in infile:
            if not line.startswith('##'):
                outfile.write(line)
    
    return output_csv

def run_variant_pipeline(fastq_files, output_dir):
    """Run the complete variant calling and annotation pipeline"""
    
    # Step 1: Align FASTQ files to reference genome using BWA
    bam_file = os.path.join(output_dir, "aligned.bam")
    ref_genome = "/app/reference/hg38.fa"  # Path in Docker container
    
    # Join multiple FASTQ files if needed
    fastq_param = " ".join(fastq_files)
    
    # BWA alignment command
    bwa_cmd = f"bwa mem {ref_genome} {fastq_param} | samtools sort -o {bam_file}"
    subprocess.run(bwa_cmd, shell=True, check=True)
    
    # Index BAM file
    subprocess.run(f"samtools index {bam_file}", shell=True, check=True)
    
    # Step 2: Variant calling with FreeBayes
    vcf_file = os.path.join(output_dir, "variants.vcf")
    freebayes_cmd = f"freebayes -f {ref_genome} {bam_file} > {vcf_file}"
    subprocess.run(freebayes_cmd, shell=True, check=True)
    
    # Step 3: Normalize and decompose variants with vt
    normalized_vcf = os.path.join(output_dir, "normalized.vcf")
    bcftools_cmd = f"bcftools norm -m-any {vcf_file} | bcftools norm -f {ref_genome} -o {normalized_vcf}"
    subprocess.run(bcftools_cmd, shell=True, check=True)
    
    # Step 4: Annotate variants with Annovar
    annovar_output = os.path.join(output_dir, "annotated")
    annovar_cmd = f"table_annovar.pl {normalized_vcf} /app/annovar/humandb/ -buildver hg38 -out {annovar_output} -remove -protocol refGene,exac03,avsnp147,dbnsfp30a -operation g,f,f,f -nastring . -csvout"
    subprocess.run(annovar_cmd, shell=True, check=True)
    

    csv_file = f"{annovar_output}.hg38_multianno.csv"
    clean_csv_file = f"{annovar_output}.clean.csv"
    clean_csv_file = clean_annovar_csv(csv_file, clean_csv_file)

    excel_file = os.path.join(output_dir, "annotated_variants.xlsx")
    
    # Read the CSV and create an Excel file with formatting
    df = pd.read_csv(clean_csv_file)
    
    # Add some basic filtering and statistics
    df['ExAC_AF'] = pd.to_numeric(df['ExAC_ALL'], errors='coerce')
    
    # Create Excel writer
    with pd.ExcelWriter(excel_file) as writer:
        # Write main variant sheet
        df.to_excel(writer, sheet_name='All Variants', index=False)
        
        # Create filtered sheets
        df[df['Func.refGene'] == 'exonic'].to_excel(writer, sheet_name='Exonic Variants', index=False)
        rare_variants = df[df['ExAC_AF'] < 0.01].copy()
        rare_variants.to_excel(writer, sheet_name='Rare Variants (AF<1%)', index=False)
        
        # Create summary sheet
        summary = pd.DataFrame({
            'Category': ['Total variants', 'Exonic variants', 'Rare variants (AF<1%)', 
                        'Nonsynonymous SNVs', 'Stopgain/Stoploss'],
            'Count': [
                len(df),
                len(df[df['Func.refGene'] == 'exonic']),
                len(df[df['ExAC_AF'] < 0.01]),
                len(df[df['ExonicFunc.refGene'].str.contains('nonsynonymous', na=False)]),
                len(df[df['ExonicFunc.refGene'].str.contains('stop', na=False)])
            ]
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
    
    return excel_file

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)